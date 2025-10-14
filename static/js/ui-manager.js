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
        this.hasLogsInUI = false; // Track if we have logs displayed in UI
        
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
           // endpointInput: document.getElementById('endpoint'),
            bulkEndpointInput: document.getElementById('bulk-endpoint'),
            modeSelect: document.getElementById('mode'),
            
            // Buttons
            startBtn: document.getElementById('start-btn'),
            stopBtn: document.getElementById('stop-btn'),
            downloadBtn: document.getElementById('download-btn'),
           // testEndpointBtn: document.getElementById('test-endpoint-btn'),
            testBulkEndpointBtn: document.getElementById('test-bulk-endpoint-btn'),
            bulkPublishBtn: document.getElementById('bulk-publish-btn'),
            clearBulkBtn: document.getElementById('clear-bulk-btn'),
            previewBulkBtn: document.getElementById('preview-bulk-btn'),
            testLogs: document.getElementById('logs-checker'),
            saveSettingsBtn: document.getElementById('save-settings-btn'),
            clearSettingsBtn: document.getElementById('clear-settings-btn'),
            
            // Status elements
            deviceStatusCard: document.getElementById('device-status'),
            deviceStatusText: document.getElementById('device-status-text'),
            deviceLastUpdate: document.getElementById('device-last-update'),
            captureStatusText: document.getElementById('capture-status-text'),
            endpointStatusText: document.getElementById('endpoint-status-text'),
           // endpointTestStatus: document.getElementById('endpoint-test-status'),
            bulkEndpointTestStatus: document.getElementById('bulk-endpoint-test-status'),
            bulkCount: document.getElementById('bulk-count'),
            
            // Info modal elements
            infoBtn: document.getElementById('info-btn'),
            dataTypesModal: document.getElementById('data-types-modal'),
            modalCloseBtn: document.getElementById('modal-close-btn'),
            modalBody: document.getElementById('modal-body'),
            
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
        //this.elements.testEndpointBtn.addEventListener('click', () => this.testEndpoint());
        this.elements.testBulkEndpointBtn.addEventListener('click', () => this.testBulkEndpoint());
        this.elements.bulkPublishBtn.addEventListener('click', () => this.bulkPublish());
        this.elements.clearBulkBtn.addEventListener('click', () => this.clearBulkLogs());
        this.elements.previewBulkBtn.addEventListener('click', () => this.previewBulkLogs());

       this.elements.testLogs.addEventListener('click', () => {
    alert('Please make sure you download the .txt logs file and upload your event sheet and logs on the event validation website');
    window.open('https://validation-script-android-1.onrender.com/', '_blank'); // Replace with your actual URL
});
        this.elements.saveSettingsBtn.addEventListener('click', () => this.saveSettings());
        this.elements.clearSettingsBtn.addEventListener('click', () => this.clearSettings());
        this.elements.startBtn.addEventListener('click', () => this.startCapture());
        this.elements.stopBtn.addEventListener('click', () => this.stopCapture());
        this.elements.downloadBtn.addEventListener('click', () => this.downloadLogs());

        // Info modal handlers
        this.elements.infoBtn.addEventListener('click', () => this.showDataTypesModal());
        this.elements.modalCloseBtn.addEventListener('click', () => this.hideDataTypesModal());
        
        // Close modal when clicking outside
        this.elements.dataTypesModal.addEventListener('click', (e) => {
            if (e.target === this.elements.dataTypesModal) {
                this.hideDataTypesModal();
            }
        });
        
        // Close modal with Escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.elements.dataTypesModal.classList.contains('show')) {
                this.hideDataTypesModal();
            }
        });

        // Auto-save settings when changed
       // this.elements.endpointInput.addEventListener('change', () => this.saveSettings());
        this.elements.bulkEndpointInput.addEventListener('change', () => this.saveSettings());
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

        this.webSocketManager.on('bulk_publish_result', (data) => {
            this.handleBulkPublishResult(data);
        });

        this.webSocketManager.on('bulk_logs_cleared', (data) => {
            this.handleBulkLogsCleared(data);
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
        
        // Update button states
        this.elements.startBtn.disabled = capturing;
        this.elements.stopBtn.disabled = !capturing;
        
        // Add visual feedback to buttons
        if (capturing) {
            this.elements.startBtn.classList.add('disabled');
            this.elements.stopBtn.classList.remove('disabled');
        } else {
            this.elements.startBtn.classList.remove('disabled');
            this.elements.stopBtn.classList.add('disabled');
        }
        
        // Update bulk button states based on capture status and log availability
        this.updateBulkButtonStates();
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
        
        // Ensure button states are consistent after status updates
        this.ensureButtonStatesConsistent();
    }

    /**
     * Ensure button states are consistent with current capture status
     */
    ensureButtonStatesConsistent() {
        // Double-check that button states match the isCapturing flag
        this.elements.startBtn.disabled = this.isCapturing;
        this.elements.stopBtn.disabled = !this.isCapturing;
        
        // Update visual feedback
        if (this.isCapturing) {
            this.elements.startBtn.classList.add('disabled');
            this.elements.stopBtn.classList.remove('disabled');
        } else {
            this.elements.startBtn.classList.remove('disabled');
            this.elements.stopBtn.classList.add('disabled');
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
        
        // Mark that we have logs in UI
        this.hasLogsInUI = true;
        
        // Update bulk button states
        this.updateBulkButtonStates();
    }

    /**
     * Load settings into UI
     */
    loadSettings(settings) {
      //  this.elements.endpointInput.value = settings.endpoint || '';
        this.elements.bulkEndpointInput.value = settings.bulk_endpoint || '';
        this.elements.modeSelect.value = settings.mode || 'raw';
       /// this.currentEndpoint = settings.endpoint || '';
        this.currentBulkEndpoint = settings.bulk_endpoint || '';
        this.currentMode = settings.mode || 'raw';
    }

    /**
     * Test endpoint connectivity
     */
    async testEndpoint() {
        const endpoint = this.elements.endpointInput.value.trim();
        if (!endpoint) {
            this.showAlert('Please enter a realtime endpoint URL', 'danger');
            return;
        }

        this.setButtonLoading(this.elements.testEndpointBtn, 'Testing...');
       
       // this.updateEndpointStatus('testing', 'Testing...', this.elements.endpointTestStatus);

        try {
            const result = await this.apiClient.testEndpoint(endpoint, 'realtime');
            
            if (result.success) {
                this.showAlert(result.message, 'success');
              //  this.updateEndpointStatus('success', 'Connected ✓', this.elements.endpointTestStatus);
                this.elements.endpointStatusText.textContent = 'Realtime endpoint is reachable';
            } else {
                this.showAlert(`Realtime endpoint test failed: ${result.message}`, 'danger');
             //   this.updateEndpointStatus('error', 'Failed ✗', this.elements.endpointTestStatus);
                this.elements.endpointStatusText.textContent = 'Realtime endpoint unreachable';
            }
        } catch (error) {
            this.showAlert(`Network error: ${error.message}`, 'danger');
          //  this.updateEndpointStatus('error', 'Error ✗', this.elements.endpointTestStatus);
        } finally {
            this.resetButtonLoading(this.elements.testEndpointBtn, '🔍 Test Realtime');
        }
    }

    /**
     * Test bulk endpoint connectivity
     */
    async testBulkEndpoint() {
        const bulkEndpoint = this.elements.bulkEndpointInput.value.trim();
        if (!bulkEndpoint) {
            this.showAlert('Please enter a bulk endpoint URL', 'danger');
            return;
        }

        this.setButtonLoading(this.elements.testBulkEndpointBtn, 'Testing...');
        this.updateEndpointStatus('testing', 'Testing...', this.elements.bulkEndpointTestStatus);

        try {
            const result = await this.apiClient.testEndpoint(bulkEndpoint, 'bulk');
            
            if (result.success) {
                this.showAlert(result.message, 'success');
                this.updateEndpointStatus('success', 'Connected ✓', this.elements.bulkEndpointTestStatus);
                this.elements.endpointStatusText.textContent = 'Bulk endpoint is reachable';
            } else {
                this.showAlert(`Bulk endpoint test failed: ${result.message}`, 'danger');
                this.updateEndpointStatus('error', 'Failed ✗', this.elements.bulkEndpointTestStatus);
                this.elements.endpointStatusText.textContent = 'Bulk endpoint unreachable';
            }
        } catch (error) {
            this.showAlert(`Network error: ${error.message}`, 'danger');
            this.updateEndpointStatus('error', 'Error ✗', this.elements.bulkEndpointTestStatus);
            this.elements.endpointStatusText.textContent = 'Bulk endpoint error';
        } finally {
            this.resetButtonLoading(this.elements.testBulkEndpointBtn, '🔍 Test Bulk');
        }
    }

    /**
     * Update endpoint status indicator
     */
    updateEndpointStatus(status, text, element = null) {
       // const statusElement = element || this.elements.endpointTestStatus;
         const statusElement = element;
        statusElement.className = `endpoint-status ${status}`;
        statusElement.textContent = text;
        statusElement.classList.remove('hidden');
    }

    /**
     * Save settings
     */
    async saveSettings() {
      //  const endpoint = this.elements.endpointInput.value.trim();
        const bulkEndpoint = this.elements.bulkEndpointInput.value.trim();
        const mode = this.elements.modeSelect.value;

        try {
            const result = await this.apiClient.saveSettings({ 
               
                bulk_endpoint: bulkEndpoint, 
                mode 
            });
            
            if (result.success) {
                this.showAlert('Settings saved successfully', 'success');
                //this.currentEndpoint = endpoint;
                this.currentBulkEndpoint = bulkEndpoint;
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
              //  this.elements.endpointInput.value = '';
                this.elements.bulkEndpointInput.value = '';
                this.elements.modeSelect.value = 'raw';
                this.currentEndpoint = '';
                this.currentBulkEndpoint = '';
                this.currentMode = 'raw';
               // this.elements.endpointTestStatus.classList.add('hidden');
                this.elements.bulkEndpointTestStatus.classList.add('hidden');
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
      //  const endpoint = this.elements.endpointInput.value.trim();
        const bulkEndpoint = this.elements.bulkEndpointInput.value.trim();
        const mode = this.elements.modeSelect.value;

        // if (!endpoint && !bulkEndpoint) {
        //     this.showAlert('Please enter at least one endpoint URL (realtime or bulk)', 'danger');
        //     return;
        // }
          if (!bulkEndpoint) {
            this.showAlert('Please enter at least one endpoint URL (realtime or bulk)', 'danger');
            return;
        }

        this.setButtonLoading(this.elements.startBtn, 'Starting...');

        try {
            const result = await this.apiClient.startCapture(bulkEndpoint, mode);
            
            if (result.success) {
                this.showAlert(result.message, 'success');
                this.updateCaptureStatus(true);
                // Note: Don't automatically enable bulk buttons here
                // They should be enabled when actual log events are received
            } else {
                this.showAlert(result.message, 'danger');
                // If start fails, ensure we're in stopped state
                this.updateCaptureStatus(false);
            }
        } catch (error) {
            this.showAlert(`Error starting capture: ${error.message}`, 'danger');
            // If error occurs, ensure we're in stopped state
            this.updateCaptureStatus(false);
        } finally {
            this.resetButtonLoading(this.elements.startBtn, '▶️ Start Capturing');
            // Ensure start button is properly enabled/disabled after reset
            if (this.isCapturing) {
                this.elements.startBtn.disabled = true;
            } else {
                this.elements.startBtn.disabled = false;
            }
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
                // Even if API fails, update UI state for consistency
                this.updateCaptureStatus(false);
            }
        } catch (error) {
            this.showAlert(`Error stopping capture: ${error.message}`, 'danger');
            // Even if there's an error, update UI state
            this.updateCaptureStatus(false);
        } finally {
            this.resetButtonLoading(this.elements.stopBtn, '⏹️ Stop Capturing');
            // Ensure stop button is disabled after reset
            if (!this.isCapturing) {
                this.elements.stopBtn.disabled = true;
            }
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
        button.innerHTML = originalText;
        // Re-enable the button only if it should be enabled based on current state
        if (button === this.elements.startBtn) {
            button.disabled = this.isCapturing;
        } else if (button === this.elements.stopBtn) {
            button.disabled = !this.isCapturing;
        } else if (button === this.elements.bulkPublishBtn) {
            // For bulk buttons, call updateBulkButtonStates to set proper state
            this.updateBulkButtonStates();
        } else {
            // For other buttons, enable them
            button.disabled = false;
        }
    }

    /**
     * Update bulk button states
     * Bulk buttons should only be enabled when:
     * 1. Capture is NOT running (stopped)
     * 2. There are logs available in the UI
     */
    updateBulkButtonStates() {
        const shouldEnable = !this.isCapturing && this.hasLogsInUI;
        
        this.elements.bulkPublishBtn.disabled = !shouldEnable;
        this.elements.clearBulkBtn.disabled = !shouldEnable;
        this.elements.previewBulkBtn.disabled = !shouldEnable;
        
        // Update button text to reflect status
        if (this.isCapturing) {
            this.elements.bulkPublishBtn.innerHTML = '📦 Publish Logs (Stop capturing first)';
        } else if (!this.hasLogsInUI) {
            this.elements.bulkPublishBtn.innerHTML = '📦 Publish Logs (No logs captured)';
        } else {
            this.elements.bulkPublishBtn.innerHTML = '📦 Publish Logs';
        }
    }

    /**
     * Update bulk count display
     */
    updateBulkCount(count) {
        // Update bulk button states based on capture status and log availability
        this.updateBulkButtonStates();
        
        // If count becomes 0, we have no logs in backend
        if (count === 0) {
            // Check if we also have no logs in UI (could be different from backend)
            const logsInUI = this.elements.logsContainer.children.length > 0;
            if (!logsInUI) {
                this.hasLogsInUI = false;
                this.updateBulkButtonStates();
            }
        }
    }

    /**
     * Bulk publish logs
     */
    async bulkPublish() {
        if (!confirm('Are you sure you want to publish all accumulated logs to the bulk endpoint?')) {
            return;
        }

        this.setButtonLoading(this.elements.bulkPublishBtn, 'Publishing...');

        try {
            const result = await this.apiClient.bulkPublish();
            
            if (result.success) {
                this.showAlert(`Successfully published ${result.published_count} events`, 'success');
                this.updateBulkCount(0);
            } else {
                this.showAlert(`Bulk publish failed: ${result.message}`, 'danger');
            }
        } catch (error) {
            this.showAlert(`Error publishing bulk data: ${error.message}`, 'danger');
        } finally {
            this.resetButtonLoading(this.elements.bulkPublishBtn, '📦 Publish Bulk ');
        }
    }

    /**
     * Clear bulk logs
     */
    async clearBulkLogs() {
        if (!confirm('Are you sure you want to clear all accumulated bulk logs?')) {
            return;
        }

        try {
            const result = await this.apiClient.clearBulkLogs();
            
            if (result.success) {
                this.showAlert(`Cleared ${result.cleared_count} bulk logs`, 'success');
                this.updateBulkCount(0);
            } else {
                this.showAlert(`Failed to clear bulk logs: ${result.message}`, 'danger');
            }
        } catch (error) {
            this.showAlert(`Error clearing bulk logs: ${error.message}`, 'danger');
        }
    }

    /**
     * Preview bulk logs
     */
    async previewBulkLogs() {
        try {
            const result = await this.apiClient.getBulkLogs();
            
            if (result.total_count === 0) {
                this.showAlert('No bulk logs to preview', 'info');
                return;
            }

            // Create preview modal or alert
            const preview = result.logs.slice(0, 5).map(log => 
                `${log.timestamp}: ${log.matched_text.substring(0, 100)}...`
            ).join('\n\n');
            
            const message = `Bulk Logs Preview (${result.total_count} total, showing first 5):\n\n${preview}`;
            if (result.has_more) {
                message += `\n\n... and ${result.total_count - 5} more events`;
            }
            
            alert(message);
        } catch (error) {
            this.showAlert(`Error previewing bulk logs: ${error.message}`, 'danger');
        }
    }

    /**
     * Handle bulk publish result from WebSocket
     */
    handleBulkPublishResult(data) {
        if (data.success) {
            this.showAlert(`Bulk publish successful: ${data.published_count} events`, 'success');
            this.updateBulkCount(0);
            // After successful publish, reset button text
            this.elements.bulkPublishBtn.innerHTML = '📦 Publish Logs';
        } else {
            this.showAlert('Bulk publish failed', 'danger');
        }
    }

    /**
     * Handle bulk logs cleared from WebSocket
     */
    handleBulkLogsCleared(data) {
        this.showAlert(`Bulk logs cleared: ${data.cleared_count} events`, 'info');
        this.updateBulkCount(0);
        // After clearing, reset button text
        this.elements.bulkPublishBtn.innerHTML = '📦 Publish Logs';
    }

    /**
     * Show supported data types modal
     */
    showDataTypesModal() {
        this.elements.dataTypesModal.classList.add('show');
        document.body.style.overflow = 'hidden'; // Prevent background scrolling
    }

    /**
     * Hide supported data types modal
     */
    hideDataTypesModal() {
        this.elements.dataTypesModal.classList.remove('show');
        document.body.style.overflow = ''; // Restore background scrolling
    }

    /**
     * Update supported data types content
     * Call this method to update the modal content with your data types information
     */
    updateSupportedDataTypes(content) {
        this.elements.modalBody.innerHTML = content;
    }

    /**
     * Initialize UI on page load
     */
    async initialize() {
        // Initialize bulk count
        this.updateBulkCount(0);
        
        // Initialize button states
        this.updateCaptureStatus(false);
        
        // Set initial hasLogsInUI state
        this.hasLogsInUI = false;
        this.updateBulkButtonStates();
        
        // Sync with server state
        try {
            const status = await this.apiClient.getStatus();
            this.updateCaptureStatus(status.is_capturing);
            
            // Update bulk count if available
            if (status.bulk_logs_count !== undefined) {
                this.updateBulkCount(status.bulk_logs_count);
            }
        } catch (error) {
            console.warn('Could not sync with server status:', error);
        }
    }
}

// Export for use in other modules
window.UIManager = UIManager;