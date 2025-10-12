#!/usr/bin/env python3
import threading
import subprocess
import re
import json
import requests
import time
from datetime import datetime
from flask import Flask, render_template, request, jsonify, Response
from flask_socketio import SocketIO, emit
import queue
import os

import secrets

app = Flask(__name__, static_folder='static', static_url_path='/static')
# Generate a secure random secret key
app.config['SECRET_KEY'] = secrets.token_hex(32)
socketio = SocketIO(app, cors_allowed_origins="*")

# Global variables for managing the log capture process
capture_process = None
capture_thread = None
device_monitor_thread = None
is_capturing = False
is_monitoring_device = False
current_endpoint = ""
current_mode = "raw"
log_queue = queue.Queue()

# File to store logs locally
LOG_FILE = "android_events.txt"
SETTINGS_FILE = "app_settings.json"

# Regex patterns to match both event types and capture the JSON object
patterns = [
    (re.compile(r'Single Event:\s*(\{.*\})'), 'Single Event'),
    (re.compile(r'Event Payload:\s*(\{.*\})'), 'Event Payload')
]

def load_settings():
    """Load persistent settings from file."""
    default_settings = {
        'endpoint': '',
        'mode': 'raw'
    }
    
    try:
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, 'r') as f:
                settings = json.load(f)
                return {**default_settings, **settings}
    except Exception as e:
        print(f"Error loading settings: {e}")
    
    return default_settings

def save_settings(endpoint, mode):
    """Save settings to file."""
    settings = {
        'endpoint': endpoint,
        'mode': mode
    }
    
    try:
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(settings, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving settings: {e}")
        return False

def clear_settings():
    """Clear persistent settings."""
    try:
        if os.path.exists(SETTINGS_FILE):
            os.remove(SETTINGS_FILE)
        return True
    except Exception as e:
        print(f"Error clearing settings: {e}")
        return False

def test_endpoint_connectivity(endpoint):
    """Test if endpoint is reachable."""
    try:
        response = requests.post(
            endpoint, 
            data="connection_test", 
            timeout=5,
            headers={'Content-Type': 'text/plain'}
        )
        return {
            'success': True,
            'status_code': response.status_code,
            'message': f'Endpoint reachable (HTTP {response.status_code})'
        }
    except requests.exceptions.Timeout:
        return {
            'success': False,
            'message': 'Connection timeout - endpoint took too long to respond'
        }
    except requests.exceptions.ConnectionError:
        return {
            'success': False,
            'message': 'Connection error - cannot reach endpoint'
        }
    except Exception as e:
        return {
            'success': False,
            'message': f'Error: {str(e)}'
        }

def send_raw(text: str, endpoint: str):
    """Send the exact matched text as plain text to the webhook."""
    try:
        resp = requests.post(endpoint, data=text.encode('utf-8'), headers={'Content-Type': 'text/plain'})
        return resp.status_code, resp.text
    except Exception as e:
        return None, str(e)

def send_json(obj: dict, endpoint: str):
    """Send the parsed JSON object to the webhook as JSON."""
    try:
        resp = requests.post(endpoint, json=obj)
        return resp.status_code, resp.text
    except Exception as e:
        return None, str(e)

def process_line(line: str, endpoint: str, mode: str):
    """Process a single decoded log line: match, log locally, and forward to endpoint."""
    for pattern, label in patterns:
        match = pattern.search(line)
        if not match:
            continue

        # Build a clean matched text using the human-readable label
        matched_text = f"{label}: {match.group(1)}"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Append to local log file
        with open(LOG_FILE, "a") as f:
            f.write(f"{timestamp} | {matched_text}\n\n")

        # Try parse JSON for json mode
        parsed = None
        try:
            parsed = json.loads(match.group(1))
        except Exception:
            parsed = None

        results = []
        if mode in ("raw", "both"):
            status, body = send_raw(matched_text, endpoint)
            results.append(("raw", status, body))

        if mode in ("json", "both") and parsed is not None:
            status, body = send_json(parsed, endpoint)
            results.append(("json", status, body))

        # Send results to web interface via WebSocket
        event_data = {
            'timestamp': timestamp,
            'matched_text': matched_text,
            'results': results,
            'parsed_event': parsed
        }
        
        socketio.emit('log_event', event_data)
        log_queue.put(event_data)

def check_device_connection():
    """Check if Android device is connected via ADB."""
    try:
        result = subprocess.run(['adb', 'devices'], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')[1:]  # Skip header line
            devices = [line for line in lines if line.strip() and 'device' in line]
            return len(devices) > 0, devices
        return False, []
    except Exception as e:
        return False, [f"Error checking devices: {str(e)}"]

def monitor_device_connection():
    """Background thread to monitor device connection continuously."""
    global is_monitoring_device
    
    last_status = None
    
    while is_monitoring_device:
        try:
            device_connected, device_info = check_device_connection()
            
            current_status = {
                'connected': device_connected,
                'devices': device_info,
                'message': f'Connected to {len(device_info)} device(s)' if device_connected else 'No devices connected',
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # Only emit if status changed
            if current_status != last_status:
                socketio.emit('device_status', current_status)
                last_status = current_status.copy()
            
            time.sleep(3)  # Check every 3 seconds
            
        except Exception as e:
            print(f"Error in device monitoring: {e}")
            time.sleep(5)

def start_device_monitoring():
    """Start the device monitoring thread."""
    global device_monitor_thread, is_monitoring_device
    
    if not is_monitoring_device:
        is_monitoring_device = True
        device_monitor_thread = threading.Thread(target=monitor_device_connection, daemon=True)
        device_monitor_thread.start()

def stop_device_monitoring():
    """Stop the device monitoring thread."""
    global is_monitoring_device
    is_monitoring_device = False

def capture_logs():
    """Background thread function to capture adb logs."""
    global capture_process, is_capturing
    
    try:
        # Check device connection first
        device_connected, device_info = check_device_connection()
        if not device_connected:
            socketio.emit('device_status', {'connected': False, 'message': 'No Android device connected'})
            socketio.emit('status_update', {'status': 'error', 'message': 'No Android device connected. Please connect your device and enable USB debugging.'})
            return
        
        # Emit device connection status
        socketio.emit('device_status', {'connected': True, 'devices': device_info, 'message': f'Connected to {len(device_info)} device(s)'})
        
        # Start reading adb logcat
        capture_process = subprocess.Popen([
            "adb", "logcat"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=False)

        socketio.emit('status_update', {'status': 'capturing', 'message': 'Started capturing Android logs...'})

        for raw in capture_process.stdout:
            if not is_capturing:
                break
                
            try:
                line = raw.decode("utf-8", errors="replace")
            except Exception:
                line = str(raw)

            process_line(line, current_endpoint, current_mode)

    except Exception as e:
        socketio.emit('status_update', {'status': 'error', 'message': f'Error during capture: {str(e)}'})
        socketio.emit('device_status', {'connected': False, 'message': f'Device connection error: {str(e)}'})
    finally:
        if capture_process:
            capture_process.terminate()
        is_capturing = False
        socketio.emit('status_update', {'status': 'stopped', 'message': 'Log capture stopped.'})

@app.route('/')
def index():
    """Main web interface."""
    # Load persistent settings
    settings = load_settings()
    return render_template('index.html', 
                         endpoint=settings['endpoint'], 
                         mode=settings['mode'])

@app.route('/api/settings', methods=['GET'])
def get_settings():
    """Get current persistent settings."""
    return jsonify(load_settings())

@app.route('/api/settings', methods=['POST'])
def update_settings():
    """Update persistent settings."""
    data = request.get_json()
    endpoint = data.get('endpoint', '').strip()
    mode = data.get('mode', 'raw')
    
    if save_settings(endpoint, mode):
        global current_endpoint, current_mode
        current_endpoint = endpoint
        current_mode = mode
        return jsonify({'success': True, 'message': 'Settings saved'})
    else:
        return jsonify({'success': False, 'message': 'Failed to save settings'})

@app.route('/api/settings/clear', methods=['POST'])
def clear_persistent_settings():
    """Clear all persistent settings."""
    if clear_settings():
        global current_endpoint, current_mode
        current_endpoint = ""
        current_mode = "raw"
        return jsonify({'success': True, 'message': 'Settings cleared'})
    else:
        return jsonify({'success': False, 'message': 'Failed to clear settings'})

@app.route('/api/test-endpoint', methods=['POST'])
def test_endpoint():
    """Test endpoint connectivity."""
    data = request.get_json()
    endpoint = data.get('endpoint', '').strip()
    
    if not endpoint:
        return jsonify({'success': False, 'message': 'Please provide an endpoint URL'})
    
    result = test_endpoint_connectivity(endpoint)
    return jsonify(result)

@app.route('/api/start', methods=['POST'])
def start_capture():
    """Start log capture."""
    global is_capturing, capture_thread, current_endpoint, current_mode
    
    if is_capturing:
        return jsonify({'success': False, 'message': 'Already capturing logs'})
    
    data = request.get_json()
    endpoint = data.get('endpoint', '').strip()
    mode = data.get('mode', 'raw')
    
    if not endpoint:
        return jsonify({'success': False, 'message': 'Please provide an endpoint URL'})
    
    # Test the endpoint first
    test_result = test_endpoint_connectivity(endpoint)
    if not test_result['success']:
        return jsonify({'success': False, 'message': f'Endpoint test failed: {test_result["message"]}'})
    
    current_endpoint = endpoint
    current_mode = mode
    
    # Save settings for persistence
    save_settings(endpoint, mode)
    
    is_capturing = True
    
    # Start capture thread
    capture_thread = threading.Thread(target=capture_logs, daemon=True)
    capture_thread.start()
    
    return jsonify({'success': True, 'message': 'Started capturing logs'})

@app.route('/api/stop', methods=['POST'])
def stop_capture():
    """Stop log capture."""
    global is_capturing, capture_process
    
    if not is_capturing:
        return jsonify({'success': False, 'message': 'Not currently capturing'})
    
    is_capturing = False
    
    if capture_process:
        capture_process.terminate()
    
    return jsonify({'success': True, 'message': 'Stopped capturing logs'})

@app.route('/api/status', methods=['GET'])
def get_status():
    """Get current capture status."""
    device_connected, device_info = check_device_connection()
    return jsonify({
        'is_capturing': is_capturing,
        'endpoint': current_endpoint,
        'mode': current_mode,
        'device_connected': device_connected,
        'devices': device_info
    })

@app.route('/api/device-status', methods=['GET'])
def get_device_status():
    """Get current device connection status."""
    device_connected, device_info = check_device_connection()
    return jsonify({
        'connected': device_connected,
        'devices': device_info,
        'message': f'Connected to {len(device_info)} device(s)' if device_connected else 'No devices connected'
    })

@app.route('/api/logs', methods=['GET'])
def get_recent_logs():
    """Get recent log entries."""
    logs = []
    while not log_queue.empty():
        try:
            logs.append(log_queue.get_nowait())
        except queue.Empty:
            break
    
    return jsonify(logs)

@app.route('/api/download', methods=['GET'])
def download_logs():
    """Download the log file."""
    if os.path.exists(LOG_FILE):
        return Response(
            open(LOG_FILE, 'rb').read(),
            mimetype='text/plain',
            headers={'Content-Disposition': f'attachment; filename={LOG_FILE}'}
        )
    else:
        return jsonify({'error': 'Log file not found'}), 404

@socketio.on('connect')
def handle_connect():
    """Handle WebSocket connection."""
    # Start device monitoring when first client connects
    start_device_monitoring()
    
    # Send initial status
    emit('status_update', {
        'status': 'connected',
        'message': 'Connected to Android Log Capturer'
    })
    
    # Send current device status
    device_connected, device_info = check_device_connection()
    emit('device_status', {
        'connected': device_connected,
        'devices': device_info,
        'message': f'Connected to {len(device_info)} device(s)' if device_connected else 'No devices connected',
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    
    # Send current settings
    settings = load_settings()
    emit('settings_loaded', settings)

@socketio.on('disconnect')
def handle_disconnect():
    """Handle WebSocket disconnection."""
    print('Client disconnected')

if __name__ == '__main__':
    # Load initial settings
    settings = load_settings()
    current_endpoint = settings['endpoint']
    current_mode = settings['mode']
    
    print("🚀 Starting Android Log Capturer Web Application")
    print("📱 Make sure your Android device is connected and USB debugging is enabled")
    print("🌐 Open your browser and go to: http://localhost:5002")
    if settings['endpoint']:
        print(f"📡 Loaded saved endpoint: {settings['endpoint']}")
    
    socketio.run(app, host='0.0.0.0', port=5002, debug=True, allow_unsafe_werkzeug=True)
