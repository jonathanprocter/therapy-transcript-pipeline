import os
import logging
import sys
from app import app
from scheduler import start_background_scheduler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('application.log', mode='a')
    ]
)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    try:
        logger.info("=== Starting Therapy Transcript Processor ===")
        
        # Start the background scheduler for monitoring Dropbox
        logger.info("Initializing background scheduler...")
        start_background_scheduler()
        logger.info("Background scheduler started successfully")
        
        # Run the Flask application
        port = int(os.environ.get("PORT", 5000))
        logger.info(f"Starting Flask app on host 0.0.0.0 port {port}")
        logger.info("Application ready to accept connections")
        
        app.run(host="0.0.0.0", port=port, debug=False, threaded=True)
        
    except KeyboardInterrupt:
        logger.info("Application shutdown requested by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Critical error starting application: {str(e)}")
        logger.error("Application failed to start properly")
        sys.exit(1)
else:
    # For production deployment, start scheduler when module is imported
    try:
        logger.info("Starting scheduler in production mode")
        start_background_scheduler()
    except Exception as e:
        logger.warning(f"Error starting scheduler in production: {str(e)}")
