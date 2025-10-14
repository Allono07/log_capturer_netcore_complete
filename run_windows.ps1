# Android Log Capturer - Windows PowerShell Script

Write-Host ""
Write-Host "========================================"
Write-Host "  Android Log Capturer - Windows"
Write-Host "========================================"
Write-Host ""
Write-Host "Starting Android Log Capturer..."
Write-Host "Web interface will be available at:"
Write-Host "  http://localhost:5001"
Write-Host ""
Write-Host "Press Ctrl+C to stop the server"
Write-Host ""

# Check if ADB is available
try {
    $adbVersion = adb version 2>$null
    Write-Host "✓ ADB found: $($adbVersion.Split("`n")[0])"
} catch {
    Write-Warning "ADB not found in PATH"
    Write-Warning "Please install Android SDK Platform Tools and add to system PATH"
    Write-Host ""
    Read-Host "Press Enter to continue anyway..."
}

# Get the directory where this script is located
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $scriptDir

# Check if executable exists
$executablePath = Join-Path $scriptDir "dist\AndroidLogCapturerSimple.exe"
if (-not (Test-Path $executablePath)) {
    Write-Error "AndroidLogCapturerSimple.exe not found"
    Write-Host "Please build the executable first using:"
    Write-Host "  pyinstaller --onefile --add-data `"templates;templates`" --add-data `"static;static`" --name `"AndroidLogCapturerSimple`" web_app_simple.py"
    Write-Host ""
    Read-Host "Press Enter to exit..."
    exit 1
}

# Run the executable
Write-Host "Running AndroidLogCapturerSimple.exe..."
Write-Host ""

try {
    & $executablePath
} catch {
    Write-Error "Failed to run executable: $($_.Exception.Message)"
} finally {
    Write-Host ""
    Write-Host "Application has stopped."
    Read-Host "Press Enter to exit..."
}