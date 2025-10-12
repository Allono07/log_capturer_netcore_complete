/**
 * WebSocket Manager Module
 * 
 * Handles WebSocket connections and real-time events.
 * Single Responsibility: Manage WebSocket communication.
 */

class WebSocketManager {
    constructor() {
        this.socket = null;
        this.eventHandlers = new Map();
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectInterval = 3000;
        this.isConnected = false;
    }

    /**
     * Initialize WebSocket connection
     */
    connect() {
        try {
            this.socket = io();
            this.setupEventHandlers();
            return true;
        } catch (error) {
            console.error('Failed to initialize WebSocket:', error);
            return false;
        }
    }

    /**
     * Setup default WebSocket event handlers
     */
    setupEventHandlers() {
        if (!this.socket) return;

        this.socket.on('connect', () => {
            console.log('WebSocket connected');
            this.isConnected = true;
            this.reconnectAttempts = 0;
            this.emit('websocket_connected');
        });

        this.socket.on('disconnect', () => {
            console.log('WebSocket disconnected');
            this.isConnected = false;
            this.emit('websocket_disconnected');
            this.handleReconnect();
        });

        this.socket.on('device_status', (data) => {
            this.emit('device_status', data);
        });

        this.socket.on('status_update', (data) => {
            this.emit('status_update', data);
        });

        this.socket.on('log_event', (data) => {
            this.emit('log_event', data);
        });

        this.socket.on('settings_loaded', (settings) => {
            this.emit('settings_loaded', settings);
        });

        this.socket.on('webhook_result', (result) => {
            this.emit('webhook_result', result);
        });

        this.socket.on('error', (error) => {
            this.emit('websocket_error', error);
        });
    }

    /**
     * Handle reconnection logic
     */
    handleReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            console.log(`Attempting to reconnect... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
            
            setTimeout(() => {
                if (!this.isConnected) {
                    this.connect();
                }
            }, this.reconnectInterval);
        } else {
            console.error('Max reconnection attempts reached');
            this.emit('websocket_connection_failed');
        }
    }

    /**
     * Register event handler
     */
    on(event, handler) {
        if (!this.eventHandlers.has(event)) {
            this.eventHandlers.set(event, []);
        }
        this.eventHandlers.get(event).push(handler);
    }

    /**
     * Remove event handler
     */
    off(event, handler) {
        if (this.eventHandlers.has(event)) {
            const handlers = this.eventHandlers.get(event);
            const index = handlers.indexOf(handler);
            if (index > -1) {
                handlers.splice(index, 1);
            }
        }
    }

    /**
     * Emit event to registered handlers
     */
    emit(event, data) {
        if (this.eventHandlers.has(event)) {
            this.eventHandlers.get(event).forEach(handler => {
                try {
                    handler(data);
                } catch (error) {
                    console.error(`Error in event handler for ${event}:`, error);
                }
            });
        }
    }

    /**
     * Check if WebSocket is connected
     */
    isWebSocketConnected() {
        return this.isConnected;
    }

    /**
     * Disconnect WebSocket
     */
    disconnect() {
        if (this.socket) {
            this.socket.disconnect();
            this.socket = null;
            this.isConnected = false;
        }
    }
}

// Export for use in other modules
window.WebSocketManager = WebSocketManager;