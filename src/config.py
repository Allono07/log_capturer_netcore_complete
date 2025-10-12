"""
Configuration Module

Centralized configuration management for the application.
Follows Single Responsibility Principle by focusing only on configuration management.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
import os


@dataclass
class AppConfig:
    """Application configuration data class"""
    # Server settings
    host: str = '0.0.0.0'
    port: int = 5003
    debug: bool = True
    
    # Device monitoring settings
    device_check_interval: int = 5
    device_type: str = 'adb'
    
    # Webhook settings
    webhook_timeout: int = 10
    webhook_retry_count: int = 3
    
    # Log capture settings
    max_log_entries: int = 50
    log_buffer_size: int = 1000
    
    # Settings file
    settings_file: str = 'settings.json'
    
    # Default webhook settings
    default_endpoint: str = ''
    default_mode: str = 'raw'


class ConfigurationProvider(ABC):
    """Abstract interface for configuration providers"""
    
    @abstractmethod
    def load_config(self) -> AppConfig:
        """Load configuration"""
        pass
    
    @abstractmethod
    def save_config(self, config: AppConfig) -> bool:
        """Save configuration"""
        pass


class EnvironmentConfigProvider(ConfigurationProvider):
    """Environment variable-based configuration provider"""
    
    def __init__(self):
        self._env_mapping = {
            'host': 'LOGCAPTURER_HOST',
            'port': 'LOGCAPTURER_PORT',
            'debug': 'LOGCAPTURER_DEBUG',
            'device_check_interval': 'LOGCAPTURER_DEVICE_CHECK_INTERVAL',
            'device_type': 'LOGCAPTURER_DEVICE_TYPE',
            'webhook_timeout': 'LOGCAPTURER_WEBHOOK_TIMEOUT',
            'webhook_retry_count': 'LOGCAPTURER_WEBHOOK_RETRY_COUNT',
            'max_log_entries': 'LOGCAPTURER_MAX_LOG_ENTRIES',
            'log_buffer_size': 'LOGCAPTURER_LOG_BUFFER_SIZE',
            'settings_file': 'LOGCAPTURER_SETTINGS_FILE',
            'default_endpoint': 'LOGCAPTURER_DEFAULT_ENDPOINT',
            'default_mode': 'LOGCAPTURER_DEFAULT_MODE'
        }
    
    def load_config(self) -> AppConfig:
        """Load configuration from environment variables"""
        config_dict = {}
        
        for field, env_var in self._env_mapping.items():
            value = os.getenv(env_var)
            if value is not None:
                # Convert string values to appropriate types
                if field in ['port', 'device_check_interval', 'webhook_timeout', 
                           'webhook_retry_count', 'max_log_entries', 'log_buffer_size']:
                    try:
                        config_dict[field] = int(value)
                    except ValueError:
                        pass  # Use default value
                elif field == 'debug':
                    config_dict[field] = value.lower() in ('true', '1', 'yes', 'on')
                else:
                    config_dict[field] = value
        
        return AppConfig(**config_dict)
    
    def save_config(self, config: AppConfig) -> bool:
        """Save configuration to environment variables (current session only)"""
        try:
            config_dict = asdict(config)
            for field, value in config_dict.items():
                env_var = self._env_mapping.get(field)
                if env_var:
                    os.environ[env_var] = str(value)
            return True
        except Exception:
            return False


class DefaultConfigProvider(ConfigurationProvider):
    """Default configuration provider"""
    
    def load_config(self) -> AppConfig:
        """Load default configuration"""
        return AppConfig()
    
    def save_config(self, config: AppConfig) -> bool:
        """Default provider doesn't save configuration"""
        return False


class CompositeConfigProvider(ConfigurationProvider):
    """Composite configuration provider that combines multiple sources"""
    
    def __init__(self):
        self._providers = [
            EnvironmentConfigProvider(),
            DefaultConfigProvider()  # Fallback to defaults
        ]
    
    def load_config(self) -> AppConfig:
        """Load configuration from all providers with priority order"""
        base_config = AppConfig()
        
        for provider in reversed(self._providers):  # Reverse for proper priority
            try:
                config = provider.load_config()
                # Merge non-default values
                for field, value in asdict(config).items():
                    if value != getattr(AppConfig(), field):  # Not default value
                        setattr(base_config, field, value)
            except Exception as e:
                print(f"Error loading config from provider {provider.__class__.__name__}: {e}")
        
        return base_config
    
    def save_config(self, config: AppConfig) -> bool:
        """Save configuration using the first provider that supports saving"""
        for provider in self._providers:
            try:
                if provider.save_config(config):
                    return True
            except Exception as e:
                print(f"Error saving config with provider {provider.__class__.__name__}: {e}")
        return False


class ConfigurationManager:
    """
    Central configuration manager.
    Single Responsibility: Manage application configuration.
    """
    
    def __init__(self, provider: Optional[ConfigurationProvider] = None):
        self._provider = provider or CompositeConfigProvider()
        self._config: Optional[AppConfig] = None
    
    def load_configuration(self) -> AppConfig:
        """Load and cache configuration"""
        self._config = self._provider.load_config()
        return self._config
    
    def get_configuration(self) -> AppConfig:
        """Get current configuration (load if not cached)"""
        if self._config is None:
            self.load_configuration()
        return self._config
    
    def update_configuration(self, **kwargs) -> bool:
        """Update configuration with new values"""
        if self._config is None:
            self.load_configuration()
        
        # Update configuration
        for key, value in kwargs.items():
            if hasattr(self._config, key):
                setattr(self._config, key, value)
        
        # Save updated configuration
        return self._provider.save_config(self._config)
    
    def reload_configuration(self) -> AppConfig:
        """Reload configuration from source"""
        return self.load_configuration()
    
    def get_server_config(self) -> Dict[str, Any]:
        """Get server-specific configuration"""
        config = self.get_configuration()
        return {
            'host': config.host,
            'port': config.port,
            'debug': config.debug
        }
    
    def get_device_config(self) -> Dict[str, Any]:
        """Get device monitoring configuration"""
        config = self.get_configuration()
        return {
            'check_interval': config.device_check_interval,
            'device_type': config.device_type
        }
    
    def get_webhook_config(self) -> Dict[str, Any]:
        """Get webhook configuration"""
        config = self.get_configuration()
        return {
            'timeout': config.webhook_timeout,
            'retry_count': config.webhook_retry_count,
            'default_endpoint': config.default_endpoint,
            'default_mode': config.default_mode
        }
    
    def get_log_config(self) -> Dict[str, Any]:
        """Get log capture configuration"""
        config = self.get_configuration()
        return {
            'max_entries': config.max_log_entries,
            'buffer_size': config.log_buffer_size
        }
    
    def get_settings_file_path(self) -> str:
        """Get settings file path"""
        config = self.get_configuration()
        return config.settings_file


class ConfigurationFactory:
    """
    Factory for creating configuration managers.
    Single Responsibility: Create configuration manager instances.
    """
    
    @staticmethod
    def create_default_manager() -> ConfigurationManager:
        """Create configuration manager with default provider"""
        return ConfigurationManager()
    
    @staticmethod
    def create_environment_manager() -> ConfigurationManager:
        """Create configuration manager with environment provider"""
        return ConfigurationManager(EnvironmentConfigProvider())
    
    @staticmethod
    def create_composite_manager() -> ConfigurationManager:
        """Create configuration manager with composite provider"""
        return ConfigurationManager(CompositeConfigProvider())


# Global configuration instance (Singleton pattern)
_global_config_manager: Optional[ConfigurationManager] = None


def get_config_manager() -> ConfigurationManager:
    """Get global configuration manager instance"""
    global _global_config_manager
    if _global_config_manager is None:
        _global_config_manager = ConfigurationFactory.create_composite_manager()
    return _global_config_manager


def get_app_config() -> AppConfig:
    """Get application configuration"""
    return get_config_manager().get_configuration()