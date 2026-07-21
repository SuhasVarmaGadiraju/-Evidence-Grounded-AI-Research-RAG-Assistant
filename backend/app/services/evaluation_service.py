import re
import time
import logging
from typing import List, Dict, Any, Optional
from flask import current_app

from app.config import Config
from app.services.hybrid_retriever import HybridRetrievalService
from app.services.cross_encoder import CrossEncoderService
from app.services.prompt_builder import PromptBuilderService
from app.services.llm_service import LLMService
from app.services.evaluation_dataset import EvaluationDatasetService

logger = logging.getLogger("rag_backend.services.evaluation_service")

class EvaluationService:
    """
    RAGAS-inspired evaluation framework for measuring Retrieval, Generation, and Citation quality.
    Operates independently without modifying the core RAG pipeline.
    """
    def __init__(
        self,
        hybrid_retriever: Optional[HybridRetrievalService] = None,
        cross_encoder: Optional[CrossEncoderService] = None,
        prompt_builder: Optional[PromptBuilderService] = None,
        llm_service: Optional[LLMService] = None,
        dataset_service: Optional[EvaluationDatasetService] = None
    ):
        self.retriever = hybrid_retriever or HybridRetrievalService()
        self.cross_encoder = cross_encoder or CrossEncoderService()
        self.prompt_builder = prompt_builder or PromptBuilderService()
        self.llm_service = llm_service or LLMService()
        self.dataset_service = dataset_service or EvaluationDatasetService()

    @staticmethod
    def _tokenize_terms(text: str) -> set:
        """Helper to extract clean alphanumeric terms for metric calculations."""
        text = text.lower()
        words = re.findall(r'\b[a-z0-9]{3,}\b', text)
        stopwords = {
            "the", "and", "is", "in", "it", "of", "to", "for", "with", "on", "at",
            "from", "by", "an", "be", "this", "that", "which", "are", "was", "were",
            "what", "how", "why", "where", "who", "when", "can", "should", "could"
        }
        return set(w for w in words if w not in stopwords)

    def compute_retrieval_precision(
        self,
        retrieved_chunks: List[Dict[str, Any]],
        ground_truth: Optional[str] = None,
        expected_documents: Optional[List[str]] = None,
        expected_pages: Optional[List[int]] = None
    ) -> float:
        """
        Calculates Retrieval Precision: fraction of retrieved chunks that are relevant.
        A chunk is relevant if it matches expected_documents / expected_pages or shares term overlap with ground_truth.
        """
        if not retrieved_chunks:
            return 0.0

        if not expected_documents and not expected_pages and not ground_truth:
            return 1.0

        gt_terms = self._tokenize_terms(ground_truth) if ground_truth else set()
        relevant_count = 0

        for chunk in retrieved_chunks:
            is_rel = False
            doc_name = chunk.get("document_name", "") or chunk.get("filename", "")
            page_num = chunk.get("page_number")

            if expected_documents and any(exp.lower() in doc_name.lower() for exp in expected_documents):
                is_rel = True
            if expected_pages and page_num in expected_pages:
                is_rel = True

            if not is_rel and gt_terms:
                chunk_terms = self._tokenize_terms(chunk.get("text", ""))
                overlap = len(gt_terms.intersection(chunk_terms))
                if len(gt_terms) > 0 and (overlap / min(len(gt_terms), 10)) >= 0.2:
                    is_rel = True

            if is_rel:
                relevant_count += 1

        return round(relevant_count / len(retrieved_chunks), 4)

    def compute_retrieval_recall(
        self,
        retrieved_chunks: List[Dict[str, Any]],
        ground_truth: Optional[str] = None,
        expected_documents: Optional[List[str]] = None,
        expected_pages: Optional[List[int]] = None
    ) -> float:
        """
        Calculates Retrieval Recall: fraction of expected document/page targets or key ground truth concepts found.
        """
        if not retrieved_chunks:
            return 0.0

        total_targets = 0
        found_targets = 0

        if expected_documents:
            retrieved_docs = set(
                (c.get("document_name", "") or c.get("filename", "")).lower()
                for c in retrieved_chunks
            )
            for exp in expected_documents:
                total_targets += 1
                if any(exp.lower() in rdoc for rdoc in retrieved_docs):
                    found_targets += 1

        if expected_pages:
            retrieved_pages = set(c.get("page_number") for c in retrieved_chunks if c.get("page_number") is not None)
            for page in expected_pages:
                total_targets += 1
                if page in retrieved_pages:
                    found_targets += 1

        if total_targets > 0:
            return round(found_targets / total_targets, 4)

        if ground_truth:
            gt_terms = self._tokenize_terms(ground_truth)
            if not gt_terms:
                return 1.0
            retrieved_text = " ".join([c.get("text", "") for c in retrieved_chunks])
            retrieved_terms = self._tokenize_terms(retrieved_text)
            overlap = len(gt_terms.intersection(retrieved_terms))
            return round(overlap / len(gt_terms), 4)

        return 1.0

    def compute_context_precision(
        self,
        retrieved_chunks: List[Dict[str, Any]],
        ground_truth: Optional[str] = None
    ) -> float:
        """
        RAGAS Context Precision: measures if top-ranked retrieved chunks contain relevant information.
        Rank-weighted cumulative precision.
        """
        if not retrieved_chunks:
            return 0.0

        gt_terms = self._tokenize_terms(ground_truth) if ground_truth else set()

        precisions_at_k = []
        relevant_so_far = 0

        for i, chunk in enumerate(retrieved_chunks, start=1):
            chunk_terms = self._tokenize_terms(chunk.get("text", ""))
            overlap = len(gt_terms.intersection(chunk_terms)) if gt_terms else 1
            is_relevant = (overlap >= 2) if gt_terms else True

            if is_relevant:
                relevant_so_far += 1
                precisions_at_k.append(relevant_so_far / i)

        if not precisions_at_k:
            return 0.0

        return round(sum(precisions_at_k) / len(precisions_at_k), 4)

    def compute_context_recall(
        self,
        retrieved_chunks: List[Dict[str, Any]],
        ground_truth: Optional[str] = None
    ) -> float:
        """
        RAGAS Context Recall: fraction of ground_truth claims/sentences attributable to context.
        """
        if not ground_truth:
            return 1.0
        if not retrieved_chunks:
            return 0.0

        retrieved_text = " ".join([c.get("text", "") for c in retrieved_chunks]).lower()
        sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+|\n+', ground_truth) if len(s.strip()) > 5]

        if not sentences:
            return 1.0

        covered = 0
        for sentence in sentences:
            terms = self._tokenize_terms(sentence)
            if not terms:
                covered += 1
                continue
            matched = sum(1 for t in terms if t in retrieved_text)
            if (matched / len(terms)) >= 0.4:
                covered += 1

        return round(covered / len(sentences), 4)

    def compute_faithfulness(
        self,
        answer: str,
        retrieved_chunks: List[Dict[str, Any]]
    ) -> float:
        """
        RAGAS Faithfulness: measures if claims in generated answer are grounded in context text.
        """
        if not answer or not retrieved_chunks:
            return 0.0

        context_text = " ".join([c.get("text", "") for c in retrieved_chunks]).lower()
        statements = [s.strip() for s in re.split(r'(?<=[.!?])\s+|\n+', answer) if len(s.strip()) > 10]

        if not statements:
            return 1.0

        grounded = 0
        for stmt in statements:
            terms = self._tokenize_terms(stmt)
            if not terms:
                grounded += 1
                continue
            matched = sum(1 for t in terms if t in context_text)
            if (matched / len(terms)) >= 0.35:
                grounded += 1

        return round(grounded / len(statements), 4)

    def compute_answer_relevancy(self, question: str, answer: str) -> float:
        """
        RAGAS Answer Relevancy: measures topical alignment between generated answer and question.
        """
        if not question or not answer:
            return 0.0

        q_terms = self._tokenize_terms(question)
        a_terms = self._tokenize_terms(answer)

        if not q_terms:
            return 1.0

        overlap = len(q_terms.intersection(a_terms))
        base_score = overlap / len(q_terms)
        
        # Penalize extremely short / empty answers
        length_multiplier = min(1.0, len(answer) / 30.0)
        return round(min(1.0, base_score * 1.5) * length_multiplier, 4)

    def compute_citation_coverage(self, answer: str) -> float:
        """
        Calculates percentage of answer sentences containing source citations (e.g. [Document X, Page Y] or [Doc X]).
        """
        if not answer:
            return 0.0

        statements = [s.strip() for s in re.split(r'(?<=[.!?])\s+|\n+', answer) if len(s.strip()) > 10]
        if not statements:
            return 0.0

        cited_count = 0
        citation_pattern = re.compile(r'\[.*?\]|\(\s*(Doc|Document|Page|p\.|pdf).*?\)', re.IGNORECASE)

        for stmt in statements:
            if citation_pattern.search(stmt):
                cited_count += 1

        return round(cited_count / len(statements), 4)

    def compute_citation_accuracy(
        self,
        answer: str,
        retrieved_chunks: List[Dict[str, Any]]
    ) -> float:
        """
        Calculates if citations in the answer reference valid document names or pages in retrieved chunks.
        """
        if not answer or not retrieved_chunks:
            return 0.0

        citations = re.findall(r'\[(.*?)\]', answer)
        if not citations:
            return 1.0  # No citations to be inaccurate

        available_docs = [
            (c.get("document_name", "") or c.get("filename", "")).lower()
            for c in retrieved_chunks
        ]
        available_pages = [str(c.get("page_number")) for c in retrieved_chunks if c.get("page_number") is not None]

        accurate = 0
        for cite in citations:
            cite_lower = cite.lower()
            match_found = False
            for doc in available_docs:
                if doc and doc in cite_lower:
                    match_found = True
                    break
            if not match_found:
                for page in available_pages:
                    if f"page {page}" in cite_lower or f"p. {page}" in cite_lower or f"p.{page}" in cite_lower:
                        match_found = True
                        break
            if match_found:
                accurate += 1

        return round(accurate / len(citations), 4)

    def evaluate_query(
        self,
        question: str,
        ground_truth: Optional[str] = None,
        expected_documents: Optional[List[str]] = None,
        expected_pages: Optional[List[int]] = None,
        top_k: int = 5,
        save_to_history: bool = True
    ) -> Dict[str, Any]:
        """
        Executes end-to-end evaluation for a given query:
        1. Retrieves context using HybridRetrievalService.
        2. Generates answer using PromptBuilder & LLMService.
        3. Computes all quality & RAGAS metrics.
        4. Calculates overall quality score.
        5. Persists evaluation run into history if configured.
        """
        start_time = time.time()

        # 1. Retrieve & Rerank Context using HybridRetrievalService & CrossEncoderService
        try:
            candidate_pool_limit = 20
            try:
                candidate_pool_limit = current_app.config.get("RERANK_CANDIDATE_POOL", 20)
            except Exception:
                pass
            candidate_top_k = max(top_k, candidate_pool_limit)

            candidates = self.retriever.search(question, top_k=candidate_top_k)
            reranked_results = self.cross_encoder.rerank(question, candidates, top_k=top_k)
        except Exception as e:
            logger.error(f"Error during evaluation retrieval/reranking: {e}", exc_info=True)
            reranked_results = []

        # 2. Build Prompt & Generate Answer via LLMService
        generated_answer = ""
        prompt_result = {}
        included_chunks = []

        if reranked_results:
            try:
                prompt_result = self.prompt_builder.build_prompt(
                    query=question,
                    retrieval_results=reranked_results
                )
                rendered_prompt = prompt_result.get("prompt", "")
                included_chunks = prompt_result.get("results", [])

                llm_res = self.llm_service.generate(rendered_prompt)
                generated_answer = llm_res.get("answer", "") or llm_res.get("content", "")
            except Exception as e:
                logger.error(f"Error during evaluation generation: {e}", exc_info=True)
                generated_answer = "Generation unavailable during evaluation."
        else:
            generated_answer = "No relevant context found to generate an answer."

        # Normalize retrieved chunks for metric computation
        retrieved_chunks = included_chunks if included_chunks else [
            self.prompt_builder._normalize_result(r) for r in reranked_results
        ]

        # 3. Compute Metrics
        ret_precision = self.compute_retrieval_precision(retrieved_chunks, ground_truth, expected_documents, expected_pages)
        ret_recall = self.compute_retrieval_recall(retrieved_chunks, ground_truth, expected_documents, expected_pages)
        ctx_precision = self.compute_context_precision(retrieved_chunks, ground_truth)
        ctx_recall = self.compute_context_recall(retrieved_chunks, ground_truth)
        faithfulness = self.compute_faithfulness(generated_answer, retrieved_chunks)
        ans_relevancy = self.compute_answer_relevancy(question, generated_answer)
        cit_coverage = self.compute_citation_coverage(generated_answer)
        cit_accuracy = self.compute_citation_accuracy(generated_answer, retrieved_chunks)

        # 4. Overall Weighted Score (0.0 to 1.0)
        overall_score = round(
            0.20 * ctx_precision +
            0.20 * ctx_recall +
            0.25 * faithfulness +
            0.15 * ans_relevancy +
            0.10 * cit_coverage +
            0.10 * cit_accuracy,
            4
        )

        elapsed_ms = round((time.time() - start_time) * 1000, 2)

        eval_result = {
            "question": question,
            "ground_truth": ground_truth or "",
            "expected_documents": expected_documents or [],
            "expected_pages": expected_pages or [],
            "generated_answer": generated_answer,
            "retrieved_chunks_count": len(retrieved_chunks),
            "retrieved_chunks": [
                {
                    "chunk_id": c.get("chunk_id"),
                    "document_name": c.get("document_name", "") or c.get("filename", ""),
                    "page_number": c.get("page_number"),
                    "score": c.get("rerank_score", c.get("rrf_score", c.get("score", 0.0))),
                    "snippet": (c.get("text", "")[:150] + "...") if len(c.get("text", "")) > 150 else c.get("text", "")
                }
                for c in retrieved_chunks[:5]
            ],
            "metrics": {
                "context_precision": ctx_precision,
                "context_recall": ctx_recall,
                "faithfulness": faithfulness,
                "answer_relevancy": ans_relevancy,
                "retrieval_precision": ret_precision,
                "retrieval_recall": ret_recall,
                "citation_coverage": cit_coverage,
                "citation_accuracy": cit_accuracy
            },
            "overall_score": overall_score,
            "latency_ms": elapsed_ms,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }

        # 5. Persist to history if enabled
        if save_to_history:
            try:
                self.dataset_service.save_evaluation_run(eval_result)
            except Exception as e:
                logger.error(f"Error saving evaluation run history: {e}")

        return eval_result
