py -m venv .venv
.\.venv\Scripts\python -m pip install -U pip

# Lite/USB SDK
.\.venv\Scripts\python -m pip install "reachy-mini"

# Offline voice deps
.\.venv\Scripts\python -m pip install vosk pyttsx3 sounddevice

if (!(Test-Path "models")) {
    New-Item -ItemType Directory -Path "models" | Out-Null
}

# Vosk small English model
$voskUrl = "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip"
$voskZip = "models\vosk-model-small-en-us-0.15.zip"
if (!(Test-Path $voskZip)) {
    Invoke-WebRequest -Uri $voskUrl -OutFile $voskZip
}
if (!(Test-Path "models\vosk-model-small-en-us-0.15")) {
    Expand-Archive -Path $voskZip -DestinationPath "models"
}

Write-Host "Lite voice setup complete."
