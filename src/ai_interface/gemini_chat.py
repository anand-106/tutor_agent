from typing import List, Dict
from ..data_processing.pipeline import DataProcessingPipeline
from ..data_processing.logger_config import setup_logger
from .agents.topic_agent import TopicAgent
from .agents.quiz_agent import QuizAgent
from .agents.diagram_agent import DiagramAgent
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
        
        # Initialize agents
        self.topic_agent = TopicAgent(api_keys)
        self.quiz_agent = QuizAgent(api_keys)
        self.diagram_agent = DiagramAgent(api_keys)
        
        self.logger.info("Initialized Gemini Tutor with all agents")

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

    def chat(self, query: str, context: str = "") -> str:
        """Process user query and generate appropriate response"""
        try:
            if not context:
                return "I couldn't find any relevant information in the documents to answer your question."
            
            # Check for specific agent requests
            query_lower = query.lower()
            self.logger.info(f"Processing query: {query_lower}")
            
            # Topic extraction request
            if "extract topics" in query_lower or "show topics" in query_lower:
                self.logger.info("Using Topic Agent")
                topics = self.topic_agent.process(context)
                return str(topics)
            
            # Quiz generation request
            quiz_triggers = ["quiz", "test", "question"]
            if any(trigger in query_lower for trigger in quiz_triggers):
                self.logger.info("Using Quiz Agent")
                quiz = self.quiz_agent.process(context)
                # Format quiz response as JSON string
                if isinstance(quiz, dict):
                    return f"```json\n{json.dumps(quiz, indent=2)}\n```"
                return str(quiz)
            
            # Diagram generation request
            diagram_triggers = ["diagram", "visualize", "flowchart", "sequence", "class diagram"]
            if any(trigger in query_lower for trigger in diagram_triggers):
                self.logger.info("Using Diagram Agent")
                # Determine diagram type from query
                diagram_type = None
                if "sequence" in query_lower:
                    diagram_type = "sequence"
                elif "class" in query_lower:
                    diagram_type = "class"
                else:
                    diagram_type = "flowchart"
                
                diagram = self.diagram_agent.process(context, diagram_type)
                # Format diagram response as JSON string
                if isinstance(diagram, dict):
                    return f"```json\n{json.dumps(diagram, indent=2)}\n```"
                return str(diagram)
            
            # For other queries, use topic extraction as default
            self.logger.info("No specific agent trigger found, using Topic Agent as default")
            return str(self.topic_agent.process(context))
                
        except Exception as e:
            self.logger.error(f"Error in chat: {str(e)}")
            return "I encountered an error while processing your request. Please try again in a moment." 