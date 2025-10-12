"""
WebSocket Event Handler Module

Handles real-time communication between server and clients via WebSocket.
Follows Single Responsibility Principle by focusing only on WebSocket operations.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
import threading
import json


class EventEmitter(ABC):
    """Abstract interface for event emission (Interface Segregation Principle)"""
    
    @abstractmethod
    def emit(self, event: str, data: Any) -> None:
        """Emit an event to clients"""
        pass
    
    @abstractmethod
    def emit_to_room(self, room: str, event: str, data: Any) -> None:
        """Emit an event to specific room"""
        pass


class WebSocketEventHandler:
    """
    WebSocket event handler for real-time communication.
    Single Responsibility: Handle WebSocket events and real-time updates.
    """
    
    def __init__(self, socketio_instance):
        self._socketio = socketio_instance
        self._connected_clients: List[str] = []
        self._lock = threading.Lock()
        
        # Register event handlers
        self._register_handlers()
    
    def _register_handlers(self) -> None:
        """Register WebSocket event handlers"""
        
        @self._socketio.on('connect')
        def handle_connect():
            """Handle client connection"""
            with self._lock:
                # Note: In real SocketIO, we'd get the session ID
                # This is a simplified version
                pass
            
            self.emit_connection_status(True)
        
        @self._socketio.on('disconnect')
        def handle_disconnect():
            """Handle client disconnection"""
            with self._lock:
                # Note: In real SocketIO, we'd remove the specific session
                pass
            
            self.emit_connection_status(False)
    
    def emit_connection_status(self, connected: bool) -> None:
        """Emit connection status to clients"""
        self._socketio.emit('connection_status', {
            'connected': connected,
            'timestamp': datetime.now().isoformat()
        })
    
    def emit_device_status(self, status: Dict[str, Any]) -> None:
        """Emit device status update to all clients"""
        self._socketio.emit('device_status', status)
    
    def emit_capture_status(self, status: str, message: str) -> None:
        """Emit capture status update to all clients"""
        self._socketio.emit('status_update', {
            'status': status,
            'message': message,
            'timestamp': datetime.now().isoformat()
        })
    
    def emit_log_event(self, log_data: Dict[str, Any]) -> None:
        """Emit log event to all clients"""
        # Add additional metadata for UI
        enhanced_data = log_data.copy()
        enhanced_data['ui_timestamp'] = datetime.now().isoformat()
        
        self._socketio.emit('log_event', enhanced_data)
    
    def emit_webhook_result(self, result: Dict[str, Any]) -> None:
        """Emit webhook operation result to all clients"""
        self._socketio.emit('webhook_result', result)
    
    def emit_settings_update(self, settings: Dict[str, Any]) -> None:
        """Emit settings update to all clients"""
        self._socketio.emit('settings_loaded', settings)
    
    def emit_error(self, error_message: str, error_type: str = 'general') -> None:
        """Emit error message to all clients"""
        self._socketio.emit('error', {
            'type': error_type,
            'message': error_message,
            'timestamp': datetime.now().isoformat()
        })
    
    def get_connected_client_count(self) -> int:
        """Get number of connected clients"""
        with self._lock:
            return len(self._connected_clients)


class EventBridge:
    """
    Bridge between application components and WebSocket events.
    Single Responsibility: Coordinate events between different modules.
    """
    
    def __init__(self, websocket_handler: WebSocketEventHandler):
        self._websocket_handler = websocket_handler
        self._event_handlers: Dict[str, List[Callable]] = {}
    
    def register_event_handler(self, event_type: str, handler: Callable) -> None:
        """Register a handler for specific event type"""
        if event_type not in self._event_handlers:
            self._event_handlers[event_type] = []
        self._event_handlers[event_type].append(handler)
    
    def emit_event(self, event_type: str, data: Any) -> None:
        """Emit event to both WebSocket and registered handlers"""
        # Emit to WebSocket clients
        if hasattr(self._websocket_handler, f'emit_{event_type}'):
            method = getattr(self._websocket_handler, f'emit_{event_type}')
            method(data)
        
        # Emit to registered handlers
        if event_type in self._event_handlers:
            for handler in self._event_handlers[event_type]:
                try:
                    handler(data)
                except Exception as e:
                    print(f"Error in event handler for {event_type}: {e}")


# Observer implementations for integration with other modules
from .device_manager import DeviceStatusObserver
from .settings_manager import SettingsObserver
from .log_capturer import LogObserver
from .webhook_manager import WebhookObserver


class WebSocketDeviceObserver(DeviceStatusObserver):
    """Device status observer that emits to WebSocket"""
    
    def __init__(self, websocket_handler: WebSocketEventHandler):
        self._websocket_handler = websocket_handler
    
    def on_device_status_changed(self, status: Dict[str, Any]) -> None:
        """Forward device status to WebSocket clients"""
        self._websocket_handler.emit_device_status(status)


class WebSocketSettingsObserver(SettingsObserver):
    """Settings observer that emits to WebSocket"""
    
    def __init__(self, websocket_handler: WebSocketEventHandler):
        self._websocket_handler = websocket_handler
    
    def on_settings_changed(self, settings: Dict[str, Any]) -> None:
        """Forward settings changes to WebSocket clients"""
        self._websocket_handler.emit_settings_update(settings)


class WebSocketLogObserver(LogObserver):
    """Log observer that emits to WebSocket"""
    
    def __init__(self, websocket_handler: WebSocketEventHandler, event_bridge: Optional[EventBridge] = None):
        self._websocket_handler = websocket_handler
        self._event_bridge = event_bridge
    
    def on_log_event(self, log_data: Dict[str, Any]) -> None:
        """Forward log events to WebSocket clients"""
        self._websocket_handler.emit_log_event(log_data)
        
        # Also emit through event bridge if available
        if self._event_bridge:
            self._event_bridge.emit_event('log_captured', log_data)


class WebSocketWebhookObserver(WebhookObserver):
    """Webhook observer that emits to WebSocket"""
    
    def __init__(self, websocket_handler: WebSocketEventHandler):
        self._websocket_handler = websocket_handler
    
    def on_webhook_result(self, result: Dict[str, Any]) -> None:
        """Forward webhook results to WebSocket clients"""
        self._websocket_handler.emit_webhook_result(result)


class ApplicationEventCoordinator:
    """
    Central coordinator for all application events.
    Single Responsibility: Coordinate events between all application modules.
    """
    
    def __init__(self, websocket_handler: WebSocketEventHandler):
        self._websocket_handler = websocket_handler
        self._event_bridge = EventBridge(websocket_handler)
        
        # Create observers
        self._device_observer = WebSocketDeviceObserver(websocket_handler)
        self._settings_observer = WebSocketSettingsObserver(websocket_handler)
        self._log_observer = WebSocketLogObserver(websocket_handler, self._event_bridge)
        self._webhook_observer = WebSocketWebhookObserver(websocket_handler)
    
    def get_device_observer(self) -> WebSocketDeviceObserver:
        """Get device status observer"""
        return self._device_observer
    
    def get_settings_observer(self) -> WebSocketSettingsObserver:
        """Get settings observer"""
        return self._settings_observer
    
    def get_log_observer(self) -> WebSocketLogObserver:
        """Get log observer"""
        return self._log_observer
    
    def get_webhook_observer(self) -> WebSocketWebhookObserver:
        """Get webhook observer"""
        return self._webhook_observer
    
    def get_event_bridge(self) -> EventBridge:
        """Get event bridge"""
        return self._event_bridge
    
    def emit_capture_status(self, status: str, message: str) -> None:
        """Emit capture status update"""
        self._websocket_handler.emit_capture_status(status, message)
    
    def emit_error(self, error_message: str, error_type: str = 'general') -> None:
        """Emit error message"""
        self._websocket_handler.emit_error(error_message, error_type)
    
    def register_custom_handler(self, event_type: str, handler: Callable) -> None:
        """Register custom event handler"""
        self._event_bridge.register_event_handler(event_type, handler)


class WebSocketEventHandlerFactory:
    """
    Factory for creating WebSocket event handlers.
    Single Responsibility: Create WebSocket-related instances.
    """
    
    @staticmethod
    def create_event_handler(socketio_instance) -> WebSocketEventHandler:
        """Create WebSocket event handler"""
        return WebSocketEventHandler(socketio_instance)
    
    @staticmethod
    def create_event_coordinator(socketio_instance) -> ApplicationEventCoordinator:
        """Create application event coordinator"""
        websocket_handler = WebSocketEventHandlerFactory.create_event_handler(socketio_instance)
        return ApplicationEventCoordinator(websocket_handler)
    
    @staticmethod
    def create_event_bridge(websocket_handler: WebSocketEventHandler) -> EventBridge:
        """Create event bridge"""
        return EventBridge(websocket_handler)