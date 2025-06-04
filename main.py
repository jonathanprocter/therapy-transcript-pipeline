import os
from app import app
from scheduler import start_background_scheduler

if __name__ == "__main__":
    # Start the background scheduler for monitoring Dropbox
    start_background_scheduler()
    
    # Run the Flask application
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
else:
    # For production deployment, start scheduler when module is imported
    start_background_scheduler()
