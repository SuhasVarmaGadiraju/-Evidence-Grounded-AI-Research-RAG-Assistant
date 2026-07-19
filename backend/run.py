import os
from app import create_app

# Create Flask application instance
app = create_app()

if __name__ == "__main__":
    host = app.config.get("HOST", "0.0.0.0")
    port = app.config.get("PORT", 5000)
    debug = app.config.get("DEBUG", True)
    
    app.logger.info(f"Running application on http://{host}:{port}")
    app.run(host=host, port=port, debug=debug)
