import os
import time
import json
import logging
import re
import pickle
import threading
from datetime import datetime, timezone
from flask import current_app
from rank_bm25 import BM25Okapi
from app.config import get_config

logger = logging.getLogger("rag_backend.bm25_index")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
INDEX_DIR = os.path.join(BASE_DIR, "data", "indexes")
CHUNKS_DIR = os.path.join(BASE_DIR, "data", "chunks")
METADATA_DIR = os.path.join(BASE_DIR, "data", "metadata")

# Ensure indexes directory exists
os.makedirs(INDEX_DIR, exist_ok=True)

def tokenize_whitespace_lower(text: str) -> list[str]:
    """
    Tokenizes text by splitting on whitespace, converting to lowercase, and
    stripping punctuation from boundaries while preserving internal punctuation
    (e.g., snake_case, version numbers like v1.2.3, IP addresses).
    """
    if not text:
        return []
    tokens = text.lower().split()
    cleaned_tokens = []
    for token in tokens:
        cleaned = token.strip('.,!?;:"()[]{}<>`\'" ')
        if cleaned:
            cleaned_tokens.append(cleaned)
    return cleaned_tokens

def tokenize_simple(text: str) -> list[str]:
    """Tokenize using alphanumeric regex word extraction in lowercase."""
    if not text:
        return []
    return re.findall(r'\w+', text.lower())

class BM25IndexService:
    """
    Thread-safe Singleton service managing the BM25 index life cycle:
    construction, disk serialization, syncing, and change detection.
    """
    _instance = None
    _lock = threading.RLock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if not cls._instance:
                cls._instance = super(BM25IndexService, cls).__new__(cls)
            return cls._instance

    def __init__(self):
        if hasattr(self, "_initialized") and self._initialized:
            return
        self._initialized = True
        self.bm25 = None
        self._chunks = []
        self._indexed_doc_signatures = {}
        self._last_loaded_time = 0.0
        self._doc_name_cache = {}
        
        # Load index files from disk on start if they exist
        try:
            self.load_index()
        except Exception as e:
            logger.warning(f"Could not auto-load existing BM25 index: {e}")

    def _get_tokenizer_name(self) -> str:
        """Resolves the tokenizer name from configuration."""
        try:
            if current_app and hasattr(current_app, "config"):
                return current_app.config.get("BM25_TOKENIZER", "whitespace_lower")
        except (RuntimeError, ImportError):
            pass
            
        try:
            config = get_config()
            return getattr(config, "BM25_TOKENIZER", "whitespace_lower")
        except Exception:
            return "whitespace_lower"

    def get_tokenizer(self):
        """Resolves the tokenizer function based on active config."""
        name = self._get_tokenizer_name()
        if name == "simple":
            return tokenize_simple
        return tokenize_whitespace_lower

    def lookup_document_name(self, doc_id: str) -> str:
        """Looks up the original filename for a document ID, caching results in memory."""
        if not doc_id:
            return "Unknown Document"
            
        with self._lock:
            if doc_id in self._doc_name_cache:
                return self._doc_name_cache[doc_id]

            meta_path = os.path.join(METADATA_DIR, f"{doc_id}_meta.json")
            if not os.path.exists(meta_path):
                return "Unknown Document"

            try:
                with open(meta_path, "r", encoding="utf-8") as f:
                    meta = json.load(f)
                original_filename = meta.get("original_filename", "Unknown Document")
                self._doc_name_cache[doc_id] = original_filename
                return original_filename
            except Exception as e:
                logger.warning(f"Failed to load document metadata for {doc_id}: {e}")
                return "Unknown Document"

    def get_index_stats(self) -> dict:
        """Returns statistics about the BM25 index."""
        with self._lock:
            self.check_and_sync_index()
            unique_docs = len(set(c.get("document_id") for c in self._chunks if "document_id" in c))
            return {
                "status": "active" if len(self._chunks) > 0 else "empty",
                "chunk_count": len(self._chunks),
                "document_count": unique_docs,
                "tokenizer": self._get_tokenizer_name(),
                "last_loaded": datetime.fromtimestamp(self._last_loaded_time, tz=timezone.utc).isoformat() if self._last_loaded_time > 0 else None
            }

    def save_index(self):
        """Persists the BM25Okapi instance, mapping, and metadata to disk."""
        with self._lock:
            if self.bm25 is None or not self._chunks:
                logger.warning("Attempted to save an empty or uninitialized BM25 index. Skipping.")
                return

            index_path = os.path.join(INDEX_DIR, "bm25_index.pkl")
            mapping_path = os.path.join(INDEX_DIR, "bm25_index_mapping.json")
            meta_path = os.path.join(INDEX_DIR, "bm25_index_meta.json")

            start_time = time.time()
            try:
                # 1. Serialize BM25Okapi binary model
                with open(index_path, "wb") as f:
                    pickle.dump(self.bm25, f, protocol=pickle.HIGHEST_PROTOCOL)

                # 2. Save mapped chunks
                with open(mapping_path, "w", encoding="utf-8") as f:
                    json.dump(self._chunks, f, indent=2, ensure_ascii=False)

                # 3. Save metadata
                unique_docs = len(set(c.get("document_id") for c in self._chunks if "document_id" in c))
                meta = {
                    "index_type": "BM25Okapi",
                    "tokenizer": self._get_tokenizer_name(),
                    "document_count": unique_docs,
                    "chunk_count": len(self._chunks),
                    "created_timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                    "indexed_doc_signatures": self._indexed_doc_signatures
                }
                with open(meta_path, "w", encoding="utf-8") as f:
                    json.dump(meta, f, indent=2, ensure_ascii=False)

                if os.path.exists(index_path):
                    self._last_loaded_time = os.path.getmtime(index_path)

                elapsed = time.time() - start_time
                logger.info(f"Saved BM25 index to {INDEX_DIR} in {elapsed:.4f}s")
            except Exception as e:
                logger.exception("Failed to save BM25 index files to disk")

    def load_index(self):
        """Loads the BM25 index files from disk. Resets state if files are missing or mismatch configs."""
        with self._lock:
            index_path = os.path.join(INDEX_DIR, "bm25_index.pkl")
            mapping_path = os.path.join(INDEX_DIR, "bm25_index_mapping.json")
            meta_path = os.path.join(INDEX_DIR, "bm25_index_meta.json")

            if not os.path.exists(index_path) or not os.path.exists(mapping_path) or not os.path.exists(meta_path):
                logger.info("BM25 index files not found on disk. Initializing empty.")
                self.bm25 = None
                self._chunks = []
                self._indexed_doc_signatures = {}
                self._last_loaded_time = 0.0
                return

            start_time = time.time()
            try:
                # 1. Read metadata
                with open(meta_path, "r", encoding="utf-8") as f:
                    meta = json.load(f)

                # Validate tokenizer configuration matches
                tokenizer_in_meta = meta.get("tokenizer", "whitespace_lower")
                current_tokenizer = self._get_tokenizer_name()
                if tokenizer_in_meta != current_tokenizer:
                    logger.warning(
                        f"BM25 index tokenizer configuration changed from '{tokenizer_in_meta}' "
                        f"to '{current_tokenizer}'. Forcing rebuild of index."
                    )
                    self.rebuild_index()
                    return

                # 2. Deserialize BM25 model
                with open(index_path, "rb") as f:
                    self.bm25 = pickle.load(f)

                # 3. Read mapping
                with open(mapping_path, "r", encoding="utf-8") as f:
                    self._chunks = json.load(f)

                self._indexed_doc_signatures = meta.get("indexed_doc_signatures", {})
                self._last_loaded_time = os.path.getmtime(index_path)

                elapsed = time.time() - start_time
                logger.info(f"Loaded BM25 index with {len(self._chunks)} chunks in {elapsed:.4f}s")
            except Exception as e:
                logger.exception("Failed to load BM25 index from disk. Resetting in-memory index.")
                self.bm25 = None
                self._chunks = []
                self._indexed_doc_signatures = {}
                self._last_loaded_time = 0.0

    def check_and_sync_index(self):
        """
        Thread-safe verification of index freshness. Checks if new files were processed
        or if the index binary on disk has been updated by another process.
        """
        with self._lock:
            # 1. Check if another worker/process updated the disk index files
            index_path = os.path.join(INDEX_DIR, "bm25_index.pkl")
            if os.path.exists(index_path):
                disk_mtime = os.path.getmtime(index_path)
                if disk_mtime > self._last_loaded_time:
                    logger.info("Detected newer BM25 index files on disk. Reloading...")
                    self.load_index()
                    return

            # 2. Query ingested documents list to detect sync delta
            try:
                from app.services.ingest import list_ingested_documents
                current_docs = list_ingested_documents()
            except Exception as e:
                logger.error(f"Failed to list ingested documents for BM25 sync: {e}")
                return

            current_doc_signatures = {
                doc.get("document_id"): (doc.get("total_chunks", 0), doc.get("upload_timestamp", ""))
                for doc in current_docs if doc.get("status") == "processed"
            }

            if current_doc_signatures != self._indexed_doc_signatures:
                logger.info("Local BM25 signatures mismatch. Synchronizing index from documents...")
                self._rebuild_index(current_docs, current_doc_signatures)

    def rebuild_index(self):
        """Forces a complete index reconstruction from raw chunk files."""
        with self._lock:
            logger.info("Forcing rebuild of BM25 index from scratch...")
            try:
                from app.services.ingest import list_ingested_documents
                current_docs = list_ingested_documents()
            except Exception as e:
                logger.error(f"Failed to list documents for rebuilding: {e}")
                return

            current_doc_signatures = {
                doc.get("document_id"): (doc.get("total_chunks", 0), doc.get("upload_timestamp", ""))
                for doc in current_docs if doc.get("status") == "processed"
            }
            self._rebuild_index(current_docs, current_doc_signatures)

    def _rebuild_index(self, processed_docs: list[dict], signatures: dict):
        """Internal lock-guaranteed rebuild logic."""
        all_chunks = []
        for doc in processed_docs:
            doc_id = doc.get("document_id")
            if not doc_id:
                continue
            chunks_path = os.path.join(CHUNKS_DIR, f"{doc_id}_chunks.json")
            if not os.path.exists(chunks_path):
                logger.warning(f"Chunks file missing for document {doc_id} during BM25 rebuild")
                continue
            try:
                with open(chunks_path, "r", encoding="utf-8") as f:
                    doc_chunks = json.load(f)
                    all_chunks.extend(doc_chunks)
            except Exception as e:
                logger.error(f"Error loading chunks for document {doc_id} during BM25 rebuild: {e}")

        if not all_chunks:
            logger.info("No chunks found. Initializing empty BM25 index.")
            self.bm25 = None
            self._chunks = []
            self._indexed_doc_signatures = signatures
            # Delete stale files on disk
            for path in [
                os.path.join(INDEX_DIR, "bm25_index.pkl"),
                os.path.join(INDEX_DIR, "bm25_index_mapping.json"),
                os.path.join(INDEX_DIR, "bm25_index_meta.json")
            ]:
                if os.path.exists(path):
                    try:
                        os.remove(path)
                    except Exception:
                        pass
            return

        tokenize_func = self.get_tokenizer()
        tokenized_corpus = []
        valid_chunks = []

        for chunk in all_chunks:
            text = chunk.get("text", "")
            if not text:
                continue
            tokenized_corpus.append(tokenize_func(text))
            valid_chunks.append(chunk)

        if not tokenized_corpus:
            logger.info("No valid text chunks to index. Initializing empty BM25 index.")
            self.bm25 = None
            self._chunks = []
            self._indexed_doc_signatures = signatures
            return

        try:
            self.bm25 = BM25Okapi(tokenized_corpus)
            self._chunks = valid_chunks
            self._indexed_doc_signatures = signatures
            
            # Save the index to disk
            self.save_index()
            logger.info(f"Rebuilt BM25 index with {len(self._chunks)} chunks.")
        except Exception as e:
            logger.exception("Failed to build BM25Okapi index model")
            self.bm25 = None
            self._chunks = []
            self._indexed_doc_signatures = {}

def get_bm25_index_service() -> BM25IndexService:
    """Returns the singleton instance of BM25IndexService."""
    return BM25IndexService()
