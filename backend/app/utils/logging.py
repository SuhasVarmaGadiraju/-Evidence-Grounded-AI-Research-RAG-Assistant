import logging
import sys
from logging.handlers import RotatingFileHandler
import os

def setup_logger(name="rag_backend", log_level=logging.INFO):
    """Sets up a logger with console and file handlers."""
    logger = logging.getLogger(name)
    
    # If logger is already configured, don't add handlers again
    if logger.handlers:
        return logger
        
    logger.setLevel(log_level)
    
    # Formatter for log messages
    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File Handler (logs directory)
    logs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "logs")
    try:
        os.makedirs(logs_dir, exist_ok=True)
        file_handler = RotatingFileHandler(
            os.path.join(logs_dir, "app.log"),
            maxBytes=10485760,  # 10MB
            backupCount=5
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        logger.warning(f"Could not initialize file log handler: {e}")
        
    return logger
