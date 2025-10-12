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
is_capturing = False
current_endpoint = ""
current_mode = "raw"
log_queue = queue.Queue()

# File to store logs locally
LOG_FILE = "android_events.txt"

# Regex patterns to match both event types and capture the JSON object
patterns = [
    (re.compile(r'Single Event:\s*(\{.*\})'), 'Single Event'),
    (re.compile(r'Event Payload:\s*(\{.*\})'), 'Event Payload')
]

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
    return render_template('index.html')

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
    try:
        test_response = requests.post(endpoint, data="test", timeout=5)
        if test_response.status_code not in [200, 201, 202]:
            return jsonify({'success': False, 'message': f'Endpoint returned status {test_response.status_code}'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Cannot reach endpoint: {str(e)}'})
    
    current_endpoint = endpoint
    current_mode = mode
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
    emit('status_update', {
        'status': 'connected',
        'message': 'Connected to Android Log Capturer'
    })

@socketio.on('disconnect')
def handle_disconnect():
    """Handle WebSocket disconnection."""
    print('Client disconnected')

if __name__ == '__main__':
    print("🚀 Starting Android Log Capturer Web Application")
    print("📱 Make sure your Android device is connected and USB debugging is enabled")
    print("🌐 Open your browser and go to: http://localhost:5001")
    socketio.run(app, host='0.0.0.0', port=5002, debug=True, allow_unsafe_werkzeug=True)
