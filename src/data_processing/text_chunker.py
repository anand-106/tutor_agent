from typing import List, Dict
from langchain.text_splitter import RecursiveCharacterTextSplitter
from dataclasses import dataclass
from .logger_config import setup_logger

@dataclass
class TextChunk:
    text: str
    metadata: Dict
    chunk_id: str

class TextChunker:
    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200
    ):
        self.logger = setup_logger('text_chunker')
        
        try:
            if chunk_size <= 0 or chunk_overlap < 0:
                raise ValueError("Invalid chunk size or overlap")
                
            if chunk_overlap >= chunk_size:
                raise ValueError("Overlap must be less than chunk size")
                
            self.text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                length_function=len,
                separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""]
            )
            
        except Exception as e:
            self.logger.error(f"Error initializing TextChunker: {str(e)}")
            raise

    def create_chunks(
        self,
        text: str,
        metadata: Dict = None
    ) -> List[TextChunk]:
        """Split text into chunks with metadata"""
        try:
            if not text:
                raise ValueError("Empty text provided")
                
            if metadata is None:
                metadata = {}

            self.logger.info(f"Creating chunks from text of length {len(text)}")
            chunks = self.text_splitter.split_text(text)
            
            if not chunks:
                self.logger.warning("No chunks created from input text")
                return []
                
            self.logger.info(f"Created {len(chunks)} chunks")
            
            return [
                TextChunk(
                    text=chunk,
                    metadata=self._enhance_metadata(chunk, metadata),
                    chunk_id=f"chunk_{idx}"
                )
                for idx, chunk in enumerate(chunks)
            ]
            
        except Exception as e:
            self.logger.error(f"Error creating chunks: {str(e)}")
            raise

    def _enhance_metadata(self, chunk: str, base_metadata: Dict) -> Dict:
        """Enhance metadata with chunk-specific information"""
        try:
            enhanced_metadata = base_metadata.copy()
            
            # Add chunk length
            enhanced_metadata['chunk_length'] = len(chunk)
            
            # Detect if chunk contains a question
            enhanced_metadata['contains_question'] = '?' in chunk
            
            # Estimate difficulty based on text complexity
            enhanced_metadata['difficulty'] = self._estimate_difficulty(chunk)
            
            return enhanced_metadata
            
        except Exception as e:
            self.logger.error(f"Error enhancing metadata: {str(e)}")
            raise

    def _estimate_difficulty(self, text: str) -> str:
        """Estimate text difficulty based on various metrics"""
        # Simple implementation - can be enhanced
        words = text.split()
        avg_word_length = sum(len(word) for word in words) / len(words)
        
        if avg_word_length > 7:
            return 'hard'
        elif avg_word_length > 5:
            return 'medium'
        return 'easy' 