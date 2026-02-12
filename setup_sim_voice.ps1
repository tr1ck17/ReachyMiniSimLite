python -m venv .venv
.\.venv\Scripts\python -m pip install -U pip

# Reachy Mini SDK (includes mujoco simulation support)
.\.venv\Scripts\python -m pip install "reachy-mini"

# Offline voice deps (all free, no API keys needed)
.\.venv\Scripts\python -m pip install vosk pyttsx3 sounddevice

if (!(Test-Path "models")) {
    New-Item -ItemType Directory -Path "models" | Out-Null
}

# Vosk small English model (~40MB download, runs locally)
$voskUrl = "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip"
$voskZip = "models\vosk-model-small-en-us-0.15.zip"
$voskDir = "models\vosk-model-small-en-us-0.15"

# Delete corrupted zip if it exists but is too small (< 1MB means bad download)
if ((Test-Path $voskZip) -and ((Get-Item $voskZip).Length -lt 1MB)) {
    Write-Host "Previous download appears corrupted, removing..."
    Remove-Item $voskZip -Force
}

if (!(Test-Path $voskZip)) {
    Write-Host "Downloading Vosk speech recognition model (~40MB)..."
    try {
        Invoke-WebRequest -Uri $voskUrl -OutFile $voskZip -UseBasicParsing
    } catch {
        Write-Host "ERROR: Download failed. Check your internet connection."
        Write-Host "You can also download manually from: $voskUrl"
        Write-Host "Place the zip in the 'models' folder and re-run this script."
        exit 1
    }
    # Verify download size (model is ~40MB, anything under 1MB is wrong)
    if ((Get-Item $voskZip).Length -lt 1MB) {
        Write-Host "ERROR: Downloaded file is too small -- likely a bad download."
        Remove-Item $voskZip -Force
        Write-Host "Please check your internet connection and try again."
        exit 1
    }
}

if (!(Test-Path $voskDir)) {
    Write-Host "Extracting Vosk model..."
    try {
        Expand-Archive -Path $voskZip -DestinationPath "models"
    } catch {
        Write-Host "ERROR: Extraction failed. The zip may be corrupted."
        Remove-Item $voskZip -Force
        Write-Host "Deleted bad zip. Please re-run this script to re-download."
        exit 1
    }
}

Write-Host ""
Write-Host "Setup complete! To run:"
Write-Host "  1. Open the Reachy Mini Dashboard"
Write-Host "  2. Select Simulation mode and wake the robot"
Write-Host "  3. Run:  .\.venv\Scripts\python reachy_solar_system_sim_voice.py"
