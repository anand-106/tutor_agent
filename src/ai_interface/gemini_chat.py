from typing import List, Dict
import google.generativeai as genai
import time
from ..data_processing.pipeline import DataProcessingPipeline
from ..data_processing.logger_config import setup_logger

class GeminiTutor:
    def __init__(
        self,
        gemini_api_key: str,
        pipeline: DataProcessingPipeline,
        model_name: str = "gemini-1.5-pro"
    ):
        self.logger = setup_logger('gemini_tutor')
        self.pipeline = pipeline
        self.current_file = None
        self.last_request_time = 0
        self.min_request_interval = 2.0  # Increased to 2 seconds
        self.retry_count = 0
        self.max_retries = 3
        
        try:
            genai.configure(api_key=gemini_api_key)
            self.model = genai.GenerativeModel(model_name)
            self.logger.info(f"Initialized Gemini model: {model_name}")
        except Exception as e:
            self.logger.error(f"Failed to initialize Gemini model: {str(e)}")
            raise

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

    def chat(self, query: str, context: str = "") -> str:
        """Generate response using Gemini with context"""
        try:
            if not context:
                return "I couldn't find any relevant information in the documents to answer your question."
            
            while self.retry_count < self.max_retries:
                try:
                    self._handle_rate_limit()
                    
                    prompt = f"""You are an intelligent AI tutor. Use the following context to answer the student's question.
                    Be detailed and thorough in your explanation. If you're explaining a concept, include examples where helpful.
                    
                    Context:
                    {context}
                    
                    Student's Question: {query}
                    
                    Please provide a clear, detailed explanation:"""

                    response = self.model.generate_content(prompt)
                    self.retry_count = 0  # Reset retry count on success
                    return response.text
                    
                except Exception as e:
                    if "429" in str(e) or "quota" in str(e).lower():
                        self.retry_count += 1
                        if self.retry_count >= self.max_retries:
                            return ("I apologize, but I'm currently experiencing high traffic. "
                                   "Please try again in a few minutes.")
                        continue
                    else:
                        raise
                
        except Exception as e:
            self.logger.error(f"Error generating response: {str(e)}")
            return "I encountered an error while processing your request. Please try again in a moment." 