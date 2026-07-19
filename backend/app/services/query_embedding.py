import time
import logging
import numpy as np
from app.services.embedding import EmbeddingService, EmbeddingServiceError

logger = logging.getLogger("rag_backend.query_embedding")

class QueryEmbeddingError(Exception):
    """Exception raised for errors in the QueryEmbeddingService."""
    pass

class QueryEmbeddingService:
    """
    Service responsible for validating search queries and generating
    L2-normalized query embeddings for downstream semantic retrieval.
    """
    def __init__(self):
        self.embedding_service = EmbeddingService()

    def generate_query_embedding(self, query: str) -> np.ndarray:
        """
        Validates the query and generates an L2-normalized float32 query embedding.
        
        Args:
            query (str): The user search query.
            
        Returns:
            np.ndarray: Normalized 1D float32 numpy array representing the query embedding.
        """
        if not isinstance(query, str):
            logger.error("Query input is not a string.")
            raise QueryEmbeddingError("Query must be a string.")
            
        cleaned_query = query.strip()
        if not cleaned_query:
            logger.warning("Empty query passed for embedding.")
            raise QueryEmbeddingError("Query cannot be empty or only whitespace.")

        # Validate excessively long queries (e.g. > 1000 characters)
        if len(cleaned_query) > 1000:
            logger.error(f"Query exceeds maximum character limit: {len(cleaned_query)} > 1000")
            raise QueryEmbeddingError(
                f"Query is too long ({len(cleaned_query)} characters). "
                f"Maximum allowed length is 1000 characters."
            )

        logger.info(f"Generating query embedding (length: {len(cleaned_query)} characters)...")
        start_time = time.time()
        
        try:
            # Generate the embedding using the central EmbeddingService
            # Returns a 1D numpy array
            embedding = self.embedding_service.embed_text(cleaned_query)
            
            # L2-normalize the vector to make inner-product searches equivalent to cosine similarity
            norm = np.linalg.norm(embedding)
            if norm > 0:
                normalized_embedding = embedding / norm
            else:
                normalized_embedding = embedding
                
            elapsed_time = time.time() - start_time
            logger.info(f"Successfully generated query embedding in {elapsed_time:.4f} seconds.")
            return normalized_embedding.astype(np.float32)
            
        except EmbeddingServiceError as e:
            logger.exception("Underlying embedding service failed during query embedding generation.")
            raise QueryEmbeddingError(f"Underlying embedding generation failed: {str(e)}") from e
        except Exception as e:
            logger.exception("Unexpected error during query embedding generation.")
            raise QueryEmbeddingError(f"Failed to generate query embedding: {str(e)}") from e
