import logging
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

logger = logging.getLogger("rag_backend.database")

# Single Primary SQLAlchemy and Flask-Migrate instances
db = SQLAlchemy()
migrate = Migrate()

def init_db(app):
    """
    Initializes the single global SQLAlchemy instance and Flask-Migrate with the Flask app.
    If DATABASE_URL is not configured, registers db with app and disables database features gracefully.
    """
    # Always call db.init_app(app) to bind app with the global SQLAlchemy instance
    db.init_app(app)

    db_uri = app.config.get("SQLALCHEMY_DATABASE_URI")
    if not db_uri:
        logger.warning("Running without PostgreSQL. Database features are disabled.")
        app.config["DATABASE_ENABLED"] = False
        return

    try:
        migrate.init_app(app, db)
        app.config["DATABASE_ENABLED"] = True
        logger.info("PostgreSQL initialized successfully.")
    except Exception as e:
        logger.warning(f"Running without PostgreSQL. Database features are disabled: {e}")
        app.config["DATABASE_ENABLED"] = False
