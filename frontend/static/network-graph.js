let cy;

async function loadNetworkData() {
    try {
        const response = await fetch('/api/v1/clusters/');
        if (response.ok) {
            const clusters = await response.json();
            updateNetworkGraph(clusters);
        }
    } catch (error) {
        console.error('Error loading network data:', error);
    }
}

function updateNetworkGraph(clusters) {
    // Clear existing elements
    cy.elements().remove();

    // Add nodes and edges for each cluster
    clusters.forEach(cluster => {
        // Add devices as nodes
        cluster.devices.forEach(device => {
            cy.add({
                group: 'nodes',
                data: {
                    id: device.id,
                    label: device.name,
                    type: device.device_type.category,
                    cluster: cluster.name
                }
            });
        });

        // Add connections as edges
        cluster.connections.forEach(conn => {
            cy.add({
                group: 'edges',
                data: {
                    source: conn.source_device.id,
                    target: conn.target_device.id,
                    status: conn.status
                }
            });
        });
    });

    // Apply layout
    cy.layout({
        name: 'cose',
        padding: 50,
        nodeRepulsion: 8000,
        idealEdgeLength: 100
    }).run();
}

function initializeNetworkGraph() {
    cy = cytoscape({
        ...cytoscapeConfig,
        container: document.getElementById('cy')
    });
    loadNetworkData();
}

function updateSystemStatus(status) {
    // Update database health
    const dbHealthBar = document.querySelector('.status-progress-bar');
    if (dbHealthBar) {
        dbHealthBar.style.width = `${status.db_health}%`;
    }

    // Update API health
    const apiHealthBar = document.querySelectorAll('.status-progress-bar')[1];
    if (apiHealthBar) {
        apiHealthBar.style.width = `${status.api_health}%`;
    }

    // Update NetBox status
    if (status.netbox_status) {
        const container = document.getElementById('netbox-status-container');
        const badge = document.getElementById('netbox-status-badge');
        const icon = document.getElementById('netbox-status-icon');
        const text = document.getElementById('netbox-status-text');
        const healthBar = document.getElementById('netbox-health-bar');

        container.classList.remove('hidden');
        text.textContent = status.netbox_status.charAt(0).toUpperCase() + status.netbox_status.slice(1);

        // Get status type
        const statusType = status.netbox_status === 'connected' ? 'success' 
                        : status.netbox_status === 'syncing' ? 'info' 
                        : 'warning';

        // Update status classes
        badge.className = `status-badge status-badge-${statusType}`;
        icon.className = `fas fa-${status.netbox_status === 'connected' ? 'check-circle' : status.netbox_status === 'syncing' ? 'sync' : 'exclamation-circle'} mr-1`;
        healthBar.className = `status-progress-bar status-progress-${statusType}`;
        healthBar.style.width = `${status.netbox_health}%`;
    } else {
        document.getElementById('netbox-status-container').classList.add('hidden');
    }
}
