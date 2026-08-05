import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

from database.database import db
from database.models.retrieval_log import RetrievalLog
from database.models.message import Message

logger = logging.getLogger("rag_backend.services.retrieval_log_service")

def save_retrieved_chunks(
    message_id: int,
    chunks: List[Dict[str, Any]],
    strategy: str = "Hybrid RRF"
) -> List[RetrievalLog]:
    """
    Bulk saves evidence attribution and 4-score retrieval logs for an assistant response.

    Captures:
        - document_uuid
        - chunk_uuid
        - page_number
        - faiss_vector_id
        - semantic_score
        - bm25_score
        - rrf_score
        - reranker_score
        - retrieval_strategy ("Hybrid RRF", "Cross Encoder", "Semantic", "BM25")
        - retrieval_rank (1, 2, 3, ...)

    Args:
        message_id (int): Foreign key ID of the parent Message turn.
        chunks (List[Dict[str, Any]]): List of retrieved chunk dictionaries from pipeline.
        strategy (str): Retrieval strategy used.

    Returns:
        List[RetrievalLog]: Created RetrievalLog ORM objects.

    Raises:
        RuntimeError: If database transaction fails.
    """
    if not message_id or not chunks:
        return []

    now = datetime.now(timezone.utc)
    log_objects: List[RetrievalLog] = []

    for rank, chunk in enumerate(chunks, start=1):
        doc_uuid = chunk.get("document_id") or chunk.get("document_uuid") or "unknown_doc"
        c_uuid = chunk.get("chunk_id") or chunk.get("chunk_uuid") or f"chunk_{rank}"
        page_num = chunk.get("page_number", 1)
        faiss_id = chunk.get("faiss_vector_id")

        # Extract scores safely
        scores = chunk.get("scores") or {}
        sem_score = scores.get("semantic", chunk.get("semantic_score", 0.0))
        bm_score = scores.get("bm25", chunk.get("bm25_score", 0.0))
        rrf_sc = scores.get("rrf", chunk.get("rrf_score", 0.0))
        rerank_sc = scores.get("cross_encoder", chunk.get("reranker_score", chunk.get("score", 0.0)))

        log_item = RetrievalLog(
            message_id=message_id,
            document_uuid=doc_uuid,
            chunk_uuid=c_uuid,
            page_number=page_num,
            faiss_vector_id=faiss_id,
            semantic_score=float(sem_score or 0.0),
            bm25_score=float(bm_score or 0.0),
            rrf_score=float(rrf_sc or 0.0),
            reranker_score=float(rerank_sc or 0.0),
            retrieval_strategy=strategy,
            retrieval_rank=rank,
            created_at=now
        )
        log_objects.append(log_item)

    try:
        db.session.add_all(log_objects)
        db.session.commit()
        logger.info(
            f"Bulk inserted {len(log_objects)} RetrievalLog entries for message_id={message_id} "
            f"using strategy='{strategy}'"
        )
        return log_objects
    except Exception as e:
        db.session.rollback()
        logger.exception(f"Failed to save retrieval logs for message_id={message_id}: {e}")
        raise RuntimeError(f"RetrievalLog bulk save failed: {str(e)}") from e

def get_retrieval_logs_for_message(message_id_or_uuid: Any) -> List[Dict[str, Any]]:
    """
    Retrieves serialized RetrievalLog entries associated with a message turn.

    Args:
        message_id_or_uuid (Any): Message ID integer or UUID string.

    Returns:
        List[Dict[str, Any]]: Serialized list of retrieval log dictionaries.
    """
    try:
        msg = None
        if isinstance(message_id_or_uuid, int) or str(message_id_or_uuid).isdigit():
            msg = Message.query.get(int(message_id_or_uuid))
        else:
            msg = Message.query.filter_by(message_uuid=str(message_id_or_uuid)).first()

        if not msg or not msg.retrieval_logs:
            return []

        return [log.to_dict() for log in msg.retrieval_logs]
    except Exception as e:
        logger.error(f"Error fetching retrieval logs for message '{message_id_or_uuid}': {e}")
        return []
