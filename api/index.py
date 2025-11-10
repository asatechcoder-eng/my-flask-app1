# api/index.py
import sys, os
from pathlib import Path

# Make sure Python can find your app.py
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app import app  # import your existing Flask app

# Required by Vercel to handle incoming requests
def handler(event, context):
    return app(event, context)
