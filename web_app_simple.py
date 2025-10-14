from flask import Flask, render_template, request, jsonify
import threading
import time
import subprocess
import json
import requests

app = Flask(__name__)

# Global variables
device_id = None
log_capture_active = False
capture_thread = None
log_lines = []
MAX_LOG_LINES = 1000
bulk_logs = []

# Configuration
settings = {
    'realtime_webhook_url': '',
    'bulk_webhook_url': '',
    'log_level': 'all'
}

def save_settings():
    """Save settings to file"""
    try:
        with open('settings.json', 'w') as f:
            json.dump(settings, f)
    except Exception as e:
        print(f"Error saving settings: {e}")

def load_settings():
    """Load settings from file"""
    global settings
    try:
        with open('settings.json', 'r') as f:
            settings.update(json.load(f))
    except FileNotFoundError:
        print("Settings file not found, using defaults")
    except Exception as e:
        print(f"Error loading settings: {e}")

def get_connected_devices():
    """Get list of connected Android devices"""
    try:
        result = subprocess.run(['adb', 'devices'], capture_output=True, text=True, timeout=10)
        if result.returncode != 0:
            return []
        
        lines = result.stdout.strip().split('\\n')[1:]  # Skip header
        devices = []
        for line in lines:
            if line.strip() and '\\t' in line:
                device_info = line.split('\\t')
                if len(device_info) >= 2 and device_info[1] == 'device':
                    devices.append(device_info[0])
        return devices
    except Exception as e:
        print(f"Error getting devices: {e}")
        return []

def send_webhook(url, data):
    """Send data to webhook URL"""
    if not url:
        return
    
    try:
        response = requests.post(url, json=data, timeout=5)
        print(f"Webhook sent to {url}, status: {response.status_code}")
    except Exception as e:
        print(f"Error sending webhook to {url}: {e}")

def capture_logs():
    """Capture logs from device"""
    global log_capture_active, log_lines, bulk_logs
    
    if not device_id:
        return
    
    try:
        # Clear existing logs
        subprocess.run(['adb', '-s', device_id, 'logcat', '-c'], 
                      capture_output=True, timeout=5)
        
        # Start logcat
        process = subprocess.Popen(
            ['adb', '-s', device_id, 'logcat'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        
        while log_capture_active and process.poll() is None:
            try:
                line = process.stdout.readline()
                if line:
                    log_entry = {
                        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                        'device_id': device_id,
                        'log': line.strip()
                    }
                    
                    # Add to memory (for web display)
                    log_lines.append(log_entry)
                    if len(log_lines) > MAX_LOG_LINES:
                        log_lines.pop(0)
                    
                    # Add to bulk logs
                    bulk_logs.append(log_entry)
                    
                    # Send realtime webhook
                    if settings['realtime_webhook_url']:
                        send_webhook(settings['realtime_webhook_url'], log_entry)
                        
            except Exception as e:
                print(f"Error reading log line: {e}")
                break
                
        process.terminate()
        
    except Exception as e:
        print(f"Error capturing logs: {e}")

@app.route('/')
def index():
    devices = get_connected_devices()
    return render_template('index_simple.html', 
                         devices=devices, 
                         current_device=device_id,
                         settings=settings)

@app.route('/api/devices')
def api_devices():
    devices = get_connected_devices()
    return jsonify({'devices': devices})

@app.route('/api/connect', methods=['POST'])
def api_connect():
    global device_id
    data = request.get_json()
    device_id = data.get('device_id')
    return jsonify({'success': True, 'device_id': device_id})

@app.route('/api/start_capture', methods=['POST'])
def api_start_capture():
    global log_capture_active, capture_thread, log_lines, bulk_logs
    
    if not device_id:
        return jsonify({'success': False, 'error': 'No device connected'})
    
    if log_capture_active:
        return jsonify({'success': False, 'error': 'Capture already active'})
    
    log_capture_active = True
    log_lines.clear()
    bulk_logs.clear()
    
    capture_thread = threading.Thread(target=capture_logs, daemon=True)
    capture_thread.start()
    
    return jsonify({'success': True})

@app.route('/api/stop_capture', methods=['POST'])
def api_stop_capture():
    global log_capture_active
    log_capture_active = False
    return jsonify({'success': True})

@app.route('/api/logs')
def api_logs():
    return jsonify({'logs': log_lines[-100:]})  # Return last 100 logs

@app.route('/api/bulk_publish', methods=['POST'])
def api_bulk_publish():
    global bulk_logs
    
    if not settings['bulk_webhook_url']:
        return jsonify({'success': False, 'error': 'No bulk webhook URL configured'})
    
    if not bulk_logs:
        return jsonify({'success': False, 'error': 'No logs to publish'})
    
    try:
        bulk_data = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'device_id': device_id,
            'log_count': len(bulk_logs),
            'logs': bulk_logs.copy()
        }
        
        send_webhook(settings['bulk_webhook_url'], bulk_data)
        bulk_logs.clear()  # Clear after sending
        
        return jsonify({'success': True, 'logs_sent': bulk_data['log_count']})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/settings', methods=['POST'])
def api_settings():
    global settings
    data = request.get_json()
    
    settings.update({
        'realtime_webhook_url': data.get('realtime_webhook_url', ''),
        'bulk_webhook_url': data.get('bulk_webhook_url', ''),
        'log_level': data.get('log_level', 'all')
    })
    
    save_settings()
    return jsonify({'success': True, 'settings': settings})

@app.route('/api/status')
def api_status():
    return jsonify({
        'device_id': device_id,
        'capture_active': log_capture_active,
        'log_count': len(log_lines),
        'bulk_count': len(bulk_logs),
        'settings': settings
    })

if __name__ == '__main__':
    load_settings()
    print("Android Log Capturer starting on http://localhost:5001")
    print("Open your web browser to access the interface")
    app.run(host='0.0.0.0', port=5001, debug=False)