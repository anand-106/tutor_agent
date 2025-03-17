from typing import List, Dict
from ..data_processing.pipeline import DataProcessingPipeline
from ..data_processing.logger_config import setup_logger
from .agents.topic_agent import TopicAgent
from .agents.quiz_agent import QuizAgent
from .agents.diagram_agent import DiagramAgent
from .agents.explainer_agent import ExplainerAgent
from .agents.flashcard_agent import FlashcardAgent
from .agents.knowledge_tracking_agent import KnowledgeTrackingAgent
from .agents.tutor_agent import TutorAgent
import json

class GeminiTutor:
    def __init__(
        self,
        api_keys: List[str],
        pipeline: DataProcessingPipeline,
        model_name: str = "gemini-1.5-pro"
    ):
        self.logger = setup_logger('gemini_tutor')
        self.pipeline = pipeline
        self.current_file = None
        
        # Initialize the main tutor agent that coordinates all other agents
        self.tutor_agent = TutorAgent(api_keys)
        
        # Keep references to individual agents for direct access if needed
        self.topic_agent = self.tutor_agent.topic_agent
        self.quiz_agent = self.tutor_agent.quiz_agent
        self.diagram_agent = self.tutor_agent.diagram_agent
        self.explainer_agent = self.tutor_agent.explainer_agent
        self.flashcard_agent = self.tutor_agent.flashcard_agent
        self.knowledge_tracking_agent = self.tutor_agent.knowledge_tracking_agent
        
        self.logger.info("Initialized Gemini Tutor with main tutor agent")

    def set_current_file(self, file_path: str):
        """Set the current file being worked with"""
        self.current_file = file_path
        self.logger.info(f"Set current file to: {file_path}")

    def get_context(self, query: str, max_chunks: int = 5) -> str:
        """Retrieve relevant context from vector store"""
        try:
            filter_criteria = None
            if self.current_file:
                filter_criteria = {"file_path": self.current_file}
                self.logger.info(f"Searching with filter for file: {self.current_file}")
            
            results = self.pipeline.search_content(query, filter_criteria, top_k=max_chunks)
            
            if isinstance(results, dict):
                documents = results.get('documents', [])
                if documents and isinstance(documents, list):
                    if documents and isinstance(documents[0], list):
                        documents = [doc for sublist in documents for doc in sublist]
                    context = "\n\n".join(documents)
                else:
                    context = ""
            else:
                context = "\n\n".join([match.metadata.get('text', '') for match in results])
            
            self.logger.debug(f"Retrieved context length: {len(context)}")
            return context
            
        except Exception as e:
            self.logger.error(f"Error retrieving context: {str(e)}")
            raise

    def set_lesson_plan(self, lesson_plan: Dict) -> None:
        """
        Set the current lesson plan for the tutor agent to teach.
        
        Args:
            lesson_plan: The lesson plan to teach
        """
        self.tutor_agent.set_lesson_plan(lesson_plan)
        self.logger.info(f"Set lesson plan: {lesson_plan.get('title', 'Untitled')}")

    def track_user_interaction(self, user_id: str, interaction_data: Dict) -> Dict:
        """
        Track user interaction and update knowledge model
        
        Args:
            user_id: Unique identifier for the user
            interaction_data: Data about the interaction (quiz results, study session, etc.)
            
        Returns:
            Dict containing updated knowledge metrics
        """
        try:
            self.logger.info(f"Tracking interaction for user {user_id}: {interaction_data.get('type', 'unknown')}")
            result = self.knowledge_tracking_agent.process(user_id, interaction_data)
            return result
        except Exception as e:
            self.logger.error(f"Error tracking user interaction: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    def get_user_knowledge_summary(self, user_id: str) -> Dict:
        """Get a summary of the user's knowledge across all topics"""
        try:
            self.logger.info(f"Getting knowledge summary for user {user_id}")
            return self.knowledge_tracking_agent.get_user_knowledge_summary(user_id)
        except Exception as e:
            self.logger.error(f"Error getting user knowledge summary: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    def get_topic_progress(self, user_id: str, topic: str) -> Dict:
        """Get detailed progress for a specific topic"""
        try:
            self.logger.info(f"Getting topic progress for user {user_id}, topic {topic}")
            return self.knowledge_tracking_agent.get_topic_progress(user_id, topic)
        except Exception as e:
            self.logger.error(f"Error getting topic progress: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    def analyze_learning_patterns(self, user_id: str) -> Dict:
        """Analyze learning patterns and provide insights"""
        try:
            self.logger.info(f"Analyzing learning patterns for user {user_id}")
            return self.knowledge_tracking_agent.analyze_learning_patterns(user_id)
        except Exception as e:
            self.logger.error(f"Error analyzing learning patterns: {str(e)}")
            return {"status": "error", "message": str(e)}

    def get_shared_state(self) -> Dict:
        """
        Get the current shared state dictionary from the tutor agent.
        
        Returns:
            Dict containing the shared state that all agents can access
        """
        try:
            self.logger.info("Getting shared state")
            return self.tutor_agent.get_shared_state()
        except Exception as e:
            self.logger.error(f"Error getting shared state: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    def update_shared_state(self, key: str, value) -> Dict:
        """
        Update a specific field in the shared state dictionary.
        
        Args:
            key: The key to update in the shared state
            value: The new value to set
            
        Returns:
            Dict containing the updated shared state
        """
        try:
            self.logger.info(f"Updating shared state: {key}")
            self.tutor_agent.update_shared_state(key, value)
            return {"status": "success", "message": f"Updated {key} in shared state"}
        except Exception as e:
            self.logger.error(f"Error updating shared state: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    def update_rag_content(self, content: str) -> Dict:
        """
        Update the RAG content in the shared state.
        
        Args:
            content: The text content of the PDF or document
            
        Returns:
            Dict containing status of the update
        """
        try:
            self.logger.info(f"Updating RAG content: {len(content)} characters")
            self.tutor_agent.update_shared_state("rag_content", content)
            
            # Also extract topics from the content
            topics = self.topic_agent.process(content)
            if isinstance(topics, dict) and "topics" in topics:
                self.tutor_agent.update_shared_state("topics", topics["topics"])
                self.tutor_agent.update_shared_state("current_topic", topics.get("title", "Document"))
            
            return {"status": "success", "message": "Updated RAG content and extracted topics"}
        except Exception as e:
            self.logger.error(f"Error updating RAG content: {str(e)}")
            return {"status": "error", "message": str(e)}

    def chat(self, query: str, context: str = "", user_id: str = "default_user") -> str:
        """Process user query and generate appropriate response using the main tutor agent"""
        try:
            self.logger.info(f"Processing query with tutor agent: {query[:50]}...")
            
            # Log the current state of the shared state
            shared_state = self.tutor_agent.get_shared_state()
            self.logger.info(f"Current shared state before processing:")
            self.logger.info(f"  - topics: {len(shared_state['topics'])} topics")
            self.logger.info(f"  - current_topic: {shared_state['current_topic']}")
            self.logger.info(f"  - progress: {len(shared_state['progress'])} topics tracked")
            self.logger.info(f"  - lesson_plan: {'Present' if shared_state['lesson_plan'] else 'None'}")
            
            # Update shared state with context and user input
            self.tutor_agent.update_shared_state("rag_content", context)
            self.tutor_agent.update_shared_state("user_input", query)
            
            # Use the main tutor agent to handle the query
            response = self.tutor_agent.process(context, query, user_id)
            
            # Log the updated state of the shared state
            shared_state = self.tutor_agent.get_shared_state()
            self.logger.info(f"Updated shared state after processing:")
            self.logger.info(f"  - topics: {len(shared_state['topics'])} topics")
            self.logger.info(f"  - current_topic: {shared_state['current_topic']}")
            self.logger.info(f"  - progress: {len(shared_state['progress'])} topics tracked")
            self.logger.info(f"  - lesson_plan: {'Present' if shared_state['lesson_plan'] else 'None'}")
            
            # If the response is a dictionary, format it appropriately
            if isinstance(response, dict):
                # Check if there are special components that need to be formatted
                if "quiz" in response:
                    self.logger.info("Response contains quiz data")
                    return f"```json\n{json.dumps(response, indent=2)}\n```"
                elif "flashcards" in response:
                    self.logger.info("Response contains flashcard data")
                    return f"```json\n{json.dumps(response, indent=2)}\n```"
                elif "has_diagram" in response and response["has_diagram"]:
                    self.logger.info("Response contains diagram data")
                    # Return the response as is, the frontend will handle the diagram
                    return f"```json\n{json.dumps(response, indent=2)}\n```"
                else:
                    # Just return the text response
                    self.logger.info("Returning text response")
                    return response["response"]
            
            # If it's not a dictionary, return as string
            self.logger.info("Returning non-dictionary response as string")
            return str(response)
                
        except Exception as e:
            self.logger.error(f"Error in chat: {str(e)}")
            return "I encountered an error while processing your request. Please try again in a moment." 