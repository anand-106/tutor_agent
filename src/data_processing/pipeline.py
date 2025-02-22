from typing import List, Dict
from pathlib import Path
from .document_processor import DocumentProcessor
from .text_chunker import TextChunker
from .vector_store import VectorStore
from .logger_config import setup_logger

class DataProcessingPipeline:
    def __init__(
        self,
        use_pinecone: bool = False,
        pinecone_credentials: Dict = None
    ):
        self.logger = setup_logger('data_pipeline')
        
        try:
            self.logger.info("Initializing DataProcessingPipeline")
            
            try:
                self.document_processor = DocumentProcessor()
                self.logger.debug("Initialized DocumentProcessor")
            except Exception as e:
                self.logger.error(f"Failed to initialize DocumentProcessor: {str(e)}")
                raise
                
            try:
                self.text_chunker = TextChunker()
                self.logger.debug("Initialized TextChunker")
            except Exception as e:
                self.logger.error(f"Failed to initialize TextChunker: {str(e)}")
                raise
                
            try:
                self.vector_store = VectorStore(
                    use_pinecone=use_pinecone,
                    **(pinecone_credentials or {})
                )
                self.logger.debug("Initialized VectorStore")
            except Exception as e:
                self.logger.error(f"Failed to initialize VectorStore: {str(e)}")
                raise
                
            self.logger.info("Successfully initialized all components")
            
        except Exception as e:
            self.logger.error(f"Error in pipeline initialization: {str(e)}")
            raise

    def process_directory(
        self,
        directory_path: str,
        metadata_mapping: Dict = None
    ):
        """Process all documents in a directory"""
        try:
            if metadata_mapping is None:
                metadata_mapping = {}

            directory = Path(directory_path)
            if not directory.exists():
                raise FileNotFoundError(f"Directory not found: {directory}")
                
            self.logger.info(f"Processing directory: {directory}")
            
            processed_files = 0
            failed_files = 0
            
            for file_path in directory.glob("**/*"):
                if file_path.suffix.lower() in self.document_processor.supported_formats:
                    try:
                        self.process_file(
                            str(file_path), 
                            metadata_mapping.get(file_path.name, {})
                        )
                        processed_files += 1
                    except Exception as e:
                        self.logger.error(f"Failed to process file {file_path}: {str(e)}")
                        failed_files += 1
                        continue
            
            self.logger.info(
                f"Directory processing complete. "
                f"Processed: {processed_files}, Failed: {failed_files}"
            )
            
        except Exception as e:
            self.logger.error(f"Error processing directory {directory_path}: {str(e)}")
            raise

    def process_file(self, file_path: str, metadata: Dict = None):
        """Process a single file"""
        try:
            self.logger.info(f"Processing file: {file_path}")
            
            # Extract text from document
            try:
                text = self.document_processor.process_document(file_path)
                self.logger.debug(f"Successfully extracted text from {file_path}")
            except Exception as e:
                self.logger.error(f"Failed to extract text from {file_path}: {str(e)}")
                raise
            
            # Create chunks with metadata
            try:
                chunks = self.text_chunker.create_chunks(text, metadata)
                self.logger.debug(f"Created {len(chunks)} chunks from {file_path}")
            except Exception as e:
                self.logger.error(f"Failed to create chunks from {file_path}: {str(e)}")
                raise
            
            # Store in vector database
            try:
                self.vector_store.add_chunks(chunks)
                self.logger.debug(f"Successfully stored chunks from {file_path}")
            except Exception as e:
                self.logger.error(f"Failed to store chunks from {file_path}: {str(e)}")
                raise
                
            self.logger.info(f"Successfully processed file: {file_path}")
            
        except Exception as e:
            self.logger.error(f"Error processing file {file_path}: {str(e)}")
            raise

    def search_content(
        self,
        query: str,
        filter_criteria: Dict = None,
        top_k: int = 5
    ) -> List[Dict]:
        """Search for relevant content"""
        try:
            self.logger.info(f"Searching content with query: {query[:100]}...")
            results = self.vector_store.search(query, filter_criteria, top_k)
            self.logger.info(f"Found {len(results)} results")
            return results
        except Exception as e:
            self.logger.error(f"Error searching content: {str(e)}")
            raise 