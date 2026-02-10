param(
    [switch]$WithMujoco
)

py -m venv .venv
.\.venv\Scripts\python -m pip install -U pip

if ($WithMujoco) {
    .\.venv\Scripts\python -m pip install "reachy-mini[mujoco]"
} else {
    .\.venv\Scripts\python -m pip install "reachy-mini"
}

.\.venv\Scripts\python -m pip install -r requirements_offline.txt

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

# TinyLlama GGUF (lightweight)
$llmUrl = "https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat.Q4_K_M.gguf"
$llmPath = "models\tinyllama-1.1b-chat.Q4_K_M.gguf"
if (!(Test-Path $llmPath)) {
    Invoke-WebRequest -Uri $llmUrl -OutFile $llmPath
}

Write-Host "Offline setup complete."
Write-Host "Models stored in ./models"
