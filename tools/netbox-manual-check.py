#!/usr/bin/env python3
"""
NetBox Manual Check Script

This script performs manual API checks against a NetBox instance to verify cluster,
device, interface and cable connection data. It's particularly useful for debugging
connection visualization issues.

Usage:
    python netbox-manual-check.py --url https://netbox.example.com --token YOUR_API_TOKEN --cluster CLUSTER_ID
    python netbox-manual-check.py --cluster CLUSTER_ID  # Uses NETBOX_URL and NETBOX_TOKEN from environment

Environment Variables:
    NETBOX_URL: The URL of your NetBox instance
    NETBOX_TOKEN: Your NetBox API token
"""

import os
import sys
import json
import logging
import argparse
from datetime import datetime
from urllib.parse import urljoin
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ANSI color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'

# Set up logging
log_dir = 'logs'
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

log_file = os.path.join(log_dir, f'netbox-check-{datetime.now().strftime("%Y%m%d-%H%M%S")}.log')
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)

class NetBoxChecker:
    def __init__(self, base_url, token, verify_ssl=True):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        
        # Configure retries
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
            'Authorization': f'Token {token}',
            'Accept': 'application/json',
        })
        
        # SSL verification
        self.session.verify = verify_ssl
        if not verify_ssl:
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    def make_request(self, method, endpoint, **kwargs):
        """Make HTTP request with error handling and logging"""
        url = urljoin(self.base_url, endpoint)
        logging.debug(f"Making {method} request to {url}")
        logging.debug(f"Request params: {kwargs.get('params')}")
        
        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"Request failed: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                logging.error(f"Response content: {e.response.text}")
            raise

    def check_cluster(self, cluster_id):
        """Check cluster details"""
        print(f"\n{Colors.HEADER}Checking Cluster {cluster_id}{Colors.END}")
        try:
            data = self.make_request('GET', f'/api/virtualization/clusters/{cluster_id}/')
            print(f"{Colors.GREEN}✓ Found cluster: {data.get('name', 'Unknown')}{Colors.END}")
            logging.debug(f"Cluster data: {json.dumps(data, indent=2)}")
            return data
        except Exception as e:
            print(f"{Colors.FAIL}✗ Failed to get cluster: {str(e)}{Colors.END}")
            return None

    def check_devices(self, cluster_id):
        """Check devices in cluster"""
        print(f"\n{Colors.HEADER}Checking Devices in Cluster{Colors.END}")
        try:
            data = self.make_request('GET', '/api/dcim/devices/', 
                                   params={'cluster_id': cluster_id})
            devices = data.get('results', [])
            if devices:
                print(f"{Colors.GREEN}✓ Found {len(devices)} devices{Colors.END}")
                for device in devices:
                    print(f"  • {device.get('name', 'Unknown')}")
            else:
                print(f"{Colors.WARNING}! No devices found{Colors.END}")
            
            logging.debug(f"Devices data: {json.dumps(devices, indent=2)}")
            return devices
        except Exception as e:
            print(f"{Colors.FAIL}✗ Failed to get devices: {str(e)}{Colors.END}")
            return []

    def check_interfaces(self, device_id):
        """Check interfaces for a device"""
        print(f"\n{Colors.BLUE}Checking Interfaces for Device {device_id}{Colors.END}")
        try:
            data = self.make_request('GET', '/api/dcim/interfaces/',
                                   params={'device_id': device_id})
            interfaces = data.get('results', [])
            if interfaces:
                print(f"{Colors.GREEN}✓ Found {len(interfaces)} interfaces{Colors.END}")
                for iface in interfaces:
                    print(f"  • {iface.get('name', 'Unknown')} ({iface.get('type', 'Unknown')})")
                    if iface.get('connected_endpoint'):
                        print(f"    └─ Connected to: {iface['connected_endpoint'].get('name', 'Unknown')}")
                    else:
                        print(f"    └─ {Colors.WARNING}No connection{Colors.END}")
            else:
                print(f"{Colors.WARNING}! No interfaces found{Colors.END}")
            
            logging.debug(f"Interfaces data for device {device_id}: {json.dumps(interfaces, indent=2)}")
            return interfaces
        except Exception as e:
            print(f"{Colors.FAIL}✗ Failed to get interfaces: {str(e)}{Colors.END}")
            return []

    def check_cables(self, device_id):
        """Check cable connections for a device"""
        print(f"\n{Colors.BLUE}Checking Cables for Device {device_id}{Colors.END}")
        try:
            data = self.make_request('GET', '/api/dcim/cables/',
                                   params={'device_id': device_id})
            cables = data.get('results', [])
            if cables:
                print(f"{Colors.GREEN}✓ Found {len(cables)} cables{Colors.END}")
                for cable in cables:
                    if cable.get('a_terminations') and cable.get('b_terminations'):
                        a_term = cable['a_terminations'][0]
                        b_term = cable['b_terminations'][0]
                        print(f"  • Cable {cable['id']}: {a_term['object'].get('name', 'Unknown')} → {b_term['object'].get('name', 'Unknown')}")
                    else:
                        print(f"  • Cable {cable['id']}: {Colors.WARNING}Invalid terminations{Colors.END}")
            else:
                print(f"{Colors.WARNING}! No cables found{Colors.END}")
            
            logging.debug(f"Cables data for device {device_id}: {json.dumps(cables, indent=2)}")
            return cables
        except Exception as e:
            print(f"{Colors.FAIL}✗ Failed to get cables: {str(e)}{Colors.END}")
            return []

def main():
    parser = argparse.ArgumentParser(description='Check NetBox API data for cluster visualization')
    parser.add_argument('--url', help='NetBox URL (or set NETBOX_URL env var)')
    parser.add_argument('--token', help='NetBox API token (or set NETBOX_TOKEN env var)')
    parser.add_argument('--cluster', required=True, help='Cluster ID to check')
    parser.add_argument('--no-verify', action='store_true', help='Disable SSL verification')
    args = parser.parse_args()

    # Get settings from args or environment
    netbox_url = args.url or os.environ.get('NETBOX_URL')
    netbox_token = args.token or os.environ.get('NETBOX_TOKEN')

    if not netbox_url or not netbox_token:
        print(f"{Colors.FAIL}Error: NetBox URL and token are required. Provide them as arguments or environment variables.{Colors.END}")
        sys.exit(1)

    print(f"\n{Colors.BOLD}NetBox Manual Check{Colors.END}")
    print(f"URL: {netbox_url}")
    print(f"Cluster ID: {args.cluster}")
    print(f"Log file: {log_file}")

    checker = NetBoxChecker(netbox_url, netbox_token, verify_ssl=not args.no_verify)

    # Check cluster
    cluster = checker.check_cluster(args.cluster)
    if not cluster:
        sys.exit(1)

    # Check devices
    devices = checker.check_devices(args.cluster)
    if not devices:
        sys.exit(1)

    # Check interfaces and cables for each device
    for device in devices:
        device_id = device['id']
        print(f"\n{Colors.BOLD}Device: {device['name']}{Colors.END}")
        checker.check_interfaces(device_id)
        checker.check_cables(device_id)

    print(f"\n{Colors.GREEN}Check complete! See {log_file} for detailed logs.{Colors.END}")

if __name__ == '__main__':
    main()
