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
        
        try:
            genai.configure(api_key=gemini_api_key)
            self.model = genai.GenerativeModel(model_name)
            self.logger.info(f"Initialized Gemini model: {model_name}")
        except Exception as e:
            self.logger.error(f"Failed to initialize Gemini model: {str(e)}")
            raise

    def get_context(self, query: str, max_chunks: int = 5) -> str:
        """Retrieve relevant context from vector store"""
        try:
            results = self.pipeline.search_content(query, top_k=max_chunks)
            if isinstance(results, dict):  # ChromaDB results
                context = "\n\n".join(results.get('documents', []))
            else:  # Pinecone results
                context = "\n\n".join([match.metadata.get('text', '') for match in results])
            return context
        except Exception as e:
            self.logger.error(f"Error retrieving context: {str(e)}")
            raise

    async def chat(self, query: str) -> str:
        """Generate response using Gemini with context"""
        try:
            context = self.get_context(query)
            
            prompt = f"""You are an intelligent AI tutor. Use the following context to answer the student's question. 
            If the context doesn't contain relevant information, say so and provide general guidance.
            
            Context:
            {context}
            
            Student's Question: {query}
            
            Please provide a clear, detailed explanation:"""

            response = await self.model.generate_content(prompt)
            return response.text
            
        except Exception as e:
            self.logger.error(f"Error generating response: {str(e)}")
            raise 