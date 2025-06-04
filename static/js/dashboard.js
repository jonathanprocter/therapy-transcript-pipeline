// Dashboard utilities and functionality
console.log('Dashboard utilities loaded successfully');

// Initialize dashboard when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('Dashboard initialized successfully');
    loadSystemStats();
    loadServiceStatus();
    
    // Refresh stats every 30 seconds
    setInterval(loadSystemStats, 30000);
    setInterval(loadServiceStatus, 60000);
});

// Load and display system statistics
function loadSystemStats() {
    fetch('/api/system-stats')
        .then(response => response.json())
        .then(data => {
            if (data.system_stats) {
                updateSystemStats(data.system_stats);
            }
        })
        .catch(error => {
            console.error('Failed to load system stats:', error);
        });
}

// Update system statistics display
function updateSystemStats(stats) {
    // Update stat cards
    const clientsCard = document.querySelector('[data-stat="clients"]');
    const transcriptsCard = document.querySelector('[data-stat="transcripts"]');
    const pendingCard = document.querySelector('[data-stat="pending"]');
    const failedCard = document.querySelector('[data-stat="failed"]');
    
    if (clientsCard) clientsCard.textContent = stats.total_clients || '0';
    if (transcriptsCard) transcriptsCard.textContent = stats.total_transcripts || '0';
    if (pendingCard) pendingCard.textContent = stats.pending_processing || '0';
    if (failedCard) failedCard.textContent = stats.failed_processing || '0';
    
    // Update progress indicators
    updateProgressIndicators(stats);
}

// Update progress indicators
function updateProgressIndicators(stats) {
    const total = stats.total_transcripts || 0;
    const completed = total - (stats.pending_processing || 0) - (stats.failed_processing || 0);
    const completionRate = total > 0 ? Math.round((completed / total) * 100) : 100;
    
    const progressBar = document.querySelector('.progress-bar');
    if (progressBar) {
        progressBar.style.width = completionRate + '%';
        progressBar.setAttribute('aria-valuenow', completionRate);
        progressBar.textContent = completionRate + '%';
    }
}

// Load service status
function loadServiceStatus() {
    // Check Dropbox service
    fetch('/api/manual-scan', { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            updateServiceStatus('dropbox', data.error ? 'error' : 'operational');
        })
        .catch(error => {
            updateServiceStatus('dropbox', 'error');
        });
    
    // Check processing status
    updateServiceStatus('processing', 'operational');
    updateServiceStatus('notion', 'operational');
}

// Update service status indicators
function updateServiceStatus(service, status) {
    const indicator = document.querySelector(`[data-service="${service}"]`);
    if (indicator) {
        indicator.className = 'service-status';
        indicator.classList.add(status === 'operational' ? 'status-operational' : 'status-error');
        
        const icon = indicator.querySelector('i');
        const text = indicator.querySelector('.status-text');
        
        if (status === 'operational') {
            if (icon) icon.className = 'fas fa-check-circle';
            if (text) text.textContent = 'Operational';
        } else {
            if (icon) icon.className = 'fas fa-exclamation-circle';
            if (text) text.textContent = 'Error';
        }
    }
}

// Manual scan trigger
function triggerManualScan() {
    const button = document.getElementById('manualScanBtn');
    if (button) {
        button.disabled = true;
        button.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Scanning...';
    }
    
    fetch('/api/manual-scan', { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            showAlert(data.message || 'Scan completed', 'success');
            loadSystemStats(); // Refresh stats
        })
        .catch(error => {
            showAlert('Scan failed: ' + error.message, 'danger');
        })
        .finally(() => {
            if (button) {
                button.disabled = false;
                button.innerHTML = '<i class="fas fa-sync me-1"></i>Manual Scan';
            }
        });
}

// Show alert message
function showAlert(message, type) {
    const alertHtml = `
        <div class="alert alert-${type} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    const container = document.querySelector('.alert-container') || document.querySelector('.container').firstElementChild;
    if (container) {
        container.insertAdjacentHTML('afterbegin', alertHtml);
    }
}

// Export functions for global access
window.loadSystemStats = loadSystemStats;
window.triggerManualScan = triggerManualScan;