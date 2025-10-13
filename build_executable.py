#!/usr/bin/env python3
"""
Build script to create executable for Android Log Capturer
"""

import os
import sys
import subprocess

def install_pyinstaller():
    """Install PyInstaller if not already installed"""
    try:
        import PyInstaller
        print("✅ PyInstaller is already installed")
    except ImportError:
        print("📦 Installing PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        print("✅ PyInstaller installed successfully")

def create_spec_file():
    """Create PyInstaller spec file with proper configuration"""
    spec_content = """
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['web_app.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('templates', 'templates'),
        ('static', 'static'),
    ],
    hiddenimports=[
        'flask',
        'flask_socketio',
        'socketio',
        'engineio',
        'requests',
        'secrets',
        'queue',
        'threading',
        'subprocess',
        're',
        'json',
        'time',
        'datetime',
        'os'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='AndroidLogCapturer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='static/favicon.png' if os.path.exists('static/favicon.png') else None,
)
"""
    
    with open('AndroidLogCapturer.spec', 'w') as f:
        f.write(spec_content)
    
    print("✅ Created AndroidLogCapturer.spec file")

def build_executable():
    """Build the executable using PyInstaller"""
    print("🔨 Building executable...")
    
    try:
        # Build using spec file
        result = subprocess.run([
            'pyinstaller', 
            '--clean',
            'AndroidLogCapturer.spec'
        ], check=True, capture_output=True, text=True)
        
        print("✅ Executable built successfully!")
        print("📁 Location: dist/AndroidLogCapturer")
        
        # Check if executable exists
        if os.name == 'nt':  # Windows
            exe_path = "dist/AndroidLogCapturer.exe"
        else:  # macOS/Linux
            exe_path = "dist/AndroidLogCapturer"
            
        if os.path.exists(exe_path):
            size_mb = os.path.getsize(exe_path) / (1024 * 1024)
            print(f"📊 Executable size: {size_mb:.1f} MB")
            print(f"🎯 Ready to distribute: {exe_path}")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Build failed: {e}")
        print("Error output:", e.stderr)
        return False
    
    return True

def main():
    """Main build process"""
    print("🚀 Android Log Capturer - Executable Builder")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not os.path.exists('web_app.py'):
        print("❌ Error: web_app.py not found in current directory")
        print("Please run this script from the project root directory")
        return
    
    # Install PyInstaller
    install_pyinstaller()
    
    # Create spec file
    create_spec_file()
    
    # Build executable
    if build_executable():
        print("\n🎉 Success! Your executable is ready!")
        print("\n📋 Distribution Notes:")
        print("• The executable includes all dependencies")
        print("• No Python installation required on target machine")
        print("• ADB must still be installed on target machine")
        print("• Android device must be connected via USB")
        print("• Run as administrator if needed for ADB access")
    else:
        print("\n❌ Build failed. Check the error messages above.")

if __name__ == '__main__':
    main()