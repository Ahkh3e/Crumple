from flask import Blueprint, jsonify, current_app
from app.models import Cluster, Device, Connection
from app.services.netbox import NetboxService

# Create blueprint without url_prefix since it's handled by parent
bp = Blueprint('api_v1_clusters', __name__)

@bp.route('/')
def list_clusters():
    """List all clusters from database"""
    try:
        clusters = Cluster.query.all()
        return jsonify({
            'status': 'success',
            'data': [cluster.to_dict() for cluster in clusters]
        })
    except Exception as e:
        current_app.logger.error(f"Error listing clusters: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@bp.route('/<cluster_id>')
def get_cluster(cluster_id):
    """Get cluster details including devices and connections"""
    try:
        # Look up by netbox_id instead of UUID
        cluster = Cluster.query.filter_by(netbox_id=cluster_id).first_or_404()
        
        # Get all devices for this cluster
        devices = Device.query.filter_by(cluster_id=cluster.id).all()
        
        # Get all connections for this cluster
        connections = Connection.query.filter_by(cluster_id=cluster.id).all()
        
        # Format for Cytoscape.js
        elements = {
            'nodes': [
                {
                    'data': {
                        'id': str(device.id),
                        'label': device.name,
                        'type': device.device_type,
                        'interfaces': device.interfaces or [],
                        'meta_data': dict(device.meta_data) if device.meta_data else {}
                    },
                    'position': device.position or {'x': 0, 'y': 0}
                }
                for device in devices
            ],
            'edges': [
                {
                    'data': {
                        'id': f'e{conn.id}',
                        'source': str(conn.device_a_id),
                        'target': str(conn.device_b_id),
                        'sourceInterface': conn.interface_a,
                        'targetInterface': conn.interface_b,
                        'meta_data': dict(conn.meta_data) if conn.meta_data else {}
                    }
                }
                for conn in connections
            ]
        }
        
        # Convert cluster data
        cluster_data = cluster.to_dict()
        cluster_data['meta_data'] = dict(cluster.meta_data) if cluster.meta_data else {}
        cluster_data['layout_data'] = dict(cluster.layout_data) if cluster.layout_data else {}
        
        return jsonify({
            'status': 'success',
            'data': {
                'cluster': cluster_data,
                'elements': elements
            }
        })
    except Exception as e:
        current_app.logger.error(f"Error getting cluster {cluster_id}: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@bp.route('/<cluster_id>/sync', methods=['POST'])
def sync_cluster(cluster_id):
    """Sync specific cluster from Netbox"""
    try:
        # Look up by netbox_id
        cluster = Cluster.query.filter_by(netbox_id=cluster_id).first()
        if not cluster:
            cluster = Cluster(netbox_id=cluster_id)
        
        netbox = NetboxService()
        
        # Get cluster data from Netbox
        cluster_data = netbox.get_cluster(cluster_id)
        if not cluster_data:
            return jsonify({
                'status': 'error',
                'message': f'Cluster {cluster_id} not found in Netbox'
            }), 404
        
        # Update cluster from Netbox data
        cluster.update_from_netbox(cluster_data)
        
        # Get and sync devices
        devices = netbox.get_cluster_devices(cluster_id)
        for device_data in devices:
            device = Device.query.filter_by(netbox_id=device_data['id']).first()
            if not device:
                device = Device(
                    netbox_id=device_data['id'],
                    cluster_id=cluster.id
                )
            device.update_from_netbox(device_data)
            
            # Get and update interfaces
            interfaces = netbox.get_device_interfaces(device_data['id'])
            device.update_interfaces(interfaces)
        
        # Get and sync connections
        for device in cluster.devices:
            connections = netbox.get_device_connections(device.netbox_id)
            for conn_data in connections:
                if conn_data.get('connected_endpoint'):
                    # Find or create connection
                    connection = Connection.query.filter_by(
                        device_a_id=device.id,
                        interface_a=conn_data['name']
                    ).first()
                    if not connection:
                        connection = Connection(
                            cluster_id=cluster.id,
                            device_a_id=device.id,
                            interface_a=conn_data['name']
                        )
                    connection.update_from_netbox(conn_data)
        
        # Convert response data
        response_data = cluster.to_dict()
        response_data['meta_data'] = dict(cluster.meta_data) if cluster.meta_data else {}
        response_data['layout_data'] = dict(cluster.layout_data) if cluster.layout_data else {}
        
        return jsonify({
            'status': 'success',
            'message': f'Cluster {cluster_id} synced successfully',
            'data': response_data
        })
    except Exception as e:
        current_app.logger.error(f"Error syncing cluster {cluster_id}: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500
