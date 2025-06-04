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

// Manual scan functionality
function performManualScan() {
    const scanButton = document.getElementById('manualScanButton');
    const statusDiv = document.getElementById('scanStatus');

    if (scanButton) {
        scanButton.disabled = true;
        scanButton.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Scanning...';
    }

    if (statusDiv) {
        statusDiv.innerHTML = '<div class="alert alert-info"><i class="fas fa-spinner fa-spin me-2"></i>Scanning for new files...</div>';
    }

    fetch('/api/manual-scan', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (scanButton) {
            scanButton.disabled = false;
            scanButton.innerHTML = '<i class="fas fa-search me-1"></i>Scan Dropbox';
        }

        if (statusDiv) {
            if (data.error) {
                statusDiv.innerHTML = `<div class="alert alert-danger"><i class="fas fa-exclamation-triangle me-2"></i>${data.error}</div>`;
                updateServiceStatus('dropbox', 'error');
            } else {
                const newFileCount = data.new_files ? data.new_files.length : 0;
                statusDiv.innerHTML = `<div class="alert alert-success"><i class="fas fa-check me-2"></i>${data.message}</div>`;
                updateServiceStatus('dropbox', 'operational');

                // Update new files count in the dashboard
                updateNewFilesCount(newFileCount);
            }
        }

        // Refresh system stats and logs
        setTimeout(() => {
            loadSystemStats();
            loadProcessingLogs();
        }, 1000);
    })
    .catch(error => {
        console.error('Error during manual scan:', error);

        if (scanButton) {
            scanButton.disabled = false;
            scanButton.innerHTML = '<i class="fas fa-search me-1"></i>Scan Dropbox';
        }

        if (statusDiv) {
            statusDiv.innerHTML = '<div class="alert alert-danger"><i class="fas fa-exclamation-triangle me-2"></i>Scan failed. Please check your connection.</div>';
        }

        updateServiceStatus('dropbox', 'error');
    });
}

function updateNewFilesCount(count) {
    const countElement = document.getElementById('newFilesCount');
    if (countElement) {
        if (count > 0) {
            countElement.textContent = `${count} new files detected`;
            countElement.className = 'badge bg-warning';
        } else {
            countElement.textContent = 'No new files';
            countElement.className = 'badge bg-success';
        }
    }
}

// Load service status
function loadServiceStatus() {
    // Check system health endpoint
    fetch('/health')
        .then(response => response.json())
        .then(data => {
            if (data.status === 'healthy') {
                updateServiceStatus('processing', 'operational');

                // Update individual services based on health check
                if (data.services) {
                    updateServiceStatus('dropbox', data.services.dropbox ? 'operational' : 'error');
                    updateServiceStatus('notion', data.services.notion ? 'operational' : 'warning');
                }
            } else {
                updateServiceStatus('processing', 'warning');
            }
        })
        .catch(error => {
            console.error('Error loading service status:', error);
            updateServiceStatus('processing', 'error');
            updateServiceStatus('dropbox', 'warning');
            updateServiceStatus('notion', 'warning');
        });
}

// Improved service status update function
function updateServiceStatus(service, status) {
    const serviceElement = document.querySelector(`[data-service="${service}"]`);
    if (!serviceElement) return;

    // Remove existing status classes
    serviceElement.classList.remove('status-operational', 'status-warning', 'status-error');

    // Add new status class
    serviceElement.classList.add(`status-${status}`);

    // Update icon and text
    const icon = serviceElement.querySelector('i');
    const statusText = serviceElement.querySelector('.status-text');

    if (icon && statusText) {
        switch (status) {
            case 'operational':
                icon.className = 'fas fa-check-circle me-2';
                statusText.textContent = 'Operational';
                break;
            case 'warning':
                icon.className = 'fas fa-exclamation-triangle me-2';
                statusText.textContent = 'Warning';
                break;
            case 'error':
                icon.className = 'fas fa-times-circle me-2';
                statusText.textContent = 'Error';
                break;
        }
    }
}

// Manual scan trigger
function triggerManualScan() {
    const scanBtn = document.getElementById('manualScanBtn');
    if (scanBtn) {
        scanBtn.disabled = true;
        scanBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Scanning...';

        fetch('/api/manual-scan', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.error) {
                showAlert('Scan failed: ' + data.error, 'danger');
                updateServiceStatus('dropbox', 'error');
            } else {
                showAlert(data.message || 'Scan completed successfully', 'success');
                updateServiceStatus('dropbox', 'operational');

                // Update new files count if available
                if (data.new_files && data.new_files.length > 0) {
                    updateNewFilesCount(data.new_files.length);
                } else {
                    updateNewFilesCount(0);
                }

                // Refresh stats and logs
                setTimeout(() => {
                    loadSystemStats();
                    loadProcessingLogs();
                }, 2000);
            }
        })
        .catch(error => {
            console.error('Manual scan error:', error);
            showAlert('Error performing manual scan: ' + error.message, 'danger');
            updateServiceStatus('dropbox', 'error');
        })
        .finally(() => {
            scanBtn.disabled = false;
            scanBtn.innerHTML = '<i class="fas fa-sync me-1"></i>Manual Scan';
        });
    }
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
// Load processing logs
function loadProcessingLogs() {
    fetch('/api/processing-logs')
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (Array.isArray(data)) {
            // Update the activity feed
            const activityFeed = document.querySelector('.activity-feed');
            if (activityFeed) {
                let html = '';
                data.slice(0, 10).forEach(log => {
                    const icon = log.status === 'success' ? 'fas fa-check-circle text-success' :
                                log.status === 'error' ? 'fas fa-exclamation-circle text-danger' :
                                'fas fa-info-circle text-info';

                    const date = new Date(log.created_at).toLocaleString();

                    html += `
                        <div class="activity-item mb-3 pb-3 border-bottom">
                            <div class="d-flex align-items-start">
                                <div class="activity-icon me-3">
                                    <i class="${icon}"></i>
                                </div>
                                <div class="activity-content flex-grow-1">
                                    <div class="activity-message">${log.message}</div>
                                    <div class="activity-meta text-muted small">
                                        <i class="fas fa-clock me-1"></i>${date}
                                    </div>
                                </div>
                            </div>
                        </div>
                    `;
                });

                activityFeed.innerHTML = html || '<div class="text-center py-4"><i class="fas fa-history fa-2x text-muted mb-2"></i><p class="text-muted mb-0">No recent activity</p></div>';
            }
        }
    })
    .catch(error => {
        console.error('Error loading processing logs:', error);
        // Show fallback message
        const activityFeed = document.querySelector('.activity-feed');
        if (activityFeed) {
            activityFeed.innerHTML = '<div class="text-center py-4"><i class="fas fa-exclamation-triangle fa-2x text-warning mb-2"></i><p class="text-muted mb-0">Unable to load activity logs</p></div>';
        }
    });
}
// Auto-refresh system stats every 30 seconds
function updateSystemStats() {
    fetch('/api/system-stats')
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.system_stats) {
            // Update stat counters
            const clientsElement = document.querySelector('[data-stat="clients"]');
            const transcriptsElement = document.querySelector('[data-stat="transcripts"]');
            const pendingElement = document.querySelector('[data-stat="pending"]');
            const failedElement = document.querySelector('[data-stat="failed"]');

            if (clientsElement) clientsElement.textContent = data.system_stats.total_clients || 0;
            if (transcriptsElement) transcriptsElement.textContent = data.system_stats.total_transcripts || 0;
            if (pendingElement) pendingElement.textContent = data.system_stats.pending_processing || 0;
            if (failedElement) failedElement.textContent = data.system_stats.failed_processing || 0;
        }
    })
    .catch(error => {
        console.error('Failed to update system stats:', error);
        // Don't show error to user, just log it
    });
}

// Manual scan functionality
function triggerManualScan() {
    const scanBtn = document.getElementById('manualScanBtn');
    if (scanBtn) {
        scanBtn.disabled = true;
        scanBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Scanning...';

        fetch('/api/manual-scan', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.error) {
                showAlert('Scan failed: ' + data.error, 'danger');
            } else {
                showAlert(data.message || 'Scan completed successfully', 'success');

                // Update new files count if available
                if (data.new_files && data.new_files.length > 0) {
                    const countElement = document.getElementById('newFilesCount');
                    if (countElement) {
                        countElement.textContent = `${data.new_files.length} new files detected`;
                    }
                }

                // Refresh stats and logs
                updateSystemStats();
                loadProcessingLogs();
            }
        })
        .catch(error => {
            console.error('Manual scan error:', error);
            showAlert('Scan failed: ' + error.message, 'danger');
        })
        .finally(() => {
            scanBtn.disabled = false;
            scanBtn.innerHTML = '<i class="fas fa-sync me-1"></i>Manual Scan';
        });
    }
}
// Initialize dashboard on page load
document.addEventListener('DOMContentLoaded', function() {
    console.log('Dashboard utilities loaded successfully');

    // Load initial data
    loadServiceStatus();
    updateSystemStats();
    loadProcessingLogs();

    console.log('Dashboard initialized successfully');
});

// Auto-refresh data every 30 seconds
setInterval(() => {
    updateSystemStats();
    loadProcessingLogs();
}, 30000);

// Auto-refresh service status every 60 seconds
setInterval(loadServiceStatus, 60000);

function manualScan() {
    const scanBtn = document.getElementById('manualScanBtn');
    if (scanBtn) {
        scanBtn.disabled = true;
        scanBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Scanning...';
    }

    fetch('/api/manual-scan', { 
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
        .then(response => {
            return response.json().then(data => {
                if (!response.ok) {
                    throw new Error(data.error || `HTTP error! status: ${response.status}`);
                }
                return data;
            });
        })
        .then(data => {
            showAlert(data.message || 'Scan completed successfully', 'success');

            // Update new files count if available
            if (data.new_files && data.new_files.length > 0) {
                const countElement = document.getElementById('newFilesCount');
                if (countElement) {
                    countElement.textContent = `${data.new_files.length} new files detected`;
                }
            }

            // Refresh data after a short delay
            setTimeout(() => {
                loadSystemStats();
                loadProcessingLogs();
            }, 2000);
        })
        .catch(error => {
            console.error('Manual scan error:', error);
            showAlert('Error performing manual scan: ' + error.message, 'danger');
        })
        .finally(() => {
            if (scanBtn) {
                scanBtn.disabled = false;
                scanBtn.innerHTML = '<i class="fas fa-sync me-2"></i>Manual Scan';
            }
        });
}

// Auto-refresh data every 60 seconds (reduced frequency)
setInterval(() => {
    updateSystemStats();
    loadProcessingLogs();
}, 60000);