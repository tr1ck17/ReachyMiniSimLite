# Mini Reachy Solar System (Simulation-first)

This project is a full, interactive solar physics lesson designed for Reachy Mini.
It targets the **Simulation** mode first and includes a clean adapter layer to
swap in **Lite** and **Wireless** SDK calls later.

## What this includes
- 6 structured levels (core → solar wind)
- Dialogue prompts with interactive Q&A
- Motion cues for each lesson
- Open-ended question loop for "extra time"

## Run (simulation mode)
```bash
python reachy_solar_system.py
```

## Quick setup (school desktop)
Lite/USB (no simulation):
```powershell
.\setup.ps1
```

Simulation + mujoco:
```powershell
.\setup.ps1 -WithMujoco
```

## Offline voice + chat (no OpenAI billing)
This uses local STT/TTS + a tiny local LLM for off-topic chat.
```powershell
.\setup_offline.ps1
.\.venv\Scripts\python reachy_solar_system_lite_voice_offline.py
```

## Lite voice (offline, no LLM)
```powershell
.\setup_lite_voice.ps1
.\.venv\Scripts\python reachy_solar_system_lite.py
```

## Next steps for Lite/Wireless
Replace `SimulationAdapter` in `reachy_solar_system.py` with a new adapter that
wraps the official Reachy Mini SDK (speech + head/antenna motions).

Suggested adapter skeleton:
- `ReachyAdapter.say(text)` → SDK speech or TTS
- `ReachyAdapter.motion(name, duration_s)` → SDK motion routines

## Notes
- Time is "unlimited" by design (menu loop + Q&A loop).
- You can expand `FAQ` with additional astronomy answers.
