from flask import Blueprint, request, jsonify
from app.services.ingest import process_ingestion
from app.utils.error_handlers import APIException
import logging

logger = logging.getLogger("rag_backend.routes.upload")

upload_bp = Blueprint("upload", __name__)

@upload_bp.route("/upload", methods=["POST"])
def upload_files():
    """
    Accepts single or multiple PDF files under the form key 'files'.
    Also accepts a 'strategy' string ('fixed', 'recursive', or 'semantic') to specify chunking.
    Accepts optional user header details (X-User-UID, X-User-Email) for PostgreSQL user association.
    """
    if "files" not in request.files:
        raise APIException("No files payload found. Make sure form key is named 'files'", status_code=400)

    uploaded_files = request.files.getlist("files")
    if not uploaded_files or (len(uploaded_files) == 1 and uploaded_files[0].filename == ''):
        raise APIException("No selected file(s) to upload", status_code=400)

    # Extract chunking strategy from form payload (fallback to request args)
    strategy = request.form.get("strategy", default=request.args.get("strategy", default="fixed"))

    # Extract user info for association if available
    user_info = {
        "firebase_uid": request.headers.get("X-User-UID") or request.form.get("firebase_uid"),
        "email": request.headers.get("X-User-Email") or request.form.get("email")
    }

    results = []
    logger.info(f"Received upload request for {len(uploaded_files)} file(s) using strategy '{strategy}'")

    for file_storage in uploaded_files:
        result = process_ingestion(file_storage, strategy=strategy, user_info=user_info)
        results.append(result)

    # Check if all files failed validation or extraction
    all_failed = all(not r["success"] for r in results)

    # Structure final JSON response
    response_data = {
        "success": not all_failed,
        "files_count": len(results),
        "results": results
    }

    status_code = 207 if any(not r["success"] for r in results) and any(r["success"] for r in results) else (500 if all_failed else 200)

    if all_failed and all("Validation failed" in (r.get("error", "")) or "signature is invalid" in (r.get("error", "")) for r in results):
        status_code = 400

    return jsonify(response_data), status_code
