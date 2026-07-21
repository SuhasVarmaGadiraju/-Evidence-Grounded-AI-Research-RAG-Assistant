import logging
from flask import Blueprint, request, jsonify, current_app
from app.services.evaluation_service import EvaluationService
from app.services.evaluation_dataset import EvaluationDatasetService

logger = logging.getLogger("rag_backend.routes.evaluation")

evaluation_bp = Blueprint("evaluation", __name__)

@evaluation_bp.route("/evaluation/run", methods=["POST"])
def run_evaluation():
    """
    POST /api/evaluation/run
    Evaluates a single query against optional ground truth and expected documents/pages.
    """
    try:
        data = request.get_json() or {}
        question = data.get("question", "").strip()

        if not question:
            return jsonify({
                "success": False,
                "error": "Missing or empty required field 'question'."
            }), 400

        ground_truth = data.get("ground_truth", "").strip() or None
        expected_documents = data.get("expected_documents")
        expected_pages = data.get("expected_pages")
        top_k = int(data.get("top_k", 5))

        eval_service = EvaluationService()
        result = eval_service.evaluate_query(
            question=question,
            ground_truth=ground_truth,
            expected_documents=expected_documents,
            expected_pages=expected_pages,
            top_k=top_k,
            save_to_history=True
        )

        return jsonify({
            "success": True,
            "data": result
        }), 200

    except Exception as e:
        logger.error(f"Unhandled error in run_evaluation endpoint: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "error": "Failed to run evaluation.",
            "details": str(e)
        }), 500

@evaluation_bp.route("/evaluation/dataset", methods=["POST", "GET"])
def manage_dataset():
    """
    POST /api/evaluation/dataset: Create evaluation dataset entry.
    GET /api/evaluation/dataset: List saved evaluation dataset entries.
    """
    dataset_service = EvaluationDatasetService()

    if request.method == "GET":
        try:
            dataset = dataset_service.get_dataset()
            return jsonify({
                "success": True,
                "data": dataset
            }), 200
        except Exception as e:
            logger.error(f"Error fetching dataset: {e}")
            return jsonify({
                "success": False,
                "error": "Failed to retrieve dataset.",
                "details": str(e)
            }), 500

    # POST
    try:
        data = request.get_json() or {}
        question = data.get("question", "").strip()
        ground_truth = data.get("ground_truth", "").strip()

        if not question or not ground_truth:
            return jsonify({
                "success": False,
                "error": "Fields 'question' and 'ground_truth' are required."
            }), 400

        expected_documents = data.get("expected_documents")
        expected_pages = data.get("expected_pages")

        entry = dataset_service.add_dataset_entry(
            question=question,
            ground_truth=ground_truth,
            expected_documents=expected_documents,
            expected_pages=expected_pages
        )

        return jsonify({
            "success": True,
            "message": "Evaluation dataset entry created successfully.",
            "data": entry
        }), 201

    except Exception as e:
        logger.error(f"Error creating dataset entry: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "error": "Failed to create dataset entry.",
            "details": str(e)
        }), 500

@evaluation_bp.route("/evaluation/history", methods=["GET"])
def get_evaluation_history():
    """
    GET /api/evaluation/history
    Returns list of previous evaluation runs.
    """
    try:
        limit = int(request.args.get("limit", 50))
        dataset_service = EvaluationDatasetService()
        history = dataset_service.get_history(limit=limit)
        return jsonify({
            "success": True,
            "data": history
        }), 200
    except Exception as e:
        logger.error(f"Error retrieving evaluation history: {e}")
        return jsonify({
            "success": False,
            "error": "Failed to retrieve evaluation history.",
            "details": str(e)
        }), 500

@evaluation_bp.route("/evaluation/report", methods=["GET"])
def get_evaluation_report():
    """
    GET /api/evaluation/report
    Returns aggregated evaluation quality statistics.
    """
    try:
        dataset_service = EvaluationDatasetService()
        report = dataset_service.get_report_statistics()
        return jsonify({
            "success": True,
            "data": report
        }), 200
    except Exception as e:
        logger.error(f"Error generating evaluation report: {e}")
        return jsonify({
            "success": False,
            "error": "Failed to generate evaluation report.",
            "details": str(e)
        }), 500
