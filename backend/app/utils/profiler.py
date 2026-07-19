import time
from typing import Dict, Any, Optional
from contextlib import contextmanager

class PipelineProfiler:
    """
    High-precision nanosecond timing profiler for monitoring end-to-end RAG pipeline performance.
    
    Tracks stage-level latencies:
      - hybrid_retrieval (semantic + bm25 + rrf_merge)
      - cross_encoder (reranking)
      - prompt_builder (formatting & minification)
      - llm_generation (NVIDIA API / cache lookup)
      - json_serialization (response formatting)
    """

    def __init__(self):
        self._start_time: float = time.perf_counter()
        self._timings: Dict[str, float] = {}

    @contextmanager
    def profile(self, stage_name: str):
        """Context manager to measure execution time of a specific pipeline block."""
        t0 = time.perf_counter()
        try:
            yield
        finally:
            t1 = time.perf_counter()
            elapsed = t1 - t0
            self._timings[stage_name] = round(elapsed, 4)

    def record_stage(self, stage_name: str, duration_seconds: float):
        """Manually record a stage duration in seconds."""
        self._timings[stage_name] = round(duration_seconds, 4)

    def get_total_latency(self) -> float:
        """Returns total elapsed latency in seconds since profiler initialization."""
        return round(time.perf_counter() - self._start_time, 4)

    def get_breakdown(self) -> Dict[str, Any]:

        """Returns dictionary containing stage-level timing breakdown and total latency."""
        breakdown = dict(self._timings)
        breakdown["total"] = self.get_total_latency()
        return breakdown
