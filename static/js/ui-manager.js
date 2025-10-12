/**
 * UI Manager Module
 * 
 * Handles all user interface interactions and updates.
 * Single Responsibility: Manage UI state and user interactions.
 */

class UIManager {
    constructor(apiClient, webSocketManager) {
        this.apiClient = apiClient;
        this.webSocketManager = webSocketManager;
        this.isCapturing = false;
        this.currentEndpoint = '';
        this.currentMode = 'raw';
        
        // DOM element cache
        this.elements = {};
        
        this.initializeElements();
        this.setupEventHandlers();
        this.setupWebSocketHandlers();
    }

    /**
     * Initialize and cache DOM elements
     */
    initializeElements() {
        this.elements = {
            // Form elements
            endpointInput: document.getElementById('endpoint'),
            modeSelect: document.getElementById('mode'),
            
            // Buttons
            startBtn: document.getElementById('start-btn'),
            stopBtn: document.getElementById('stop-btn'),
            downloadBtn: document.getElementById('download-btn'),
            testEndpointBtn: document.getElementById('test-endpoint-btn'),
            saveSettingsBtn: document.getElementById('save-settings-btn'),
            clearSettingsBtn: document.getElementById('clear-settings-btn'),
            
            // Status elements
            deviceStatusCard: document.getElementById('device-status'),
            deviceStatusText: document.getElementById('device-status-text'),
            deviceLastUpdate: document.getElementById('device-last-update'),
            captureStatusText: document.getElementById('capture-status-text'),
            endpointStatusText: document.getElementById('endpoint-status-text'),
            endpointTestStatus: document.getElementById('endpoint-test-status'),
            
            // Containers
            logsContainer: document.getElementById('logs-container'),
            alertContainer: document.getElementById('alert-container')
        };
    }

    /**
     * Setup UI event handlers
     */
    setupEventHandlers() {
        // Button click handlers
        this.elements.testEndpointBtn.addEventListener('click', () => this.testEndpoint());
        this.elements.saveSettingsBtn.addEventListener('click', () => this.saveSettings());
        this.elements.clearSettingsBtn.addEventListener('click', () => this.clearSettings());
        this.elements.startBtn.addEventListener('click', () => this.startCapture());
        this.elements.stopBtn.addEventListener('click', () => this.stopCapture());
        this.elements.downloadBtn.addEventListener('click', () => this.downloadLogs());

        // Auto-save settings when changed
        this.elements.endpointInput.addEventListener('change', () => this.saveSettings());
        this.elements.modeSelect.addEventListener('change', () => this.saveSettings());
    }

    /**
     * Setup WebSocket event handlers
     */
    setupWebSocketHandlers() {
        this.webSocketManager.on('websocket_connected', () => {
            this.showAlert('Connected to server', 'success');
        });

        this.webSocketManager.on('websocket_disconnected', () => {
            this.showAlert('Disconnected from server', 'danger');
        });

        this.webSocketManager.on('device_status', (data) => {
            this.updateDeviceStatus(data);
        });

        this.webSocketManager.on('status_update', (data) => {
            this.handleStatusUpdate(data);
        });

        this.webSocketManager.on('log_event', (data) => {
            this.addLogEntry(data);
        });

        this.webSocketManager.on('settings_loaded', (settings) => {
            this.loadSettings(settings);
        });
    }

    /**
     * Show alert message
     */
    showAlert(message, type = 'info') {
        const alert = document.createElement('div');
        alert.className = `alert alert-${type}`;
        alert.textContent = message;
        this.elements.alertContainer.appendChild(alert);
        
        setTimeout(() => {
            alert.remove();
        }, 5000);
    }

    /**
     * Update device status display
     */
    updateDeviceStatus(data) {
        this.elements.deviceStatusText.textContent = data.message;
        this.elements.deviceLastUpdate.textContent = `Last updated: ${data.timestamp || 'Just now'}`;
        
        if (data.connected) {
            this.elements.deviceStatusCard.className = 'status-card device-connected';
        } else {
            this.elements.deviceStatusCard.className = 'status-card device-disconnected';
        }
    }

    /**
     * Update capture status
     */
    updateCaptureStatus(capturing) {
        this.isCapturing = capturing;
        this.elements.captureStatusText.textContent = capturing ? 'Capturing logs...' : 'Not capturing';
        document.getElementById('capture-status').className = capturing ? 'status-card capturing' : 'status-card';
        
        this.elements.startBtn.disabled = capturing;
        this.elements.stopBtn.disabled = !capturing;
    }

    /**
     * Handle status updates from WebSocket
     */
    handleStatusUpdate(data) {
        if (data.status === 'capturing') {
            this.updateCaptureStatus(true);
        } else if (data.status === 'stopped') {
            this.updateCaptureStatus(false);
        }
        
        if (data.message) {
            const alertType = data.status === 'error' ? 'danger' : 'info';
            this.showAlert(data.message, alertType);
        }
    }

    /**
     * Add log entry to the display
     */
    addLogEntry(data) {
        const logEntry = document.createElement('div');
        logEntry.className = 'log-entry';
        
        const timestamp = document.createElement('div');
        timestamp.className = 'timestamp';
        timestamp.textContent = data.timestamp;
        
        const content = document.createElement('div');
        content.textContent = data.matched_text;
        
        logEntry.appendChild(timestamp);
        logEntry.appendChild(content);
        
        // Add status indicator
        if (data.results && data.results.length > 0) {
            const success = data.results.every(r => r[1] !== null);
            logEntry.className += success ? ' success' : ' error';
        }
        
        this.elements.logsContainer.appendChild(logEntry);
        
        // Remove placeholder text
        const placeholder = this.elements.logsContainer.querySelector('p[style*="text-align: center"]');
        if (placeholder) {
            placeholder.remove();
        }
        
        // Auto-scroll to bottom
        this.elements.logsContainer.scrollTop = this.elements.logsContainer.scrollHeight;
        
        // Limit to 50 entries
        while (this.elements.logsContainer.children.length > 50) {
            this.elements.logsContainer.removeChild(this.elements.logsContainer.firstChild);
        }
    }

    /**
     * Load settings into UI
     */
    loadSettings(settings) {
        this.elements.endpointInput.value = settings.endpoint || '';
        this.elements.modeSelect.value = settings.mode || 'raw';
        this.currentEndpoint = settings.endpoint || '';
        this.currentMode = settings.mode || 'raw';
    }

    /**
     * Test endpoint connectivity
     */
    async testEndpoint() {
        const endpoint = this.elements.endpointInput.value.trim();
        if (!endpoint) {
            this.showAlert('Please enter an endpoint URL', 'danger');
            return;
        }

        this.setButtonLoading(this.elements.testEndpointBtn, 'Testing...');
        this.updateEndpointStatus('testing', 'Testing...');

        try {
            const result = await this.apiClient.testEndpoint(endpoint);
            
            if (result.success) {
                this.showAlert(result.message, 'success');
                this.updateEndpointStatus('success', 'Connected ✓');
                this.elements.endpointStatusText.textContent = 'Endpoint is reachable';
            } else {
                this.showAlert(`Endpoint test failed: ${result.message}`, 'danger');
                this.updateEndpointStatus('error', 'Failed ✗');
                this.elements.endpointStatusText.textContent = 'Endpoint unreachable';
            }
        } catch (error) {
            this.showAlert(`Network error: ${error.message}`, 'danger');
            this.updateEndpointStatus('error', 'Error ✗');
        } finally {
            this.resetButtonLoading(this.elements.testEndpointBtn, '🔍 Test Endpoint');
        }
    }

    /**
     * Update endpoint status indicator
     */
    updateEndpointStatus(status, text) {
        this.elements.endpointTestStatus.className = `endpoint-status ${status}`;
        this.elements.endpointTestStatus.textContent = text;
        this.elements.endpointTestStatus.classList.remove('hidden');
    }

    /**
     * Save settings
     */
    async saveSettings() {
        const endpoint = this.elements.endpointInput.value.trim();
        const mode = this.elements.modeSelect.value;

        try {
            const result = await this.apiClient.saveSettings({ endpoint, mode });
            
            if (result.success) {
                this.showAlert('Settings saved successfully', 'success');
                this.currentEndpoint = endpoint;
                this.currentMode = mode;
            } else {
                this.showAlert(`Failed to save settings: ${result.message}`, 'danger');
            }
        } catch (error) {
            this.showAlert(`Error saving settings: ${error.message}`, 'danger');
        }
    }

    /**
     * Clear settings
     */
    async clearSettings() {
        if (!confirm('Are you sure you want to clear all saved settings?')) {
            return;
        }

        try {
            const result = await this.apiClient.clearSettings();
            
            if (result.success) {
                this.showAlert('Settings cleared successfully', 'success');
                this.elements.endpointInput.value = '';
                this.elements.modeSelect.value = 'raw';
                this.currentEndpoint = '';
                this.currentMode = 'raw';
                this.elements.endpointTestStatus.classList.add('hidden');
                this.elements.endpointStatusText.textContent = 'Not tested';
            } else {
                this.showAlert(`Failed to clear settings: ${result.message}`, 'danger');
            }
        } catch (error) {
            this.showAlert(`Error clearing settings: ${error.message}`, 'danger');
        }
    }

    /**
     * Start capture
     */
    async startCapture() {
        const endpoint = this.elements.endpointInput.value.trim();
        const mode = this.elements.modeSelect.value;

        if (!endpoint) {
            this.showAlert('Please enter an endpoint URL', 'danger');
            return;
        }

        this.setButtonLoading(this.elements.startBtn, 'Starting...');

        try {
            const result = await this.apiClient.startCapture(endpoint, mode);
            
            if (result.success) {
                this.showAlert(result.message, 'success');
                this.updateCaptureStatus(true);
            } else {
                this.showAlert(result.message, 'danger');
            }
        } catch (error) {
            this.showAlert(`Error starting capture: ${error.message}`, 'danger');
        } finally {
            this.resetButtonLoading(this.elements.startBtn, '▶️ Start Capturing');
        }
    }

    /**
     * Stop capture
     */
    async stopCapture() {
        this.setButtonLoading(this.elements.stopBtn, 'Stopping...');

        try {
            const result = await this.apiClient.stopCapture();
            
            if (result.success) {
                this.showAlert(result.message, 'success');
                this.updateCaptureStatus(false);
            } else {
                this.showAlert(result.message, 'danger');
            }
        } catch (error) {
            this.showAlert(`Error stopping capture: ${error.message}`, 'danger');
        } finally {
            this.resetButtonLoading(this.elements.stopBtn, '⏹️ Stop Capturing');
        }
    }

    /**
     * Download logs
     */
    downloadLogs() {
        this.apiClient.downloadLogs();
    }

    /**
     * Set button to loading state
     */
    setButtonLoading(button, text) {
        button.disabled = true;
        button.innerHTML = `<span class="spinner"></span> ${text}`;
    }

    /**
     * Reset button from loading state
     */
    resetButtonLoading(button, originalText) {
        button.disabled = false;
        button.innerHTML = originalText;
    }

    /**
     * Initialize UI on page load
     */
    initialize() {
        // Auto-test endpoint if one is configured
        if (this.elements.endpointInput.value.trim()) {
            setTimeout(() => this.testEndpoint(), 1000);
        }
    }
}

// Export for use in other modules
window.UIManager = UIManager;