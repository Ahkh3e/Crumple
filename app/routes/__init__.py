from .main import bp as main_bp
from .settings import bp as settings_bp
from .api import bp as api_bp
from .auth import bp as auth_bp

__all__ = ['main_bp', 'settings_bp', 'api_bp', 'auth_bp']
