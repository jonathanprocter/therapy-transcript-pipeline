/**
 * Dashboard JavaScript for Therapy Transcript Processor
 * Handles client-side interactions, API calls, and UI updates
 */

// Global variables
let loadingModal;

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeDashboard();
});

/**
 * Initialize dashboard components
 */
function initializeDashboard() {
    // Initialize loading modal
    loadingModal = new bootstrap.Modal(document.getElementById('loadingModal'), {
        backdrop: 'static',
        keyboard: false
    });
    
    // Set up auto-refresh for activity feeds
    startAutoRefresh();
    
    // Initialize tooltips
    initializeTooltips();
    
    // Set up form validation
    setupFormValidation();
    
    console.log('Dashboard initialized successfully');
}

/**
 * Initialize Bootstrap tooltips
 */
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

/**
 * Setup form validation
 */
function setupFormValidation() {
    // Add custom validation styles
    const forms = document.querySelectorAll('.needs-validation');
    
    Array.prototype.slice.call(forms).forEach(function(form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });
}

/**
 * Start auto-refresh for activity feeds
 */
function startAutoRefresh() {
    // Refresh activity feed every 30 seconds
    if (typeof loadProcessingLogs === 'function') {
        setInterval(loadProcessingLogs, 30000);
    }
    
    // Refresh page statistics every 2 minutes
    setInterval(refreshPageStats, 120000);
}

/**
 * Refresh page statistics
 */
function refreshPageStats() {
    // Update system stats if on dashboard
    if (window.location.pathname === '/') {
        updateSystemStats();
    }
    
    // Update service status if on settings page
    if (window.location.pathname === '/settings') {
        updateServiceStatus();
    }
}

/**
 * Update system statistics
 */
function updateSystemStats() {
    fetch('/api/system-stats')
    .then(response => response.json())
    .then(data => {
        if (data.system_stats) {
            updateStatCard('total-clients', data.system_stats.total_clients);
            updateStatCard('total-transcripts', data.system_stats.total_transcripts);
            updateStatCard('pending-processing', data.system_stats.pending_processing);
            updateStatCard('failed-processing', data.system_stats.failed_processing);
        }
    })
    .catch(error => {
        console.warn('Failed to update system stats:', error);
    });
}

/**
 * Update a stat card value
 */
function updateStatCard(cardId, value) {
    const element = document.getElementById(cardId);
    if (element) {
        element.textContent = value || 0;
        
        // Add update animation
        element.classList.add('loading-pulse');
        setTimeout(() => {
            element.classList.remove('loading-pulse');
        }, 1000);
    }
}

/**
 * Update service status indicators
 */
function updateServiceStatus() {
    fetch('/api/service-status')
    .then(response => response.json())
    .then(data => {
        updateServiceIndicator('dropbox', data.dropbox);
        updateServiceIndicator('notion', data.notion);
        updateServiceIndicator('openai', data.openai);
        updateServiceIndicator('anthropic', data.anthropic);
        updateServiceIndicator('gemini', data.gemini);
    })
    .catch(error => {
        console.warn('Failed to update service status:', error);
    });
}

/**
 * Update a service status indicator
 */
function updateServiceIndicator(service, status) {
    const card = document.querySelector(`[data-service="${service}"]`);
    if (card) {
        const cardElement = card.closest('.card');
        if (status) {
            cardElement.className = cardElement.className.replace('bg-danger', 'bg-success');
        } else {
            cardElement.className = cardElement.className.replace('bg-success', 'bg-danger');
        }
    }
}

/**
 * Show loading modal
 */
function showLoading(message = 'Processing...') {
    const modalBody = document.querySelector('#loadingModal .modal-body');
    if (modalBody) {
        const messageElement = modalBody.querySelector('p');
        if (messageElement) {
            messageElement.textContent = message;
        }
    }
    
    if (loadingModal) {
        loadingModal.show();
    }
}

/**
 * Hide loading modal
 */
function hideLoading() {
    if (loadingModal) {
        loadingModal.hide();
    }
}

/**
 * Show alert message
 */
function showAlert(message, type = 'info', duration = 5000) {
    // Create alert element
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.setAttribute('role', 'alert');
    
    // Add icon based on type
    let icon = 'fas fa-info-circle';
    switch (type) {
        case 'success':
            icon = 'fas fa-check-circle';
            break;
        case 'warning':
            icon = 'fas fa-exclamation-triangle';
            break;
        case 'danger':
            icon = 'fas fa-times-circle';
            break;
    }
    
    alertDiv.innerHTML = `
        <i class="${icon} me-2"></i>
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    // Insert at top of main content
    const container = document.querySelector('main.container');
    if (container) {
        container.insertBefore(alertDiv, container.firstChild);
        
        // Auto-hide after duration
        if (duration > 0) {
            setTimeout(() => {
                const alert = bootstrap.Alert.getInstance(alertDiv);
                if (alert) {
                    alert.close();
                }
            }, duration);
        }
    }
}

/**
 * Format date for display
 */
function formatDate(dateString) {
    if (!dateString) return 'N/A';
    
    try {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    } catch (error) {
        return 'Invalid Date';
    }
}

/**
 * Format file size for display
 */
function formatFileSize(bytes) {
    if (!bytes || bytes === 0) return '0 B';
    
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    
    return parseFloat((bytes / Math.pow(1024, i)).toFixed(2)) + ' ' + sizes[i];
}

/**
 * Debounce function for search inputs
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * Copy text to clipboard
 */
function copyToClipboard(text) {
    if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(text).then(() => {
            showAlert('Copied to clipboard!', 'success', 2000);
        }).catch(err => {
            console.error('Failed to copy text: ', err);
            showAlert('Failed to copy to clipboard', 'danger', 3000);
        });
    } else {
        // Fallback for older browsers
        const textArea = document.createElement('textarea');
        textArea.value = text;
        textArea.style.position = 'fixed';
        textArea.style.left = '-999999px';
        textArea.style.top = '-999999px';
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();
        
        try {
            document.execCommand('copy');
            showAlert('Copied to clipboard!', 'success', 2000);
        } catch (err) {
            console.error('Failed to copy text: ', err);
            showAlert('Failed to copy to clipboard', 'danger', 3000);
        } finally {
            document.body.removeChild(textArea);
        }
    }
}

/**
 * Validate email format
 */
function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

/**
 * Sanitize HTML content
 */
function sanitizeHTML(str) {
    const temp = document.createElement('div');
    temp.textContent = str;
    return temp.innerHTML;
}

/**
 * Handle API errors consistently
 */
function handleApiError(error, context = '') {
    console.error(`API Error ${context}:`, error);
    
    let message = 'An unexpected error occurred';
    
    if (error.response) {
        // Server responded with error status
        if (error.response.status === 404) {
            message = 'Resource not found';
        } else if (error.response.status === 403) {
            message = 'Access denied';
        } else if (error.response.status === 500) {
            message = 'Server error - please try again later';
        } else if (error.response.data && error.response.data.message) {
            message = error.response.data.message;
        }
    } else if (error.request) {
        // Network error
        message = 'Network error - please check your connection';
    } else if (error.message) {
        message = error.message;
    }
    
    showAlert(`Error: ${message}`, 'danger');
}

/**
 * Create loading skeleton for tables
 */
function createTableSkeleton(rows = 3, cols = 5) {
    let html = '<tbody>';
    
    for (let i = 0; i < rows; i++) {
        html += '<tr>';
        for (let j = 0; j < cols; j++) {
            html += '<td><div class="placeholder-glow"><span class="placeholder col-8"></span></div></td>';
        }
        html += '</tr>';
    }
    
    html += '</tbody>';
    return html;
}

/**
 * Update table with loading state
 */
function setTableLoading(tableSelector, show = true) {
    const table = document.querySelector(tableSelector);
    if (!table) return;
    
    const tbody = table.querySelector('tbody');
    if (!tbody) return;
    
    if (show) {
        tbody.innerHTML = createTableSkeleton();
    }
}

/**
 * Smooth scroll to element
 */
function scrollToElement(elementId, offset = 0) {
    const element = document.getElementById(elementId);
    if (element) {
        const elementPosition = element.getBoundingClientRect().top + window.pageYOffset;
        const offsetPosition = elementPosition - offset;
        
        window.scrollTo({
            top: offsetPosition,
            behavior: 'smooth'
        });
    }
}

/**
 * Check if element is in viewport
 */
function isInViewport(element) {
    const rect = element.getBoundingClientRect();
    return (
        rect.top >= 0 &&
        rect.left >= 0 &&
        rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
        rect.right <= (window.innerWidth || document.documentElement.clientWidth)
    );
}

/**
 * Animate number counting
 */
function animateNumber(element, targetNumber, duration = 1000) {
    const startNumber = parseInt(element.textContent) || 0;
    const startTime = Date.now();
    
    function updateNumber() {
        const elapsed = Date.now() - startTime;
        const progress = Math.min(elapsed / duration, 1);
        
        // Easing function for smooth animation
        const easeOutCubic = 1 - Math.pow(1 - progress, 3);
        const currentNumber = Math.round(startNumber + (targetNumber - startNumber) * easeOutCubic);
        
        element.textContent = currentNumber;
        
        if (progress < 1) {
            requestAnimationFrame(updateNumber);
        }
    }
    
    requestAnimationFrame(updateNumber);
}

/**
 * Local storage helpers
 */
const storage = {
    set: function(key, value) {
        try {
            localStorage.setItem(key, JSON.stringify(value));
        } catch (error) {
            console.warn('Failed to save to localStorage:', error);
        }
    },
    
    get: function(key, defaultValue = null) {
        try {
            const item = localStorage.getItem(key);
            return item ? JSON.parse(item) : defaultValue;
        } catch (error) {
            console.warn('Failed to read from localStorage:', error);
            return defaultValue;
        }
    },
    
    remove: function(key) {
        try {
            localStorage.removeItem(key);
        } catch (error) {
            console.warn('Failed to remove from localStorage:', error);
        }
    }
};

/**
 * Export functions for use in other scripts
 */
window.dashboardUtils = {
    showLoading,
    hideLoading,
    showAlert,
    formatDate,
    formatFileSize,
    debounce,
    copyToClipboard,
    isValidEmail,
    sanitizeHTML,
    handleApiError,
    setTableLoading,
    scrollToElement,
    isInViewport,
    animateNumber,
    storage
};

// Global error handler
window.addEventListener('error', function(event) {
    console.error('Global error:', event.error);
    // Don't show alerts for every error to avoid spam
});

// Handle network status changes
window.addEventListener('online', function() {
    showAlert('Connection restored', 'success', 3000);
});

window.addEventListener('offline', function() {
    showAlert('Connection lost - some features may not work', 'warning', 5000);
});

console.log('Dashboard utilities loaded successfully');
