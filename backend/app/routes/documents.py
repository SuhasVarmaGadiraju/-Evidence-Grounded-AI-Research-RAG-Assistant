import uuid
from flask import Blueprint, jsonify, request, send_from_directory
import os
import json
import logging
from typing import Tuple, Any, List, Dict, Optional

from database.database import db
from database.models.document import Document
from database.models.chunk import Chunk
from app.services.ingest import list_ingested_documents

logger = logging.getLogger("rag_backend.routes.documents")

documents_bp = Blueprint("documents", __name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CHUNKS_DIR = os.path.join(BASE_DIR, "data", "chunks")
RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
METADATA_DIR = os.path.join(BASE_DIR, "data", "metadata")

@documents_bp.route("/documents", methods=["GET"])
def get_documents() -> Tuple[Any, int]:
    """
    Lists successfully processed documents from PostgreSQL database (with file fallback).
    Returns identical response structure for frontend & API contracts.
    """
    try:
        docs = list_ingested_documents()

        # Retrieve vector index stats
        from app.services.vector_index import get_vector_index_service
        try:
            index_service = get_vector_index_service()
            index_stats = index_service.get_index_stats()
        except Exception as e:
            logger.warning(f"Could not load vector index statistics: {e}")
            index_stats = {
                "status": "error",
                "version": "N/A",
                "vector_count": 0
            }

        return jsonify({
            "success": True,
            "count": len(docs),
            "documents": docs,
            "index_stats": index_stats
        }), 200
    except Exception as e:
        logger.exception("Failed to retrieve document library")
        return jsonify({
            "success": False,
            "message": f"Library retrieval failed: {str(e)}"
        }), 500

@documents_bp.route("/documents/<doc_id>/chunks", methods=["GET"])
def get_document_chunks(doc_id: str) -> Tuple[Any, int]:
    """
    Returns text chunks for a document ID from PostgreSQL (falling back to disk JSON).
    Supports a 'limit' query parameter (default: 3) to control payload size.
    """
    try:
        uuid.UUID(doc_id, version=4)
    except ValueError:
        return jsonify({
            "success": False,
            "message": "Invalid document ID format. Must be a valid UUIDv4."
        }), 400

    limit = request.args.get("limit", default=3, type=int)

    # 1. Attempt retrieval from PostgreSQL database
    try:
        doc = Document.query.filter_by(document_uuid=doc_id).first()
        if doc:
            db_chunks = Chunk.query.filter_by(document_id=doc.id).order_by(Chunk.chunk_index).all()
            if db_chunks:
                all_chunks = [
                    {
                        "chunk_id": c.chunk_uuid,
                        "document_id": doc_id,
                        "page_number": c.page_number,
                        "chunk_index": c.chunk_index,
                        "text": c.text,
                        "faiss_vector_id": c.faiss_vector_id
                    }
                    for c in db_chunks
                ]
                preview_chunks = all_chunks[:limit] if limit > 0 else all_chunks
                return jsonify({
                    "success": True,
                    "document_id": doc_id,
                    "total_chunks": len(all_chunks),
                    "preview_limit": limit,
                    "chunks": preview_chunks
                }), 200
    except Exception as db_err:
        logger.warning(f"Failed to fetch chunks from PostgreSQL for doc {doc_id}: {db_err}. Trying file fallback.")

    # 2. File Fallback
    chunks_path = os.path.join(CHUNKS_DIR, f"{doc_id}_chunks.json")
    if not os.path.exists(chunks_path):
        return jsonify({
            "success": False,
            "message": f"Chunks for document ID {doc_id} were not found"
        }), 404

    try:
        with open(chunks_path, "r", encoding="utf-8") as f:
            all_chunks = json.load(f)

        preview_chunks = all_chunks[:limit] if limit > 0 else all_chunks

        return jsonify({
            "success": True,
            "document_id": doc_id,
            "total_chunks": len(all_chunks),
            "preview_limit": limit,
            "chunks": preview_chunks
        }), 200

    except Exception as e:
        logger.exception(f"Failed to read chunks for document {doc_id}")
        return jsonify({
            "success": False,
            "message": f"Failed to retrieve chunks: {str(e)}"
        }), 500

@documents_bp.route("/documents/<doc_id>", methods=["PATCH"])
def rename_document(doc_id: str) -> Tuple[Any, int]:
    """
    Renames a document by updating its title in PostgreSQL and JSON backup metadata.
    """
    try:
        uuid.UUID(doc_id, version=4)
    except ValueError:
        return jsonify({
            "success": False,
            "message": "Invalid document ID format. Must be a valid UUIDv4."
        }), 400

    data = request.get_json() or {}
    new_filename = data.get("filename", "").strip()
    if not new_filename:
        return jsonify({
            "success": False,
            "message": "New filename cannot be empty."
        }), 400

    doc_record = None
    meta_path = os.path.join(METADATA_DIR, f"{doc_id}_meta.json")

    # 1. Update PostgreSQL record
    try:
        doc_record = Document.query.filter_by(document_uuid=doc_id).first()
        if doc_record:
            doc_record.title = new_filename
            db.session.commit()
            logger.info(f"Renamed PostgreSQL Document ID={doc_record.id} title -> '{new_filename}'")
    except Exception as db_err:
        db.session.rollback()
        logger.warning(f"PostgreSQL rename failed for doc {doc_id}: {db_err}")

    # Check if doc exists in either DB or disk
    if not doc_record and not os.path.exists(meta_path):
        return jsonify({
            "success": False,
            "message": f"Document with ID {doc_id} not found."
        }), 404

    # 2. Update JSON backup file on disk
    meta = {}
    if os.path.exists(meta_path):
        try:
            with open(meta_path, "r", encoding="utf-8") as f:
                meta = json.load(f)

            meta["filename"] = new_filename
            meta["original_filename"] = new_filename

            with open(meta_path, "w", encoding="utf-8") as f:
                json.dump(meta, f, indent=2)
        except Exception as file_err:
            logger.warning(f"JSON metadata rename failed for doc {doc_id}: {file_err}")

    return jsonify({
        "success": True,
        "message": "Document renamed successfully.",
        "document": meta if meta else (doc_record.to_dict() if doc_record else {})
    }), 200

@documents_bp.route("/documents/<doc_id>/download", methods=["GET"])
def download_document(doc_id: str) -> Tuple[Any, int]:
    """
    Downloads the raw PDF file associated with the document ID.
    """
    try:
        uuid.UUID(doc_id, version=4)
    except ValueError:
        return jsonify({
            "success": False,
            "message": "Invalid document ID format. Must be a valid UUIDv4."
        }), 400

    raw_filename = None
    original_title = None

    # 1. Try PostgreSQL lookup
    try:
        doc = Document.query.filter_by(document_uuid=doc_id).first()
        if doc:
            raw_filename = doc.filename
            original_title = doc.title
    except Exception as db_err:
        logger.warning(f"PostgreSQL lookup failed during download of {doc_id}: {db_err}")

    # 2. Try JSON metadata lookup if missing
    meta_path = os.path.join(METADATA_DIR, f"{doc_id}_meta.json")
    if not raw_filename and os.path.exists(meta_path):
        try:
            with open(meta_path, "r", encoding="utf-8") as f:
                meta = json.load(f)
            raw_filename = meta.get("filename")
            original_title = meta.get("original_filename", raw_filename)
        except Exception as f_err:
            logger.warning(f"File metadata read error for download of {doc_id}: {f_err}")

    if not raw_filename or not os.path.exists(os.path.join(RAW_DIR, raw_filename)):
        return jsonify({
            "success": False,
            "message": f"Raw PDF file for document ID {doc_id} not found."
        }), 404

    try:
        return send_from_directory(
            RAW_DIR,
            raw_filename,
            as_attachment=True,
            download_name=original_title or raw_filename
        )
    except Exception as e:
        logger.exception(f"Failed to download document {doc_id}")
        return jsonify({
            "success": False,
            "message": f"Download failed: {str(e)}"
        }), 500

@documents_bp.route("/documents/<doc_id>", methods=["DELETE"])
def delete_document(doc_id: str) -> Tuple[Any, int]:
    """
    Deletes document record from PostgreSQL (cascading chunks), purges disk files, and rebuilds FAISS index.
    """
    try:
        uuid.UUID(doc_id, version=4)
    except ValueError:
        return jsonify({
            "success": False,
            "message": "Invalid document ID format. Must be a valid UUIDv4."
        }), 400

    meta_path = os.path.join(METADATA_DIR, f"{doc_id}_meta.json")
    raw_filename = None
    doc_record = None

    # 1. Lookup in PostgreSQL
    try:
        doc_record = Document.query.filter_by(document_uuid=doc_id).first()
        if doc_record:
            raw_filename = doc_record.filename
    except Exception as db_err:
        logger.warning(f"PostgreSQL lookup failed during deletion of {doc_id}: {db_err}")

    # 2. Check meta file if raw_filename not yet resolved
    if not raw_filename and os.path.exists(meta_path):
        try:
            with open(meta_path, "r", encoding="utf-8") as f:
                meta = json.load(f)
            raw_filename = meta.get("filename")
        except Exception as e:
            logger.error(f"Failed to read metadata for deletion of {doc_id}: {e}")

    # Return 404 if found in neither DB nor file system
    if not doc_record and not os.path.exists(meta_path) and not (raw_filename and os.path.exists(os.path.join(RAW_DIR, raw_filename))):
        return jsonify({
            "success": False,
            "message": f"Document with ID {doc_id} not found."
        }), 404

    # 3. Delete from PostgreSQL (Cascades deletion to chunks table)
    if doc_record:
        try:
            db.session.delete(doc_record)
            db.session.commit()
            logger.info(f"Deleted Document row ID={doc_record.id} from PostgreSQL (cascaded chunks).")
        except Exception as delete_err:
            db.session.rollback()
            logger.error(f"Failed to delete Document from PostgreSQL for {doc_id}: {delete_err}")

    # 4. Remove all files from disk
    paths_to_delete = [
        meta_path,
        os.path.join(BASE_DIR, "data", "extracted", f"{doc_id}_raw.json"),
        os.path.join(BASE_DIR, "data", "processed", f"{doc_id}_clean.json"),
        os.path.join(BASE_DIR, "data", "chunks", f"{doc_id}_chunks.json"),
        os.path.join(BASE_DIR, "data", "embeddings", f"{doc_id}_embeddings.npy"),
        os.path.join(BASE_DIR, "data", "embeddings", f"{doc_id}_meta.json")
    ]
    if raw_filename:
        paths_to_delete.append(os.path.join(RAW_DIR, raw_filename))

    deleted_count = 0
    for p in paths_to_delete:
        if os.path.exists(p):
            try:
                os.remove(p)
                deleted_count += 1
            except Exception as e:
                logger.error(f"Failed to remove file {p}: {e}")

    # 5. Rebuild FAISS vector index
    try:
        from app.services.vector_index import get_vector_index_service
        index_service = get_vector_index_service()
        index_service.rebuild_index()
    except Exception as e:
        logger.error(f"Failed to rebuild index after document deletion of {doc_id}: {e}")
        return jsonify({
            "success": False,
            "message": f"Purged files, but vector index rebuild failed: {str(e)}"
        }), 500

    return jsonify({
        "success": True,
        "message": f"Successfully deleted document {doc_id} and rebuilt vector index.",
        "purged_files": deleted_count
    }), 200
