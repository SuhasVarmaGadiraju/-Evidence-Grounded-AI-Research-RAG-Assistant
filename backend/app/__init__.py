import time
from flask import Flask
from flask_cors import CORS
from app.config import get_config
from app.utils.logging import setup_logger
from app.utils.error_handlers import register_error_handlers
from app.routes import register_routes
from app.services.warmup import warmup_services
from database import init_db

STARTUP_TIME = time.time()

def create_app():
    """Application factory for Flask app."""
    # 1. Initialize Flask app
    app = Flask(__name__)
    
    # 2. Load configuration
    config_obj = get_config()
    app.config.from_object(config_obj)
    app.config["STARTUP_TIME"] = STARTUP_TIME
    
    # 3. Setup logging
    logger = setup_logger(log_level=app.config.get("LOG_LEVEL", "INFO"))
    logger.info(f"Initializing app in {app.config.get('FLASK_ENV')} mode...")
    
    # 4. Initialize Database (SQLAlchemy)
    try:
        init_db(app)
    except Exception as e:
        logger.warning(f"Running without PostgreSQL. Database features are disabled.")
        app.config["DATABASE_ENABLED"] = False
    
    # 5. Enable Cross-Origin Resource Sharing (CORS)
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    logger.info("CORS successfully configured for /api/*")
    
    # 6. Register error handlers
    register_error_handlers(app)
    logger.info("Global error handlers registered.")
    
    # 7. Register routes / blueprints
    register_routes(app)
    logger.info("Blueprints and routes registered.")
    
    # 8. Startup Warm-up (Skip if ENABLE_WARMUP evaluates to False or during testing)
    if not app.config.get("TESTING", False) and app.config.get("ENABLE_WARMUP", False):
        try:
            warmup_status = warmup_services(app)
            app.config["WARMUP_STATUS"] = warmup_status
        except Exception as e:
            logger.warning(f"Startup warmup encountered warning: {e}")
    else:
        logger.info("Startup warmup skipped.")
        app.config["WARMUP_STATUS"] = {"skipped": True}

    return app
