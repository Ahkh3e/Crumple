import logging
import time
import json
from urllib.parse import urlparse
import requests
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
from ..models.settings import AppSettings
from ..models import db, Cluster, Device, Connection

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Add file handler
import os
if not os.path.exists('logs'):
    os.makedirs('logs')
fh = logging.FileHandler('logs/netbox.log')
fh.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
logger.addHandler(fh)

class NetboxService:
    def __init__(self, url=None, token=None, verify_ssl=None, timeout=None):
        """Initialize with optional URL and token, otherwise load from settings"""
        settings = AppSettings.get_settings()
        self.base_url = url or settings.netbox_url
        # Use the actual token from settings if not provided
        self.token = token or settings.get_token()
        self.verify_ssl = verify_ssl if verify_ssl is not None else settings.verify_ssl
        self.timeout = timeout or settings.timeout

        logger.info(f"Initializing NetboxService with URL: {self.base_url}, SSL Verify: {self.verify_ssl}, Timeout: {self.timeout}")
        
        # Validate URL
        if self.base_url:
            try:
                parsed = urlparse(self.base_url)
                if not parsed.scheme or not parsed.netloc:
                    logger.error(f"Invalid Netbox URL format: {self.base_url}")
            except Exception as e:
                logger.error(f"Failed to parse Netbox URL: {str(e)}")
        
        # Set up session with retries
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=[500, 502, 503, 504]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Set headers
        self.session.headers.update({
            'Authorization': f'Token {self.token}',
            'Accept': 'application/json',
        })
        
        # Configure SSL verification
        self.session.verify = self.verify_ssl
        if not self.verify_ssl:
            logger.warning("SSL verification is disabled")
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    def _make_request(self, method, url, **kwargs):
        """Make HTTP request with error handling and logging"""
        start_time = time.time()
        request_id = f"req_{int(start_time * 1000)}"
        
        logger.debug(f"[{request_id}] Making {method} request to {url}")
        logger.debug(f"[{request_id}] Request params: {kwargs.get('params')}")
        
        try:
            kwargs['timeout'] = self.timeout
            response = self.session.request(method, url, **kwargs)
            elapsed = time.time() - start_time
            
            logger.debug(f"[{request_id}] Response time: {elapsed:.2f}s")
            logger.debug(f"[{request_id}] Response status: {response.status_code}")
            
            response.raise_for_status()
            data = response.json()
            
            if isinstance(data, dict):
                result_count = len(data.get('results', [])) if 'results' in data else 1
                logger.info(f"[{request_id}] Successfully retrieved {result_count} items from {url}")
            
            return data
            
        except Exception as e:
            logger.error(f"[{request_id}] Request error: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"[{request_id}] Response content: {e.response.text}")
            raise

    def test_connection(self):
        """Test connection to Netbox"""
        logger.info("Testing Netbox connection")
        try:
            self._make_request('GET', f'{self.base_url}/api/status/')
            logger.info("Connection test successful")
            return True
        except Exception as e:
            logger.error(f"Connection test failed: {str(e)}")
            raise

    def get_clusters(self):
        """Get all clusters from Netbox"""
        logger.info("Fetching all clusters")
        try:
            data = self._make_request('GET', f'{self.base_url}/api/virtualization/clusters/')
            results = data.get('results', [])
            logger.info(f"Retrieved {len(results)} clusters")
            return results
        except Exception as e:
            logger.error(f"Failed to fetch clusters: {str(e)}")
            raise

    def get_cluster(self, cluster_id):
        """Get a specific cluster from Netbox"""
        logger.info(f"Fetching cluster {cluster_id}")
        try:
            data = self._make_request('GET', f'{self.base_url}/api/virtualization/clusters/{cluster_id}/')
            logger.info(f"Successfully retrieved cluster {cluster_id}")
            return data
        except Exception as e:
            logger.error(f"Failed to fetch cluster {cluster_id}: {str(e)}")
            raise

    def get_cluster_devices(self, cluster_id):
        """Get all devices in a cluster"""
        logger.info(f"Fetching devices for cluster {cluster_id}")
        try:
            data = self._make_request('GET', f'{self.base_url}/api/dcim/devices/', 
                                    params={'cluster_id': cluster_id})
            results = data.get('results', [])
            logger.info(f"Retrieved {len(results)} devices for cluster {cluster_id}")
            return results
        except Exception as e:
            logger.error(f"Failed to fetch devices for cluster {cluster_id}: {str(e)}")
            raise

    def get_device_interfaces(self, device_id):
        """Get all interfaces for a device"""
        logger.info(f"Fetching interfaces for device {device_id}")
        try:
            data = self._make_request('GET', f'{self.base_url}/api/dcim/interfaces/',
                                    params={'device_id': device_id})
            results = data.get('results', [])
            logger.info(f"Retrieved {len(results)} interfaces for device {device_id}")
            return results
        except Exception as e:
            logger.error(f"Failed to fetch interfaces for device {device_id}: {str(e)}")
            raise

    def get_device_connections(self, device_id):
        """Get all connections for a device"""
        logger.info(f"Fetching connections for device {device_id}")
        try:
            data = self._make_request('GET', f'{self.base_url}/api/dcim/cables/',
                                    params={'device_id': device_id})
            results = data.get('results', [])
            
            valid_results = []
            skipped_count = 0
            
            for result in results:
                # Check if both terminations are present
                if (result.get('a_terminations') and result.get('b_terminations') and
                    len(result['a_terminations']) > 0 and len(result['b_terminations']) > 0):
                    valid_results.append(result)
                else:
                    skipped_count += 1
                    logger.warning(f"Skipping connection without valid terminations for device {device_id}")
                    logger.debug(f"Skipped connection data: {json.dumps(result, indent=2)}")
            
            logger.info(f"Retrieved {len(valid_results)} valid connections for device {device_id} (skipped {skipped_count})")
            return valid_results
        except Exception as e:
            logger.error(f"Failed to fetch connections for device {device_id}: {str(e)}")
            raise

    def sync_cluster(self, cluster_id):
        """Sync a cluster and all its components"""
        logger.info(f"Starting sync for cluster {cluster_id}")
        try:
            # Get cluster data
            cluster_data = self.get_cluster(cluster_id)
            cluster = Cluster.query.filter_by(netbox_id=cluster_id).first()
            if not cluster:
                cluster = Cluster(netbox_id=cluster_id)
            cluster.update_from_netbox(cluster_data)
            db.session.commit()

            # Get and sync devices
            devices = self.get_cluster_devices(cluster_id)
            for device_data in devices:
                device = Device.query.filter_by(netbox_id=device_data['id']).first()
                if not device:
                    device = Device(netbox_id=device_data['id'], cluster_id=cluster.id)
                device.update_from_netbox(device_data)
                
                # Get and update interfaces
                interfaces = self.get_device_interfaces(device_data['id'])
                device.update_interfaces(interfaces)
                db.session.commit()

            # Get and sync connections
            # Clear existing connections for this cluster
            Connection.query.filter_by(cluster_id=cluster.id).delete()
            
            # Create new connections
            processed_cables = set()
            for device in cluster.devices:
                cables = self.get_device_connections(device.netbox_id)
                for cable_data in cables:
                    cable_id = cable_data['id']
                    if cable_id in processed_cables:
                        continue
                    
                    # Get termination points
                    a_term = cable_data['a_terminations'][0]['object']
                    b_term = cable_data['b_terminations'][0]['object']
                    
                    # Create connection
                    connection = Connection(
                        cluster_id=cluster.id,
                        device_a_id=Device.query.filter_by(name=a_term['device']['name']).first().id,
                        interface_a=a_term['name'],
                        device_b_id=Device.query.filter_by(name=b_term['device']['name']).first().id,
                        interface_b=b_term['name']
                    )
                    connection.update_from_netbox(cable_data)
                    db.session.add(connection)
                    processed_cables.add(cable_id)
            
            db.session.commit()
            logger.info(f"Successfully synced cluster {cluster_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to sync cluster {cluster_id}: {str(e)}")
            db.session.rollback()
            raise
