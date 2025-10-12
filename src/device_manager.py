"""
Device Manager Module

Handles Android device detection and monitoring.
Follows Single Responsibility Principle by focusing only on device-related operations.
"""

import subprocess
import threading
import time
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime


class DeviceInterface(ABC):
    """Abstract interface for device operations (Interface Segregation Principle)"""
    
    @abstractmethod
    def get_connected_devices(self) -> List[str]:
        """Get list of connected device IDs"""
        pass
    
    @abstractmethod
    def is_device_connected(self) -> bool:
        """Check if any device is connected"""
        pass


class DeviceStatusObserver(ABC):
    """Observer interface for device status updates (Observer Pattern)"""
    
    @abstractmethod
    def on_device_status_changed(self, status: Dict[str, Any]) -> None:
        """Called when device status changes"""
        pass


class ADBDeviceManager(DeviceInterface):
    """
    Concrete implementation for ADB device management.
    Single Responsibility: Handle ADB device operations only.
    """
    
    def __init__(self):
        self._last_device_count = 0
        self._last_check_time = None
    
    def get_connected_devices(self) -> List[str]:
        """Get list of connected ADB devices"""
        try:
            result = subprocess.run(
                ['adb', 'devices'], 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            
            if result.returncode != 0:
                return []
            
            devices = []
            lines = result.stdout.strip().split('\n')[1:]  # Skip header
            
            for line in lines:
                line = line.strip()
                if line and '\tdevice' in line:
                    device_id = line.split('\t')[0]
                    devices.append(device_id)
            
            return devices
            
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
            return []
    
    def is_device_connected(self) -> bool:
        """Check if any device is connected"""
        return len(self.get_connected_devices()) > 0
    
    def get_device_info(self) -> Dict[str, Any]:
        """Get detailed device information"""
        devices = self.get_connected_devices()
        device_count = len(devices)
        
        status = {
            'connected': device_count > 0,
            'device_count': device_count,
            'devices': devices,
            'timestamp': datetime.now().strftime('%H:%M:%S'),
        }
        
        if device_count > 0:
            status['message'] = f"Connected to {device_count} device(s)"
        else:
            status['message'] = "No devices connected"
        
        return status


class DeviceMonitor:
    """
    Device monitoring service with observer pattern support.
    Open/Closed Principle: Extensible through observers without modification.
    """
    
    def __init__(self, device_manager: DeviceInterface, check_interval: int = 5):
        self._device_manager = device_manager
        self._check_interval = check_interval
        self._observers: List[DeviceStatusObserver] = []
        self._monitoring = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._last_status = None
    
    def add_observer(self, observer: DeviceStatusObserver) -> None:
        """Add observer for device status changes"""
        self._observers.append(observer)
    
    def remove_observer(self, observer: DeviceStatusObserver) -> None:
        """Remove observer"""
        if observer in self._observers:
            self._observers.remove(observer)
    
    def _notify_observers(self, status: Dict[str, Any]) -> None:
        """Notify all observers of status change"""
        for observer in self._observers:
            try:
                observer.on_device_status_changed(status)
            except Exception as e:
                print(f"Error notifying observer: {e}")
    
    def start_monitoring(self) -> None:
        """Start device monitoring in background thread"""
        if self._monitoring:
            return
        
        self._monitoring = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
    
    def stop_monitoring(self) -> None:
        """Stop device monitoring"""
        self._monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=1)
    
    def _monitor_loop(self) -> None:
        """Main monitoring loop"""
        while self._monitoring:
            try:
                if isinstance(self._device_manager, ADBDeviceManager):
                    current_status = self._device_manager.get_device_info()
                else:
                    # Fallback for other device managers
                    current_status = {
                        'connected': self._device_manager.is_device_connected(),
                        'devices': self._device_manager.get_connected_devices(),
                        'timestamp': datetime.now().strftime('%H:%M:%S'),
                        'message': 'Device status checked'
                    }
                
                # Only notify if status changed
                if self._has_status_changed(current_status):
                    self._last_status = current_status.copy()
                    self._notify_observers(current_status)
                
                time.sleep(self._check_interval)
                
            except Exception as e:
                print(f"Error in device monitoring: {e}")
                time.sleep(self._check_interval)
    
    def _has_status_changed(self, new_status: Dict[str, Any]) -> bool:
        """Check if device status has changed significantly"""
        if self._last_status is None:
            return True
        
        # Compare key fields
        return (
            self._last_status.get('connected') != new_status.get('connected') or
            self._last_status.get('device_count') != new_status.get('device_count') or
            len(self._last_status.get('devices', [])) != len(new_status.get('devices', []))
        )
    
    def get_current_status(self) -> Optional[Dict[str, Any]]:
        """Get the last known device status"""
        if isinstance(self._device_manager, ADBDeviceManager):
            return self._device_manager.get_device_info()
        return None


class DeviceManagerFactory:
    """
    Factory for creating device managers.
    Single Responsibility: Create appropriate device manager instances.
    """
    
    @staticmethod
    def create_device_manager(device_type: str = 'adb') -> DeviceInterface:
        """Create device manager based on type"""
        if device_type.lower() == 'adb':
            return ADBDeviceManager()
        else:
            raise ValueError(f"Unsupported device type: {device_type}")
    
    @staticmethod
    def create_monitor(device_type: str = 'adb', check_interval: int = 5) -> DeviceMonitor:
        """Create device monitor with appropriate device manager"""
        device_manager = DeviceManagerFactory.create_device_manager(device_type)
        return DeviceMonitor(device_manager, check_interval)