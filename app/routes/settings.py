from flask import Blueprint, render_template, jsonify, request
from ..models.settings import AppSettings
from ..services.netbox import NetboxService
from ..tasks.sync import perform_sync
from .. import db

bp = Blueprint('settings', __name__, url_prefix='/settings')

@bp.route('/', methods=['GET'])
def index():
    """Settings page"""
    settings = AppSettings.get_settings()
    return render_template('settings.html', settings=settings)

@bp.route('/api/settings', methods=['GET'])
def get_settings():
    """Get current settings"""
    settings = AppSettings.get_settings()
    return jsonify(settings.to_dict())

@bp.route('/api/settings', methods=['POST'])
def update_settings():
    """Update settings"""
    settings = AppSettings.get_settings()
    data = request.get_json()
    
    # Update settings
    settings.update(data)
    
    # Test connection if Netbox settings changed
    if 'netbox_url' in data or 'netbox_token' in data:
        try:
            netbox = NetboxService(settings.netbox_url, settings.netbox_token)
            netbox.test_connection()
            settings.is_connected = True
            db.session.commit()
        except Exception as e:
            settings.is_connected = False
            db.session.commit()
            return jsonify({'error': str(e)}), 400
    
    return jsonify(settings.to_dict())

@bp.route('/api/test-connection', methods=['POST'])
def test_connection():
    """Test Netbox connection"""
    settings = AppSettings.get_settings()
    try:
        netbox = NetboxService(settings.netbox_url, settings.netbox_token)
        netbox.test_connection()
        settings.is_connected = True
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Connection successful'})
    except Exception as e:
        settings.is_connected = False
        db.session.commit()
        return jsonify({'status': 'error', 'message': str(e)}), 400

@bp.route('/api/sync-now', methods=['POST'])
def sync_now():
    """Trigger immediate sync"""
    settings = AppSettings.get_settings()
    
    # Perform sync
    success, error = perform_sync(settings)
    
    if success:
        return jsonify({
            'status': 'success',
            'message': 'Sync completed successfully',
            'last_sync': settings.last_sync.strftime('%Y-%m-%d %H:%M:%S UTC') if settings.last_sync else None
        })
    else:
        return jsonify({
            'status': 'error',
            'message': error
        }), 400
