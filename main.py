import os
import logging
import sys
from app import app

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

# Initialize scheduler when module is imported (for Gunicorn)
try:
    logger.info("=== Initializing Therapy Transcript Processor ===")
    
    # Test database connection
    with app.app_context():
        from models import Client
        client_count = Client.query.count()
        logger.info(f"Database connection successful - {client_count} clients found")
    
    # Start the background scheduler for monitoring Dropbox
    logger.info("Initializing background scheduler...")
    from scheduler import start_background_scheduler
    start_background_scheduler()
    logger.info("Background scheduler started successfully")
    logger.info("=== Application initialization completed successfully ===")
    
except Exception as e:
    logger.error(f"Error during application initialization: {str(e)}")
    # Don't exit, let Gunicorn handle the error

if __name__ == "__main__":
    # For direct Python execution (development only)
    try:
        port = int(os.environ.get("PORT", 5000))
        logger.info(f"Starting Flask app in development mode on port {port}")
        app.run(host="0.0.0.0", port=port, debug=True, threaded=True)
    except KeyboardInterrupt:
        logger.info("Application shutdown requested by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Critical error starting application: {str(e)}")
        sys.exit(1)
