import os
from app import create_app
from asgiref.wsgi import WsgiToAsgi

# Create Flask application with Docker-aware configuration
flask_app = create_app(os.getenv('FLASK_CONFIG', 'development'))

# Create WSGI to ASGI wrapper for Uvicorn
app = WsgiToAsgi(flask_app)
