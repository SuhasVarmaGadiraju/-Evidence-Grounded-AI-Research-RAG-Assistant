import time
import hashlib
import threading
import logging
from typing import Dict, Any, Optional, Tuple
from collections import OrderedDict

logger = logging.getLogger("rag_backend.services.cache_service")

class BaseLRUCache:
    """Thread-safe LRU cache with Time-To-Live (TTL) expiration."""

    def __init__(self, max_size: int = 100, ttl_seconds: int = 300, name: str = "cache"):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.name = name
        self._cache: OrderedDict = OrderedDict()
        self._lock = threading.Lock()
        self.hits = 0
        self.misses = 0
        self.evictions = 0

    def _hash_key(self, raw_key: str) -> str:
        """Generates SHA-256 hash for raw string key."""
        return hashlib.sha256(raw_key.strip().encode("utf-8")).hexdigest()

    def get(self, raw_key: str) -> Optional[Any]:
        """Retrieves item from cache if key exists and has not expired."""
        key = self._hash_key(raw_key)
        now = time.time()

        with self._lock:
            if key not in self._cache:
                self.misses += 1
                return None

            value, timestamp = self._cache[key]
            if now - timestamp > self.ttl_seconds:
                # Expired entry
                del self._cache[key]
                self.misses += 1
                logger.debug(f"[{self.name}] Cache key {key[:8]} expired.")
                return None

            # Move to end (most recently used)
            self._cache.move_to_end(key)
            self.hits += 1
            logger.info(f"[{self.name}] Cache HIT for key SHA256: {key[:12]}...")
            return value

    def set(self, raw_key: str, value: Any):
        """Stores item in cache with current timestamp, evicting oldest if max_size exceeded."""
        key = self._hash_key(raw_key)
        now = time.time()

        with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
            self._cache[key] = (value, now)

            if len(self._cache) > self.max_size:
                oldest_key, _ = self._cache.popitem(last=False)
                self.evictions += 1
                logger.debug(f"[{self.name}] Evicted LRU key {oldest_key[:8]}.")

    def clear(self):
        """Clears all cached entries and resets metrics."""
        with self._lock:
            self._cache.clear()
            self.hits = 0
            self.misses = 0
            self.evictions = 0

    def stats(self) -> Dict[str, Any]:
        """Returns statistics for observability and health endpoints."""
        with self._lock:
            now = time.time()
            # Count active unexpired items
            active_count = sum(1 for _, (_, ts) in self._cache.items() if now - ts <= self.ttl_seconds)
            return {
                "name": self.name,
                "size": len(self._cache),
                "active_items": active_count,
                "max_size": self.max_size,
                "ttl_seconds": self.ttl_seconds,
                "hits": self.hits,
                "misses": self.misses,
                "evictions": self.evictions
            }

class LLMCache(BaseLRUCache):
    """In-memory cache for rendered prompt LLM generation responses (TTL: 10 minutes)."""
    def __init__(self, max_size: int = 100, ttl_seconds: int = 600):
        super().__init__(max_size=max_size, ttl_seconds=ttl_seconds, name="LLMCache")

class RetrievalCache(BaseLRUCache):
    """In-memory cache for search retrieval & prompt builder outputs (TTL: 5 minutes)."""
    def __init__(self, max_size: int = 100, ttl_seconds: int = 300):
        super().__init__(max_size=max_size, ttl_seconds=ttl_seconds, name="RetrievalCache")

# Global Cache Instances
llm_cache = LLMCache()
retrieval_cache = RetrievalCache()

def get_all_cache_stats() -> Dict[str, Any]:
    """Returns combined stats for all system caches."""
    return {
        "llm_cache": llm_cache.stats(),
        "retrieval_cache": retrieval_cache.stats()
    }
