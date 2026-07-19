import time
from flask import Flask
from flask_cors import CORS
from app.config import get_config
from app.utils.logging import setup_logger
from app.utils.error_handlers import register_error_handlers
from app.routes import register_routes
from app.services.warmup import warmup_services

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
    
    # 4. Enable Cross-Origin Resource Sharing (CORS)
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    logger.info("CORS successfully configured for /api/*")
    
    # 5. Register error handlers
    register_error_handlers(app)
    logger.info("Global error handlers registered.")
    
    # 6. Register routes / blueprints
    register_routes(app)
    logger.info("Blueprints and routes registered.")
    
    # 7. Eager Startup Warm-up (Skip if running under unit tests)
    if not app.config.get("TESTING", False):
        try:
            warmup_status = warmup_services(app)
            app.config["WARMUP_STATUS"] = warmup_status
        except Exception as e:
            logger.warning(f"Startup warmup encountered warning: {e}")

    return app
