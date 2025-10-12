# Android Log Capturer Web Application

A web-based application for capturing Android device logs and forwarding them to webhook endpoints in real-time.

## Features

- 🌐 **Web Interface**: User-friendly web application for easy configuration and monitoring
- 📱 **Real-time Log Capture**: Live capture of Android logs via ADB
- 🔄 **Multiple Send Modes**: Send logs as raw text, JSON, or both
- 📊 **Live Statistics**: Real-time tracking of captured events and send status
- 📥 **Log Download**: Download captured logs as text files
- 🚀 **WebSocket Updates**: Real-time updates via WebSocket connections
- 🎨 **Modern UI**: Beautiful, responsive interface with custom NetCore branding and live status indicators

## Prerequisites

1. **Android Device**: Connected Android device with USB debugging enabled
2. **ADB**: Android Debug Bridge installed and accessible in PATH
3. **Python 3.7+**: Python 3.7 or higher installed (tested with Python 3.13)

## Installation

1. **Clone or download the project files**

2. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Connect your Android device**:
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

### Using the Interface

1. **Configure the webhook**:
   - Enter your webhook endpoint URL in the "Webhook Endpoint URL" field
   - Select the send mode (Raw Text, JSON, or Both)

2. **Start capturing**:
   - Click "🚀 Start Capture" to begin log capture
   - The application will test the endpoint connection first

3. **Monitor logs**:
   - View real-time log entries in the "Live Logs" panel
   - Monitor statistics (total events, successful/failed sends)
   - Check connection status and details

4. **Stop capturing**:
   - Click "⏹️ Stop Capture" to stop the log capture

5. **Download logs**:
   - Click "📥 Download Logs" to download the captured logs as a text file

## API Endpoints

- `GET /`: Main web interface
- `POST /api/start`: Start log capture
- `POST /api/stop`: Stop log capture
- `GET /api/status`: Get current capture status
- `GET /api/logs`: Get recent log entries
- `GET /api/download`: Download log file

## WebSocket Events

- `status_update`: Real-time status updates
- `log_event`: New log events with processing results

## Configuration

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
├── web_app.py              # Main web application
├── app.py                  # Original command-line script
├── webhook_receiver.py     # Webhook receiver for testing
├── templates/
│   └── index.html         # Web interface template
├── static/                # Static assets directory
│   ├── favicon.ico        # Website favicon
│   ├── netcore_logo.png   # NetCore company logo
│   └── README.md          # Static files instructions
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

## Troubleshooting

### Common Issues

1. **"ADB not found"**: Ensure ADB is installed and in your PATH
2. **"No devices connected"**: Check USB connection and enable USB debugging
3. **"Cannot reach endpoint"**: Verify the webhook URL is correct and accessible
4. **WebSocket connection issues**: Ensure port 5000 is not blocked by firewall

### Testing the Webhook

You can test the webhook functionality using the included `webhook_receiver.py`:

```bash
python webhook_receiver.py --port 5013
```

Then use `http://127.0.0.1:5013/webhook` as your endpoint URL.

## Development

### Running in Development Mode

The application runs with debug mode enabled by default. For production use, modify `web_app.py`:

```python
socketio.run(app, host='0.0.0.0', port=5000, debug=False)
```

### Adding New Features

The application is built with Flask and Socket.IO, making it easy to extend with additional features like:
- Authentication
- Multiple device support
- Log filtering
- Custom pattern matching
- Database storage

## License

This project is open source and available under the MIT License.
