from typing import List, Dict
import google.generativeai as genai
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

    def chat(self, query: str) -> str:
        """Generate response using Gemini with context"""
        try:
            context = self.get_context(query)
            
            if not context:
                self.logger.warning("No relevant context found for query")
                return "I couldn't find any relevant information in the documents to answer your question."
            
            prompt = f"""You are an intelligent AI tutor. Use the following context to answer the student's question. 
            If the context doesn't contain relevant information, say so and provide general guidance.
            
            Context:
            {context}
            
            Student's Question: {query}
            
            Please provide a clear, detailed explanation:"""

            response = self.model.generate_content(prompt)
            return response.text
            
        except Exception as e:
            self.logger.error(f"Error generating response: {str(e)}")
            raise 