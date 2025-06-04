import os
import sys

# Add the current directory to the path so Python can find the modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the Flask application
try:
    from src.main import app as application
except ImportError:
    from main import app as application

# This is the entry point for Gunicorn
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3000))
    application.run(host="0.0.0.0", port=port)
