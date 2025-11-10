# api/index.py

from ..app import app  # 👈 Import your existing app.py Flask app

def handler(event, context):
    return app(event, context)
