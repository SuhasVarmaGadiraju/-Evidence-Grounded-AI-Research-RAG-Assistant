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
    If DATABASE_URL is not configured, disables database features gracefully.
    """
    db_uri = app.config.get("SQLALCHEMY_DATABASE_URI")
    if not db_uri:
        logger.warning("Running without PostgreSQL. Database features are disabled.")
        app.config["DATABASE_ENABLED"] = False
        return

    try:
        db.init_app(app)
        migrate.init_app(app, db)
        app.config["DATABASE_ENABLED"] = True
        logger.info("PostgreSQL initialized successfully.")
    except Exception as e:
        logger.warning(f"Running without PostgreSQL. Database features are disabled.")
        app.config["DATABASE_ENABLED"] = False
