"""
Webhook Manager Module

Handles webhook operations including testing and sending data.
Follows Single Responsibility Principle by focusing only on webhook operations.
"""

import requests
import json
import threading
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from urllib.parse import urlparse
import time


class WebhookSender(ABC):
    """Abstract interface for webhook sending (Interface Segregation Principle)"""
    
    @abstractmethod
    def send_raw(self, endpoint: str, data: str) -> Tuple[bool, Optional[int], Optional[str]]:
        """Send raw text data to webhook"""
        pass
    
    @abstractmethod
    def send_json(self, endpoint: str, data: Dict[str, Any]) -> Tuple[bool, Optional[int], Optional[str]]:
        """Send JSON data to webhook"""
        pass
    
    @abstractmethod
    def test_connectivity(self, endpoint: str) -> Tuple[bool, str]:
        """Test webhook endpoint connectivity"""
        pass


class WebhookObserver(ABC):
    """Observer interface for webhook events (Observer Pattern)"""
    
    @abstractmethod
    def on_webhook_result(self, result: Dict[str, Any]) -> None:
        """Called when webhook operation completes"""
        pass


class HTTPWebhookSender(WebhookSender):
    """
    HTTP-based webhook sender.
    Single Responsibility: Handle HTTP webhook operations.
    """
    
    def __init__(self, timeout: int = 10, retry_count: int = 3):
        self._timeout = timeout
        self._retry_count = retry_count
        self._session = requests.Session()
        
        # Set common headers
        self._session.headers.update({
            'User-Agent': 'Android-Log-Capturer/1.0',
            'Accept': 'application/json, text/plain, */*'
        })
    
    def send_raw(self, endpoint: str, data: str) -> Tuple[bool, Optional[int], Optional[str]]:
        """Send raw text data to webhook"""
        headers = {'Content-Type': 'text/plain'}
        return self._send_request(endpoint, data, headers)
    
    def send_json(self, endpoint: str, data: Dict[str, Any]) -> Tuple[bool, Optional[int], Optional[str]]:
        """Send JSON data to webhook"""
        headers = {'Content-Type': 'application/json'}
        json_data = json.dumps(data)
        return self._send_request(endpoint, json_data, headers)
    
    def test_connectivity(self, endpoint: str) -> Tuple[bool, str]:
        """Test webhook endpoint connectivity"""
        try:
            # Validate URL format
            parsed = urlparse(endpoint)
            if not parsed.scheme or not parsed.netloc:
                return False, "Invalid URL format"
            
            # Send a simple test request
            test_data = {
                'test': True,
                'message': 'Connectivity test from Android Log Capturer',
                'timestamp': datetime.now().isoformat()
            }
            
            response = self._session.post(
                endpoint,
                json=test_data,
                timeout=self._timeout,
                allow_redirects=True
            )
            
            if response.status_code < 400:
                return True, f"Connected successfully (HTTP {response.status_code})"
            else:
                return False, f"HTTP {response.status_code}: {response.reason}"
                
        except requests.exceptions.ConnectionError:
            return False, "Connection failed - endpoint unreachable"
        except requests.exceptions.Timeout:
            return False, f"Connection timeout after {self._timeout} seconds"
        except requests.exceptions.InvalidURL:
            return False, "Invalid URL format"
        except Exception as e:
            return False, f"Unexpected error: {str(e)}"
    
    def _send_request(self, endpoint: str, data: str, headers: Dict[str, str]) -> Tuple[bool, Optional[int], Optional[str]]:
        """Send HTTP request with retry logic"""
        last_error = None
        
        for attempt in range(self._retry_count):
            try:
                response = self._session.post(
                    endpoint,
                    data=data,
                    headers=headers,
                    timeout=self._timeout,
                    allow_redirects=True
                )
                
                # Consider 2xx and 3xx as success
                if response.status_code < 400:
                    return True, response.status_code, None
                else:
                    last_error = f"HTTP {response.status_code}: {response.reason}"
                    
            except requests.exceptions.ConnectionError as e:
                last_error = f"Connection error: {str(e)}"
            except requests.exceptions.Timeout as e:
                last_error = f"Timeout error: {str(e)}"
            except Exception as e:
                last_error = f"Unexpected error: {str(e)}"
            
            # Wait before retry (exponential backoff)
            if attempt < self._retry_count - 1:
                time.sleep(2 ** attempt)
        
        return False, None, last_error
    
    def close(self) -> None:
        """Close the HTTP session"""
        self._session.close()


class WebhookManager:
    """
    Manager for webhook operations.
    Single Responsibility: Coordinate webhook sending and testing operations.
    """
    
    def __init__(self, sender: WebhookSender):
        self._sender = sender
        self._observers: List[WebhookObserver] = []
        self._endpoint: Optional[str] = None
        self._mode: str = 'raw'
    
    def add_observer(self, observer: WebhookObserver) -> None:
        """Add observer for webhook events"""
        self._observers.append(observer)
    
    def remove_observer(self, observer: WebhookObserver) -> None:
        """Remove observer"""
        if observer in self._observers:
            self._observers.remove(observer)
    
    def _notify_observers(self, result: Dict[str, Any]) -> None:
        """Notify all observers of webhook result"""
        for observer in self._observers:
            try:
                observer.on_webhook_result(result)
            except Exception as e:
                print(f"Error notifying webhook observer: {e}")
    
    def configure(self, endpoint: str, mode: str = 'raw') -> None:
        """Configure webhook settings"""
        self._endpoint = endpoint.strip()
        self._mode = mode
    
    def test_endpoint(self, endpoint: Optional[str] = None) -> Dict[str, Any]:
        """Test webhook endpoint connectivity"""
        test_endpoint = endpoint or self._endpoint
        if not test_endpoint:
            return {
                'success': False,
                'message': 'No endpoint configured',
                'timestamp': datetime.now().isoformat()
            }
        
        success, message = self._sender.test_connectivity(test_endpoint)
        
        result = {
            'success': success,
            'message': message,
            'endpoint': test_endpoint,
            'timestamp': datetime.now().isoformat()
        }
        
        self._notify_observers(result)
        return result
    
    def send_log_data(self, log_data: Dict[str, Any]) -> List[Tuple[str, bool, Optional[int], Optional[str]]]:
        """Send log data according to configured mode"""
        if not self._endpoint:
            return [('error', False, None, 'No endpoint configured')]
        
        results = []
        matched_text = log_data.get('matched_text', '')
        parsed_json = log_data.get('parsed_json')
        
        if self._mode in ['raw', 'both']:
            success, status_code, error = self._sender.send_raw(self._endpoint, matched_text)
            results.append(('raw', success, status_code, error))
        
        if self._mode in ['json', 'both'] and parsed_json:
            success, status_code, error = self._sender.send_json(self._endpoint, parsed_json)
            results.append(('json', success, status_code, error))
        
        # Notify observers
        webhook_result = {
            'log_data': log_data,
            'results': results,
            'endpoint': self._endpoint,
            'mode': self._mode,
            'timestamp': datetime.now().isoformat()
        }
        self._notify_observers(webhook_result)
        
        return results
    
    def get_configuration(self) -> Dict[str, Any]:
        """Get current webhook configuration"""
        return {
            'endpoint': self._endpoint,
            'mode': self._mode
        }


class AsyncWebhookManager:
    """
    Asynchronous webhook manager for non-blocking operations.
    Single Responsibility: Handle webhook operations asynchronously.
    """
    
    def __init__(self, webhook_manager: WebhookManager):
        self._webhook_manager = webhook_manager
        self._send_queue = []
        self._processing = False
        self._worker_thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
    
    def start_worker(self) -> None:
        """Start background worker thread"""
        if self._processing:
            return
        
        self._processing = True
        self._worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self._worker_thread.start()
    
    def stop_worker(self) -> None:
        """Stop background worker thread"""
        self._processing = False
        if self._worker_thread:
            self._worker_thread.join(timeout=2)
    
    def queue_send(self, log_data: Dict[str, Any]) -> None:
        """Queue log data for async sending"""
        with self._lock:
            self._send_queue.append(log_data)
    
    def test_endpoint_async(self, endpoint: Optional[str] = None) -> None:
        """Test endpoint asynchronously"""
        def test_worker():
            self._webhook_manager.test_endpoint(endpoint)
        
        thread = threading.Thread(target=test_worker, daemon=True)
        thread.start()
    
    def _worker_loop(self) -> None:
        """Main worker loop for processing queued sends"""
        while self._processing:
            try:
                # Get items from queue
                items_to_process = []
                with self._lock:
                    if self._send_queue:
                        items_to_process = self._send_queue[:]
                        self._send_queue.clear()
                
                # Process items
                for log_data in items_to_process:
                    self._webhook_manager.send_log_data(log_data)
                
                # Sleep briefly to avoid busy waiting
                time.sleep(0.1)
                
            except Exception as e:
                print(f"Error in webhook worker loop: {e}")
    
    def configure(self, endpoint: str, mode: str = 'raw') -> None:
        """Configure webhook settings"""
        self._webhook_manager.configure(endpoint, mode)
    
    def add_observer(self, observer: WebhookObserver) -> None:
        """Add observer for webhook events"""
        self._webhook_manager.add_observer(observer)
    
    def remove_observer(self, observer: WebhookObserver) -> None:
        """Remove observer"""
        self._webhook_manager.remove_observer(observer)


class WebhookManagerFactory:
    """
    Factory for creating webhook managers.
    Single Responsibility: Create appropriate webhook manager instances.
    """
    
    @staticmethod
    def create_http_sender(timeout: int = 10, retry_count: int = 3) -> HTTPWebhookSender:
        """Create HTTP webhook sender"""
        return HTTPWebhookSender(timeout, retry_count)
    
    @staticmethod
    def create_webhook_manager(timeout: int = 10, retry_count: int = 3) -> WebhookManager:
        """Create webhook manager with HTTP sender"""
        sender = WebhookManagerFactory.create_http_sender(timeout, retry_count)
        return WebhookManager(sender)
    
    @staticmethod
    def create_async_webhook_manager(timeout: int = 10, retry_count: int = 3) -> AsyncWebhookManager:
        """Create async webhook manager"""
        webhook_manager = WebhookManagerFactory.create_webhook_manager(timeout, retry_count)
        async_manager = AsyncWebhookManager(webhook_manager)
        async_manager.start_worker()
        return async_manager