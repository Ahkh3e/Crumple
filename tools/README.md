# Tools Directory

This directory contains standalone utility scripts and tools to help with development, debugging and maintenance.

## Available Tools

### netbox-manual-check.py
A script to manually check NetBox API data for cluster connection visualization issues. It checks:
- Cluster details
- Devices in the cluster
- Interface configurations
- Cable connections

Usage:
```bash
# Using environment variables:
export NETBOX_URL=https://netbox.example.com
export NETBOX_TOKEN=your_api_token
python netbox-manual-check.py --cluster CLUSTER_ID

# Or using command line arguments:
python netbox-manual-check.py --url https://netbox.example.com --token your_api_token --cluster CLUSTER_ID

# To disable SSL verification:
python netbox-manual-check.py --no-verify --cluster CLUSTER_ID
```

The script logs all API responses to the logs directory for detailed debugging.
