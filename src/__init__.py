"""
Android Log Capturer - Modular Architecture

This package contains the modular components of the Android Log Capturer application.
Each module follows SOLID principles for maintainability and scalability.

Modules:
- config: Configuration management
- device_manager: Device detection and monitoring
- settings_manager: Settings persistence and management
- log_capturer: Log capture and processing
- webhook_manager: Webhook operations and testing
- websocket_handler: Real-time WebSocket communication
"""

# Version information
__version__ = "2.0.0"
__author__ = "Android Log Capturer Team"

# Import main classes for easy access
from .config import ConfigurationManager, AppConfig, get_config_manager, get_app_config
from .device_manager import DeviceManagerFactory, DeviceMonitor, ADBDeviceManager
from .settings_manager import SettingsManagerFactory, JSONSettingsManager, CompositeSettingsManager
from .log_capturer import LogCapturerFactory, LogCaptureManager, AndroidLogProcessor
from .webhook_manager import WebhookManagerFactory, WebhookManager, AsyncWebhookManager
from .websocket_handler import WebSocketEventHandlerFactory, ApplicationEventCoordinator

__all__ = [
    # Configuration
    'ConfigurationManager', 'AppConfig', 'get_config_manager', 'get_app_config',
    
    # Device Management
    'DeviceManagerFactory', 'DeviceMonitor', 'ADBDeviceManager',
    
    # Settings Management
    'SettingsManagerFactory', 'JSONSettingsManager', 'CompositeSettingsManager',
    
    # Log Capture
    'LogCapturerFactory', 'LogCaptureManager', 'AndroidLogProcessor',
    
    # Webhook Management
    'WebhookManagerFactory', 'WebhookManager', 'AsyncWebhookManager',
    
    # WebSocket Handling
    'WebSocketEventHandlerFactory', 'ApplicationEventCoordinator'
]