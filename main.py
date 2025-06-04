import os
import logging
from app import app
from scheduler import start_background_scheduler

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    try:
        # Start the background scheduler for monitoring Dropbox
        logger.info("Starting background scheduler...")
        start_background_scheduler()
        
        # Run the Flask application
        port = int(os.environ.get("PORT", 5000))
        logger.info(f"Starting Flask app on host 0.0.0.0 port {port}")
        app.run(host="0.0.0.0", port=port, debug=False, threaded=True)
    except Exception as e:
        logger.error(f"Error starting application: {str(e)}")
        raise
else:
    # For production deployment, start scheduler when module is imported
    try:
        start_background_scheduler()
    except Exception as e:
        logger.error(f"Error starting scheduler: {str(e)}")
