# Android Log Capturer Web Application

A comprehensive web-based application for capturing Android device logs and forwarding them to webhook endpoints in real-time, featuring persistent settings, device monitoring, and endpoint testing.

## Features

- 🌐 **Enhanced Web Interface**: Modern, user-friendly interface with persistent settings
- 📱 **Real-time Device Monitoring**: Automatic device detection with live status updates
- 🔧 **Endpoint Testing**: Test webhook connectivity before starting capture
- � **Persistent Settings**: Settings automatically save and restore across browser sessions
- 📊 **Live Log Display**: Real-time log streaming with success/error indicators
- 🔄 **Multiple Send Modes**: Send logs as raw text, JSON, or both
- 📥 **Log Download**: Download captured logs as `.jsonl` files
- 🚀 **WebSocket Updates**: Real-time updates via Socket.IO
- 🎨 **Modern UI**: Responsive design with status cards and live indicators
- ⚙️ **Settings Management**: Save, clear, and auto-restore configuration

## Prerequisites

1. **Android Device**: Connected Android device with USB debugging enabled
2. **ADB**: Android Debug Bridge installed and accessible in PATH
3. **Python 3.7+**: Python 3.7 or higher installed (tested with Python 3.13)

## Installation

1. **Clone or download the project files**

2. **Create virtual environment** (recommended):
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On macOS/Linux
   # or
   .venv\Scripts\activate     # On Windows
   ```

3. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Connect your Android device**:
   - Enable USB debugging on your Android device
   - Connect via USB cable
   - Verify connection: `adb devices`

## Usage

### Starting the Web Application

1. **Run the web application**:
   ```bash
   python web_app.py
   ```

2. **Open your browser** and navigate to:
   ```
   http://localhost:5000
   ```

### Using the Enhanced Interface

1. **Configure the webhook**:
   - Enter your webhook endpoint URL in the "Webhook Endpoint URL" field
   - Select the send mode (Raw Text, JSON, or Both)
   - Settings are automatically saved when changed

2. **Test endpoint connectivity**:
   - Click "� Test Endpoint" to verify your webhook is reachable
   - Status indicator shows connection results

3. **Monitor device status**:
   - View real-time device connection status in the status cards
   - Automatic updates every few seconds

4. **Start capturing**:
   - Click "▶️ Start Capturing" to begin log capture
   - Real-time status updates show capture progress

5. **Monitor logs**:
   - View live log entries with timestamps
   - Success/error indicators for each log entry
   - Auto-scrolling log display

6. **Manage settings**:
   - Click "💾 Save Settings" to manually save current configuration
   - Click "🗑️ Clear Settings" to reset all saved settings
   - Settings persist across browser sessions

7. **Download logs**:
   - Click "📥 Download Logs" to download captured logs as `.jsonl` file

### Command Line Usage

For advanced users, the original CLI interface is still available:

```bash
python app.py --endpoint https://your-webhook.com/webhook --mode json
```

### Local Testing

Start the webhook receiver for local testing:

```bash
python webhook_receiver.py
```

This provides a local endpoint at `http://localhost:5001/webhook` for testing.

## API Endpoints

### Web Interface
- `GET /`: Main web interface
- `POST /api/start`: Start log capture
- `POST /api/stop`: Stop log capture
- `GET /api/status`: Get current capture status
- `GET /api/device-status`: Check connected devices
- `POST /api/test-endpoint`: Test webhook connectivity
- `POST /api/settings`: Save settings
- `POST /api/settings/clear`: Clear saved settings
- `GET /api/download`: Download log file

### WebSocket Events

**Server → Client:**
- `device_status`: Device connection updates
- `status_update`: Capture status changes
- `log_event`: New log entries with results
- `settings_loaded`: Restored settings on connection

## Configuration

### Persistent Settings

Settings are automatically saved to `settings.json` and include:
- Webhook endpoint URL
- Send mode preference
- Auto-restoration on browser refresh

### Send Modes

- **Raw Text**: Sends the matched log text as plain text
- **JSON**: Parses JSON from logs and sends as JSON payload
- **Both**: Sends both raw text and parsed JSON

### Log Patterns

The application captures logs matching these patterns:
- `Single Event: {json_object}`
- `Event Payload: {json_object}`

## File Structure

```
├── web_app.py              # Enhanced web application with persistent settings
├── app.py                  # Original command-line script
├── webhook_receiver.py     # Local webhook receiver for testing
├── templates/
│   └── index.html         # Enhanced web interface template
├── requirements.txt       # Python dependencies
├── settings.json          # Persistent settings (auto-created)
├── received_events.jsonl  # Captured logs (auto-created)
└── README.md             # This documentation
```

## Troubleshooting

### Common Issues

1. **"ADB not found"**: Ensure ADB is installed and in your PATH
2. **"No devices connected"**: Check USB connection and enable USB debugging
3. **"Cannot reach endpoint"**: Use the test endpoint feature to verify connectivity
4. **WebSocket connection issues**: Ensure port 5000 is not blocked by firewall
5. **Settings not saving**: Check file permissions in the project directory

### Device Connection

Ensure your Android device:
1. Has **USB Debugging** enabled (Settings → Developer Options)
2. Is **connected via USB** or network ADB
3. Has **authorized** the computer for debugging
4. Shows up when running `adb devices`

### Testing the Webhook

You can test webhook functionality multiple ways:

1. **Using the built-in tester**: Click "🔍 Test Endpoint" in the web interface
2. **Using the local receiver**:
   ```bash
   python webhook_receiver.py
   # Then use http://127.0.0.1:5001/webhook as your endpoint
   ```
3. **Using external services**: RequestBin, ngrok, or similar webhook testing services

## Development

### Running in Development Mode

The application runs with debug mode enabled by default. For production use, modify `web_app.py`:

```python
socketio.run(app, host='0.0.0.0', port=5000, debug=False)
```

### Adding New Features

The application is built with Flask and Socket.IO, making it easy to extend with additional features like:
- Authentication and user management
- Multiple device support
- Advanced log filtering and search
- Custom pattern matching rules
- Database storage for logs
- Export to different formats
- Scheduled captures

### Architecture

- **Backend**: Flask with Socket.IO for real-time communication
- **Frontend**: Modern JavaScript with Socket.IO client
- **Storage**: JSON files for settings, `.jsonl` for logs
- **Communication**: RESTful API + WebSocket events

## License

This project is open source and available under the MIT License.
