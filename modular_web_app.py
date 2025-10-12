"""
Modular Web Application

Refactored web application using SOLID principles and dependency injection.
This replaces the monolithic web_app.py with a modular, scalable architecture.
"""

from flask import Flask, app, render_template, request, jsonify, send_file
from flask_socketio import SocketIO
import threading
import time
import json
from datetime import datetime
from typing import Optional, Dict, Any
import os

import socketio

# Import our modular components
from src import (
    get_config_manager, get_app_config,
    DeviceManagerFactory,
    SettingsManagerFactory,
    LogCapturerFactory,
    WebhookManagerFactory,
    WebSocketEventHandlerFactory
)


class ApplicationCore:
    """
    Core application class that coordinates all modules.
    Single Responsibility: Coordinate application components using dependency injection.
    """
    
    def __init__(self):
        # Load configuration
        self._config_manager = get_config_manager()
        self._app_config = self._config_manager.get_configuration()
        
        # Initialize Flask and SocketIO
        self._app = Flask(__name__)
        self._app.config['SECRET_KEY'] = 'android-log-capturer-secret-key'
        self._socketio = SocketIO(self._app, cors_allowed_origins="*")
        
        # Initialize core modules
        self._settings_manager = SettingsManagerFactory.create_composite_manager(
            self._app_config.settings_file
        )
        
        device_config = self._config_manager.get_device_config()
        self._device_monitor = DeviceManagerFactory.create_monitor(
            device_config['device_type'],
            device_config['check_interval']
        )
        
        self._log_capture_manager = LogCapturerFactory.create_manager()
        
        webhook_config = self._config_manager.get_webhook_config()
        self._webhook_manager = WebhookManagerFactory.create_async_webhook_manager(
            webhook_config['timeout'],
            webhook_config['retry_count']
        )
        
        # Initialize WebSocket event coordination
        self._event_coordinator = WebSocketEventHandlerFactory.create_event_coordinator(
            self._socketio
        )
        
        # State management
        self._is_capturing = False
        self._capture_thread: Optional[threading.Thread] = None
        
        # Setup observers and integrations
        self._setup_observers()
        
        # Register Flask routes
        self._register_routes()
        
        # Load initial settings
        self._load_initial_settings()
    
    def _setup_observers(self) -> None:
        """Setup observers to connect modules with WebSocket events"""
        # Device monitoring
        self._device_monitor.add_observer(self._event_coordinator.get_device_observer())
        
        # Settings management
        self._settings_manager.add_observer(self._event_coordinator.get_settings_observer())
        
        # Log capture
        self._log_capture_manager.add_observer(self._event_coordinator.get_log_observer())
        
        # Webhook management
        self._webhook_manager.add_observer(self._event_coordinator.get_webhook_observer())
        
        # Custom event handlers
        self._event_coordinator.register_custom_handler(
            'log_captured', 
            self._handle_log_captured
        )
    
    def _handle_log_captured(self, log_data: Dict[str, Any]) -> None:
        """Handle captured log events by sending to webhook"""
        if self._is_capturing:
            self._webhook_manager.queue_send(log_data)
    
    def _load_initial_settings(self) -> None:
        """Load and apply initial settings"""
        try:
            settings = self._settings_manager.load_settings()
            
            # Configure webhook manager
            self._webhook_manager.configure(
                settings.get('endpoint', ''),
                settings.get('mode', 'raw')
            )
            
            # Emit settings to connected clients
            self._event_coordinator.get_settings_observer().on_settings_changed(settings)
            
        except Exception as e:
            print(f"Error loading initial settings: {e}")
    
    def _register_routes(self) -> None:
        """Register Flask routes"""
        
        @self._app.route('/')
        def index():
            """Main page"""
            settings = self._settings_manager.load_settings()
            return render_template('index.html', **settings)
        
        @self._app.route('/api/start', methods=['POST'])
        def start_capture():
            """Start log capture"""
            try:
                data = request.get_json() or {}
                endpoint = data.get('endpoint', '').strip()
                mode = data.get('mode', 'raw')
                
                if not endpoint:
                    return jsonify({
                        'success': False,
                        'message': 'Endpoint URL is required'
                    })
                
                # Save settings
                settings = {'endpoint': endpoint, 'mode': mode}
                self._settings_manager.save_settings(settings)
                
                # Configure webhook manager
                self._webhook_manager.configure(endpoint, mode)
                
                # Start capture
                if self._log_capture_manager.start_adb_capture():
                    self._is_capturing = True
                    self._event_coordinator.emit_capture_status('capturing', 'Log capture started')
                    
                    return jsonify({
                        'success': True,
                        'message': 'Log capture started successfully'
                    })
                else:
                    return jsonify({
                        'success': False,
                        'message': 'Failed to start log capture - check ADB connection'
                    })
                    
            except Exception as e:
                return jsonify({
                    'success': False,
                    'message': f'Error starting capture: {str(e)}'
                })
        
        @self._app.route('/api/stop', methods=['POST'])
        def stop_capture():
            """Stop log capture"""
            try:
                if self._log_capture_manager.stop_capture():
                    self._is_capturing = False
                    self._event_coordinator.emit_capture_status('stopped', 'Log capture stopped')
                    
                    return jsonify({
                        'success': True,
                        'message': 'Log capture stopped successfully'
                    })
                else:
                    return jsonify({
                        'success': False,
                        'message': 'Failed to stop log capture'
                    })
                    
            except Exception as e:
                return jsonify({
                    'success': False,
                    'message': f'Error stopping capture: {str(e)}'
                })
        
        @self._app.route('/api/status', methods=['GET'])
        def get_status():
            """Get current application status"""
            try:
                device_status = self._device_monitor.get_current_status()
                settings = self._settings_manager.load_settings()
                
                return jsonify({
                    'success': True,
                    'is_capturing': self._is_capturing,
                    'device_status': device_status,
                    'settings': settings,
                    'webhook_config': self._webhook_manager.get_configuration()
                })
                
            except Exception as e:
                return jsonify({
                    'success': False,
                    'message': f'Error getting status: {str(e)}'
                })
        
        @self._app.route('/api/device-status', methods=['GET'])
        def get_device_status():
            """Get device status"""
            try:
                status = self._device_monitor.get_current_status()
                return jsonify({
                    'success': True,
                    **status
                })
                
            except Exception as e:
                return jsonify({
                    'success': False,
                    'message': f'Error getting device status: {str(e)}'
                })
        
        @self._app.route('/api/test-endpoint', methods=['POST'])
        def test_endpoint():
            """Test webhook endpoint connectivity"""
            try:
                data = request.get_json() or {}
                endpoint = data.get('endpoint', '').strip()
                
                if not endpoint:
                    return jsonify({
                        'success': False,
                        'message': 'Endpoint URL is required'
                    })
                
                result = self._webhook_manager.test_endpoint(endpoint)
                return jsonify(result)
                
            except Exception as e:
                return jsonify({
                    'success': False,
                    'message': f'Error testing endpoint: {str(e)}'
                })
        
        @self._app.route('/api/settings', methods=['POST'])
        def save_settings():
            """Save application settings"""
            try:
                data = request.get_json() or {}
                
                if self._settings_manager.save_settings(data):
                    # Update webhook manager configuration
                    self._webhook_manager.configure(
                        data.get('endpoint', ''),
                        data.get('mode', 'raw')
                    )
                    
                    return jsonify({
                        'success': True,
                        'message': 'Settings saved successfully'
                    })
                else:
                    return jsonify({
                        'success': False,
                        'message': 'Failed to save settings'
                    })
                    
            except Exception as e:
                return jsonify({
                    'success': False,
                    'message': f'Error saving settings: {str(e)}'
                })
        
        @self._app.route('/api/settings/clear', methods=['POST'])
        def clear_settings():
            """Clear all settings"""
            try:
                if self._settings_manager.clear_settings():
                    # Reset webhook manager
                    self._webhook_manager.configure('', 'raw')
                    
                    return jsonify({
                        'success': True,
                        'message': 'Settings cleared successfully'
                    })
                else:
                    return jsonify({
                        'success': False,
                        'message': 'Failed to clear settings'
                    })
                    
            except Exception as e:
                return jsonify({
                    'success': False,
                    'message': f'Error clearing settings: {str(e)}'
                })
        
        @self._app.route('/api/download', methods=['GET'])
        def download_logs():
            """Download captured logs"""
            try:
                # This would need to be implemented based on where logs are stored
                # For now, return a simple response
                return jsonify({
                    'success': False,
                    'message': 'Log download not implemented in modular version yet'
                })
                
            except Exception as e:
                return jsonify({
                    'success': False,
                    'message': f'Error downloading logs: {str(e)}'
                })
    
    def start_background_services(self) -> None:
        """Start background services"""
        # Start device monitoring
        self._device_monitor.start_monitoring()
    
    def stop_background_services(self) -> None:
        """Stop background services"""
        # Stop device monitoring
        self._device_monitor.stop_monitoring()
        
        # Stop webhook manager
        self._webhook_manager.stop_worker()
        
        # Stop log capture
        if self._is_capturing:
            self._log_capture_manager.stop_capture()
    
    def get_app(self) -> Flask:
        """Get Flask application instance"""
        return self._app
    
    def get_socketio(self) -> SocketIO:
        """Get SocketIO instance"""
        return self._socketio
    
    def run(self) -> None:
        """Run the application"""
        # Start background services
        self.start_background_services()
        
        try:
            # Get server configuration
            server_config = self._config_manager.get_server_config()
            
            print(f"Starting Android Log Capturer Web Application...")
            print(f"Server: http://{server_config['host']}:{server_config['port']}")
            print(f"Debug mode: {server_config['debug']}")
            
            # Run the application
            self._socketio.run(
                self._app,
                host=server_config['host'],
                port=server_config['port'],
                debug=server_config['debug']
            )
            
        except KeyboardInterrupt:
            print("\nShutting down gracefully...")
        finally:
            # Stop background services
            self.stop_background_services()


def create_app() -> ApplicationCore:
    """
    Application factory function.
    Creates and configures the application with all dependencies.
    """
    return ApplicationCore()


def main():
    """Main entry point"""
    app_core = create_app()
    app_core.run()


if __name__ == '__main__':
    main()