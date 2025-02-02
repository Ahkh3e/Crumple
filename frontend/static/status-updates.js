function initializeStatusUpdates() {
    // Initial status update
    const container = document.getElementById('netbox-status-container');
    if (container) {
        const status = container.dataset.status;
        updateNetboxStatus(status);
    }

    // Update data periodically
    setInterval(async function() {
        try {
            const response = await fetch('/api/v1/system/status');
            if (response.ok) {
                const status = await response.json();
                updateSystemStatus(status);
            }
        } catch (error) {
            console.error('Error fetching system status:', error);
        }
    }, 30000); // Update every 30 seconds
}

function updateNetboxStatus(status) {
    const statusType = status === 'connected' ? 'success'
                    : status === 'syncing' ? 'info'
                    : 'warning';
    const iconName = status === 'connected' ? 'check-circle'
                  : status === 'syncing' ? 'sync'
                  : 'exclamation-circle';

    const badge = document.getElementById('netbox-status-badge');
    const icon = document.getElementById('netbox-status-icon');
    const healthBar = document.getElementById('netbox-health-bar');

    badge.className = `status-badge status-badge-${statusType}`;
    icon.className = `fas fa-${iconName} mr-1`;
    healthBar.className = `status-progress-bar status-progress-${statusType}`;
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
        const text = document.getElementById('netbox-status-text');
        const healthBar = document.getElementById('netbox-health-bar');

        container.classList.remove('hidden');
        text.textContent = status.netbox_status.charAt(0).toUpperCase() + status.netbox_status.slice(1);
        updateNetboxStatus(status.netbox_status);
        healthBar.style.width = `${status.netbox_health}%`;
    } else {
        document.getElementById('netbox-status-container').classList.add('hidden');
    }
}
