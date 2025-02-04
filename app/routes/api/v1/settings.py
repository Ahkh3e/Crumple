from flask import Blueprint, jsonify, request, current_app
from app.models import AppSettings
from app.services import NetboxService

# Create blueprint without url_prefix since it's handled by parent
bp = Blueprint('api_v1_settings', __name__)

@bp.route('/')
def get_settings():
    """Get current settings"""
    try:
        settings = AppSettings.get_settings()
        return jsonify({
            'status': 'success',
            'data': settings.to_dict()
        })
    except Exception as e:
        current_app.logger.error(f"Error getting settings: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@bp.route('/', methods=['POST'])
def update_settings():
    """Update settings"""
    try:
        settings = AppSettings.get_settings()
        data = request.get_json()
        
        # Update settings
        settings.update(data)
        
        # Test connection if Netbox settings changed
        if 'netbox_url' in data or 'netbox_token' in data or 'verify_ssl' in data or 'timeout' in data:
            try:
                netbox = NetboxService()
                netbox.test_connection()
                settings.is_connected = True
            except Exception as e:
                settings.is_connected = False
                return jsonify({
                    'status': 'error',
                    'message': f'Failed to connect to Netbox: {str(e)}'
                }), 400
        
        return jsonify({
            'status': 'success',
            'message': 'Settings updated successfully',
            'data': settings.to_dict()
        })
    except Exception as e:
        current_app.logger.error(f"Error updating settings: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@bp.route('/test', methods=['POST'])
def test_connection():
    """Test Netbox connection"""
    try:
        settings = AppSettings.get_settings()
        netbox = NetboxService()
        netbox.test_connection()
        settings.is_connected = True
        
        return jsonify({
            'status': 'success',
            'message': 'Connection successful',
            'data': {
                'is_connected': True,
                'last_sync': settings.last_sync.strftime('%Y-%m-%d %H:%M:%S UTC') if settings.last_sync else None
            }
        })
    except Exception as e:
        current_app.logger.error(f"Connection test failed: {str(e)}")
        settings = AppSettings.get_settings()
        settings.is_connected = False
        return jsonify({
            'status': 'error',
            'message': f'Connection failed: {str(e)}'
        }), 400
