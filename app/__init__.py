from flask import Flask, session, request, jsonify, redirect, url_for
from flask_login import current_user
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from limits.storage import RedisStorage
from sqlalchemy import text
from config import config

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="redis://redis:6379/0"
)

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
    login_manager.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)
    
    # Configure security headers
    app.config['SESSION_COOKIE_SECURE'] = False  # Set to False for development
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['PERMANENT_SESSION_LIFETIME'] = 1800  # 30 minutes
    app.config['REMEMBER_COOKIE_DURATION'] = 1800  # 30 minutes
    app.config['REMEMBER_COOKIE_SECURE'] = False  # Set to False for development
    app.config['REMEMBER_COOKIE_HTTPONLY'] = True
    app.config['REMEMBER_COOKIE_SAMESITE'] = 'Lax'
    
    # Register blueprints
    from .routes import main_bp, settings_bp, api_bp, auth_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(auth_bp)
    
    # Configure Flask-Login
    from .models.user import User
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    
    # Create database tables and initialize admin user
    with app.app_context():
        db.create_all()
        
        # Ensure schemas exist using text()
        db.session.execute(text('CREATE SCHEMA IF NOT EXISTS workboard'))
        db.session.execute(text('CREATE SCHEMA IF NOT EXISTS netbox'))
        db.session.commit()
        
        # Create admin user if it doesn't exist
        from .models.user import User
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(username='admin', is_admin=True)
            admin.password = 'admin'  # This uses the password setter to hash
            db.session.add(admin)
            db.session.commit()

        # Initialize AppSettings if it doesn't exist
        from .models.settings import AppSettings
        settings = AppSettings.get_settings()
        if not settings:
            settings = AppSettings(
                netbox_url='',
                netbox_token='',
                sync_interval=300,
                is_connected=False
            )
            db.session.add(settings)
            db.session.commit()
    
    @app.after_request
    def after_request(response):
        """Ensure proper headers for Docker networking"""
        response.headers.add('X-Content-Type-Options', 'nosniff')
        response.headers.add('X-Frame-Options', 'DENY')
        response.headers.add('X-XSS-Protection', '1; mode=block')
        
        # Set security headers
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com https://code.jquery.com https://cdnjs.cloudflare.com; "
            "style-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com; "
            "font-src 'self' data:; "
            "img-src 'self' data:; "
            "connect-src 'self'; "
            "frame-ancestors 'none'"
        )
        
        # Set CORS headers for development only
        if app.debug:
            allowed_origin = 'http://localhost:3000'
            if request.headers.get('Origin') == allowed_origin:
                response.headers['Access-Control-Allow-Origin'] = allowed_origin
                response.headers['Access-Control-Allow-Headers'] = 'Content-Type, X-CSRF-Token'
                response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
                response.headers['Access-Control-Allow-Credentials'] = 'true'
        
        return response

    @app.before_request
    def check_auth_and_config():
        """Redirect to settings if Netbox is not configured"""
        from .models.settings import AppSettings
        from flask import request, redirect, url_for
        
        # Skip auth check for static files and login-related endpoints
        if not request.endpoint or request.endpoint.startswith('static'):
            return
            
        if request.endpoint and (
            request.endpoint.startswith('auth.') or 
            request.endpoint.startswith('static.')
        ):
            return

        # For API endpoints, return JSON response for auth failures
        is_api = request.endpoint and (
            request.endpoint.startswith('api.') or 
            '/api/' in request.path
        )
            
        # Require authentication for all other endpoints
        if not current_user.is_authenticated:
            if is_api:
                return jsonify({'error': 'Authentication required'}), 401
            return redirect(url_for('auth.login'))
        
        # Check Netbox connection status
        if request.endpoint != 'settings.index' and not is_api:
            # Only check connection status if not already on settings page and not an API endpoint
            settings = AppSettings.get_settings()
            if not settings or not settings.is_connected:
                return redirect(url_for('settings.index'))
    
    return app
