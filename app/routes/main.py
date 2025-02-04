import json
from flask import Blueprint, render_template, jsonify, request, current_app
from ..models import Cluster, Device, Connection
from ..services import NetboxService, RabbitMQService
from .. import db

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    """Render main workboard page"""
    clusters = Cluster.query.all()
    return render_template('index.html', clusters=clusters)

@bp.route('/api/clusters')
def list_clusters():
    """List all clusters"""
    clusters = Cluster.query.all()
    return jsonify([cluster.to_dict() for cluster in clusters])

@bp.route('/api/clusters/<cluster_id>')
def get_cluster(cluster_id):
    """Get cluster details including devices and connections"""
    cluster = Cluster.query.get_or_404(cluster_id)
    
    # Get all devices for this cluster
    devices = Device.query.filter_by(cluster_id=cluster_id).all()
    
    # Get all connections for this cluster
    connections = Connection.query.filter_by(cluster_id=cluster_id).all()
    
    # Format for Cytoscape.js
    elements = {
        'nodes': [
            {
                'data': {
                    'id': str(device.id),
                    'label': device.name,
                    'type': device.device_type,
                    'interfaces': list(device.interfaces) if device.interfaces else [],
                    'metadata': dict(device.meta_data) if device.meta_data else {}
                },
                'position': device.position or {'x': 0, 'y': 0}
            }
            for device in devices
        ],
        'edges': [conn.to_cytoscape_edge() for conn in connections]
    }
    
    return jsonify({
        'cluster': cluster.to_dict(),
        'elements': elements
    })

@bp.route('/api/clusters/<cluster_id>/sync', methods=['POST'])
def sync_cluster(cluster_id):
    """Trigger cluster sync"""
    try:
        cluster = Cluster.query.get_or_404(cluster_id)
        
        # Don't schedule if sync already in progress
        if cluster.sync_in_progress:
            return jsonify({'status': 'sync already in progress'})
        
        # Schedule sync task
        rabbitmq = RabbitMQService.from_app(current_app)
        if rabbitmq.schedule_sync(int(cluster_id)):
            cluster.sync_in_progress = True
            db.session.commit()
            return jsonify({'status': 'sync scheduled'})
        return jsonify({'error': 'failed to schedule sync'}), 500
    except Exception as e:
        current_app.logger.error(f"Error scheduling sync: {str(e)}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/clusters/<cluster_id>/sync/status', methods=['GET'])
def get_sync_status(cluster_id):
    """Get cluster sync status"""
    try:
        cluster = Cluster.query.get_or_404(cluster_id)
        return jsonify({
            'sync_in_progress': cluster.sync_in_progress,
            'last_sync': cluster.last_sync.isoformat() if cluster.last_sync else None
        })
    except Exception as e:
        current_app.logger.error(f"Error getting sync status: {str(e)}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/clusters/<cluster_id>/layout', methods=['POST'])
def save_layout(cluster_id):
    """Save Cytoscape layout positions"""
    try:
        cluster = Cluster.query.get_or_404(cluster_id)
        layout_data = request.json
        
        # Update device positions
        for node_id, position in layout_data.items():
            device = Device.query.get(node_id)
            if device and device.cluster_id == cluster.id:
                device.position = position
        
        db.session.commit()
        return jsonify({'status': 'layout saved'})
    except Exception as e:
        current_app.logger.error(f"Error saving layout: {str(e)}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/clusters/<cluster_id>/export', methods=['GET'])
def export_cluster(cluster_id):
    """Export cluster as YAML"""
    try:
        cluster = Cluster.query.get_or_404(cluster_id)
        devices = Device.query.filter_by(cluster_id=cluster_id).all()
        connections = Connection.query.filter_by(cluster_id=cluster_id).all()
        
        # Build export data structure
        export_data = {
            'cluster': {
                'name': cluster.name,
                'type': cluster.type,
                'netbox_id': cluster.netbox_id,
                'metadata': dict(cluster.meta_data) if cluster.meta_data else {}
            },
            'devices': [
                {
                    'name': device.name,
                    'type': device.device_type,
                    'netbox_id': device.netbox_id,
                    'interfaces': list(device.interfaces) if device.interfaces else [],
                    'metadata': dict(device.meta_data) if device.meta_data else {}
                }
                for device in devices
            ],
            'connections': [
                {
                    'device_a': conn.device_a.name,
                    'device_b': conn.device_b.name,
                    'interface_a': conn.interface_a,
                    'interface_b': conn.interface_b,
                    'metadata': dict(conn.meta_data) if conn.meta_data else {}
                }
                for conn in connections
            ]
        }
        
        return jsonify(export_data)
    except Exception as e:
        current_app.logger.error(f"Error exporting cluster: {str(e)}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/netbox/sync', methods=['POST'])
def sync_from_netbox():
    """Sync all clusters from Netbox"""
    try:
        netbox = NetboxService.from_app(current_app)
        clusters = netbox.get_clusters()
        
        for cluster_data in clusters:
            # Schedule sync for each cluster
            rabbitmq = RabbitMQService.from_app(current_app)
            rabbitmq.schedule_sync(cluster_data['id'])
        
        return jsonify({
            'status': 'sync scheduled',
            'clusters': len(clusters)
        })
    except Exception as e:
        current_app.logger.error(f"Error syncing from Netbox: {str(e)}")
        return jsonify({'error': str(e)}), 500
