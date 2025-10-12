/**
 * Main Application Module
 * 
 * Entry point for the modular frontend application.
 * Coordinates all modules and initializes the application.
 */

class Application {
    constructor() {
        this.apiClient = null;
        this.webSocketManager = null;
        this.uiManager = null;
        this.initialized = false;
    }

    /**
     * Initialize the application
     */
    async initialize() {
        if (this.initialized) {
            console.warn('Application already initialized');
            return;
        }

        try {
            console.log('Initializing Android Log Capturer Application...');

            // Initialize API client
            this.apiClient = new APIClient();
            console.log('✓ API Client initialized');

            // Initialize WebSocket manager
            this.webSocketManager = new WebSocketManager();
            if (!this.webSocketManager.connect()) {
                throw new Error('Failed to initialize WebSocket connection');
            }
            console.log('✓ WebSocket Manager initialized');

            // Initialize UI manager
            this.uiManager = new UIManager(this.apiClient, this.webSocketManager);
            console.log('✓ UI Manager initialized');

            // Setup error handlers
            this.setupErrorHandlers();

            // Initialize UI
            this.uiManager.initialize();

            this.initialized = true;
            console.log('✓ Application initialization complete');

        } catch (error) {
            console.error('Application initialization failed:', error);
            this.showCriticalError('Failed to initialize application', error.message);
        }
    }

    /**
     * Setup global error handlers
     */
    setupErrorHandlers() {
        // Handle uncaught JavaScript errors
        window.addEventListener('error', (event) => {
            console.error('Uncaught error:', event.error);
            this.handleError('JavaScript Error', event.error.message);
        });

        // Handle unhandled promise rejections
        window.addEventListener('unhandledrejection', (event) => {
            console.error('Unhandled promise rejection:', event.reason);
            this.handleError('Promise Rejection', event.reason);
        });

        // Handle WebSocket connection failures
        this.webSocketManager.on('websocket_connection_failed', () => {
            this.showCriticalError(
                'WebSocket Connection Failed',
                'Unable to establish real-time connection to server. Please refresh the page.'
            );
        });
    }

    /**
     * Handle application errors
     */
    handleError(type, message) {
        if (this.uiManager) {
            this.uiManager.showAlert(`${type}: ${message}`, 'danger');
        } else {
            // Fallback if UI manager is not available
            console.error(`${type}: ${message}`);
        }
    }

    /**
     * Show critical error that prevents app functionality
     */
    showCriticalError(title, message) {
        // Create a modal or prominent error display
        const errorDiv = document.createElement('div');
        errorDiv.style.cssText = `
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: #dc3545;
            color: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.3);
            z-index: 9999;
            max-width: 400px;
            text-align: center;
        `;
        
        errorDiv.innerHTML = `
            <h3>${title}</h3>
            <p>${message}</p>
            <button onclick="location.reload()" style="
                background: white;
                color: #dc3545;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                cursor: pointer;
                margin-top: 10px;
            ">Reload Page</button>
        `;
        
        document.body.appendChild(errorDiv);
    }

    /**
     * Cleanup application resources
     */
    cleanup() {
        if (this.webSocketManager) {
            this.webSocketManager.disconnect();
        }
        
        console.log('Application cleanup complete');
    }

    /**
     * Get application status
     */
    getStatus() {
        return {
            initialized: this.initialized,
            webSocketConnected: this.webSocketManager?.isWebSocketConnected() || false,
            capturing: this.uiManager?.isCapturing || false
        };
    }
}

// Global application instance
let app = null;

/**
 * Initialize application when DOM is ready
 */
document.addEventListener('DOMContentLoaded', async () => {
    console.log('DOM loaded, initializing application...');
    
    try {
        app = new Application();
        await app.initialize();
    } catch (error) {
        console.error('Failed to initialize application:', error);
    }
});

/**
 * Cleanup on page unload
 */
window.addEventListener('beforeunload', () => {
    if (app) {
        app.cleanup();
    }
});

// Export application instance for debugging
window.app = app;