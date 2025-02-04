from flask import Blueprint

# Create v1 blueprint with url_prefix
bp = Blueprint('api_v1', __name__, url_prefix='/api/v1')

# Import route modules
from . import clusters, sync, settings

# Register route blueprints with their prefixes
bp.register_blueprint(clusters.bp, url_prefix='/clusters')
bp.register_blueprint(sync.bp, url_prefix='/sync')
bp.register_blueprint(settings.bp, url_prefix='/settings')
