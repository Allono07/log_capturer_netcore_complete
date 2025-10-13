/**
 * API Client Module
 * 
 * Handles all API communication with the server.
 * Single Responsibility: Manage HTTP requests to the backend API.
 */

class APIClient {
    constructor(baseURL = '') {
        this.baseURL = baseURL;
        this.defaultHeaders = {
            'Content-Type': 'application/json'
        };
    }

    /**
     * Make a generic API request
     */
    async makeRequest(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const config = {
            headers: { ...this.defaultHeaders, ...options.headers },
            ...options
        };

        try {
            const response = await fetch(url, config);
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.message || `HTTP ${response.status}: ${response.statusText}`);
            }
            
            return data;
        } catch (error) {
            console.error(`API request failed for ${endpoint}:`, error);
            throw error;
        }
    }

    /**
     * Start log capture
     */
    async startCapture(endpoint, bulkEndpoint, mode) {
        return this.makeRequest('/api/start', {
            method: 'POST',
            body: JSON.stringify({ 
                endpoint, 
                bulk_endpoint: bulkEndpoint, 
                mode 
            })
        });
    }

    /**
     * Stop log capture
     */
    async stopCapture() {
        return this.makeRequest('/api/stop', {
            method: 'POST'
        });
    }

    /**
     * Get application status
     */
    async getStatus() {
        return this.makeRequest('/api/status');
    }

    /**
     * Get device status
     */
    async getDeviceStatus() {
        return this.makeRequest('/api/device-status');
    }

    /**
     * Test webhook endpoint connectivity
     */
    async testEndpoint(endpoint, type = 'realtime') {
        return this.makeRequest('/api/test-endpoint', {
            method: 'POST',
            body: JSON.stringify({ endpoint, type })
        });
    }

    /**
     * Save settings
     */
    async saveSettings(settings) {
        return this.makeRequest('/api/settings', {
            method: 'POST',
            body: JSON.stringify(settings)
        });
    }

    /**
     * Clear settings
     */
    async clearSettings() {
        return this.makeRequest('/api/settings/clear', {
            method: 'POST'
        });
    }

    /**
     * Download logs
     */
    downloadLogs() {
        window.open('/api/download', '_blank');
    }

    /**
     * Publish bulk logs
     */
    async bulkPublish() {
        return this.makeRequest('/api/bulk-publish', {
            method: 'POST'
        });
    }

    /**
     * Get bulk logs for preview
     */
    async getBulkLogs() {
        return this.makeRequest('/api/bulk-logs');
    }

    /**
     * Clear bulk logs
     */
    async clearBulkLogs() {
        return this.makeRequest('/api/bulk-logs/clear', {
            method: 'POST'
        });
    }
}

// Export for use in other modules
window.APIClient = APIClient;