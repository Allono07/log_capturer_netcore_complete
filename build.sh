#!/bin/bash
# Build script for macOS/Linux

echo "🚀 Building Android Log Capturer Executable..."

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt
pip install pyinstaller

# Build executable
echo "🔨 Creating executable..."
pyinstaller --onefile \
    --add-data "templates:templates" \
    --add-data "static:static" \
    --name "AndroidLogCapturer" \
    --console \
    web_app.py

echo "✅ Build complete!"
echo "📁 Executable location: dist/AndroidLogCapturer"
echo ""
echo "📋 Usage Instructions:"
echo "1. Copy the executable to target machine"
echo "2. Ensure ADB is installed on target machine"
echo "3. Connect Android device via USB"
echo "4. Run: ./AndroidLogCapturer"
echo "5. Open browser to: http://localhost:5002"