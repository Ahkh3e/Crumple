from flask import Blueprint, jsonify, current_app
from app.models import AppSettings
from app.services import NetboxService
from app.tasks.sync import perform_sync

# Create blueprint without url_prefix since it's handled by parent
bp = Blueprint('api_v1_sync', __name__)

@bp.route('/', methods=['POST'])
def sync_all():
    """Sync all clusters from Netbox"""
    try:
        settings = AppSettings.get_settings()
        success, error = perform_sync(settings)
        
        if success:
            return jsonify({
                'status': 'success',
                'message': 'All clusters synced successfully',
                'last_sync': settings.last_sync.strftime('%Y-%m-%d %H:%M:%S UTC') if settings.last_sync else None
            })
        else:
            return jsonify({
                'status': 'error',
                'message': error
            }), 500
            
    except Exception as e:
        current_app.logger.error(f"Error during sync: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@bp.route('/status')
def sync_status():
    """Get sync status"""
    try:
        settings = AppSettings.get_settings()
        return jsonify({
            'status': 'success',
            'data': {
                'is_connected': settings.is_connected,
                'last_sync': settings.last_sync.strftime('%Y-%m-%d %H:%M:%S UTC') if settings.last_sync else None,
                'sync_interval': settings.sync_interval
            }
        })
    except Exception as e:
        current_app.logger.error(f"Error getting sync status: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500
