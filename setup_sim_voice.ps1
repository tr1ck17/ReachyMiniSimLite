py -m venv .venv
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
if (!(Test-Path $voskZip)) {
    Write-Host "Downloading Vosk speech recognition model..."
    Invoke-WebRequest -Uri $voskUrl -OutFile $voskZip
}
if (!(Test-Path "models\vosk-model-small-en-us-0.15")) {
    Write-Host "Extracting Vosk model..."
    Expand-Archive -Path $voskZip -DestinationPath "models"
}

Write-Host ""
Write-Host "Setup complete! To run:"
Write-Host "  1. Open the Reachy Mini Dashboard"
Write-Host "  2. Select Simulation mode and wake the robot"
Write-Host "  3. Run:  .\.venv\Scripts\python reachy_solar_system_sim_voice.py"
