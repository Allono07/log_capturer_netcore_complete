# 🤖 Android Log Capturer - Executable Distribution

## Overview

The Android Log Capturer is now available as a standalone executable application! This version provides all the functionality of the original modular application without requiring Python installation or dependency management.

## Features

✅ **Dual Webhook System**
- **Realtime Webhook**: Sends individual log entries as they occur
- **Bulk Webhook**: Sends accumulated logs in bulk when manually triggered

✅ **SOLID Architecture** 
- Modular, scalable codebase following SOLID principles
- Easy to maintain and extend

✅ **Web Interface**
- Modern, responsive design
- Real-time log monitoring
- Device management
- Webhook configuration

✅ **Cross-Platform**
- Works on macOS, Windows, and Linux
- No Python installation required

## Executable Files

### AndroidLogCapturerSimple
- **Location**: `dist/AndroidLogCapturerSimple`
- **Size**: ~11MB
- **Dependencies**: None (all bundled)
- **Features**: Full functionality without WebSocket (polling-based updates)

### AndroidLogCapturer (Original)
- **Status**: Has SocketIO compatibility issues in executable form
- **Recommendation**: Use `AndroidLogCapturerSimple` for distribution

## Usage Instructions

### 1. Building for Different Platforms

The current executables are built for macOS. To create executables for other platforms:

#### For Windows (Build on Windows machine):
```cmd
# Install PyInstaller
pip install pyinstaller

# Build Windows executable
pyinstaller --onefile --add-data "templates;templates" --add-data "static;static" --name "AndroidLogCapturerSimple" web_app_simple.py

# The executable will be created as: dist\AndroidLogCapturerSimple.exe
```

#### For Linux (Build on Linux machine):
```bash
# Install PyInstaller
pip install pyinstaller

# Build Linux executable
pyinstaller --onefile --add-data "templates:templates" --add-data "static:static" --name "AndroidLogCapturerSimple" web_app_simple.py

# The executable will be created as: dist/AndroidLogCapturerSimple
```

### 2. Running the Application

#### On Windows:
```cmd
# Navigate to the dist folder
cd dist

# Run the Windows executable
AndroidLogCapturerSimple.exe
```

#### On macOS/Linux:
```bash
# Make executable (macOS/Linux)
chmod +x ./dist/AndroidLogCapturerSimple

# Run the application
./dist/AndroidLogCapturerSimple
```

The application will start and display:
```
Android Log Capturer starting on http://localhost:5001
Open your web browser to access the interface
* Running on all addresses (0.0.0.0)
* Running on http://127.0.0.1:5001
```

### 2. Accessing the Web Interface

Open your web browser and navigate to:
- Local: `http://localhost:5001`
- Network: `http://[your-ip]:5001`

### 3. Setting Up Device Connection

1. **Connect Android Device**
   - Enable USB debugging on your Android device
   - Connect via USB cable
   - Accept ADB debugging authorization if prompted

2. **Select Device**
   - Click "🔄 Refresh Devices" to scan for connected devices
   - Select your device from the dropdown
   - Click "🔗 Connect" to establish connection

### 4. Configuring Webhooks

#### Realtime Webhook
- **Purpose**: Sends individual log entries immediately as they occur
- **Format**: Single log entry per request
- **Usage**: For real-time monitoring and alerting

```json
{
  "timestamp": "2024-01-15 10:30:45",
  "device_id": "ABC123456789",
  "log": "I/ActivityManager: Starting activity..."
}
```

#### Bulk Webhook  
- **Purpose**: Sends accumulated logs in bulk when manually triggered
- **Format**: Array of log entries with metadata
- **Usage**: For batch processing and analytics

```json
{
  "timestamp": "2024-01-15 10:30:45",
  "device_id": "ABC123456789", 
  "log_count": 150,
  "logs": [
    {
      "timestamp": "2024-01-15 10:30:45",
      "device_id": "ABC123456789",
      "log": "I/ActivityManager: Starting activity..."
    }
    // ... more log entries
  ]
}
```

### 5. Log Capture Operations

1. **Start Capture**: Click "▶️ Start Capture" to begin monitoring
2. **Monitor Logs**: View real-time logs in the interface
3. **Bulk Publish**: Click "📤 Bulk Publish" to send accumulated logs
4. **Stop Capture**: Click "⏹️ Stop Capture" to halt monitoring

## Architecture

### Executable Structure
```
AndroidLogCapturerSimple
├── Templates (bundled)
│   └── index_simple.html
├── Static assets (bundled) 
│   └── CSS, JS files
├── Python runtime (bundled)
├── Flask framework (bundled)
├── ADB functionality (system dependency)
└── All dependencies (bundled)
```

### System Requirements
- **Operating System**: macOS 10.14+, Windows 10+, or Linux
- **ADB**: Android Debug Bridge must be installed and in PATH
- **Network**: Port 5001 available for web interface
- **USB**: For Android device connection

### Port Configuration
- **Default Port**: 5001
- **Binding**: All interfaces (0.0.0.0)
- **Access**: Local and network access enabled

## Troubleshooting

### Common Issues

**Port Already in Use**
```
Error: Address already in use
```
*Solution*: Another service is using port 5001. Either stop the conflicting service or modify the executable to use a different port.

**No Devices Found**
```
Status: Found 0 device(s)
```
*Solutions*:
- Ensure ADB is installed and in PATH
- Enable USB debugging on Android device  
- Accept ADB authorization popup on device
- Try different USB cable/port

**ADB Command Not Found**
```
Error: 'adb' is not recognized as an internal or external command
```
*Solutions*:
- Install Android SDK Platform Tools
- Add ADB to system PATH
- Restart terminal/command prompt

**Webhook Delivery Failures**
```
Error sending webhook to [URL]: Connection timeout
```
*Solutions*:
- Verify webhook URL is accessible
- Check network connectivity
- Ensure webhook endpoint accepts POST requests
- Review webhook server logs

### Performance Tips

1. **Log Management**: The interface shows last 100 logs to prevent memory issues
2. **Bulk Publishing**: Clear bulk queue regularly to prevent memory accumulation
3. **Network Usage**: Realtime webhooks generate more network traffic than bulk
- **Resource Usage**: Stop capture when not needed to reduce CPU/memory usage

## Windows-Specific Instructions

### Prerequisites for Windows

1. **Install ADB (Android Debug Bridge)**
   - Download Android SDK Platform Tools from [developer.android.com](https://developer.android.com/studio/releases/platform-tools)
   - Extract to a folder (e.g., `C:\platform-tools\`)
   - Add the folder to your Windows PATH:
     - Press `Win + X` → System → Advanced System Settings
     - Click "Environment Variables"
     - Under "System Variables", find and select "Path"
     - Click "Edit" → "New" → Add `C:\platform-tools\`
     - Click "OK" to save

2. **Verify ADB Installation**
   ```cmd
   # Open Command Prompt and test
   adb version
   
   # Should show something like:
   # Android Debug Bridge version 1.0.41
   ```

### Building on Windows

1. **Install Python** (if building from source)
   - Download Python 3.8+ from [python.org](https://python.org)
   - ⚠️ **Important**: Check "Add Python to PATH" during installation

2. **Install Dependencies**
   ```cmd
   pip install flask requests pyinstaller
   ```

3. **Build the Executable**
   ```cmd
   # Navigate to project directory
   cd C:\path\to\your\project

   # Build executable (note the semicolon separator for Windows)
   pyinstaller --onefile --add-data "templates;templates" --add-data "static;static" --name "AndroidLogCapturerSimple" web_app_simple.py
   ```

4. **Run the Executable**
   ```cmd
   # Navigate to dist folder
   cd dist

   # Run the executable
   AndroidLogCapturerSimple.exe
   ```

### Easy Windows Launch (Helper Scripts)

For convenience, use the provided helper scripts:

**Option 1: Batch File (run_windows.bat)**
- Double-click `run_windows.bat` in Windows Explorer
- Automatically checks for ADB and runs the executable
- Provides helpful error messages and instructions

**Option 2: PowerShell Script (run_windows.ps1)**
- Right-click `run_windows.ps1` → "Run with PowerShell" 
- More advanced error handling and status messages
- May require execution policy changes (see troubleshooting)

### Windows-Specific Troubleshooting

**Firewall Issues**
```
Error: Windows Security Alert - Python wants to access the network
```
*Solution*: Click "Allow access" when Windows Firewall prompts appear

**ADB Driver Issues**
```
Error: device not found or no permissions
```
*Solutions*:
- Install proper USB drivers for your Android device
- Enable "USB Debugging" in Developer Options on Android
- Try different USB ports (prefer USB 2.0 over USB 3.0)
- Use "Revoke USB debugging authorizations" and reconnect

**Port Already in Use (Windows)**
```
Error: [WinError 10048] Only one usage of each socket address is normally permitted
```
*Solutions*:
- Check what's using port 5001: `netstat -ano | findstr :5001`
- Kill the process: `taskkill /PID [process_id] /F`
- Or modify the executable to use a different port

**PowerShell Execution Policy**
```
Error: execution of scripts is disabled on this system
```
*Solution*:
```powershell
# Run PowerShell as Administrator
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Running from Different Locations

**Option 1: Double-Click (GUI)**
- Navigate to the `dist` folder in Windows Explorer
- Double-click `AndroidLogCapturerSimple.exe`
- A Command Prompt window will open showing the server output

**Option 2: Command Prompt**
```cmd
# Full path execution
C:\path\to\project\dist\AndroidLogCapturerSimple.exe

# Or navigate and run
cd C:\path\to\project\dist
AndroidLogCapturerSimple.exe
```

**Option 3: PowerShell**
```powershell
# Navigate and run
cd C:\path\to\project\dist
.\AndroidLogCapturerSimple.exe
```

### Creating a Windows Shortcut

1. Right-click on `AndroidLogCapturerSimple.exe`
2. Select "Create shortcut"
3. Move the shortcut to Desktop or Start Menu
4. Right-click shortcut → Properties → Change icon (optional)

## Development vs Executable

### Advantages of Executable
- No Python installation required
- All dependencies bundled
- Easy distribution and deployment  
- Consistent runtime environment
- No version conflicts

### Limitations of Executable
- Larger file size (~11MB vs few KB for scripts)
- Cannot modify code without rebuilding
- Platform-specific binaries needed
- No WebSocket support (uses polling instead)

### When to Use Each
- **Executable**: Production deployment, end-user distribution, locked environments
- **Development**: Code modifications, debugging, development environments

## Build Information

- **PyInstaller Version**: 6.16.0
- **Python Version**: 3.13.5
- **Build Platform**: macOS ARM64
- **Bundle Type**: One-file executable
- **Async Mode**: Standard Flask (no SocketIO)

## File Structure

```
project/
├── dist/
│   ├── AndroidLogCapturerSimple          # ✅ Working executable
│   └── AndroidLogCapturer               # ❌ SocketIO issues
├── src/                                 # Modular source code
├── templates/
│   ├── index.html                       # WebSocket version
│   └── index_simple.html               # Polling version  
├── static/                              # CSS/JS assets
├── web_app.py                          # WebSocket version
├── web_app_simple.py                   # Polling version
├── requirements.txt                     # Dependencies
└── build scripts (build.sh, build.bat, etc.)
```

## Support

For issues, questions, or contributions:
1. Check this README for common solutions
2. Verify ADB installation and device connection
3. Test with development version if executable fails
4. Check network connectivity for webhook issues

---

**🎉 Congratulations!** You now have a fully functional, distributable Android Log Capturer executable with dual webhook support and a modern web interface!