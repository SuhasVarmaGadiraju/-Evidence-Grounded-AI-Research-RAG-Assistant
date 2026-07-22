import uuid
from flask import Blueprint, jsonify, request, send_from_directory
import os
import json
from app.services.ingest import list_ingested_documents
import logging

logger = logging.getLogger("rag_backend.routes.documents")

documents_bp = Blueprint("documents", __name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CHUNKS_DIR = os.path.join(BASE_DIR, "data", "chunks")
RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
METADATA_DIR = os.path.join(BASE_DIR, "data", "metadata")

@documents_bp.route("/documents", methods=["GET"])
def get_documents():
    """Lists successfully processed documents from file system metadata."""
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
def get_document_chunks(doc_id):
    """
    Returns the generated text chunks for a specific document ID.
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
def rename_document(doc_id):
    """
    Renames a document by updating its filename in metadata.
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

    meta_path = os.path.join(METADATA_DIR, f"{doc_id}_meta.json")
    if not os.path.exists(meta_path):
        return jsonify({
            "success": False,
            "message": f"Document with ID {doc_id} not found."
        }), 404

    try:
        with open(meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)

        meta["filename"] = new_filename
        meta["original_filename"] = new_filename

        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)

        return jsonify({
            "success": True,
            "message": "Document renamed successfully.",
            "document": meta
        }), 200
    except Exception as e:
        logger.exception(f"Failed to rename document {doc_id}")
        return jsonify({
            "success": False,
            "message": f"Failed to rename document: {str(e)}"
        }), 500

@documents_bp.route("/documents/<doc_id>/download", methods=["GET"])
def download_document(doc_id):
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

    meta_path = os.path.join(METADATA_DIR, f"{doc_id}_meta.json")
    if not os.path.exists(meta_path):
        return jsonify({
            "success": False,
            "message": f"Document metadata for ID {doc_id} not found."
        }), 404

    try:
        with open(meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)
        
        raw_filename = meta.get("filename")
        if not raw_filename or not os.path.exists(os.path.join(RAW_DIR, raw_filename)):
            return jsonify({
                "success": False,
                "message": f"Raw PDF file for document ID {doc_id} not found."
            }), 404

        return send_from_directory(
            RAW_DIR,
            raw_filename,
            as_attachment=True,
            download_name=meta.get("original_filename", raw_filename)
        )
    except Exception as e:
        logger.exception(f"Failed to download document {doc_id}")
        return jsonify({
            "success": False,
            "message": f"Download failed: {str(e)}"
        }), 500

@documents_bp.route("/documents/<doc_id>", methods=["DELETE"])
def delete_document(doc_id):
    """
    Deletes all files associated with a given document ID and rebuilds FAISS index.
    """
    try:
        uuid.UUID(doc_id, version=4)
    except ValueError:
        return jsonify({
            "success": False,
            "message": "Invalid document ID format. Must be a valid UUIDv4."
        }), 400

    meta_path = os.path.join(METADATA_DIR, f"{doc_id}_meta.json")
    if not os.path.exists(meta_path):
        return jsonify({
            "success": False,
            "message": f"Document with ID {doc_id} not found."
        }), 404

    try:
        with open(meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)
        raw_filename = meta.get("filename")
    except Exception as e:
        logger.error(f"Failed to read metadata for deletion of {doc_id}: {e}")
        raw_filename = None

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
