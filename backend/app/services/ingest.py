import os
import uuid
import logging
from datetime import datetime, timezone
import json
from werkzeug.utils import secure_filename
from pypdf import PdfReader
from flask import current_app
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

# Ensure directories exist
for path in [RAW_DIR, EXTRACTED_DIR, PROCESSED_DIR, CHUNKS_DIR, METADATA_DIR]:
    os.makedirs(path, exist_ok=True)

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

def validate_pdf(file_stream, filename):
    """
    Validates that a file is a non-empty PDF under size constraints.
    Returns (is_valid, error_message).
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

def save_metadata(doc_id, metadata):
    """Saves document metadata to a JSON file."""
    meta_path = os.path.join(METADATA_DIR, f"{doc_id}_meta.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

def save_raw_extracted_text(doc_id, pages_data):
    """Saves raw page-by-page extracted text to a JSON file under data/extracted."""
    extracted_path = os.path.join(EXTRACTED_DIR, f"{doc_id}_raw.json")
    with open(extracted_path, "w", encoding="utf-8") as f:
        json.dump(pages_data, f, indent=2, ensure_ascii=False)

def save_cleaned_text(doc_id, pages_data):
    """Saves cleaned page-by-page text to a JSON file under data/processed."""
    processed_path = os.path.join(PROCESSED_DIR, f"{doc_id}_clean.json")
    with open(processed_path, "w", encoding="utf-8") as f:
        json.dump(pages_data, f, indent=2, ensure_ascii=False)

def process_ingestion(file_storage, strategy="fixed_character"):
    """
    Process a single PDF upload:
    1. Validate
    2. Save raw file with unique UUID prefix
    3. Extract text page-by-page (raw)
    4. Save raw extracted text in data/extracted
    5. Clean text page-by-page (skipping empty pages)
    6. Save cleaned text in data/processed
    7. Generate chunks based on chosen chunking strategy (fixed, recursive, or semantic)
    8. Save generated chunks in data/chunks
    9. Save metadata
    Returns a dict with document details.
    """
    original_filename = file_storage.filename
    doc_id = str(uuid.uuid4())
    safe_name = secure_filename(original_filename)
    unique_filename = f"{doc_id}_{safe_name}"
    raw_path = os.path.join(RAW_DIR, unique_filename)
    
    # Standardize strategy parameter
    if strategy == "semantic":
        active_strategy = "semantic"
    elif strategy == "recursive":
        active_strategy = "recursive"
    else:
        active_strategy = "fixed_character"
    
    # 1. Validation
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
        
        # 2. Extract text page by page
        logger.info(f"Extracting text from {unique_filename}...")
        reader = PdfReader(raw_path)
        total_pages = len(reader.pages)
        
        raw_pages_data = []
        cleaned_pages_data = []
        raw_char_count = 0
        clean_char_count = 0
        
        for idx, page in enumerate(reader.pages):
            raw_text = page.extract_text() or ""
            raw_char_count += len(raw_text)
            
            # Record raw text
            raw_pages_data.append({
                "page_number": idx + 1,
                "text": raw_text
            })
            
            # 3. Clean the text using the cleaner service
            cleaned_text = clean_page_text(raw_text)
            
            # 4. Skip empty pages
            if len(cleaned_text.strip()) < 5:
                logger.info(f"Skipping empty or non-text page {idx + 1} in document {doc_id}")
                continue
                
            clean_char_count += len(cleaned_text)
            cleaned_pages_data.append({
                "page_number": idx + 1,
                "text": cleaned_text
            })
            
        # 5. Save raw text & cleaned text
        save_raw_extracted_text(doc_id, raw_pages_data)
        save_cleaned_text(doc_id, cleaned_pages_data)
        
        # 6. Generate chunks using configured parameters and strategy
        chunk_size = current_app.config.get("CHUNK_SIZE", 500)
        chunk_overlap = current_app.config.get("CHUNK_OVERLAP", 100)
        semantic_threshold = current_app.config.get("SEMANTIC_THRESHOLD", 0.6)
        
        logger.info(f"Generating chunks for {doc_id} using strategy '{active_strategy}' ({chunk_size}/{chunk_overlap})...")
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
            
        # 7. Save chunks list
        save_document_chunks(doc_id, document_chunks, CHUNKS_DIR)
        
        # 7.5. Generate chunk embeddings
        logger.info(f"Generating chunk embeddings for document {doc_id}...")
        try:
            from app.services.embedding_generator import generate_embeddings_for_document
            emb_res = generate_embeddings_for_document(doc_id)
            embedding_status = "completed"
            embedding_model = emb_res["embedding_model"]
            embedding_dimension = emb_res["embedding_dimension"]
        except Exception as e:
            logger.error(f"Failed to generate embeddings for document {doc_id}: {e}")
            raise RuntimeError(f"Embedding generation failed: {str(e)}") from e
        
        # 7.6. Add embeddings to FAISS vector index
        logger.info(f"Adding embeddings to FAISS index for document {doc_id}...")
        try:
            from app.services.vector_index import get_vector_index_service
            index_service = get_vector_index_service()
            index_service.add_document_to_index(doc_id)
        except Exception as e:
            logger.error(f"Failed to update FAISS index for document {doc_id}: {e}")
            raise RuntimeError(f"FAISS indexing failed: {str(e)}") from e
        
        # 8. Record final metadata details
        metadata = {
            "document_id": doc_id,
            "filename": unique_filename,
            "original_filename": original_filename,
            "file_size_bytes": file_size,
            "total_pages": total_pages,
            "active_pages": len(cleaned_pages_data),
            "raw_char_count": raw_char_count,
            "clean_char_count": clean_char_count,
            "total_chunks": len(document_chunks),
            "chunking_strategy": active_strategy,
            "chunk_size": chunk_size,
            "chunk_overlap": chunk_overlap,
            "semantic_threshold": semantic_threshold if active_strategy == "semantic" else None,
            "upload_timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "status": "processed",
            "embedding_status": embedding_status,
            "embedding_model": embedding_model,
            "embedding_dimension": embedding_dimension
        }
        
        save_metadata(doc_id, metadata)
        logger.info(f"Successfully processed, cleaned, and chunked document {doc_id} ({original_filename})")
        
        return {
            "success": True,
            "document_id": doc_id,
            "metadata": metadata
        }
        
    except Exception as e:
        logger.exception(f"Error occurred while processing {original_filename}")
        
        # Clean up files if they exist on failure
        if os.path.exists(raw_path):
            try:
                os.remove(raw_path)
            except Exception:
                pass
                
        return {
            "success": False,
            "original_filename": original_filename,
            "error": f"Ingestion pipeline failure: {str(e)}"
        }

def list_ingested_documents():
    """Scans metadata folder and returns a list of all successfully processed documents."""
    documents = []
    if not os.path.exists(METADATA_DIR):
        return documents
        
    for fname in os.listdir(METADATA_DIR):
        if fname.endswith("_meta.json"):
            meta_path = os.path.join(METADATA_DIR, fname)
            try:
                with open(meta_path, "r", encoding="utf-8") as f:
                    meta_data = json.load(f)
                    if meta_data.get("status") == "processed":
                        documents.append(meta_data)
            except Exception as e:
                logger.error(f"Error reading metadata file {meta_path}: {e}")
                
    # Sort by upload timestamp descending
    documents.sort(key=lambda x: x.get("upload_timestamp", ""), reverse=True)
    return documents
