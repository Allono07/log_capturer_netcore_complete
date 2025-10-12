"""
Settings Manager Module

Handles configuration persistence and management.
Follows Single Responsibility Principle by focusing only on settings operations.
"""

import json
import os
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from pathlib import Path


class SettingsInterface(ABC):
    """Abstract interface for settings operations (Interface Segregation Principle)"""
    
    @abstractmethod
    def load_settings(self) -> Dict[str, Any]:
        """Load settings from storage"""
        pass
    
    @abstractmethod
    def save_settings(self, settings: Dict[str, Any]) -> bool:
        """Save settings to storage"""
        pass
    
    @abstractmethod
    def clear_settings(self) -> bool:
        """Clear all settings"""
        pass
    
    @abstractmethod
    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a specific setting value"""
        pass
    
    @abstractmethod
    def set_setting(self, key: str, value: Any) -> bool:
        """Set a specific setting value"""
        pass


class SettingsObserver(ABC):
    """Observer interface for settings changes (Observer Pattern)"""
    
    @abstractmethod
    def on_settings_changed(self, settings: Dict[str, Any]) -> None:
        """Called when settings change"""
        pass


class JSONSettingsManager(SettingsInterface):
    """
    JSON-based settings manager.
    Single Responsibility: Handle JSON file-based settings persistence.
    """
    
    def __init__(self, settings_file: str = "settings.json"):
        self._settings_file = Path(settings_file)
        self._settings_cache: Optional[Dict[str, Any]] = None
        self._observers: List[SettingsObserver] = []
        self._default_settings = {
            'endpoint': '',
            'mode': 'raw'
        }
    
    def add_observer(self, observer: SettingsObserver) -> None:
        """Add observer for settings changes"""
        self._observers.append(observer)
    
    def remove_observer(self, observer: SettingsObserver) -> None:
        """Remove observer"""
        if observer in self._observers:
            self._observers.remove(observer)
    
    def _notify_observers(self, settings: Dict[str, Any]) -> None:
        """Notify all observers of settings change"""
        for observer in self._observers:
            try:
                observer.on_settings_changed(settings)
            except Exception as e:
                print(f"Error notifying settings observer: {e}")
    
    def load_settings(self) -> Dict[str, Any]:
        """Load settings from JSON file"""
        try:
            if self._settings_file.exists():
                with open(self._settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    # Merge with defaults to ensure all keys exist
                    merged_settings = self._default_settings.copy()
                    merged_settings.update(settings)
                    self._settings_cache = merged_settings
                    return merged_settings
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading settings: {e}")
        
        # Return defaults if file doesn't exist or has errors
        self._settings_cache = self._default_settings.copy()
        return self._settings_cache
    
    def save_settings(self, settings: Dict[str, Any]) -> bool:
        """Save settings to JSON file"""
        try:
            # Validate settings before saving
            validated_settings = self._validate_settings(settings)
            
            with open(self._settings_file, 'w', encoding='utf-8') as f:
                json.dump(validated_settings, f, indent=2, ensure_ascii=False)
            
            self._settings_cache = validated_settings
            self._notify_observers(validated_settings)
            return True
            
        except (IOError, TypeError) as e:
            print(f"Error saving settings: {e}")
            return False
    
    def clear_settings(self) -> bool:
        """Clear all settings by deleting the file"""
        try:
            if self._settings_file.exists():
                self._settings_file.unlink()
            
            self._settings_cache = self._default_settings.copy()
            self._notify_observers(self._settings_cache)
            return True
            
        except OSError as e:
            print(f"Error clearing settings: {e}")
            return False
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a specific setting value"""
        if self._settings_cache is None:
            self.load_settings()
        
        return self._settings_cache.get(key, default)
    
    def set_setting(self, key: str, value: Any) -> bool:
        """Set a specific setting value"""
        if self._settings_cache is None:
            self.load_settings()
        
        self._settings_cache[key] = value
        return self.save_settings(self._settings_cache)
    
    def _validate_settings(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and sanitize settings"""
        validated = {}
        
        # Validate endpoint
        endpoint = settings.get('endpoint', '')
        if isinstance(endpoint, str):
            validated['endpoint'] = endpoint.strip()
        else:
            validated['endpoint'] = ''
        
        # Validate mode
        mode = settings.get('mode', 'raw')
        valid_modes = ['raw', 'json', 'both']
        if mode in valid_modes:
            validated['mode'] = mode
        else:
            validated['mode'] = 'raw'
        
        return validated
    
    def get_settings_file_path(self) -> str:
        """Get the path to the settings file"""
        return str(self._settings_file.absolute())


class EnvironmentSettingsManager(SettingsInterface):
    """
    Environment variable-based settings manager.
    Single Responsibility: Handle environment variable-based settings.
    """
    
    def __init__(self):
        self._env_mapping = {
            'endpoint': 'WEBHOOK_ENDPOINT',
            'mode': 'SEND_MODE'
        }
        self._default_settings = {
            'endpoint': '',
            'mode': 'raw'
        }
    
    def load_settings(self) -> Dict[str, Any]:
        """Load settings from environment variables"""
        settings = {}
        
        for key, env_var in self._env_mapping.items():
            value = os.getenv(env_var)
            if value is not None:
                settings[key] = value
            else:
                settings[key] = self._default_settings[key]
        
        return settings
    
    def save_settings(self, settings: Dict[str, Any]) -> bool:
        """Save settings to environment variables (current session only)"""
        try:
            for key, value in settings.items():
                if key in self._env_mapping:
                    os.environ[self._env_mapping[key]] = str(value)
            return True
        except Exception as e:
            print(f"Error saving environment settings: {e}")
            return False
    
    def clear_settings(self) -> bool:
        """Clear environment variables"""
        try:
            for env_var in self._env_mapping.values():
                if env_var in os.environ:
                    del os.environ[env_var]
            return True
        except Exception as e:
            print(f"Error clearing environment settings: {e}")
            return False
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get setting from environment variable"""
        env_var = self._env_mapping.get(key)
        if env_var:
            return os.getenv(env_var, default)
        return default
    
    def set_setting(self, key: str, value: Any) -> bool:
        """Set environment variable"""
        env_var = self._env_mapping.get(key)
        if env_var:
            os.environ[env_var] = str(value)
            return True
        return False


class CompositeSettingsManager(SettingsInterface):
    """
    Composite settings manager that combines multiple sources.
    Follows Composite Pattern and Single Responsibility Principle.
    Priority: JSON file > Environment variables > Defaults
    """
    
    def __init__(self, json_manager: JSONSettingsManager, env_manager: EnvironmentSettingsManager):
        self._json_manager = json_manager
        self._env_manager = env_manager
        self._observers: List[SettingsObserver] = []
    
    def add_observer(self, observer: SettingsObserver) -> None:
        """Add observer for settings changes"""
        self._observers.append(observer)
        # Also add to JSON manager since it's the primary source
        if hasattr(self._json_manager, 'add_observer'):
            self._json_manager.add_observer(observer)
    
    def remove_observer(self, observer: SettingsObserver) -> None:
        """Remove observer"""
        if observer in self._observers:
            self._observers.remove(observer)
        if hasattr(self._json_manager, 'remove_observer'):
            self._json_manager.remove_observer(observer)
    
    def load_settings(self) -> Dict[str, Any]:
        """Load settings with priority: JSON > Environment > Defaults"""
        env_settings = self._env_manager.load_settings()
        json_settings = self._json_manager.load_settings()
        
        # Merge with JSON taking priority
        final_settings = env_settings.copy()
        for key, value in json_settings.items():
            if value:  # Only override if JSON value is not empty
                final_settings[key] = value
        
        return final_settings
    
    def save_settings(self, settings: Dict[str, Any]) -> bool:
        """Save settings to JSON file (primary storage)"""
        return self._json_manager.save_settings(settings)
    
    def clear_settings(self) -> bool:
        """Clear JSON settings (keep environment variables)"""
        return self._json_manager.clear_settings()
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get setting with priority order"""
        # Try JSON first
        json_value = self._json_manager.get_setting(key)
        if json_value:
            return json_value
        
        # Fall back to environment
        env_value = self._env_manager.get_setting(key)
        if env_value:
            return env_value
        
        return default
    
    def set_setting(self, key: str, value: Any) -> bool:
        """Set setting in JSON file (primary storage)"""
        return self._json_manager.set_setting(key, value)


class SettingsManagerFactory:
    """
    Factory for creating settings managers.
    Single Responsibility: Create appropriate settings manager instances.
    """
    
    @staticmethod
    def create_json_manager(settings_file: str = "settings.json") -> JSONSettingsManager:
        """Create JSON settings manager"""
        return JSONSettingsManager(settings_file)
    
    @staticmethod
    def create_environment_manager() -> EnvironmentSettingsManager:
        """Create environment settings manager"""
        return EnvironmentSettingsManager()
    
    @staticmethod
    def create_composite_manager(settings_file: str = "settings.json") -> CompositeSettingsManager:
        """Create composite settings manager with JSON and environment support"""
        json_manager = SettingsManagerFactory.create_json_manager(settings_file)
        env_manager = SettingsManagerFactory.create_environment_manager()
        return CompositeSettingsManager(json_manager, env_manager)