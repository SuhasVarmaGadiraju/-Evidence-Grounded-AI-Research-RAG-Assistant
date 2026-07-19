import os
import time
import json
import logging
from datetime import datetime, timezone
from abc import ABC, abstractmethod
import numpy as np
import faiss
from flask import current_app
from app.services.embedding import EmbeddingService, EmbeddingServiceError
from app.config import get_config

logger = logging.getLogger("rag_backend.vector_index")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
INDEX_DIR = os.path.join(BASE_DIR, "data", "indexes")
EMBEDDINGS_DIR = os.path.join(BASE_DIR, "data", "embeddings")
CHUNKS_DIR = os.path.join(BASE_DIR, "data", "chunks")
METADATA_DIR = os.path.join(BASE_DIR, "data", "metadata")

# Ensure index folder exists
os.makedirs(INDEX_DIR, exist_ok=True)

class VectorIndexServiceError(Exception):
    """Exception raised for errors in the VectorIndexService."""
    pass

class BaseVectorIndex(ABC):
    """
    Abstract base class defining the vector index interface.
    This guarantees modularity so FAISS can be replaced by Qdrant, Chroma, etc.
    """
    @abstractmethod
    def create_index(self, dimension: int):
        """Initializes a new vector index."""
        pass

    @abstractmethod
    def add_embeddings(self, embeddings: np.ndarray, metadata: list[dict]):
        """Adds embeddings and corresponding metadata mapping to the index."""
        pass

    @abstractmethod
    def save_index(self):
        """Persists the index to disk."""
        pass

    @abstractmethod
    def load_index(self):
        """Loads the index from disk."""
        pass

    @abstractmethod
    def search(self, query_vector: np.ndarray, k: int = 5) -> list[dict]:
        """Queries the vector index for top-k matches."""
        pass

    @abstractmethod
    def rebuild_index(self):
        """Reconstructs the index from scratch using all stored documents."""
        pass

    @abstractmethod
    def get_index_stats(self) -> dict:
        """Returns metadata statistics about the active index."""
        pass


class FAISSIndexService(BaseVectorIndex):
    """
    Concrete implementation of BaseVectorIndex using FAISS.
    Uses IndexFlatIP with L2-normalized float32 vectors for cosine similarity.
    """
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(FAISSIndexService, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        # Prevent re-initialization of instance state
        if hasattr(self, "_initialized") and self._initialized:
            return
        self._initialized = True
        self._index = None
        self._mapping = []
        self.dimension = None
        self._last_loaded_time = 0.0
        
        # Attempt to auto-load existing index files on start
        try:
            self.load_index()
        except Exception as e:
            logger.warning(f"Could not auto-load existing FAISS index: {e}")

    def create_index(self, dimension: int):
        """Creates a new empty FAISS IndexFlatIP index with the specified dimension."""
        logger.info(f"Creating new FAISS IndexFlatIP index with dimension {dimension}")
        self.dimension = dimension
        self._index = faiss.IndexFlatIP(dimension)
        self._mapping = []

    def normalize_vectors(self, vectors: np.ndarray) -> np.ndarray:
        """L2 normalizes vectors for cosine similarity computation in IndexFlatIP."""
        vectors = vectors.astype(np.float32)
        if vectors.ndim == 1:
            norm = np.linalg.norm(vectors)
            return vectors / norm if norm > 0 else vectors
        elif vectors.ndim == 2:
            norms = np.linalg.norm(vectors, axis=1, keepdims=True)
            # Avoid division by zero
            norms[norms == 0] = 1.0
            return vectors / norms
        return vectors

    def add_embeddings(self, embeddings: np.ndarray, metadata: list[dict]):
        """
        L2-normalizes embeddings and adds them along with their metadata map to the FAISS index.
        """
        # Multi-worker sync check before modifying
        self.check_and_sync_index()
        if not isinstance(embeddings, np.ndarray):
            raise VectorIndexServiceError("Embeddings must be a numpy ndarray.")

        if not isinstance(metadata, list):
            raise VectorIndexServiceError("Metadata must be a list of dictionaries.")

        if len(embeddings) != len(metadata):
            raise VectorIndexServiceError(
                f"Length mismatch: {len(embeddings)} embeddings vs {len(metadata)} metadata items."
            )

        if len(embeddings) == 0:
            return

        dimension = embeddings.shape[1]
        
        # Lazy creation of index if not yet initialized
        if self._index is None:
            self.create_index(dimension)
        elif self.dimension != dimension:
            raise VectorIndexServiceError(
                f"Dimension mismatch. Index dimension: {self.dimension}, "
                f"input embedding dimension: {dimension}"
            )

        # 1. Normalize embeddings to unit vectors for inner product (cosine similarity)
        normalized = self.normalize_vectors(embeddings)
        
        # 2. Insert into index
        try:
            self._index.add(normalized)
        except Exception as e:
            logger.exception("Failed to add vectors to FAISS index")
            raise VectorIndexServiceError(f"FAISS add failed: {str(e)}") from e
        
        # 3. Append to local mapping lists
        self._mapping.extend(metadata)
        logger.info(f"Successfully added {len(embeddings)} vectors. Total in index: {self._index.ntotal}")

    def save_index(self):
        """Saves the FAISS index (.faiss), mapping (.json), and metadata (.json) to disk."""
        if self._index is None:
            raise VectorIndexServiceError("Cannot save: Vector index is not initialized.")

        index_path = os.path.join(INDEX_DIR, "global_index.faiss")
        mapping_path = os.path.join(INDEX_DIR, "global_index_mapping.json")
        meta_path = os.path.join(INDEX_DIR, "global_index_meta.json")

        start_time = time.time()
        try:
            # 1. Save FAISS binary index
            faiss.write_index(self._index, index_path)
            
            # 2. Save index-to-chunk mapping
            with open(mapping_path, "w", encoding="utf-8") as f:
                json.dump(self._mapping, f, indent=2, ensure_ascii=False)

            # 3. Save index metadata
            try:
                # Retrieve active model information
                embedding_service = EmbeddingService()
                model_info = embedding_service.get_model_info()
                model_name = model_info["model_name"]
            except Exception:
                # Fallback model name if outside context/service fails
                model_name = "all-MiniLM-L6-v2"
                
            unique_docs = len(set(m.get("document_id") for m in self._mapping if "document_id" in m))
            
            meta = {
                "index_type": "IndexFlatIP",
                "embedding_model": model_name,
                "embedding_dimension": self.dimension,
                "document_count": unique_docs,
                "chunk_count": self._index.ntotal,
                "index_version": "1.0",
                "created_timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            }
            
            with open(meta_path, "w", encoding="utf-8") as f:
                json.dump(meta, f, indent=2, ensure_ascii=False)

            # Store the current file system modification time after saving successfully
            if os.path.exists(index_path):
                self._last_loaded_time = os.path.getmtime(index_path)

            elapsed = time.time() - start_time
            logger.info(f"Saved FAISS index to {INDEX_DIR} in {elapsed:.2f}s")
        except Exception as e:
            logger.exception("Failed to save FAISS files to disk")
            raise VectorIndexServiceError(f"Save index failed: {str(e)}") from e

    def load_index(self):
        """Loads index files and maps from disk. Resets index states if files are missing or corrupted."""
        index_path = os.path.join(INDEX_DIR, "global_index.faiss")
        mapping_path = os.path.join(INDEX_DIR, "global_index_mapping.json")
        meta_path = os.path.join(INDEX_DIR, "global_index_meta.json")

        if not os.path.exists(index_path) or not os.path.exists(mapping_path) or not os.path.exists(meta_path):
            logger.info("Index files not found on disk. Initializing empty.")
            self._index = None
            self._mapping = []
            self.dimension = None
            return

        start_time = time.time()
        try:
            # 1. Read FAISS binary
            self._index = faiss.read_index(index_path)
            self.dimension = self._index.d
            
            # 2. Read mapping array
            with open(mapping_path, "r", encoding="utf-8") as f:
                self._mapping = json.load(f)

            # Validate mapping integrity
            if self._index.ntotal != len(self._mapping):
                logger.warning(
                    f"Integrity mismatch: index has {self._index.ntotal} vectors, "
                    f"but mapping lists {len(self._mapping)} entries. Rebuilding index..."
                )
                self.rebuild_index()
            else:
                # Store the current file system modification time upon successful load
                if os.path.exists(index_path):
                    self._last_loaded_time = os.path.getmtime(index_path)
                elapsed = time.time() - start_time
                logger.info(f"Loaded FAISS index with {self._index.ntotal} vectors in {elapsed:.2f}s")
        except Exception as e:
            logger.exception("Error loading FAISS index files. Resetting index.")
            self._index = None
            self._mapping = []
            self.dimension = None
            self._last_loaded_time = 0.0
            raise VectorIndexServiceError(f"Load index failed: {str(e)}") from e

    def check_and_sync_index(self):
        """
        Compares modification time of disk index files with memory load time.
        Reloads the index automatically if changes are detected on disk.
        """
        index_path = os.path.join(INDEX_DIR, "global_index.faiss")
        if os.path.exists(index_path):
            disk_mtime = os.path.getmtime(index_path)
            if disk_mtime > self._last_loaded_time:
                logger.info("Detected newer FAISS index files on disk. Reloading...")
                try:
                    self.load_index()
                except Exception as e:
                    logger.error(f"Failed to auto-reload FAISS index: {e}")

    def search(self, query_vector: np.ndarray, k: int = 5) -> list[dict]:
        """
        Searches the FAISS IndexFlatIP index for the top-k nearest neighbors.
        
        Args:
            query_vector (np.ndarray): 1D array of floats representing the query embedding.
            k (int): Number of nearest neighbors to retrieve.
            
        Returns:
            list[dict]: Sorted nearest matches containing metadata and cosine similarity scores.
        """
        self.check_and_sync_index()
        
        if not isinstance(query_vector, np.ndarray):
            raise VectorIndexServiceError("Query vector must be a numpy ndarray.")

        if self._index is not None and self.dimension is not None:
            if query_vector.ndim == 1:
                if len(query_vector) != self.dimension:
                    raise VectorIndexServiceError(
                        f"Query vector size {len(query_vector)} mismatch with index dimension {self.dimension}"
                    )
                # Reshape to a 2D array of shape (1, dimension)
                query_vector = query_vector.reshape(1, -1)
            elif query_vector.ndim == 2:
                if query_vector.shape[1] != self.dimension:
                    raise VectorIndexServiceError(
                        f"Query vector dimension {query_vector.shape[1]} mismatch with index dimension {self.dimension}"
                    )
            else:
                raise VectorIndexServiceError("Query vector must be a 1D or 2D array.")
        else:
            logger.warning("Search queried on an empty or uninitialized index.")
            return []

        if self._index.ntotal == 0:
            logger.warning("Search queried on an empty or uninitialized index.")
            return []

        # L2-normalize query vector for inner product similarity
        query_normalized = self.normalize_vectors(query_vector)

        start_time = time.time()
        try:
            scores, indices = self._index.search(query_normalized, k)
            elapsed = time.time() - start_time
            logger.info(f"FAISS search queried {self._index.ntotal} vectors in {elapsed:.4f}s")
        except Exception as e:
            logger.exception("FAISS index search call failed")
            raise VectorIndexServiceError(f"FAISS search failed: {str(e)}") from e

        results = []
        for score, idx in zip(scores[0], indices[0]):
            # FAISS returns -1 if there are not enough vectors in index
            if idx == -1 or idx >= len(self._mapping):
                continue
            
            chunk_meta = self._mapping[idx]
            results.append({
                "chunk_id": chunk_meta.get("chunk_id"),
                "document_id": chunk_meta.get("document_id"),
                "text": chunk_meta.get("text", ""),
                "page_number": chunk_meta.get("page_number", 0),
                "score": float(score)  # Cosine similarity score
            })

        return results

    def add_document_to_index(self, doc_id: str):
        """Loads a document's embeddings and chunk files, and adds them to the index."""
        npy_path = os.path.join(EMBEDDINGS_DIR, f"{doc_id}_embeddings.npy")
        chunks_path = os.path.join(CHUNKS_DIR, f"{doc_id}_chunks.json")

        if not os.path.exists(npy_path) or not os.path.exists(chunks_path):
            raise VectorIndexServiceError(f"Embeddings or chunks files missing for doc {doc_id}")

        try:
            embeddings = np.load(npy_path)
            with open(chunks_path, "r", encoding="utf-8") as f:
                chunks = json.load(f)
        except Exception as e:
            logger.exception(f"Error loading document files for {doc_id}")
            raise VectorIndexServiceError(f"Failed to read document files: {e}") from e

        metadata_list = []
        for c in chunks:
            metadata_list.append({
                "chunk_id": c["chunk_id"],
                "document_id": c["document_id"],
                "text": c.get("text", ""),
                "page_number": c.get("page_number", 0)
            })

        logger.info(f"Adding document {doc_id} with {len(chunks)} chunks to FAISS index...")
        self.add_embeddings(embeddings, metadata_list)
        self.save_index()

    def rebuild_index(self):
        """
        Reconstructs the index from scratch by reading all successfully
        ingested document embeddings and metadata.
        """
        logger.info("Rebuilding FAISS index from scratch...")
        start_time = time.time()
        
        # Reset current index state
        self._index = None
        self._mapping = []
        self.dimension = None

        if not os.path.exists(METADATA_DIR):
            logger.info("Metadata folder does not exist. Saving empty rebuilt index.")
            # Save empty index
            self.create_index(384) # fallback default dimension
            self.save_index()
            return

        # Find all processed metadata documents
        indexed_count = 0
        for fname in os.listdir(METADATA_DIR):
            if fname.endswith("_meta.json"):
                meta_path = os.path.join(METADATA_DIR, fname)
                try:
                    with open(meta_path, "r", encoding="utf-8") as f:
                        meta_data = json.load(f)
                    
                    doc_id = meta_data.get("document_id")
                    status = meta_data.get("status")
                    
                    if status == "processed" and doc_id:
                        npy_path = os.path.join(EMBEDDINGS_DIR, f"{doc_id}_embeddings.npy")
                        chunks_path = os.path.join(CHUNKS_DIR, f"{doc_id}_chunks.json")
                        
                        if os.path.exists(npy_path) and os.path.exists(chunks_path):
                            logger.info(f"Re-indexing document {doc_id}...")
                            self.add_document_to_index(doc_id)
                            indexed_count += 1
                except Exception as e:
                    logger.error(f"Error rebuilding document index from {fname}: {e}")

        # If no documents were indexed, create a default empty index so search/auto-load doesn't throw errors
        if self._index is None:
            logger.info("No documents found to index during rebuild. Initializing empty.")
            self.create_index(384)
            self.save_index()
        else:
            logger.info(f"FAISS index successfully rebuilt from {indexed_count} documents in {time.time() - start_time:.2f}s")

    def get_index_stats(self) -> dict:
        """Returns metadata statistics about the active index."""
        self.check_and_sync_index()
        meta_path = os.path.join(INDEX_DIR, "global_index_meta.json")
        if not os.path.exists(meta_path):
            return {
                "status": "empty",
                "version": "1.0",
                "vector_count": 0,
                "document_count": 0,
                "index_type": "IndexFlatIP",
                "embedding_model": "all-MiniLM-L6-v2"
            }
            
        try:
            with open(meta_path, "r", encoding="utf-8") as f:
                meta = json.load(f)
                
            return {
                "status": "active" if meta.get("chunk_count", 0) > 0 else "empty",
                "version": meta.get("index_version", "1.0"),
                "vector_count": meta.get("chunk_count", 0),
                "document_count": meta.get("document_count", 0),
                "index_type": meta.get("index_type", "IndexFlatIP"),
                "embedding_model": meta.get("embedding_model", "all-MiniLM-L6-v2")
            }
        except Exception as e:
            logger.error(f"Error reading index metadata: {e}")
            return {
                "status": "error",
                "version": "N/A",
                "vector_count": 0,
                "document_count": 0
            }

def get_vector_index_service() -> FAISSIndexService:
    """Returns the singleton instance of FAISSIndexService."""
    return FAISSIndexService()
