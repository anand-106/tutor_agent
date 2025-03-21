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
            prompt = f"""Analyze this topic and select the best teaching strategy.
            Choose between:
            1. Explanation (for conceptual topics)
            2. Examples (for practical topics)
            3. Step-by-step (for processes)
            4. Q&A Format (for testing understanding)
            5. Analogies (for complex topics)

            Topic: {topic}
            Context: {context}

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
                Context: {context}"""
        }
        
        return strategy_prompts.get(strategy, strategy_prompts[1])

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
                    strategy = self._select_teaching_strategy(topic, context)
                    
                    # Get prompt for strategy
                    prompt = self._get_strategy_prompt(strategy, topic, context)
                    
                    try:
                        response = self.model.generate_content(prompt)
                        if response and response.text:
                            self.retry_count = 0
                            return response.text
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