# FFmpeg Setup for GIF ⇄ MP4 Converter

## Overview

FFmpeg is required for the GIF ⇄ MP4 converter to function. This guide will help you install FFmpeg on your Windows system.

## Option 1: Download Pre-built Binary (Recommended)

### Step 1: Download FFmpeg
1. Go to https://ffmpeg.org/download.html#build-windows
2. Click on "Windows builds by BtbN"
3. Download the latest release (e.g., `ffmpeg-master-latest-win64-gpl.zip`)

### Step 2: Extract FFmpeg
1. Create a folder: `C:\ffmpeg`
2. Extract the downloaded ZIP file to this folder
3. You should have: `C:\ffmpeg\bin\ffmpeg.exe`

### Step 3: Add to System PATH
1. Press `Win + R`, type `sysdm.cpl`, press Enter
2. Click "Advanced" tab → "Environment Variables"
3. Under "System Variables", find "Path" → Click "Edit"
4. Click "New" → Add `C:\ffmpeg\bin`
5. Click "OK" on all dialogs

### Step 4: Verify Installation
Open Command Prompt or PowerShell and run:
```powershell
ffmpeg -version
```

You should see FFmpeg version information.

## Option 2: Using Package Manager

### Using Chocolatey
If you have Chocolatey installed:
```powershell
# Run as Administrator
choco install ffmpeg
```

### Using Winget (Windows 10/11)
```powershell
winget install ffmpeg
```

### Using Scoop
If you have Scoop installed:
```powershell
scoop install ffmpeg
```

## Option 3: Quick Setup Script

Create `install_ffmpeg.ps1` and run as Administrator:

```powershell
# PowerShell script to install FFmpeg
$ffmpegPath = "C:\ffmpeg"
$downloadUrl = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"
$zipPath = "$env:TEMP\ffmpeg.zip"

# Create directory
New-Item -ItemType Directory -Force -Path $ffmpegPath

# Download FFmpeg
Write-Host "Downloading FFmpeg..." -ForegroundColor Green
Invoke-WebRequest -Uri $downloadUrl -OutFile $zipPath

# Extract
Write-Host "Extracting FFmpeg..." -ForegroundColor Green
Expand-Archive -Path $zipPath -DestinationPath $ffmpegPath -Force

# Move files to correct location
$extractedFolder = Get-ChildItem -Path $ffmpegPath -Directory | Select-Object -First 1
Move-Item -Path "$($extractedFolder.FullName)\*" -Destination $ffmpegPath -Force
Remove-Item -Path $extractedFolder.FullName -Recurse

# Add to PATH
$currentPath = [Environment]::GetEnvironmentVariable("PATH", "Machine")
if ($currentPath -notlike "*$ffmpegPath\bin*") {
    [Environment]::SetEnvironmentVariable("PATH", "$currentPath;$ffmpegPath\bin", "Machine")
    Write-Host "Added FFmpeg to system PATH" -ForegroundColor Green
}

# Clean up
Remove-Item -Path $zipPath -Force

Write-Host "FFmpeg installation complete!" -ForegroundColor Green
Write-Host "Please restart your terminal/IDE to use FFmpeg." -ForegroundColor Yellow

# Test installation
try {
    & "$ffmpegPath\bin\ffmpeg.exe" -version
    Write-Host "✅ FFmpeg is working correctly!" -ForegroundColor Green
} catch {
    Write-Host "⚠️ FFmpeg installation may have issues" -ForegroundColor Red
}
```

## Verification

After installation, verify FFmpeg is working:

1. **Test basic functionality:**
```powershell
ffmpeg -version
ffprobe -version
```

2. **Test with the converter:**
   - Start your Flask application
   - Navigate to `http://localhost:5000/gif-mp4/`
   - You should NOT see "FFmpeg Not Available" error
   - Try uploading a small GIF or MP4 file

## Troubleshooting

### FFmpeg not found error
- **Symptom:** "FFmpeg Not Available" in converter
- **Solution:** 
  1. Verify PATH is set correctly
  2. Restart terminal/IDE
  3. Try running `ffmpeg -version` in Command Prompt

### Permission denied
- **Symptom:** Access denied when running conversion
- **Solution:**
  1. Run Command Prompt as Administrator
  2. Check antivirus isn't blocking FFmpeg
  3. Ensure `C:\ffmpeg` has proper permissions

### Codec not supported
- **Symptom:** "Codec not found" errors
- **Solution:** 
  1. Download GPL build (not LGPL)
  2. Use pre-built binaries from official sources

### Path too long
- **Symptom:** Installation fails on Windows
- **Solution:**
  1. Use shorter path like `C:\ffmpeg`
  2. Enable long path support in Windows

## Alternative: Portable FFmpeg

For development/testing, you can place FFmpeg in your project:

1. Create `C:\Users\himan\Desktop\converter\bin\`
2. Place `ffmpeg.exe` and `ffprobe.exe` there
3. Update the Flask route to check local path first:

```python
def check_ffmpeg_availability():
    """Check if FFmpeg is available"""
    # Check local path first
    local_ffmpeg = os.path.join(os.path.dirname(__file__), '..', 'bin', 'ffmpeg.exe')
    if os.path.exists(local_ffmpeg):
        try:
            subprocess.run([local_ffmpeg, '-version'], capture_output=True, timeout=10)
            return True
        except:
            pass
    
    # Check system PATH
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, timeout=10)
        return True
    except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
        return False
```

## System Requirements

- **Windows 7** or later
- **64-bit** system (recommended)
- **~100MB** free disk space
- **Administrative privileges** for installation

## Performance Tips

1. **SSD recommended** for faster processing
2. **8GB+ RAM** for large video files
3. **Close other applications** during conversion
4. **Use medium quality** for balance of speed/quality

---

**Note:** After installing FFmpeg, restart your development environment and Flask application for the changes to take effect.
