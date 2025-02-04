from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from sqlalchemy import text
from config import config

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()

def create_app(config_name='default'):
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config[config_name])
    
    # Configure for running behind proxy in Docker
    app.config['PREFERRED_URL_SCHEME'] = app.config.get('PREFERRED_URL_SCHEME', 'http')
    if app.config.get('SERVER_NAME'):
        app.config['SESSION_COOKIE_DOMAIN'] = app.config['SERVER_NAME']
    
    # Initialize extensions with app
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Register blueprints
    from .routes import main_bp, settings_bp, api_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(api_bp)
    
    # Create database tables
    with app.app_context():
        db.create_all()
        
        # Ensure schemas exist using text()
        db.session.execute(text('CREATE SCHEMA IF NOT EXISTS workboard'))
        db.session.execute(text('CREATE SCHEMA IF NOT EXISTS netbox'))
        db.session.commit()
    
    @app.after_request
    def after_request(response):
        """Ensure proper headers for Docker networking"""
        response.headers.add('X-Content-Type-Options', 'nosniff')
        response.headers.add('X-Frame-Options', 'DENY')
        response.headers.add('X-XSS-Protection', '1; mode=block')
        
        # Allow the frontend container to access the API
        if app.debug:
            response.headers.add('Access-Control-Allow-Origin', '*')
            response.headers.add('Access-Control-Allow-Headers', '*')
            response.headers.add('Access-Control-Allow-Methods', '*')
        
        return response

    @app.before_request
    def check_netbox_config():
        """Redirect to settings if Netbox is not configured"""
        from .models.settings import AppSettings
        from flask import request, redirect, url_for
        
        if not request.endpoint or request.endpoint.startswith('static'):
            return
        
        # Skip check for API and settings endpoints
        if request.endpoint.startswith('api.') or request.endpoint.startswith('settings.'):
            return
            
        settings = AppSettings.get_settings()
        if not settings.is_connected:
            return redirect(url_for('settings.index'))
    
    return app
