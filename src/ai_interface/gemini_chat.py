from typing import List, Dict
import google.generativeai as genai
import time
from ..data_processing.pipeline import DataProcessingPipeline
from ..data_processing.logger_config import setup_logger

class GeminiTutor:
    def __init__(
        self,
        api_keys: List[str],  # Now accepts a list of API keys
        pipeline: DataProcessingPipeline,
        model_name: str = "gemini-1.5-pro"
    ):
        self.logger = setup_logger('gemini_tutor')
        self.pipeline = pipeline
        self.current_file = None
        self.last_request_time = 0
        self.min_request_interval = 2.0
        self.retry_count = 0
        self.max_retries = 3
        
        # Store API keys and their status
        self.api_keys = [
            {"key": key, "quota_limited": False, "last_used": 0} 
            for key in api_keys if key
        ]
        self.current_key_index = 0
        
        if not self.api_keys:
            raise ValueError("No valid API keys provided")
            
        try:
            self._initialize_model()
            self.logger.info(f"Initialized Gemini model: {model_name}")
        except Exception as e:
            self.logger.error(f"Failed to initialize Gemini model: {str(e)}")
            raise

    def _initialize_model(self):
        """Initialize model with current API key"""
        if not self.api_keys:
            raise ValueError("No API keys available")
            
        key_info = self.api_keys[self.current_key_index]
        genai.configure(api_key=key_info["key"])
        self.model = genai.GenerativeModel('gemini-1.5-pro')
        key_info["last_used"] = time.time()

    def _switch_api_key(self):
        """Switch to next available API key"""
        original_index = self.current_key_index
        
        while True:
            # Move to next key
            self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
            
            # Check if we've tried all keys
            if self.current_key_index == original_index:
                if all(k["quota_limited"] for k in self.api_keys):
                    raise Exception("All API keys have reached their quota limit")
                break
                
            # If this key isn't quota limited, use it
            if not self.api_keys[self.current_key_index]["quota_limited"]:
                break
        
        self._initialize_model()
        self.logger.info(f"Switched to API key {self.current_key_index + 1}")

    def _handle_api_error(self, error: Exception):
        """Handle API-related errors and switch keys if needed"""
        error_msg = str(error)
        current_key = self.api_keys[self.current_key_index]
        
        if "quota" in error_msg.lower():
            current_key["quota_limited"] = True
            self.logger.warning(f"API key {self.current_key_index + 1} has reached quota limit")
            
            try:
                self._switch_api_key()
                return True  # Switched successfully
            except Exception as e:
                self.logger.error(f"Failed to switch API key: {str(e)}")
                return False
                
        return False  # Not a quota error

    def set_current_file(self, file_path: str):
        """Set the current file being worked with"""
        self.current_file = file_path
        self.logger.info(f"Set current file to: {file_path}")

    def get_context(self, query: str, max_chunks: int = 5) -> str:
        """Retrieve relevant context from vector store"""
        try:
            # Create filter for current file if set
            filter_criteria = None
            if self.current_file:
                filter_criteria = {"file_path": self.current_file}
                self.logger.info(f"Searching with filter for file: {self.current_file}")
            
            results = self.pipeline.search_content(query, filter_criteria, top_k=max_chunks)
            
            # Handle ChromaDB results
            if isinstance(results, dict):
                # ChromaDB returns a dictionary with 'documents' key containing list of texts
                documents = results.get('documents', [])
                if documents and isinstance(documents, list):
                    # Flatten if documents is a list of lists
                    if documents and isinstance(documents[0], list):
                        documents = [doc for sublist in documents for doc in sublist]
                    context = "\n\n".join(documents)
                else:
                    context = ""
            else:
                # Handle Pinecone results
                context = "\n\n".join([match.metadata.get('text', '') for match in results])
            
            self.logger.debug(f"Retrieved context length: {len(context)}")
            return context
            
        except Exception as e:
            self.logger.error(f"Error retrieving context: {str(e)}")
            raise

    def _handle_rate_limit(self):
        """Implement rate limiting with exponential backoff"""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        
        # Calculate wait time with exponential backoff
        wait_time = self.min_request_interval * (2 ** self.retry_count)
        
        if time_since_last_request < wait_time:
            sleep_duration = wait_time - time_since_last_request
            self.logger.info(f"Rate limiting: waiting {sleep_duration:.2f} seconds")
            time.sleep(sleep_duration)
            
        self.last_request_time = time.time()

    def _select_teaching_strategy(self, topic: str, context: str) -> str:
        """Select the best teaching strategy based on topic and context"""
        try:
            # First check for explicit quiz or diagram requests
            topic_lower = topic.lower()
            if any(quiz_term in topic_lower for quiz_term in ['quiz', 'test', 'question', 'practice']):
                self.logger.info(f"Quiz request detected in topic: {topic}")
                return 4  # Quiz strategy
            
            if any(diagram_term in topic_lower for diagram_term in [
                'diagram', 'flowchart', 'sequence diagram', 'class diagram',
                'architecture', 'process flow', 'workflow', 'structure'
            ]):
                self.logger.info(f"Diagram request detected in topic: {topic}")
                return 6  # Diagram strategy

            prompt = f"""Analyze this topic and select the best teaching strategy.
            Choose between:
            1. Explanation (for conceptual topics)
            2. Examples (for practical topics)
            3. Step-by-step (for processes)
            4. Q&A Format (for testing understanding)
            5. Analogies (for complex topics)
            6. Visual Diagram (for processes, structures, or relationships)

            Topic: {topic}
            Context: {context}

            Consider:
            - If the topic asks for practice or testing, choose 4 (Q&A)
            - If the topic involves procedures or methods, choose 3 (Step-by-step)
            - If the topic is theoretical or abstract, choose 1 (Explanation)
            - If the topic needs real-world application, choose 2 (Examples)
            - If the topic is complex or technical, choose 5 (Analogies)
            - If the topic involves processes, structures, or relationships, choose 6 (Visual Diagram)

            Return ONLY the strategy number and a brief reason why.
            Format: <number>: <reason>"""

            response = self.model.generate_content(prompt)
            strategy_text = response.text.strip()
            
            # Extract strategy number
            strategy_num = int(strategy_text.split(':')[0])
            self.logger.info(f"Selected teaching strategy {strategy_num} for topic: {topic}")
            
            return strategy_num
            
        except Exception as e:
            self.logger.error(f"Error selecting teaching strategy: {str(e)}")
            return 1  # Default to explanation strategy

    def _get_strategy_prompt(self, strategy: int, topic: str, context: str) -> str:
        """Get the prompt for the selected teaching strategy"""
        strategy_prompts = {
            1: f"""Explain this topic clearly and thoroughly:
                - Start with a clear definition
                - Break down complex concepts
                - Use simple language
                
                Topic: {topic}
                Context: {context}""",
                
            2: f"""Explain this topic using practical examples:
                - Start with a brief overview
                - Provide 2-3 concrete examples
                - Explain how each example illustrates the concept
                
                Topic: {topic}
                Context: {context}""",
                
            3: f"""Break down this topic into clear steps:
                - List each step in sequence
                - Explain each step briefly
                - Connect the steps logically
                
                Topic: {topic}
                Context: {context}""",
                
            4: f"""Create an interactive quiz about this topic.
                Format the response in this exact JSON structure:
                {{
                    "topic": "Topic Title",
                    "questions": [
                        {{
                            "question": "Clear, concise question?",
                            "options": ["Option A", "Option B", "Option C", "Option D"],
                            "correct_answer": "Correct option exactly as written above",
                            "explanation": "Brief explanation of the correct answer"
                        }}
                    ]
                }}

                Rules:
                - Create exactly 5 questions
                - Keep questions clear and concise
                - Each question must have exactly 4 options
                - Ensure correct_answer matches one option exactly
                - Questions should test understanding, not memorization
                - Use the context provided to create relevant questions
                
                Topic: {topic}
                Context: {context}""",
                
            5: f"""Explain this topic using analogies:
                - Start with a simple overview
                - Use familiar analogies
                - Connect the analogy to the concept
                
                Topic: {topic}
                Context: {context}""",

            6: f"""Create a Mermaid diagram to visualize this topic.
                First, analyze the topic and choose the most appropriate diagram type:
                1. Flowchart (for processes and workflows)
                2. Sequence diagram (for interactions and message flows)
                3. Class diagram (for structure and relationships)

                Then, create a Mermaid diagram code block that clearly represents the topic.
                Include a brief explanation before the diagram.

                Format your response like this:
                Brief explanation of what the diagram shows...

                ```mermaid
                [Your Mermaid diagram code here]
                ```

                Guidelines:
                - Keep the diagram clear and focused
                - Use meaningful labels and descriptions
                - Show relationships and connections clearly
                - Include a legend or explanation if needed
                - For flowcharts, use TD (top-down) direction
                - For sequence diagrams, show clear actor interactions
                - For class diagrams, show important relationships

                Topic: {topic}
                Context: {context}"""
        }
        
        return strategy_prompts.get(strategy, strategy_prompts[1])

    def _generate_response(self, topic: str, context: str, strategy: int) -> str:
        """Generate a response using the selected teaching strategy"""
        try:
            if strategy == 4:  # Quiz strategy
                prompt = self._get_strategy_prompt(strategy, topic, context)
                response = self.model.generate_content(prompt)
                return response.text.strip()
            elif strategy == 6:  # Diagram strategy
                prompt = self._get_strategy_prompt(strategy, topic, context)
                response = self.model.generate_content(prompt)
                # Ensure the response contains a Mermaid diagram
                if "```mermaid" not in response.text:
                    # Extract the diagram code
                    lines = response.text.strip().split('\n')
                    diagram_lines = []
                    is_class_diagram = False
                    
                    for line in lines:
                        if line.strip().startswith('class '):
                            is_class_diagram = True
                        diagram_lines.append(line)
                    
                    # Add appropriate header based on content
                    if is_class_diagram:
                        diagram_code = "classDiagram\n" + "\n".join(diagram_lines)
                    else:
                        diagram_code = "graph TD\n" + "\n".join(diagram_lines)
                    
                    return f"Here's a diagram to explain {topic}:\n\n```mermaid\n{diagram_code}\n```"
                return response.text.strip()
            else:
                # Other strategies remain unchanged
                strategy_prompts = {
                    1: "Explain this topic clearly and concisely:",
                    2: "Provide practical examples of this topic:",
                    3: "Explain this topic step by step:",
                    5: "Explain this topic using analogies:"
                }
                
                prompt = f"""{strategy_prompts.get(strategy, strategy_prompts[1])}
                Topic: {topic}
                Context: {context}
                """
                
                response = self.model.generate_content(prompt)
                return response.text.strip()
                
        except Exception as e:
            self.logger.error(f"Error generating response: {str(e)}")
            return f"I apologize, but I encountered an error while generating the response: {str(e)}"

    def chat(self, query: str, context: str = "") -> str:
        """Generate response using Gemini with context and teaching strategy"""
        try:
            if not context:
                return "I couldn't find any relevant information in the documents to answer your question."
            
            while self.retry_count < self.max_retries:
                try:
                    self._handle_rate_limit()
                    
                    # Extract the topic and get strategy
                    topic = query.replace("Teach me about:", "").strip()
                    
                    # Force quiz strategy if it's a quiz request
                    if any(term in query.lower() for term in ['quiz', 'test me', 'practice questions']):
                        strategy = 4
                        self.logger.info("Forcing quiz strategy based on request")
                    else:
                        strategy = self._select_teaching_strategy(topic, context)
                    
                    try:
                        response = self._generate_response(topic, context, strategy)
                        if response:
                            if strategy == 4:
                                # Ensure quiz response is properly formatted
                                if not response.startswith('```json'):
                                    response = f"```json\n{response}\n```"
                                self.logger.info("Generated quiz response")
                            self.retry_count = 0
                            return response
                        else:
                            raise ValueError("Empty response from model")
                            
                    except Exception as e:
                        if self._handle_api_error(e):
                            continue  # Try again with new API key
                        raise
                        
                except Exception as e:
                    error_msg = str(e)
                    if "Rate limit exceeded" in error_msg:
                        self.retry_count += 1
                        if self.retry_count >= self.max_retries:
                            return ("I apologize, but I'm currently experiencing high traffic. "
                                   "Please try again in a few minutes.")
                        continue
                    else:
                        self.logger.error(f"Error generating response: {error_msg}")
                        raise
                
        except Exception as e:
            self.logger.error(f"Error in chat: {str(e)}")
            return "I encountered an error while processing your request. Please try again in a moment." 