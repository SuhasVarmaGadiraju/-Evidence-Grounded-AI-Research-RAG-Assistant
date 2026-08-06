import os
import gc
import time
import uuid
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Tuple, Optional
import json
from werkzeug.utils import secure_filename
from pypdf import PdfReader
from flask import current_app

from database.database import db
from database.models.document import Document, VALID_DOCUMENT_STATUSES
from database.models.chunk import Chunk
from database.models.user import User
from app.services.cleaner import clean_page_text
from app.retrieval.chunker import chunk_page_text, save_document_chunks

logger = logging.getLogger("rag_backend.ingest")

# Define base storage directories
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE_DIR, "data")
RAW_DIR = os.path.join(DATA_DIR, "raw")
EXTRACTED_DIR = os.path.join(DATA_DIR, "extracted")
PROCESSED_DIR = os.path.join(DATA_DIR, "processed")
CHUNKS_DIR = os.path.join(DATA_DIR, "chunks")
METADATA_DIR = os.path.join(DATA_DIR, "metadata")

# Ensure storage directories exist
for path in [RAW_DIR, EXTRACTED_DIR, PROCESSED_DIR, CHUNKS_DIR, METADATA_DIR]:
    os.makedirs(path, exist_ok=True)

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

def get_ram_usage_mb() -> str:
    """Helper to monitor process RSS memory usage if psutil is installed."""
    try:
        import psutil
        process = psutil.Process(os.getpid())
        mem_bytes = process.memory_info().rss
        return f"{mem_bytes / (1024 * 1024):.1f}MB"
    except Exception:
        return "N/A"

def validate_pdf(file_stream: Any, filename: str) -> Tuple[bool, Optional[str]]:
    """
    Validates that a file is a non-empty PDF under size constraints.

    Args:
        file_stream (Any): Binary file stream object.
        filename (str): Name of the uploaded file.

    Returns:
        Tuple[bool, Optional[str]]: (is_valid, error_message)
    """
    file_stream.seek(0, os.SEEK_END)
    file_size = file_stream.tell()
    file_stream.seek(0)

    if file_size == 0:
        return False, "File is empty"

    if file_size > MAX_FILE_SIZE:
        return False, f"File exceeds maximum size of {MAX_FILE_SIZE // (1024 * 1024)}MB"

    if not filename.lower().endswith('.pdf'):
        return False, "Only PDF files are supported"

    magic_number = file_stream.read(4)
    file_stream.seek(0)
    if magic_number != b"%PDF":
        return False, "File signature is invalid (not a valid PDF)"

    return True, None

def save_metadata(doc_id: str, metadata: Dict[str, Any]) -> None:
    """Saves document metadata to a JSON file backup."""
    meta_path = os.path.join(METADATA_DIR, f"{doc_id}_meta.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

def save_raw_extracted_text(doc_id: str, pages_data: List[Dict[str, Any]]) -> None:
    """Saves raw page-by-page extracted text to a JSON file under data/extracted."""
    extracted_path = os.path.join(EXTRACTED_DIR, f"{doc_id}_raw.json")
    with open(extracted_path, "w", encoding="utf-8") as f:
        json.dump(pages_data, f, indent=2, ensure_ascii=False)

def save_cleaned_text(doc_id: str, pages_data: List[Dict[str, Any]]) -> None:
    """Saves cleaned page-by-page text to a JSON file under data/processed."""
    processed_path = os.path.join(PROCESSED_DIR, f"{doc_id}_clean.json")
    with open(processed_path, "w", encoding="utf-8") as f:
        json.dump(pages_data, f, indent=2, ensure_ascii=False)

def update_document_status(doc_record: Optional[Document], status: str) -> None:
    """
    Updates the document status in PostgreSQL transactionally if database is enabled.

    Args:
        doc_record (Optional[Document]): Document ORM instance.
        status (str): New status string from VALID_DOCUMENT_STATUSES.
    """
    if current_app.config.get("DATABASE_ENABLED", True) and doc_record and status in VALID_DOCUMENT_STATUSES:
        try:
            doc_record.status = status
            db.session.commit()
            logger.info(f"Updated document {doc_record.document_uuid} status -> '{status}'")
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to update document {doc_record.document_uuid} status to '{status}': {e}")

def resolve_user_id(user_info: Optional[Dict[str, Any]]) -> Optional[int]:
    """
    Resolves PostgreSQL user integer ID from user_info payload if database is enabled.

    Args:
        user_info (Optional[Dict[str, Any]]): Dictionary containing firebase_uid or email.

    Returns:
        Optional[int]: User primary key ID if found, else None.
    """
    if not user_info or not current_app.config.get("DATABASE_ENABLED", True):
        return None
    firebase_uid = user_info.get("firebase_uid") or user_info.get("uid") or user_info.get("id")
    email = user_info.get("email")
    if firebase_uid or email:
        try:
            user = User.query.filter(
                (User.firebase_uid == firebase_uid) | (User.email == email)
            ).first()
            if user:
                return user.id
        except Exception as e:
            logger.warning(f"User resolution warning: {e}")
    return None

def process_ingestion(
    file_storage: Any,
    strategy: str = "fixed_character",
    user_info: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Process a single PDF upload with memory-optimized 10-step execution:
    Step 1: Upload received
    Step 2: PDF extraction
    Step 3: Cleaning
    Step 4: Chunking
    Step 5: Loading embedding model (lazy load)
    Step 6: Generating embeddings
    Step 7: Saving embeddings
    Step 8: Building FAISS
    Step 9: Database update
    Step 10: Ingestion finished

    Returns:
        Dict[str, Any]: Ingestion result payload with success flag and metadata.
    """
    t_start = time.time()
    original_filename = file_storage.filename
    doc_id = str(uuid.uuid4())
    safe_name = secure_filename(original_filename)
    unique_filename = f"{doc_id}_{safe_name}"
    raw_path = os.path.join(RAW_DIR, unique_filename)
    doc_record: Optional[Document] = None

    # Step 1: Upload received
    logger.info(f"[Ingestion Step 1/10] Upload received for '{original_filename}' (RAM: {get_ram_usage_mb()})")

    # Standardize strategy parameter
    if strategy == "semantic":
        active_strategy = "semantic"
    elif strategy == "recursive":
        active_strategy = "recursive"
    else:
        active_strategy = "fixed_character"

    # Validation
    is_valid, err_msg = validate_pdf(file_storage.stream, original_filename)
    if not is_valid:
        logger.warning(f"Validation failed for {original_filename}: {err_msg}")
        return {
            "success": False,
            "original_filename": original_filename,
            "error": err_msg
        }

    try:
        # Save raw PDF file
        file_storage.save(raw_path)
        file_size = os.path.getsize(raw_path)

        # Resolve user ID if authenticated
        uploaded_by_id = resolve_user_id(user_info)

        # Create Document row in PostgreSQL if DATABASE_ENABLED is True
        now_utc = datetime.now(timezone.utc)
        if current_app.config.get("DATABASE_ENABLED", True):
            doc_record = Document(
                document_uuid=doc_id,
                title=original_filename,
                filename=unique_filename,
                filepath=raw_path,
                pages=0,
                file_size=file_size,
                uploaded_by=uploaded_by_id,
                status="Uploading",
                chunk_count=0,
                embedding_count=0,
                created_at=now_utc
            )
            db.session.add(doc_record)
            db.session.commit()
            logger.info(f"Created PostgreSQL Document row ID={doc_record.id} for UUID '{doc_id}'")

        # Step 2: PDF extraction
        t_step2 = time.time()
        logger.info(f"[Ingestion Step 2/10] Extracting text from {unique_filename} (RAM: {get_ram_usage_mb()})")
        update_document_status(doc_record, "Extracting")
        reader = PdfReader(raw_path)
        total_pages = len(reader.pages)

        if current_app.config.get("DATABASE_ENABLED", True) and doc_record:
            doc_record.pages = total_pages
            db.session.commit()

        raw_pages_data = []
        cleaned_pages_data = []
        raw_char_count = 0
        clean_char_count = 0

        # Step 3: Cleaning
        t_step3 = time.time()
        logger.info(f"[Ingestion Step 3/10] Cleaning extracted text (RAM: {get_ram_usage_mb()}) - Extracted in {t_step3 - t_step2:.2f}s")
        update_document_status(doc_record, "Cleaning")
        for idx, page in enumerate(reader.pages):
            raw_text = page.extract_text() or ""
            raw_char_count += len(raw_text)

            raw_pages_data.append({
                "page_number": idx + 1,
                "text": raw_text
            })

            cleaned_text = clean_page_text(raw_text)

            if len(cleaned_text.strip()) < 5:
                logger.info(f"Skipping empty or non-text page {idx + 1} in document {doc_id}")
                continue

            clean_char_count += len(cleaned_text)
            cleaned_pages_data.append({
                "page_number": idx + 1,
                "text": cleaned_text
            })

        save_raw_extracted_text(doc_id, raw_pages_data)
        save_cleaned_text(doc_id, cleaned_pages_data)
        del raw_pages_data
        gc.collect()

        # Step 4: Chunking
        t_step4 = time.time()
        logger.info(f"[Ingestion Step 4/10] Chunking text with strategy '{active_strategy}' (RAM: {get_ram_usage_mb()}) - Cleaned in {t_step4 - t_step3:.2f}s")
        update_document_status(doc_record, "Chunking")
        chunk_size = current_app.config.get("CHUNK_SIZE", 500)
        chunk_overlap = current_app.config.get("CHUNK_OVERLAP", 100)
        semantic_threshold = current_app.config.get("SEMANTIC_THRESHOLD", 0.6)

        document_chunks = []
        for page_data in cleaned_pages_data:
            page_chunks = chunk_page_text(
                cleaned_text=page_data["text"],
                doc_id=doc_id,
                page_number=page_data["page_number"],
                chunk_size=chunk_size,
                overlap=chunk_overlap,
                strategy=active_strategy,
                threshold=semantic_threshold
            )
            document_chunks.extend(page_chunks)

        save_document_chunks(doc_id, document_chunks, CHUNKS_DIR)
        del cleaned_pages_data
        gc.collect()

        # Bulk insert Chunk records into PostgreSQL if DATABASE_ENABLED is True
        if current_app.config.get("DATABASE_ENABLED", True) and doc_record:
            chunk_objects = []
            for chunk_idx, c_item in enumerate(document_chunks):
                c_uuid = c_item.get("chunk_id") or str(uuid.uuid4())
                c_obj = Chunk(
                    chunk_uuid=c_uuid,
                    document_id=doc_record.id,
                    page_number=c_item.get("page_number", 1),
                    chunk_index=chunk_idx,
                    text=c_item.get("text", ""),
                    faiss_vector_id=None,
                    created_at=now_utc
                )
                chunk_objects.append(c_obj)

            db.session.add_all(chunk_objects)
            doc_record.chunk_count = len(document_chunks)
            db.session.commit()
            del chunk_objects
            gc.collect()

        # Step 5: Loading embedding model (lazy load)
        t_step5 = time.time()
        logger.info(f"[Ingestion Step 5/10] Loading embedding model (RAM: {get_ram_usage_mb()}) - Chunked in {t_step5 - t_step4:.2f}s")
        update_document_status(doc_record, "Embedding")

        # Step 6 & Step 7: Generating & Saving embeddings
        t_step6 = time.time()
        logger.info(f"[Ingestion Step 6/10] Generating & Step 7 Saving chunk embeddings (RAM: {get_ram_usage_mb()})")
        try:
            from app.services.embedding_generator import generate_embeddings_for_document
            emb_res = generate_embeddings_for_document(doc_id)
            embedding_status = "completed"
            embedding_model = emb_res["embedding_model"]
            embedding_dimension = emb_res["embedding_dimension"]

            if current_app.config.get("DATABASE_ENABLED", True) and doc_record:
                doc_record.embedding_count = len(document_chunks)
                db.session.commit()
        except Exception as e:
            logger.error(f"Failed to generate embeddings for document {doc_id}: {e}")
            raise RuntimeError(f"Embedding generation failed: {str(e)}") from e

        # Step 8: Building FAISS
        t_step8 = time.time()
        logger.info(f"[Ingestion Step 8/10] Building FAISS vector index for doc {doc_id} (RAM: {get_ram_usage_mb()}) - Embeddings in {t_step8 - t_step6:.2f}s")
        try:
            from app.services.vector_index import get_vector_index_service
            index_service = get_vector_index_service()
            index_service.add_document_to_index(doc_id)
        except Exception as e:
            logger.error(f"Failed to update FAISS index for document {doc_id}: {e}")
            raise RuntimeError(f"FAISS indexing failed: {str(e)}") from e

        # Step 9: Database update
        t_step9 = time.time()
        logger.info(f"[Ingestion Step 9/10] Updating final database status (RAM: {get_ram_usage_mb()}) - FAISS indexed in {t_step9 - t_step8:.2f}s")
        update_document_status(doc_record, "Completed")

        # Save JSON backup metadata
        metadata = {
            "document_id": doc_id,
            "filename": unique_filename,
            "original_filename": original_filename,
            "file_size_bytes": file_size,
            "total_pages": total_pages,
            "active_pages": len(document_chunks),
            "raw_char_count": raw_char_count,
            "clean_char_count": clean_char_count,
            "total_chunks": len(document_chunks),
            "chunking_strategy": active_strategy,
            "chunk_size": chunk_size,
            "chunk_overlap": chunk_overlap,
            "semantic_threshold": semantic_threshold if active_strategy == "semantic" else None,
            "upload_timestamp": now_utc.isoformat().replace("+00:00", "Z"),
            "status": "processed",
            "embedding_status": embedding_status,
            "embedding_model": embedding_model,
            "embedding_dimension": embedding_dimension
        }
        save_metadata(doc_id, metadata)
        
        del document_chunks
        gc.collect()

        # Step 10: Ingestion finished
        t_finish = time.time()
        logger.info(f"[Ingestion Step 10/10] Successfully ingested document {doc_id} ({original_filename}) in {t_finish - t_start:.2f}s total (RAM: {get_ram_usage_mb()})")

        return {
            "success": True,
            "document_id": doc_id,
            "metadata": metadata
        }

    except Exception as e:
        logger.exception(f"Error occurred while processing {original_filename}: {e}")
        if current_app.config.get("DATABASE_ENABLED", True):
            try:
                db.session.rollback()
                if doc_record:
                    doc_record.status = "Failed"
                    db.session.commit()
            except Exception as status_err:
                logger.error(f"Failed to set status='Failed' for doc {doc_id}: {status_err}")

        # Clean up raw file on disk if created
        if os.path.exists(raw_path):
            try:
                os.remove(raw_path)
            except Exception:
                pass

        gc.collect()

        return {
            "success": False,
            "original_filename": original_filename,
            "error": f"Ingestion pipeline failure: {str(e)}"
        }

def list_ingested_documents() -> List[Dict[str, Any]]:
    """
    Retrieves all successfully processed documents from PostgreSQL.
    Falls back to scanning file metadata if database query fails or is disabled.

    Returns:
        List[Dict[str, Any]]: List of document metadata dictionaries.
    """
    documents = []
    if current_app.config.get("DATABASE_ENABLED", True):
        try:
            db_docs = Document.query.filter(
                Document.status.in_(["Completed", "processed", "Indexed"])
            ).order_by(Document.created_at.desc()).all()

            for doc in db_docs:
                documents.append({
                    "document_id": doc.document_uuid,
                    "id": doc.id,
                    "filename": doc.filename,
                    "original_filename": doc.title,
                    "file_size_bytes": doc.file_size,
                    "total_pages": doc.pages,
                    "total_chunks": doc.chunk_count,
                    "embedding_count": doc.embedding_count,
                    "status": "processed",
                    "upload_timestamp": doc.created_at.isoformat().replace("+00:00", "Z") if doc.created_at else "",
                    "uploaded_by": doc.uploaded_by
                })
            return documents
        except Exception as e:
            logger.error(f"Error querying documents from PostgreSQL database: {e}. Falling back to file metadata.")

    # Fallback to scanning metadata folder if database is unavailable or disabled
    if not os.path.exists(METADATA_DIR):
        return documents

    for fname in os.listdir(METADATA_DIR):
        if fname.endswith("_meta.json"):
            meta_path = os.path.join(METADATA_DIR, fname)
            try:
                with open(meta_path, "r", encoding="utf-8") as f:
                    meta_data = json.load(f)
                    if meta_data.get("status") in ["processed", "Completed", "Indexed"]:
                        documents.append(meta_data)
            except Exception as read_err:
                logger.error(f"Error reading metadata file {meta_path}: {read_err}")

    documents.sort(key=lambda x: x.get("upload_timestamp", ""), reverse=True)
    return documents
