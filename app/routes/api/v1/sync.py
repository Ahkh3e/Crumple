from flask import Blueprint, jsonify, current_app
from app.models import AppSettings, Cluster
from app.services import NetboxService
from app.tasks.sync import perform_sync
from app import db

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

@bp.route('/<cluster_id>', methods=['POST'])
def sync_cluster(cluster_id):
    """Sync a specific cluster"""
    try:
        # Try to find cluster by UUID first
        cluster = Cluster.query.get(cluster_id)
        if not cluster:
            # If not found, try by netbox_id
            cluster = Cluster.query.filter_by(netbox_id=cluster_id).first_or_404()
        
        # Don't schedule if sync already in progress
        if cluster.sync_in_progress:
            return jsonify({'status': 'sync already in progress'})
        
        # Mark sync as started
        cluster.sync_in_progress = True
        db.session.commit()
        
        try:
            # Perform sync directly
            netbox = NetboxService()
            netbox.sync_cluster(cluster.netbox_id)
            
            # Update sync status
            cluster.sync_in_progress = False
            cluster.last_sync = db.func.current_timestamp()
            db.session.commit()
            
            return jsonify({
                'status': 'success',
                'message': f'Cluster {cluster.name} synced successfully'
            })
        except Exception as e:
            # Reset sync status on error
            cluster.sync_in_progress = False
            db.session.commit()
            raise
            
    except Exception as e:
        current_app.logger.error(f"Error syncing cluster {cluster_id}: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500
