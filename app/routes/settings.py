from flask import Blueprint, render_template, jsonify, request, session
from flask_login import login_required, current_user
from flask_wtf.csrf import generate_csrf
from ..models.settings import AppSettings
from ..services.netbox import NetboxService
from ..tasks.sync import perform_sync
from .. import db, limiter, csrf

bp = Blueprint('settings', __name__, url_prefix='/settings')

# Exempt API endpoints from CSRF
csrf.exempt(bp)

@bp.route('/', methods=['GET'])
@login_required
def index():
    """Settings page"""
    settings = AppSettings.get_settings()
    return render_template('settings.html', settings=settings, csrf_token_value=generate_csrf())

@bp.route('/api/settings', methods=['GET'])
@login_required
@limiter.limit("30/minute")
def get_settings():
    """Get current settings"""
    try:
        # Check if user is authenticated
        if not current_user.is_authenticated:
            return jsonify({'error': 'Authentication required'}), 401

        settings = AppSettings.get_settings()
        response = jsonify(settings.to_dict(include_token=False))
        response.headers['Content-Type'] = 'application/json'
        return response
    except Exception as e:
        print(f"Error getting settings: {str(e)}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/settings', methods=['POST'])
@login_required
@limiter.limit("10/minute")
def update_settings():
    """Update settings"""
    try:
        # Check if user is authenticated
        if not current_user.is_authenticated:
            return jsonify({'error': 'Authentication required'}), 401

        settings = AppSettings.get_settings()
        data = request.get_json()
        
        # Log request data for debugging
        print(f"Update settings request: {data}")
        print(f"Request headers: {dict(request.headers)}")
        print(f"User authenticated: {current_user.is_authenticated}")
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        # Validate required fields
        if 'netbox_url' in data and not data['netbox_url']:
            return jsonify({'error': 'Netbox URL is required'}), 400
        
        # Update settings
        settings.update(data)
        
        # Test connection if Netbox settings changed
        if 'netbox_url' in data or 'netbox_token' in data:
            try:
                # Use the actual token for connection test
                netbox = NetboxService(settings.netbox_url, settings.get_token())
                netbox.test_connection()
                settings.is_connected = True
                db.session.commit()
            except Exception as e:
                settings.is_connected = False
                db.session.commit()
                return jsonify({'error': str(e)}), 400
        
        response = jsonify(settings.to_dict(include_token=False))
        response.headers['Content-Type'] = 'application/json'
        return response
    except Exception as e:
        print(f"Error updating settings: {str(e)}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/test-connection', methods=['POST'])
@login_required
@limiter.limit("10/minute")
def test_connection():
    """Test Netbox connection"""
    try:
        # Check if user is authenticated
        if not current_user.is_authenticated:
            return jsonify({'error': 'Authentication required'}), 401

        settings = AppSettings.get_settings()
        netbox = NetboxService(settings.netbox_url, settings.get_token())
        netbox.test_connection()
        settings.is_connected = True
        db.session.commit()
        
        response = jsonify({'status': 'success', 'message': 'Connection successful'})
        response.headers['Content-Type'] = 'application/json'
        return response
    except Exception as e:
        settings.is_connected = False
        db.session.commit()
        print(f"Error testing connection: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 400

@bp.route('/api/sync-now', methods=['POST'])
@login_required
@limiter.limit("2/minute")
def sync_now():
    """Trigger immediate sync"""
    try:
        # Check if user is authenticated
        if not current_user.is_authenticated:
            return jsonify({'error': 'Authentication required'}), 401

        settings = AppSettings.get_settings()
        
        # Perform sync
        success, error = perform_sync(settings)
        
        if success:
            response = jsonify({
                'status': 'success',
                'message': 'Sync completed successfully',
                'last_sync': settings.last_sync.strftime('%Y-%m-%d %H:%M:%S UTC') if settings.last_sync else None
            })
            response.headers['Content-Type'] = 'application/json'
            return response
        else:
            print(f"Sync error: {error}")
            return jsonify({
                'status': 'error',
                'message': error
            }), 400
    except Exception as e:
        print(f"Error during sync: {str(e)}")
        return jsonify({'error': str(e)}), 500
