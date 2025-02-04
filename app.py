import os
from app import create_app

# Create Flask application with Docker-aware configuration
app = create_app(os.getenv('FLASK_CONFIG', 'development'))

if __name__ == '__main__':
    # In Docker, we need to listen on 0.0.0.0
    app.run(
        host='0.0.0.0',
        port=int(os.getenv('PORT', 3000)),
        # Use threaded mode for better container performance
        threaded=True
    )
