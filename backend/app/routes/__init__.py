from app.routes.health import health_bp
from app.routes.upload import upload_bp
from app.routes.documents import documents_bp
from app.routes.query import query_bp
from app.routes.retrieval import retrieval_bp
from app.routes.prompt import prompt_bp
from app.routes.chat import chat_bp
from app.routes.evaluation import evaluation_bp
from app.routes.database_routes import database_bp

def register_routes(app):
    """Registers all API blueprints under the '/api' prefix."""
    app.register_blueprint(health_bp, url_prefix="/api")
    app.register_blueprint(upload_bp, url_prefix="/api")
    app.register_blueprint(documents_bp, url_prefix="/api")
    app.register_blueprint(query_bp, url_prefix="/api")
    app.register_blueprint(retrieval_bp, url_prefix="/api")
    app.register_blueprint(prompt_bp, url_prefix="/api")
    app.register_blueprint(chat_bp, url_prefix="/api")
    app.register_blueprint(evaluation_bp, url_prefix="/api")
    app.register_blueprint(database_bp, url_prefix="/api")



