from typing import List, Dict
from pathlib import Path
from .document_processor import DocumentProcessor
from .text_chunker import TextChunker
from .vector_store import VectorStore
from .logger_config import setup_logger
from .topic_extractor import TopicExtractor

class DataProcessingPipeline:
    def __init__(
        self,
        use_pinecone: bool = False,
        pinecone_credentials: Dict = None,
        gemini_api_key: str = None,
        topic_api_key: str = None
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
                
            try:
                self.topic_extractor = TopicExtractor(topic_api_key or gemini_api_key)
                self.topics_cache = {}  # Cache for storing extracted topics
                self.logger.debug("Initialized TopicExtractor")
            except Exception as e:
                self.logger.error(f"Failed to initialize TopicExtractor: {str(e)}")
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
            
            # Clear existing vectors to start fresh
            try:
                self.vector_store.clear_collection()
                self.logger.info("Cleared existing vectors")
            except Exception as e:
                self.logger.error(f"Failed to clear vectors: {str(e)}")
                # Continue processing even if clearing fails
            
            # Clear topics cache
            self.topics_cache = {}
            self.logger.info("Cleared topics cache")
            
            if metadata is None:
                metadata = {}
            
            # Use consistent key if provided
            consistent_key = metadata.get("consistent_key")
            
            # Add file path to metadata
            file_metadata = metadata.copy()
            file_metadata['file_path'] = file_path
            file_metadata['file_name'] = Path(file_path).name
            
            # Extract text from document
            try:
                text = self.document_processor.process_document(file_path)
                self.logger.debug(f"Successfully extracted text from {file_path}")
            except Exception as e:
                self.logger.error(f"Failed to extract text from {file_path}: {str(e)}")
                raise
            
            # Extract topics
            try:
                topics = self.topic_extractor.extract_topics(text)
                
                # Use consistent key if provided, otherwise use file_path
                cache_key = consistent_key if consistent_key else file_path
                self.topics_cache[cache_key] = topics
                self.logger.info(f"Extracted topics structure for {file_path}, stored with key {cache_key}")
            except Exception as e:
                self.logger.error(f"Failed to extract topics from {file_path}: {str(e)}")
                raise
            
            # Create chunks with metadata
            try:
                chunks = self.text_chunker.create_chunks(text, file_metadata)
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

    def get_topics(self, file_path: str = None) -> Dict:
        """Get topics structure for a specific file or all files"""
        try:
            if file_path:
                if file_path not in self.topics_cache:
                    raise KeyError(f"No topics found for file: {file_path}")
                return self.topics_cache[file_path]
            return self.topics_cache
        except Exception as e:
            self.logger.error(f"Error retrieving topics: {str(e)}")
            raise

    def get_topic_by_path(self, file_path: str, topic_path: List[str]) -> Dict:
        """Get specific topic/subtopic using path"""
        try:
            topics = self.get_topics(file_path)
            current = topics
            
            for key in topic_path:
                found = False
                if isinstance(current, list):
                    for item in current:
                        if item.get('title') == key:
                            current = item
                            found = True
                            break
                elif isinstance(current, dict):
                    if 'subtopics' in current:
                        for item in current['subtopics']:
                            if item.get('title') == key:
                                current = item
                                found = True
                                break
                
                if not found:
                    raise KeyError(f"Topic path not found: {topic_path}")
                    
            return current
            
        except Exception as e:
            self.logger.error(f"Error retrieving topic by path: {str(e)}")
            raise 