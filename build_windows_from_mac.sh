#!/bin/bash

echo "Building Windows executable using Docker..."
echo "This will create a Windows .exe file from macOS"
echo ""

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop."
    exit 1
fi

echo "🐳 Building Windows executable in Docker container..."

# Build the Windows executable using Docker
docker build -f Dockerfile.windows -t android-log-capturer-windows .

# Create a temporary container to extract the executable
echo "📦 Extracting Windows executable..."
docker create --name temp-container android-log-capturer-windows

# Copy the executable from the container
mkdir -p dist/windows
docker cp temp-container:/app/dist/AndroidLogCapturerSimple.exe dist/windows/

# Clean up
docker rm temp-container

if [ -f "dist/windows/AndroidLogCapturerSimple.exe" ]; then
    echo "✅ Windows executable created successfully!"
    echo "📁 Location: dist/windows/AndroidLogCapturerSimple.exe"
    echo ""
    echo "You can now copy this .exe file to any Windows machine and run it directly."
else
    echo "❌ Failed to create Windows executable"
    exit 1
fi