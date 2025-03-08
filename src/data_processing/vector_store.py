from typing import List, Dict
import chromadb
import pinecone
from sentence_transformers import SentenceTransformer
from .text_chunker import TextChunk
from .logger_config import setup_logger


class VectorStore:
    def __init__(
        self,
        use_pinecone: bool = False,
        pinecone_api_key: str = None,
        pinecone_environment: str = None,
        pinecone_index: str = None
    ):
        self.logger = setup_logger('vector_store')
        try:
            self.use_pinecone = use_pinecone
            self.logger.info(f"Initializing VectorStore with {'Pinecone' if use_pinecone else 'ChromaDB'}")
            
            # Initialize embedding model
            try:
                self.model = SentenceTransformer('all-MiniLM-L6-v2')
                self.logger.debug("Initialized SentenceTransformer model")
            except Exception as e:
                self.logger.error(f"Failed to initialize SentenceTransformer: {str(e)}")
                raise
            
            if use_pinecone:
                if not all([pinecone_api_key, pinecone_environment, pinecone_index]):
                    raise ValueError("Pinecone credentials required")
                
                try:
                    pinecone.init(
                        api_key=pinecone_api_key,
                        environment=pinecone_environment
                    )
                    
                    if pinecone_index not in pinecone.list_indexes():
                        pinecone.create_index(
                            name=pinecone_index,
                            dimension=384,  # dimension for 'all-MiniLM-L6-v2'
                            metric='cosine'
                        )
                    
                    self.index = pinecone.Index(pinecone_index)
                    self.logger.info("Successfully initialized Pinecone")
                except Exception as e:
                    self.logger.error(f"Failed to initialize Pinecone: {str(e)}")
                    raise
            else:
                try:
                    # New ChromaDB initialization
                    self.client = chromadb.PersistentClient(path="./chroma_db")
                    
                    # Get or create collection
                    try:
                        self.collection = self.client.get_collection("education_content")
                    except:
                        self.collection = self.client.create_collection(
                            name="education_content",
                            metadata={"hnsw:space": "cosine"}  # Use cosine similarity
                        )
                        
                    self.logger.info("Successfully initialized ChromaDB")
                except Exception as e:
                    self.logger.error(f"Failed to initialize ChromaDB: {str(e)}")
                    raise
                    
        except Exception as e:
            self.logger.error(f"Error in VectorStore initialization: {str(e)}")
            raise

    def add_chunks(self, chunks: List[TextChunk]):
        """Add text chunks to vector store"""
        try:
            if not chunks:
                self.logger.warning("No chunks provided to add_chunks")
                return
                
            self.logger.info(f"Adding {len(chunks)} chunks to vector store")
            
            try:
                embeddings = self.model.encode([chunk.text for chunk in chunks])
                self.logger.debug("Successfully created embeddings")
            except Exception as e:
                self.logger.error(f"Failed to create embeddings: {str(e)}")
                raise
            
            if self.use_pinecone:
                try:
                    vectors = [
                        (chunk.chunk_id, embedding.tolist(), chunk.metadata)
                        for chunk, embedding in zip(chunks, embeddings)
                    ]
                    self.index.upsert(vectors=vectors)
                    self.logger.info("Successfully added vectors to Pinecone")
                except Exception as e:
                    self.logger.error(f"Failed to add vectors to Pinecone: {str(e)}")
                    raise
            else:
                try:
                    self.collection.add(
                        embeddings=embeddings.tolist(),
                        documents=[chunk.text for chunk in chunks],
                        metadatas=[chunk.metadata for chunk in chunks],
                        ids=[chunk.chunk_id for chunk in chunks]
                    )
                    self.logger.info("Successfully added vectors to ChromaDB")
                except Exception as e:
                    self.logger.error(f"Failed to add vectors to ChromaDB: {str(e)}")
                    raise
                    
        except Exception as e:
            self.logger.error(f"Error in add_chunks: {str(e)}")
            raise

    def search(
        self,
        query: str,
        filter_criteria: Dict = None,
        top_k: int = 5
    ) -> List[Dict]:
        """Search for relevant chunks"""
        try:
            if not query:
                raise ValueError("Empty query provided")
                
            self.logger.info(f"Searching with query: {query[:100]}...")
            if filter_criteria:
                self.logger.info(f"Using filter criteria: {filter_criteria}")
            
            try:
                query_embedding = self.model.encode(query).tolist()
                self.logger.debug("Successfully created query embedding")
            except Exception as e:
                self.logger.error(f"Failed to create query embedding: {str(e)}")
                raise
            
            if self.use_pinecone:
                try:
                    results = self.index.query(
                        vector=query_embedding,
                        top_k=top_k,
                        filter=filter_criteria
                    )
                    self.logger.info(f"Found {len(results)} results in Pinecone")
                    return results
                except Exception as e:
                    self.logger.error(f"Failed to query Pinecone: {str(e)}")
                    raise
            else:
                try:
                    # For ChromaDB, ensure the filter criteria is properly formatted
                    where_filter = {}
                    if filter_criteria and 'file_path' in filter_criteria:
                        # Format the filter for ChromaDB
                        where_filter = {"file_path": {"$eq": filter_criteria['file_path']}}
                        self.logger.info(f"ChromaDB filter: {where_filter}")
                    
                    results = self.collection.query(
                        query_embeddings=[query_embedding],
                        n_results=top_k,
                        where=where_filter if where_filter else None
                    )
                    
                    # Log the metadata of returned results for debugging
                    if 'metadatas' in results and results['metadatas']:
                        for i, metadata in enumerate(results['metadatas'][0]):
                            self.logger.debug(f"Result {i} metadata: {metadata}")
                    
                    self.logger.info(f"Found {len(results.get('ids', [[]])[0])} results in ChromaDB")
                    return results
                except Exception as e:
                    self.logger.error(f"Failed to query ChromaDB: {str(e)}")
                    raise
                    
        except Exception as e:
            self.logger.error(f"Error in search: {str(e)}")
            raise

    def clear_collection(self):
        """Clear all vectors from the collection"""
        try:
            if self.use_pinecone:
                self.logger.info("Clearing Pinecone index")
                self.index.delete(delete_all=True)
            else:
                self.logger.info("Clearing ChromaDB collection")
                try:
                    # Delete the collection
                    self.client.delete_collection("education_content")
                    # Recreate it
                    self.collection = self.client.create_collection(
                        name="education_content",
                        metadata={"hnsw:space": "cosine"}
                    )
                    self.logger.info("Successfully cleared ChromaDB collection")
                except Exception as e:
                    self.logger.error(f"Failed to clear ChromaDB collection: {str(e)}")
                    raise
        except Exception as e:
            self.logger.error(f"Error clearing collection: {str(e)}")
            raise 