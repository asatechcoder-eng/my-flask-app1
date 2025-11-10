# api/index.py
import sys
import os
from pathlib import Path
from flask import Flask, Response
from werkzeug.wrappers import Request

# Ensure Python can find your Flask app file
sys.path.append(str(Path(__file__).resolve().parent.parent))

# Import your existing Flask app
from app import app  # Make sure this matches your file name (app.py)

# ✅ Vercel entry point
@Request.application
def handler(request):
    # Use Flask's test_client to handle the request internally
    with app.test_client() as client:
        environ = request.environ
        response = client.open(
            path=environ["PATH_INFO"],
            query_string=environ["QUERY_STRING"],
            method=environ["REQUEST_METHOD"],
            headers={key: value for key, value in request.headers},
            data=environ["wsgi.input"].read(),
        )
        return Response(
            response.get_data(),
            status=response.status_code,
            headers=response.headers
        )
