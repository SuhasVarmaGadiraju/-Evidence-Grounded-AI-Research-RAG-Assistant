import os
import json
import uuid
import time
import logging
from typing import List, Dict, Any, Optional
from flask import current_app
from app.config import Config

logger = logging.getLogger("rag_backend.services.evaluation_dataset")

class EvaluationDatasetService:
    """
    Manages evaluation datasets, run history persistence, and report aggregation.
    """
    def __init__(self, storage_dir: Optional[str] = None):
        if storage_dir:
            self.storage_dir = storage_dir
        else:
            try:
                self.storage_dir = current_app.config.get("EVALUATION_DATASET_PATH")
            except Exception:
                self.storage_dir = Config.EVALUATION_DATASET_PATH

        os.makedirs(self.storage_dir, exist_ok=True)
        self.dataset_file = os.path.join(self.storage_dir, "dataset.json")
        self.history_file = os.path.join(self.storage_dir, "history.json")

    def _read_json(self, filepath: str) -> List[Dict[str, Any]]:
        if not os.path.exists(filepath):
            return []
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error reading JSON from {filepath}: {e}")
            return []

    def _write_json(self, filepath: str, data: Any) -> bool:
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            logger.error(f"Error writing JSON to {filepath}: {e}")
            return False

    def add_dataset_entry(
        self,
        question: str,
        ground_truth: str,
        expected_documents: Optional[List[str]] = None,
        expected_pages: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """
        Creates and stores a new evaluation dataset entry.
        """
        entry = {
            "id": f"eval_ds_{uuid.uuid4().hex[:8]}",
            "question": question.strip(),
            "ground_truth": ground_truth.strip(),
            "expected_documents": expected_documents or [],
            "expected_pages": expected_pages or [],
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }

        dataset = self._read_json(self.dataset_file)
        dataset.append(entry)
        self._write_json(self.dataset_file, dataset)
        return entry

    def get_dataset(self) -> List[Dict[str, Any]]:
        """
        Returns all saved dataset entries.
        """
        return self._read_json(self.dataset_file)

    def save_evaluation_run(self, run_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Saves a single evaluation run result into history.json.
        """
        history = self._read_json(self.history_file)
        
        if "eval_id" not in run_data:
            run_data["eval_id"] = f"run_{uuid.uuid4().hex[:8]}"
        if "timestamp" not in run_data:
            run_data["timestamp"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        history.append(run_data)
        self._write_json(self.history_file, history)
        return run_data

    def get_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Returns history of evaluation runs, newest first.
        """
        history = self._read_json(self.history_file)
        history.reverse()
        return history[:limit]

    def get_report_statistics(self) -> Dict[str, Any]:
        """
        Aggregates statistics from stored evaluation history.
        """
        history = self._read_json(self.history_file)
        total_runs = len(history)

        if total_runs == 0:
            return {
                "total_evaluations": 0,
                "overall_score_avg": 0.0,
                "metrics_averages": {
                    "context_precision": 0.0,
                    "context_recall": 0.0,
                    "faithfulness": 0.0,
                    "answer_relevancy": 0.0,
                    "retrieval_precision": 0.0,
                    "retrieval_recall": 0.0,
                    "citation_coverage": 0.0,
                    "citation_accuracy": 0.0
                },
                "latest_run_timestamp": None
            }

        metric_keys = [
            "context_precision",
            "context_recall",
            "faithfulness",
            "answer_relevancy",
            "retrieval_precision",
            "retrieval_recall",
            "citation_coverage",
            "citation_accuracy"
        ]

        metric_sums = {k: 0.0 for k in metric_keys}
        overall_sum = 0.0

        for run in history:
            metrics = run.get("metrics", {})
            overall_sum += run.get("overall_score", 0.0)
            for k in metric_keys:
                metric_sums[k] += metrics.get(k, 0.0)

        averages = {k: round(metric_sums[k] / total_runs, 4) for k in metric_keys}

        return {
            "total_evaluations": total_runs,
            "overall_score_avg": round(overall_sum / total_runs, 4),
            "metrics_averages": averages,
            "latest_run_timestamp": history[-1].get("timestamp") if history else None
        }
