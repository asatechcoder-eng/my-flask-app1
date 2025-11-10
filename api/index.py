# api/index.py
import sys, os
from pathlib import Path
from flask import Flask
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from werkzeug.wrappers import Request, Response

# Ensure path to your app.py
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app import app  # Import your existing Flask app instance

# ✅ Create a callable for Vercel
def handler(request, context):
    # Convert Vercel request -> Werkzeug request
    @Request.application
    def application(request):
        return app.full_dispatch_request()
    return application(request)
