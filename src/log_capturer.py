"""
Log Capturer Module

Handles Android log capture and processing.
Follows Single Responsibility Principle by focusing only on log operations.
"""

import subprocess
import threading
import re
import json
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Callable, Tuple
from datetime import datetime
import queue
import time


class LogProcessor(ABC):
    """Abstract interface for log processing (Interface Segregation Principle)"""
    
    @abstractmethod
    def process_line(self, line: str) -> Optional[Dict[str, Any]]:
        """Process a single log line"""
        pass


class LogObserver(ABC):
    """Observer interface for log events (Observer Pattern)"""
    
    @abstractmethod
    def on_log_event(self, log_data: Dict[str, Any]) -> None:
        """Called when a log event is captured"""
        pass


class AndroidLogProcessor(LogProcessor):
    """
    Android-specific log processor.
    Single Responsibility: Process Android log lines according to specific patterns.
    """
    
    def __init__(self):
        # Compile regex patterns for better performance
        self._patterns = [
            (re.compile(r'Event Payload:\s*(.+)'), 'event_payload'),
            (re.compile(r'Single Event:\s*(.+)'), 'single_event')
        ]
    
    def process_line(self, line: str) -> Optional[Dict[str, Any]]:
        """Process a log line and extract structured data"""
        line = line.strip()
        if not line:
            return None
        
        for pattern, event_type in self._patterns:
            match = pattern.search(line)
            if match:
                matched_text = match.group(1).strip()
                
                return {
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'event_type': event_type,
                    'matched_text': matched_text,
                    'original_line': line,
                    'parsed_json': self._try_parse_json(matched_text)
                }
        
        return None
    
    def _try_parse_json(self, text: str) -> Optional[Dict[str, Any]]:
        """Try to parse text as JSON"""
        try:
            return json.loads(text)
        except (json.JSONDecodeError, TypeError):
            return None


class ADBLogCapturer:
    """
    ADB-based log capturer.
    Single Responsibility: Capture logs from ADB and coordinate processing.
    """
    
    def __init__(self, log_processor: LogProcessor):
        self._log_processor = log_processor
        self._observers: List[LogObserver] = []
        self._capturing = False
        self._capture_thread: Optional[threading.Thread] = None
        self._process: Optional[subprocess.Popen] = None
        self._log_queue = queue.Queue()
        self._processing_thread: Optional[threading.Thread] = None
    
    def add_observer(self, observer: LogObserver) -> None:
        """Add observer for log events"""
        self._observers.append(observer)
    
    def remove_observer(self, observer: LogObserver) -> None:
        """Remove observer"""
        if observer in self._observers:
            self._observers.remove(observer)
    
    def _notify_observers(self, log_data: Dict[str, Any]) -> None:
        """Notify all observers of log event"""
        for observer in self._observers:
            try:
                observer.on_log_event(log_data)
            except Exception as e:
                print(f"Error notifying log observer: {e}")
    
    def start_capture(self) -> bool:
        """Start capturing logs"""
        if self._capturing:
            return False
        
        try:
            # Start ADB logcat process
            self._process = subprocess.Popen(
                ['adb', 'logcat'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=False  # Handle bytes
            )
            
            self._capturing = True
            
            # Start capture thread
            self._capture_thread = threading.Thread(target=self._capture_loop, daemon=True)
            self._capture_thread.start()
            
            # Start processing thread
            self._processing_thread = threading.Thread(target=self._processing_loop, daemon=True)
            self._processing_thread.start()
            
            return True
            
        except (subprocess.SubprocessError, FileNotFoundError) as e:
            print(f"Error starting ADB logcat: {e}")
            return False
    
    def stop_capture(self) -> bool:
        """Stop capturing logs"""
        if not self._capturing:
            return False
        
        self._capturing = False
        
        # Terminate ADB process
        if self._process:
            self._process.terminate()
            try:
                self._process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._process.kill()
            self._process = None
        
        # Wait for threads to finish
        if self._capture_thread:
            self._capture_thread.join(timeout=2)
        if self._processing_thread:
            self._processing_thread.join(timeout=2)
        
        return True
    
    def _capture_loop(self) -> None:
        """Main capture loop running in separate thread"""
        if not self._process:
            return
        
        while self._capturing and self._process:
            try:
                # Read line from ADB output
                line_bytes = self._process.stdout.readline()
                if not line_bytes:
                    break
                
                # Decode bytes safely
                try:
                    line = line_bytes.decode('utf-8', errors='replace').strip()
                except UnicodeDecodeError:
                    continue
                
                if line:
                    self._log_queue.put(line)
                    
            except Exception as e:
                print(f"Error in capture loop: {e}")
                break
    
    def _processing_loop(self) -> None:
        """Process queued log lines"""
        while self._capturing:
            try:
                # Get line from queue with timeout
                line = self._log_queue.get(timeout=1)
                
                # Process line
                log_data = self._log_processor.process_line(line)
                if log_data:
                    self._notify_observers(log_data)
                
                self._log_queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Error in processing loop: {e}")
    
    def is_capturing(self) -> bool:
        """Check if currently capturing"""
        return self._capturing


class StdinLogCapturer:
    """
    Standard input log capturer for testing.
    Single Responsibility: Capture logs from stdin for testing purposes.
    """
    
    def __init__(self, log_processor: LogProcessor):
        self._log_processor = log_processor
        self._observers: List[LogObserver] = []
        self._capturing = False
    
    def add_observer(self, observer: LogObserver) -> None:
        """Add observer for log events"""
        self._observers.append(observer)
    
    def remove_observer(self, observer: LogObserver) -> None:
        """Remove observer"""
        if observer in self._observers:
            self._observers.remove(observer)
    
    def _notify_observers(self, log_data: Dict[str, Any]) -> None:
        """Notify all observers of log event"""
        for observer in self._observers:
            try:
                observer.on_log_event(log_data)
            except Exception as e:
                print(f"Error notifying log observer: {e}")
    
    def capture_from_stdin(self) -> None:
        """Capture logs from stdin (blocking)"""
        self._capturing = True
        
        try:
            while self._capturing:
                line = input().strip()
                if line:
                    log_data = self._log_processor.process_line(line)
                    if log_data:
                        self._notify_observers(log_data)
        except (EOFError, KeyboardInterrupt):
            pass
        finally:
            self._capturing = False
    
    def stop_capture(self) -> bool:
        """Stop capturing"""
        self._capturing = False
        return True
    
    def is_capturing(self) -> bool:
        """Check if currently capturing"""
        return self._capturing


class LogCaptureManager:
    """
    Manager for coordinating log capture operations.
    Single Responsibility: Coordinate different log capturers and processors.
    """
    
    def __init__(self):
        self._current_capturer: Optional[Any] = None
        self._log_processor = AndroidLogProcessor()
        self._observers: List[LogObserver] = []
    
    def add_observer(self, observer: LogObserver) -> None:
        """Add observer for log events"""
        self._observers.append(observer)
    
    def remove_observer(self, observer: LogObserver) -> None:
        """Remove observer"""
        if observer in self._observers:
            self._observers.remove(observer)
    
    def start_adb_capture(self) -> bool:
        """Start ADB log capture"""
        if self._current_capturer and self._current_capturer.is_capturing():
            return False
        
        self._current_capturer = ADBLogCapturer(self._log_processor)
        
        # Add all observers to the capturer
        for observer in self._observers:
            self._current_capturer.add_observer(observer)
        
        return self._current_capturer.start_capture()
    
    def start_stdin_capture(self) -> bool:
        """Start stdin log capture"""
        if self._current_capturer and self._current_capturer.is_capturing():
            return False
        
        self._current_capturer = StdinLogCapturer(self._log_processor)
        
        # Add all observers to the capturer
        for observer in self._observers:
            self._current_capturer.add_observer(observer)
        
        # This is blocking, so should be run in a separate thread
        capture_thread = threading.Thread(
            target=self._current_capturer.capture_from_stdin, 
            daemon=True
        )
        capture_thread.start()
        
        return True
    
    def stop_capture(self) -> bool:
        """Stop current capture"""
        if self._current_capturer:
            result = self._current_capturer.stop_capture()
            self._current_capturer = None
            return result
        return False
    
    def is_capturing(self) -> bool:
        """Check if currently capturing"""
        return (
            self._current_capturer is not None and 
            self._current_capturer.is_capturing()
        )
    
    def get_current_capturer_type(self) -> str:
        """Get the type of current capturer"""
        if not self._current_capturer:
            return "none"
        elif isinstance(self._current_capturer, ADBLogCapturer):
            return "adb"
        elif isinstance(self._current_capturer, StdinLogCapturer):
            return "stdin"
        else:
            return "unknown"


class LogCapturerFactory:
    """
    Factory for creating log capturers.
    Single Responsibility: Create appropriate log capturer instances.
    """
    
    @staticmethod
    def create_adb_capturer() -> ADBLogCapturer:
        """Create ADB log capturer"""
        processor = AndroidLogProcessor()
        return ADBLogCapturer(processor)
    
    @staticmethod
    def create_stdin_capturer() -> StdinLogCapturer:
        """Create stdin log capturer"""
        processor = AndroidLogProcessor()
        return StdinLogCapturer(processor)
    
    @staticmethod
    def create_manager() -> LogCaptureManager:
        """Create log capture manager"""
        return LogCaptureManager()