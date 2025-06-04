import os
from flask import Flask
from src.main import app as application

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3000))
    application.run(host="0.0.0.0", port=port)
