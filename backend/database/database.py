import logging
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

logger = logging.getLogger("rag_backend.database")

# Primary SQLAlchemy and Flask-Migrate instances
db = SQLAlchemy()
migrate = Migrate()

def init_db(app):
    """
    Initializes SQLAlchemy and Flask-Migrate with the Flask app instance.
    Enforces strict database configuration without silent fallbacks.
    """
    db_uri = app.config.get("SQLALCHEMY_DATABASE_URI")
    if not db_uri:
        logger.error("DATABASE_URL / SQLALCHEMY_DATABASE_URI is not set in application configuration.")
        raise ValueError("Missing required database configuration: DATABASE_URL")
    
    db.init_app(app)
    migrate.init_app(app, db)
    logger.info("SQLAlchemy database instance and Flask-Migrate initialized successfully.")

