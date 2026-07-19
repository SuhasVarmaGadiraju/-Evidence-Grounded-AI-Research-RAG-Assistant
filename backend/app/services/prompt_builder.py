import os
import time
import math
import hashlib
import logging
from typing import List, Union, Dict, Any, Optional, Tuple
from flask import current_app
from app.services.base_retriever import RetrievalResult

logger = logging.getLogger("rag_backend.services.prompt_builder")

class PromptBuilderError(Exception):
    """Custom exception raised for critical prompt builder service errors."""
    pass

class PromptValidationError(PromptBuilderError):
    """Raised when request payload fails validation criteria."""
    pass

class PromptValidator:
    """
    Validation layer for Prompt Builder requests and template syntax.
    """
    @staticmethod
    def validate_request(
        query: Optional[str],
        retrieval_results: Optional[List[Any]],
        max_chunks: int,
        max_chars: int
    ) -> Dict[str, Any]:
        """
        Validates request parameters prior to prompt construction.
        
        Returns:
            dict: Structured validation status containing warnings and errors.
        """
        warnings = []
        errors = []

        # Query validation
        clean_query = (query or "").strip()
        if not clean_query:
            warnings.append("User query is empty or whitespace-only.")

        # Evidence validation
        results_list = retrieval_results or []
        if not results_list:
            warnings.append("No retrieval results provided. Prompt will be generated with empty evidence clause.")

        # Bounds validation
        if max_chunks <= 0:
            errors.append(f"Invalid max_chunks parameter ({max_chunks}). Must be > 0.")

        if max_chars < 200:
            errors.append(f"Invalid max_chars parameter ({max_chars}). Minimum required limit is 200 characters.")

        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }

    @staticmethod
    def validate_template_syntax(template_content: str, template_name: str) -> None:
        """Verifies template content contains mandatory interpolation placeholders."""
        required_placeholders = ["{query}", "{evidence}", "{metadata}"]
        missing = [p for p in required_placeholders if p not in template_content]
        if missing:
            raise PromptBuilderError(
                f"Template '{template_name}' is invalid. Missing required placeholders: {missing}"
            )

class PromptBuilderService:
    """
    Production-ready Prompt Builder Service.
    
    Transforms Cross-Encoder reranked evidence into structured, grounded prompts
    for downstream LLM inference.
    
    Strictly independent: Does NOT execute retrieval or invoke LLM APIs.
    """

    def __init__(self, templates_dir: Optional[str] = None):
        if templates_dir:
            self.templates_dir = templates_dir
        elif current_app:
            self.templates_dir = current_app.config.get(
                "TEMPLATES_DIR",
                os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "templates"))
            )
        else:
            self.templates_dir = os.path.abspath(
                os.path.join(os.path.dirname(__file__), "..", "..", "templates")
            )

    def _resolve_template_path(self, template_version: str) -> Tuple[Optional[str], str]:
        """
        Resolves template path given version name (e.g. 'v1', 'rag_prompt_v1', 'study_mode').
        Supports version aliases and future template modes.
        """
        version_name = template_version or "rag_prompt_v1"
        
        # Build candidate filenames
        candidates = []
        if version_name.endswith(".txt"):
            candidates.append(version_name)
        else:
            candidates.append(f"{version_name}.txt")
            if not version_name.startswith("rag_prompt_"):
                candidates.append(f"rag_prompt_{version_name}.txt")

        possible_dirs = [
            self.templates_dir,
            os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "templates")),
            os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "templates")),
            os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "templates"))
        ]

        for d in possible_dirs:
            for filename in candidates:
                filepath = os.path.join(d, filename)
                if os.path.exists(filepath):
                    return filepath, filename

        return None, candidates[0]

    def minify_prompt(self, raw_prompt: str) -> str:
        """
        Optimizes rendered prompt size by collapsing duplicate blank lines and trailing whitespace
        without altering evidence text or template semantics.
        """
        if not raw_prompt:
            return ""

        import re
        lines = [line.rstrip() for line in raw_prompt.splitlines()]
        cleaned = "\n".join(lines)
        minified = re.sub(r'\n{3,}', '\n\n', cleaned)
        return minified.strip()



    def load_template(self, template_version: str) -> Tuple[str, str, bool]:
        """
        Loads prompt template text file by version name.
        If requested template is missing, falls back to 'rag_prompt_v1.txt' gracefully.
        
        Returns:
            Tuple[str, str, bool]: (template_content, actual_version_used, is_fallback)
        """
        filepath, resolved_name = self._resolve_template_path(template_version)
        is_fallback = False

        if not filepath:
            # Fallback to default rag_prompt_v1
            logger.warning(
                f"Requested template version '{template_version}' not found. Falling back to default 'rag_prompt_v1'."
            )
            filepath, resolved_name = self._resolve_template_path("rag_prompt_v1")
            is_fallback = True

            if not filepath:
                raise PromptBuilderError(
                    f"Default prompt template 'rag_prompt_v1.txt' not found in templates directory '{self.templates_dir}'."
                )

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()

            PromptValidator.validate_template_syntax(content, resolved_name)
            
            actual_version = template_version if not is_fallback else "rag_prompt_v1"
            return content, actual_version, is_fallback
        except PromptBuilderError:
            raise
        except Exception as e:
            raise PromptBuilderError(f"Failed to read prompt template file '{filepath}': {str(e)}")

    def _normalize_result(self, res: Union[RetrievalResult, Dict[str, Any]]) -> RetrievalResult:
        """Normalizes result dictionaries to RetrievalResult instances."""
        if isinstance(res, RetrievalResult):
            return res
        elif isinstance(res, dict):
            return RetrievalResult(
                rank=res.get("rank", 0),
                score=res.get("score", 0.0),
                retrieval_type=res.get("retrieval_type", "unknown"),
                document_id=res.get("document_id", "unknown"),
                document_name=res.get("document_name", "unknown"),
                page_number=res.get("page_number", 0),
                chunk_id=res.get("chunk_id", "unknown"),
                text=res.get("text", ""),
                match_source=res.get("match_source"),
                rerank_score=res.get("rerank_score")
            )
        else:
            raise ValueError(f"Unsupported retrieval result type: {type(res)}")

    def deduplicate_and_preserve_order(
        self,
        results: List[RetrievalResult]
    ) -> List[RetrievalResult]:
        """
        Deduplicates evidence chunks by chunk_id and text content while
        STRICTLY preserving the original Cross-Encoder reranked position.
        """
        seen_ids = set()
        seen_texts = set()
        unique_results = []

        for item in results:
            clean_text = (item.text or "").strip()
            cid = item.chunk_id

            # Skip exact duplicates
            if cid and cid in seen_ids:
                continue
            if clean_text and clean_text in seen_texts:
                continue

            if cid:
                seen_ids.add(cid)
            if clean_text:
                seen_texts.add(clean_text)

            unique_results.append(item)

        return unique_results

    def build_prompt(
        self,
        query: str,
        retrieval_results: Optional[List[Union[RetrievalResult, Dict[str, Any]]]] = None,
        template_version: Optional[str] = None,
        max_chunks: Optional[int] = None,
        max_chars: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Builds a structured RAG prompt for an LLM given a user query and reranked evidence.
        """
        start_time = time.time()

        # 1. Resolve configuration parameters
        if current_app:
            default_max_chunks = current_app.config.get("MAX_CONTEXT_CHUNKS", 5)
            default_max_chars = current_app.config.get("MAX_CONTEXT_CHARACTERS", 4000)
            default_template_ver = current_app.config.get("PROMPT_TEMPLATE_VERSION", "rag_prompt_v1")
            prompt_version = current_app.config.get("PROMPT_VERSION", "1.0.0")
            pipeline_version = current_app.config.get("PIPELINE_VERSION", "1.0.0")
        else:
            default_max_chunks = 5
            default_max_chars = 4000
            default_template_ver = "rag_prompt_v1"
            prompt_version = "1.0.0"
            pipeline_version = "1.0.0"

        actual_max_chunks = max_chunks if (isinstance(max_chunks, int) and max_chunks > 0) else default_max_chunks
        actual_max_chars = max_chars if (isinstance(max_chars, int) and max_chars > 0) else default_max_chars
        requested_template_ver = template_version or default_template_ver

        # 2. Validation step
        validation_report = PromptValidator.validate_request(
            query=query,
            retrieval_results=retrieval_results,
            max_chunks=actual_max_chunks,
            max_chars=actual_max_chars
        )

        if not validation_report["is_valid"]:
            error_msg = "; ".join(validation_report["errors"])
            raise PromptValidationError(f"Prompt build validation failed: {error_msg}")

        clean_query = (query or "").strip()

        # 3. Load template file with fallback handling
        template_content, actual_template_ver, is_fallback = self.load_template(requested_template_ver)
        if is_fallback:
            validation_report["warnings"].append(
                f"Requested template '{requested_template_ver}' was not found; fell back to 'rag_prompt_v1'."
            )

        # 4. Normalize & Deduplicate evidence chunks (preserving Cross-Encoder rank order)
        raw_results = retrieval_results or []
        normalized_results = [self._normalize_result(r) for r in raw_results]
        deduped_results = self.deduplicate_and_preserve_order(normalized_results)

        # Slice to max_chunks
        selected_results = deduped_results[:actual_max_chunks]

        # 5. Build Evidence & Metadata blocks
        evidence_blocks = []
        source_docs = set()
        included_chunks = []

        if not selected_results:
            evidence_str = "No relevant evidence chunks retrieved."
            metadata_str = "Total Evidence Chunks: 0\nSource Documents: None"
        else:
            for idx, item in enumerate(selected_results, start=1):
                doc_name = item.document_name or "Unknown Document"
                page_num = item.page_number if item.page_number is not None else "Unknown"
                chunk_id = item.chunk_id or f"chunk_{idx}"
                chunk_text = (item.text or "").strip()

                chunk_entry = (
                    f"[Evidence Chunk {idx}]\n"
                    f"- Document Name: {doc_name}\n"
                    f"- Page Number: {page_num}\n"
                    f"- Chunk ID: {chunk_id}\n"
                    f"- Chunk Text:\n{chunk_text}"
                )

                evidence_blocks.append(chunk_entry)
                source_docs.add(f"{doc_name} (Page {page_num})")
                included_chunks.append(item)

            evidence_str = "\n\n".join(evidence_blocks)
            doc_list_str = "\n".join([f"- {d}" for d in sorted(source_docs)])
            metadata_str = f"Total Evidence Chunks: {len(included_chunks)}\nSource Documents:\n{doc_list_str}"

        # 6. Render Prompt
        rendered_prompt = template_content.format(
            query=clean_query if clean_query else "[No user query provided]",
            evidence=evidence_str,
            metadata=metadata_str
        )

        # 7. Apply Minification & Context Truncation Budget
        orig_char_count = len(rendered_prompt)
        minified_prompt = self.minify_prompt(rendered_prompt)
        minified_char_count = len(minified_prompt)
        reduction_pct = round(((orig_char_count - minified_char_count) / orig_char_count * 100.0), 2) if orig_char_count > 0 else 0.0

        final_prompt = minified_prompt
        truncated = False
        if len(minified_prompt) > actual_max_chars:
            truncated = True
            notice_msg = "\n\n[NOTICE: Prompt context truncated to observe character budget limit]"
            target_len = actual_max_chars - len(notice_msg)
            if target_len > 0:
                final_prompt = minified_prompt[:target_len] + notice_msg
            else:
                final_prompt = minified_prompt[:actual_max_chars]

        # 8. Compute Metadata metrics & SHA-256 Hash
        elapsed_time = time.time() - start_time
        char_count = len(final_prompt)
        prompt_line_count = len(final_prompt.splitlines())
        estimated_tokens = math.ceil(char_count / 4.0)
        chunk_count = len(included_chunks)
        prompt_hash = hashlib.sha256(final_prompt.encode("utf-8")).hexdigest()

        # 9. Privacy-Safe Logging (never logging raw query or text)
        logger.info(
            f"Prompt generated in {elapsed_time:.4f}s | "
            f"Prompt Version: {prompt_version} | "
            f"Template Version: {actual_template_ver} | "
            f"Pipeline Version: {pipeline_version} | "
            f"Lines: {prompt_line_count} | "
            f"Original Chars: {orig_char_count} | "
            f"Optimized Chars: {char_count} | "
            f"Reduction: {reduction_pct}% | "
            f"Est. Tokens: {estimated_tokens} | "
            f"Chunk Count: {chunk_count} | "
            f"SHA256: {prompt_hash[:12]}... | "
            f"Truncated: {truncated}"
        )


        if validation_report["warnings"]:
            for warning in validation_report["warnings"]:
                logger.warning(f"Prompt Builder Validation Warning: {warning}")

        return {
            "prompt": final_prompt,
            "query": clean_query,
            "prompt_length": prompt_line_count,
            "character_count": char_count,
            "context_chunk_count": chunk_count,
            "estimated_tokens": estimated_tokens,
            "template_version": actual_template_ver,
            "prompt_version": prompt_version,
            "pipeline_version": pipeline_version,
            "prompt_hash": prompt_hash,
            "generation_time_seconds": elapsed_time,
            "truncated": truncated,
            "validation": validation_report,
            "results": [c.to_dict() for c in included_chunks]
        }
