from flask import Blueprint
from .v1 import bp as v1_bp

# Create main API blueprint
bp = Blueprint('api', __name__)

# Register API version blueprints
bp.register_blueprint(v1_bp)

# Import routes to ensure they are registered
from . import v1
