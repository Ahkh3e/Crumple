from flask import Flask, render_template, jsonify, request
import os
import requests

app = Flask(__name__)

# Backend API URL
BACKEND_URL = os.getenv('BACKEND_URL', 'http://backend:8000')

@app.route('/')
def index():
    try:
        # Fetch all required data
        clusters_response = requests.get(f"{BACKEND_URL}/api/v1/clusters/")
        devices_response = requests.get(f"{BACKEND_URL}/api/v1/devices/")
        device_types_response = requests.get(f"{BACKEND_URL}/api/v1/devices/types/")
        netbox_response = requests.get(f"{BACKEND_URL}/api/v1/netbox/connections/")

        # Process clusters
        clusters = clusters_response.json() if clusters_response.ok else []
        clusters.sort(key=lambda x: x.get('updated_at', ''), reverse=True)
        recent_clusters = clusters[:5]
        active_clusters = len(clusters)
        healthy_clusters = sum(1 for c in clusters if not c.get('warnings', []))
        warning_clusters = active_clusters - healthy_clusters

        # Process devices
        devices = devices_response.json() if devices_response.ok else []
        total_devices = len(devices)
        server_count = sum(1 for d in devices if d.get('device_type', {}).get('category') == 'server')
        switch_count = sum(1 for d in devices if d.get('device_type', {}).get('category') == 'switch')

        # Process device types
        device_types = device_types_response.json() if device_types_response.ok else []
        total_device_types = len(device_types)
        manufacturers = {dt.get('manufacturer') for dt in device_types if dt.get('manufacturer')}
        manufacturer_count = len(manufacturers)

        # Process connections
        total_connections = sum(len(c.get('connections', [])) for c in clusters)
        active_connections = sum(len([conn for conn in c.get('connections', []) if conn.get('status') == 'active']) for c in clusters)
        pending_connections = total_connections - active_connections

        # Get NetBox status
        netbox_connections = netbox_response.json() if netbox_response.ok else []
        netbox_status = 'connected' if netbox_connections else None
        netbox_health = 100 if netbox_status == 'connected' else 0

        # System health metrics
        db_health = 100  # We'll implement actual health checks later
        api_health = 100 if all([clusters_response.ok, devices_response.ok, device_types_response.ok]) else 50

        return render_template('index.html',
            clusters=recent_clusters,
            total_devices=total_devices,
            server_count=server_count,
            switch_count=switch_count,
            active_clusters=active_clusters,
            healthy_clusters=healthy_clusters,
            warning_clusters=warning_clusters,
            total_connections=total_connections,
            active_connections=active_connections,
            pending_connections=pending_connections,
            total_device_types=total_device_types,
            manufacturer_count=manufacturer_count,
            db_health=db_health,
            api_health=api_health,
            netbox_status=netbox_status,
            netbox_health=netbox_health
        )
    except requests.exceptions.RequestException as e:
        return render_template('index.html', 
            clusters=[],
            total_devices=0,
            server_count=0,
            switch_count=0,
            active_clusters=0,
            healthy_clusters=0,
            warning_clusters=0,
            total_connections=0,
            active_connections=0,
            pending_connections=0,
            total_device_types=0,
            manufacturer_count=0,
            db_health=0,
            api_health=0,
            error=str(e)
        )

@app.route('/api/v1/system/status')
def system_status():
    """Get system status for dashboard"""
    try:
        # Check API health
        api_checks = [
            requests.get(f"{BACKEND_URL}/api/v1/clusters/"),
            requests.get(f"{BACKEND_URL}/api/v1/devices/"),
            requests.get(f"{BACKEND_URL}/api/v1/devices/types/")
        ]
        api_health = sum(check.ok for check in api_checks) / len(api_checks) * 100

        # Check NetBox status
        netbox_response = requests.get(f"{BACKEND_URL}/api/v1/netbox/connections/")
        netbox_connections = netbox_response.json() if netbox_response.ok else []
        netbox_status = 'connected' if netbox_connections else None
        netbox_health = 100 if netbox_status == 'connected' else 0

        return jsonify({
            'db_health': 100,  # We'll implement actual DB health checks later
            'api_health': api_health,
            'netbox_status': netbox_status,
            'netbox_health': netbox_health
        })
    except requests.exceptions.RequestException as e:
        return jsonify({
            'error': str(e),
            'db_health': 0,
            'api_health': 0
        }), 500

@app.route('/new-cluster')
def new_cluster():
    try:
        # Fetch device types
        response = requests.get(f"{BACKEND_URL}/api/v1/devices/types/")
        device_types = response.json() if response.ok else []
        
        return render_template('new_cluster.html', device_types=device_types)
    except requests.exceptions.RequestException as e:
        return render_template('new_cluster.html', device_types=[], error=str(e))

@app.route('/clusters')
def clusters():
    try:
        # Fetch clusters with their devices and connections
        response = requests.get(f"{BACKEND_URL}/api/v1/clusters/")
        clusters = response.json() if response.ok else []
        
        return render_template('clusters.html', clusters=clusters)
    except requests.exceptions.RequestException as e:
        return render_template('clusters.html', clusters=[], error=str(e))

@app.route('/clusters/<int:cluster_id>')
def cluster_detail(cluster_id):
    try:
        # Fetch cluster details
        cluster_response = requests.get(f"{BACKEND_URL}/api/v1/clusters/{cluster_id}")
        if not cluster_response.ok:
            return render_template('404.html'), 404
        
        cluster = cluster_response.json()
        
        # Fetch topology
        topology_response = requests.get(f"{BACKEND_URL}/api/v1/clusters/{cluster_id}/topology")
        topology = topology_response.json() if topology_response.ok else {"nodes": [], "edges": []}
        
        return render_template('cluster_detail.html', cluster=cluster, topology=topology)
    except requests.exceptions.RequestException as e:
        return render_template('cluster_detail.html', cluster=None, topology=None, error=str(e))

@app.route('/devices')
def devices():
    try:
        # Fetch device types
        device_types_response = requests.get(f"{BACKEND_URL}/api/v1/devices/types/")
        device_types = device_types_response.json() if device_types_response.ok else []

        # Fetch devices
        devices_response = requests.get(f"{BACKEND_URL}/api/v1/devices/")
        devices = devices_response.json() if devices_response.ok else []

        # Fetch clusters
        clusters_response = requests.get(f"{BACKEND_URL}/api/v1/clusters/")
        clusters = clusters_response.json() if clusters_response.ok else []

        return render_template('devices.html', 
                            device_types=device_types,
                            devices=devices,
                            clusters=clusters)
    except requests.exceptions.RequestException as e:
        # If API is not available, render template with empty data
        return render_template('devices.html', 
                            device_types=[],
                            devices=[],
                            clusters=[],
                            error=str(e))

@app.route('/netbox')
def netbox():
    """NetBox integration page"""
    return render_template('import_netbox.html')

@app.route('/device-types')
def device_types():
    try:
        # Fetch device types
        response = requests.get(f"{BACKEND_URL}/api/v1/devices/types/")
        device_types = response.json() if response.ok else []
        
        return render_template('device_types.html', device_types=device_types)
    except requests.exceptions.RequestException as e:
        return render_template('device_types.html', device_types=[], error=str(e))

# API proxy routes
@app.route('/api/v1/<path:endpoint>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def proxy_api(endpoint):
    url = f"{BACKEND_URL}/api/v1/{endpoint}"
    method = request.method
    headers = {
        key: value for key, value in request.headers
        if key.lower() not in ['host', 'content-length']
    }
    
    try:
        if method == 'GET':
            response = requests.get(url, headers=headers, params=request.args)
        elif method == 'POST':
            response = requests.post(url, headers=headers, json=request.get_json())
        elif method == 'PUT':
            response = requests.put(url, headers=headers, json=request.get_json())
        elif method == 'DELETE':
            response = requests.delete(url, headers=headers)
        
        return (
            response.content,
            response.status_code,
            {'Content-Type': response.headers.get('Content-Type', 'application/json')}
        )
    except requests.exceptions.RequestException as e:
        return jsonify({'error': str(e)}), 500

# WebSocket proxy route for real-time updates
@app.route('/ws')
def proxy_websocket():
    return jsonify({'error': 'WebSocket connections should be made directly to the backend'}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
