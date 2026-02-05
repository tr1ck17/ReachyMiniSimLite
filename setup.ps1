param(
    [switch]$WithMujoco
)

py -m venv .venv
.\.venv\Scripts\python -m pip install -U pip

if ($WithMujoco) {
    .\.venv\Scripts\python -m pip install "reachy-mini[mujoco]" openai
} else {
    .\.venv\Scripts\python -m pip install -r requirements.txt
}

Write-Host "Setup complete."
if ($WithMujoco) {
    Write-Host "Mujoco installed for simulation."
} else {
    Write-Host "Lite/USB dependencies installed."
}
