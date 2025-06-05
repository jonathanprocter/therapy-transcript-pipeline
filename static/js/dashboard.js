// Dashboard utilities and functionality
(function() {
    'use strict';
    
    // Prevent multiple initializations
    if (window.dashboardInitialized) {
        console.log('Dashboard already initialized, skipping...');
        return;
    }
    window.dashboardInitialized = true;
    
    console.log('Dashboard utilities loaded successfully');

    // Initialize dashboard when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initializeDashboard);
    } else {
        initializeDashboard();
    }

    function initializeDashboard() {
        console.log('Dashboard initialized successfully');
        loadSystemStats();
        loadServiceStatus();

        // Refresh stats every 30 seconds (only set once)
        if (!window.dashboardIntervals) {
            window.dashboardIntervals = true;
            setInterval(loadSystemStats, 30000);
            setInterval(loadServiceStatus, 60000);
        }
    }
})();

// Load and display system statistics
function loadSystemStats() {
    fetch('/api/system-stats')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('System stats loaded:', data);
            
            // Validate response structure - check for both nested and direct formats
            if (data && typeof data === 'object') {
                if (data.data && data.data.system_stats && typeof data.data.system_stats === 'object') {
                    // New API format with data wrapper
                    updateSystemStats(data.data.system_stats);
                } else if (data.system_stats && typeof data.system_stats === 'object') {
                    // Legacy format
                    updateSystemStats(data.system_stats);
                } else {
                    console.warn('Invalid system stats data format:', data);
                    // Use default stats
                    updateSystemStats({
                        total_clients: 0,
                        total_transcripts: 0,
                        pending_processing: 0,
                        failed_processing: 0
                    });
                }
            } else {
                console.warn('Invalid system stats data format:', data);
                // Use default stats
                updateSystemStats({
                    total_clients: 0,
                    total_transcripts: 0,
                    pending_processing: 0,
                    failed_processing: 0
                });
            }
        })
        .catch(error => {
            console.error('Failed to load system stats:', error);
            // Use default stats on error
            updateSystemStats({
                total_clients: 0,
                total_transcripts: 0,
                pending_processing: 0,
                failed_processing: 0
            });
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
    // Check system health endpoint
    fetch('/health')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            return response.json();
        })
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
    const newFilesCount = document.getElementById('newFilesCount');

    if (scanBtn) {
        scanBtn.disabled = true;
        scanBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Scanning...';
    }

    if (newFilesCount) {
        newFilesCount.textContent = 'Scanning...';
        newFilesCount.className = 'badge bg-warning';
    }

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
            if (newFilesCount) {
                newFilesCount.textContent = 'Scan failed';
                newFilesCount.className = 'badge bg-danger';
            }
        } else {
            showAlert(data.message || 'Scan completed successfully', 'success');
            updateServiceStatus('dropbox', 'operational');

            // Update new files count if available
            if (data.new_files && data.new_files.length > 0) {
                if (newFilesCount) {
                    newFilesCount.textContent = `${data.new_files.length} new files detected`;
                    newFilesCount.className = 'badge bg-success';
                }
            } else {
                if (newFilesCount) {
                    newFilesCount.textContent = 'No new files';
                    newFilesCount.className = 'badge bg-secondary';
                }
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
        if (newFilesCount) {
            newFilesCount.textContent = 'Scan failed';
            newFilesCount.className = 'badge bg-danger';
        }
    })
    .finally(() => {
        if (scanBtn) {
            scanBtn.disabled = false;
            scanBtn.innerHTML = '<i class="fas fa-sync me-1"></i>Manual Scan';
        }
    });
}

// Load processing logs
function loadProcessingLogs() {
    const activityFeed = document.querySelector('.activity-feed');
    const refreshButton = document.getElementById('refreshActivityBtn'); // Assuming this ID will be added to the button in dashboard.html
    let originalButtonHtml; // Declare here to be accessible in finally

    if (refreshButton) {
        refreshButton.disabled = true;
        // Optional: Change button text to show loading state
        originalButtonHtml = refreshButton.innerHTML; // Store original HTML
        refreshButton.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Loading...';
    }

    if (activityFeed) {
        activityFeed.innerHTML = `
            <div class="text-center py-4">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <p class="text-muted mt-2 mb-0">Loading recent activity...</p>
            </div>`;
    }

    fetch('/api/processing-logs')
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        console.log('Processing logs loaded:', data);
        
        let logs = [];
        if (Array.isArray(data)) {
            logs = data;
        } else {
            console.warn('Processing logs returned unexpected data type:', typeof data, data);
            logs = []; // Default to empty array if data is not as expected
        }
        
        if (activityFeed) {
            let html = '';
            if (logs.length > 0) {
                logs.slice(0, 10).forEach(log => {
                    try {
                        const iconClass = log.status === 'success' ? 'fas fa-check-circle text-success' :
                                        log.status === 'error' ? 'fas fa-exclamation-circle text-danger' :
                                        'fas fa-info-circle text-info';
                        const dateStr = log.created_at ? new Date(log.created_at).toLocaleString() : 'Unknown time';
                        const messageText = log.message || 'No message available';

                        html += `
                            <div class="activity-item mb-3 pb-3 border-bottom">
                                <div class="d-flex align-items-start">
                                    <div class="activity-icon me-3">
                                        <i class="${iconClass}"></i>
                                    </div>
                                    <div class="activity-content flex-grow-1">
                                        <div class="activity-message">${messageText}</div>
                                        <div class="activity-meta text-muted small">
                                            <i class="fas fa-clock me-1"></i>${dateStr}
                                        </div>
                                    </div>
                                </div>
                            </div>
                        `;
                    } catch (logError) {
                        console.warn('Error processing individual log entry:', logError, log);
                        // Optionally skip this log or add a placeholder error entry
                    }
                });
            }
            activityFeed.innerHTML = html || '<div class="text-center py-4"><i class="fas fa-history fa-2x text-muted mb-2"></i><p class="text-muted mb-0">No recent activity</p></div>';
        }
    })
    .catch(error => {
        console.error('Error loading processing logs:', error);
        if (activityFeed) {
            activityFeed.innerHTML = `
                <div class="text-center py-4">
                    <i class="fas fa-exclamation-triangle fa-2x text-warning mb-2"></i>
                    <p class="text-muted mb-0">Unable to load activity logs.</p>
                    <p class="text-danger small">${error.message}</p>
                </div>`;
        }
        // No need to return empty array here as it's handled by the UI update
    })
    .finally(() => {
        if (refreshButton) {
            refreshButton.disabled = false;
            if(originalButtonHtml) { // Restore original button HTML
                 refreshButton.innerHTML = originalButtonHtml;
            } else { // Fallback if originalButtonHtml wasn't captured (should not happen)
                 refreshButton.innerHTML = '<i class="fas fa-sync-alt me-1"></i>Refresh Activity';
            }
        }
    });
}

// Show alert message
function showAlert(message, type) {
    // Remove existing alerts
    const existingAlerts = document.querySelectorAll('.alert-container .alert');
    existingAlerts.forEach(alert => alert.remove());

    const alertHtml = `
        <div class="alert alert-${type} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;

    let container = document.querySelector('.alert-container');
    if (!container) {
        // Create alert container if it doesn't exist
        container = document.createElement('div');
        container.className = 'alert-container';
        container.style.cssText = 'position: fixed; top: 20px; right: 20px; z-index: 1050; width: 400px;';
        document.body.appendChild(container);
    }

    container.insertAdjacentHTML('beforeend', alertHtml);

    // Auto-remove alert after 5 seconds
    setTimeout(() => {
        const alert = container.querySelector('.alert');
        if (alert) {
            alert.remove();
        }
    }, 5000);
}

// Show loading indicator
function showLoading() {
    const loadingHtml = `
        <div id="loadingIndicator" class="alert alert-info">
            <i class="fas fa-spinner fa-spin me-2"></i>Processing...
        </div>
    `;

    let container = document.querySelector('.alert-container');
    if (!container) {
        container = document.createElement('div');
        container.className = 'alert-container';
        container.style.cssText = 'position: fixed; top: 20px; right: 20px; z-index: 1050; width: 400px;';
        document.body.appendChild(container);
    }

    container.insertAdjacentHTML('beforeend', loadingHtml);
}

// Hide loading indicator
function hideLoading() {
    const loading = document.getElementById('loadingIndicator');
    if (loading) {
        loading.remove();
    }
}

// Test Dropbox connection
function testDropboxConnection() {
    const testBtn = document.getElementById('testDropboxBtn');
    
    if (testBtn) {
        testBtn.disabled = true;
        testBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Testing...';
    }

    fetch('/api/test-dropbox', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(data => {
                throw new Error(data.error || `HTTP ${response.status}`);
            });
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            showAlert(`Dropbox Connected Successfully!<br>
                Account: ${data.account_name}<br>
                ${data.folder_status}<br>
                Files found: ${data.files_found}`, 'success');
            updateServiceStatus('dropbox', 'operational');
        } else {
            showAlert(`Dropbox Test Failed: ${data.error}`, 'danger');
            updateServiceStatus('dropbox', 'error');
        }
    })
    .catch(error => {
        console.error('Dropbox test error:', error);
        showAlert(`Dropbox Test Failed: ${error.message}`, 'danger');
        updateServiceStatus('dropbox', 'error');
    })
    .finally(() => {
        if (testBtn) {
            testBtn.disabled = false;
            testBtn.innerHTML = '<i class="fas fa-plug me-1"></i>Test Connection';
        }
    });
}

// Export functions for global access (only if not already exported)
if (!window.loadSystemStats) {
    window.loadSystemStats = loadSystemStats;
    window.triggerManualScan = triggerManualScan;
    window.loadProcessingLogs = loadProcessingLogs;
    window.testDropboxConnection = testDropboxConnection;
    window.showAlert = showAlert;
    window.showLoading = showLoading;
    window.hideLoading = hideLoading;
}