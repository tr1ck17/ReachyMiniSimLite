"""
Reachy Mini Solar System Program (Lite / USB + Offline Voice)

Connects to a physical Reachy Mini Lite via USB with full offline voice:
- Offline TTS via pyttsx3 (free, uses Windows SAPI5)
- Offline STT via Vosk (free, local speech recognition)
- All speech spoken aloud, all input via voice or keyboard

Prerequisites:
  pip install reachy-mini vosk pyttsx3 sounddevice numpy
  (or run setup_lite_voice_full.ps1)

Models expected in ./models:
  - vosk-model-small-en-us-0.15
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional
import json
import os
import tempfile
import time
import wave

import numpy as np
from reachy_mini import ReachyMini
from reachy_mini.utils import create_head_pose

try:
    import pyttsx3
except Exception:
    pyttsx3 = None

try:
    import vosk
except Exception:
    vosk = None

try:
    import sounddevice as sd
except Exception:
    sd = None


VOSK_MODEL_PATH = os.getenv("VOSK_MODEL_PATH", "models/vosk-model-small-en-us-0.15")


# ----------------------------
# Auto-detect Reachy audio devices
# ----------------------------

# Prioritised keyword lists for finding the Reachy's audio devices.
# Searched in order -- first match wins. More specific names first.

# For the microphone: prefer the speakerphone, avoid the camera mic.
REACHY_MIC_KEYWORDS = [
    "reachy mini audio",       # The speakerphone mic (best quality)
    "echo cancelling",         # Speakerphone with echo cancelling
    "reachy",                  # Generic fallback
    "pollen",                  # Pollen Robotics
]

# For the speaker: look for the dedicated audio output.
REACHY_SPEAKER_KEYWORDS = [
    "output (reachy",          # "Output (Reachy Mini Audio)"
    "reachy mini audio",       # The audio output device
    "reachy",                  # Generic fallback
    "pollen",                  # Pollen Robotics
]


def find_reachy_device(direction: str) -> Optional[int]:
    """
    Auto-detect the Reachy's audio device by scanning device names.

    Uses separate prioritised keyword lists for mic vs speaker to
    ensure the speakerphone mic is preferred over the camera mic,
    and the audio output is preferred over the speakerphone output.

    Args:
        direction: 'input' or 'output'.

    Returns:
        Device index, or None if not found.
    """
    devices = sd.query_devices()
    keywords = REACHY_MIC_KEYWORDS if direction == "input" else REACHY_SPEAKER_KEYWORDS

    # Search by priority: try each keyword in order across all devices
    for keyword in keywords:
        for i, dev in enumerate(devices):
            if direction == "input" and dev["max_input_channels"] == 0:
                continue
            if direction == "output" and dev["max_output_channels"] == 0:
                continue
            if keyword in dev["name"].lower():
                return i
    return None


def detect_reachy_audio() -> tuple[Optional[int], Optional[int]]:
    """
    Auto-detect the Reachy Mini Lite's built-in mic and speaker.

    Scans all audio devices for names matching known Reachy/USB audio
    keywords. Falls back to system defaults if not found.

    Returns:
        (input_device_index, output_device_index) -- None means system default.
    """
    devices = sd.query_devices()

    # Always show all devices so user can verify what was detected
    print("\n  All audio devices on this system:")
    print("  " + "-" * 60)
    for i, dev in enumerate(devices):
        ins = dev["max_input_channels"]
        outs = dev["max_output_channels"]
        tags = []
        if ins > 0:
            tags.append("mic")
        if outs > 0:
            tags.append("speaker")
        print(f"    {i}: {dev['name']}  [{', '.join(tags)}]")
    print("  " + "-" * 60)

    input_idx = find_reachy_device("input")
    output_idx = find_reachy_device("output")

    if input_idx is not None:
        dev = devices[input_idx]
        print(f"[Audio] Reachy mic    -> device {input_idx} ({dev['name']})")
        print(f"        channels={dev['max_input_channels']}, "
              f"default_sr={dev['default_samplerate']}")
    else:
        print("[Audio] Reachy mic not detected -- using system default microphone.")

    if output_idx is not None:
        dev = devices[output_idx]
        print(f"[Audio] Reachy speaker -> device {output_idx} ({dev['name']})")
        print(f"        channels={dev['max_output_channels']}, "
              f"default_sr={dev['default_samplerate']}")
        # Verify the device can actually be opened for playback
        try:
            test_audio = np.zeros(1000, dtype=np.int16)
            sd.play(test_audio, samplerate=22050, device=output_idx)
            sd.wait()
            print("[Audio] Speaker device verified -- playback works.")
        except Exception as exc:
            print(f"[Audio] WARNING: Speaker device {output_idx} failed: {exc}")
            print("[Audio] Trying to find an alternative Reachy output device...")
            # Try all other output devices with 'reachy' in the name
            alt_found = False
            for i, d in enumerate(devices):
                if i == output_idx:
                    continue
                if d["max_output_channels"] == 0:
                    continue
                if "reachy" not in d["name"].lower():
                    continue
                try:
                    sd.play(test_audio, samplerate=22050, device=i)
                    sd.wait()
                    print(f"[Audio] Alternative speaker found: device {i} ({d['name']})")
                    output_idx = i
                    alt_found = True
                    break
                except Exception:
                    continue
            if not alt_found:
                print("[Audio] No working Reachy speaker found -- falling back to system default.")
                output_idx = None
    else:
        print("[Audio] Reachy speaker not detected -- using system default speaker.")

    return input_idx, output_idx


def test_microphone(input_device: Optional[int], sample_rate: int = 16000) -> bool:
    """
    Quick mic test: record 2 seconds and check if any sound was picked up.

    Returns True if the mic seems to be working.
    """
    print("\n[Mic Test] Recording 2 seconds of audio -- speak or make noise...")
    try:
        frames = sample_rate * 2
        audio = sd.rec(frames, samplerate=sample_rate, channels=1, dtype="int16", device=input_device)
        sd.wait()

        # Check audio level
        peak = int(np.max(np.abs(audio)))
        rms = int(np.sqrt(np.mean(audio.astype(np.float64) ** 2)))
        print(f"[Mic Test] Peak level: {peak}  |  RMS level: {rms}  (out of 32767)")

        if peak < 100:
            print("[Mic Test] WARNING: Almost no sound detected. The mic may not be working")
            print("           or the wrong device was selected.")
            return False
        elif peak < 1000:
            print("[Mic Test] Low volume detected. Speech recognition may struggle.")
            print("           Try speaking louder or closer to the mic.")
            return True
        else:
            print("[Mic Test] Mic is working! Sound detected.")
            return True
    except Exception as exc:
        print(f"[Mic Test] ERROR: {exc}")
        return False


# ----------------------------
# Offline Voice I/O
# ----------------------------

class OfflineVoiceIO:
    """
    Free, offline TTS + STT using pyttsx3 and Vosk.

    Supports routing audio to specific devices (e.g. Reachy's built-in
    mic and speaker) instead of the system defaults.
    """

    def __init__(
        self,
        sample_rate: int = 16000,
        record_seconds: float = 5.0,
        input_device: Optional[int] = None,
        output_device: Optional[int] = None,
    ) -> None:
        if vosk is None:
            raise RuntimeError("vosk is not installed. Run: pip install vosk")
        if pyttsx3 is None:
            raise RuntimeError("pyttsx3 is not installed. Run: pip install pyttsx3")
        if sd is None:
            raise RuntimeError("sounddevice is not installed. Run: pip install sounddevice")
        if not os.path.isdir(VOSK_MODEL_PATH):
            raise RuntimeError(
                f"Vosk model not found at '{VOSK_MODEL_PATH}'. "
                "Run setup_lite_voice_full.ps1 or download from https://alphacephei.com/vosk/models"
            )
        self.sample_rate = sample_rate
        self.record_seconds = record_seconds
        self.input_device = input_device
        self.output_device = output_device
        self.model = vosk.Model(VOSK_MODEL_PATH)
        self.tts_rate = 165

        # Verify TTS works on init (also warms up SAPI5)
        engine = pyttsx3.init()
        engine.setProperty("rate", self.tts_rate)
        engine.stop()
        del engine

    def listen(self) -> str:
        """Record from the microphone and return recognised text."""
        dev_name = ""
        if self.input_device is not None:
            dev_name = f" (device {self.input_device})"
        print(f"  [Listening{dev_name}... speak now]")
        frames = int(self.sample_rate * self.record_seconds)
        audio = sd.rec(
            frames,
            samplerate=self.sample_rate,
            channels=1,
            dtype="int16",
            device=self.input_device,
        )
        sd.wait()

        # Log audio level so we can tell if the mic is picking up sound
        peak = int(np.max(np.abs(audio)))
        print(f"  [Audio level: peak={peak}/32767]")
        if peak < 100:
            print("  [WARNING: Almost no sound detected -- check mic]")

        rec = vosk.KaldiRecognizer(self.model, self.sample_rate)
        rec.AcceptWaveform(audio.tobytes())
        result = json.loads(rec.Result())
        text = result.get("text", "").strip()
        if text:
            print(f"  [Heard: {text}]")
        else:
            print("  [Nothing recognised]")
        return text

    def speak(self, text: str) -> None:
        """
        Speak text aloud.

        If an output device is set (e.g. Reachy's speaker), renders speech
        to a temp WAV file via pyttsx3, then plays it through sounddevice
        to the correct device. Falls back to system default if that fails.
        """
        engine = pyttsx3.init()
        engine.setProperty("rate", self.tts_rate)

        if self.output_device is not None:
            # Save speech to a temp WAV, then play through the Reachy speaker
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp_path = tmp.name
            try:
                engine.save_to_file(text, tmp_path)
                engine.runAndWait()
                engine.stop()
                del engine
                self._play_wav(tmp_path)
                return
            except Exception as exc:
                print(f"  [TTS] Reachy speaker failed ({exc}), using system default.")
                # Fall back to system default below
            finally:
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass

        # Play through system default speaker directly (or as fallback)
        try:
            engine = pyttsx3.init()
            engine.setProperty("rate", self.tts_rate)
            engine.say(text)
            engine.runAndWait()
            engine.stop()
            del engine
        except Exception:
            pass

    def _play_wav(self, path: str) -> None:
        """Play a WAV file through the selected output device."""
        with wave.open(path, "rb") as wf:
            n_channels = wf.getnchannels()
            sample_width = wf.getsampwidth()
            framerate = wf.getframerate()
            raw = wf.readframes(wf.getnframes())

        # Convert raw bytes to numpy array
        if sample_width == 2:
            dtype = np.int16
        elif sample_width == 4:
            dtype = np.int32
        else:
            dtype = np.int16

        audio = np.frombuffer(raw, dtype=dtype)
        if n_channels > 1:
            audio = audio.reshape(-1, n_channels)

        sd.play(audio, samplerate=framerate, device=self.output_device)
        sd.wait()


# ----------------------------
# Platform adapter
# ----------------------------

class ReachyAdapter:
    """Minimal interface for Reachy motion and speech."""

    def say(self, text: str) -> None:
        raise NotImplementedError()

    def motion(self, motion_id: str, duration_s: float = 2.0) -> None:
        raise NotImplementedError()

    def wait(self, seconds: float) -> None:
        time.sleep(seconds)


class ReachyLiteVoiceAdapter(ReachyAdapter):
    """
    Reachy Mini Lite adapter (USB connection)
    with offline voice (pyttsx3 TTS + Vosk STT).
    """

    def __init__(self, mini: ReachyMini, voice: Optional[OfflineVoiceIO]) -> None:
        self.mini = mini
        self.voice = voice
        self._neutral()

    def say(self, text: str) -> None:
        print(f"\nReachy: {text}")
        if self.voice:
            try:
                self.voice.speak(text)
            except Exception as exc:
                print(f"  [TTS Warning] {exc}")

    def motion(self, motion_id: str, duration_s: float = 2.0) -> None:
        motions = {
            "gas_spin": self._motion_gas_spin,
            "fusion_snap": self._motion_fusion_snap,
            "random_walk": self._motion_random_walk,
            "convection_wave": self._motion_convection_wave,
            "magnetic_twist": self._motion_magnetic_twist,
            "solar_wind_shiver": self._motion_solar_wind_shiver,
        }
        motion_fn = motions.get(motion_id)
        if not motion_fn:
            return
        motion_fn(duration_s)

    # -- low-level motion helpers --

    def _goto(
        self,
        head_xyz_mm: Optional[tuple[float, float, float]] = None,
        antennas_deg: Optional[tuple[float, float]] = None,
        body_yaw_deg: Optional[float] = None,
        duration_s: float = 2.0,
        method: str = "minjerk",
    ) -> None:
        kwargs = {}
        if head_xyz_mm is not None:
            x, y, z = head_xyz_mm
            kwargs["head"] = create_head_pose(x=x, y=y, z=z, mm=True)
        if antennas_deg is not None:
            kwargs["antennas"] = np.deg2rad(np.array(antennas_deg))
        if body_yaw_deg is not None:
            kwargs["body_yaw"] = np.deg2rad(body_yaw_deg)
        if kwargs:
            self.mini.goto_target(duration=duration_s, method=method, **kwargs)

    def _neutral(self) -> None:
        self.mini.enable_motors()
        self._goto(head_xyz_mm=(0.0, 0.0, 5.0), antennas_deg=(0.0, 0.0), duration_s=1.0)

    # -- named motions --

    def _motion_gas_spin(self, duration_s: float) -> None:
        steps = 6
        radius = 8.0
        for i in range(steps):
            angle = 2 * np.pi * (i / steps)
            x = radius * np.cos(angle)
            y = radius * np.sin(angle)
            antennas = (20.0, -20.0) if i % 2 == 0 else (-20.0, 20.0)
            self._goto(head_xyz_mm=(x, y, 8.0), antennas_deg=antennas, duration_s=duration_s / steps)

    def _motion_fusion_snap(self, duration_s: float) -> None:
        self._goto(head_xyz_mm=(0.0, 0.0, 12.0), duration_s=duration_s * 0.6, method="ease_in_out")
        self._goto(head_xyz_mm=(0.0, 0.0, 2.0), duration_s=duration_s * 0.4, method="cartoon")

    def _motion_random_walk(self, duration_s: float) -> None:
        points = [(-6, 0, 6), (6, 4, 8), (-4, -6, 5), (4, -2, 9)]
        step = max(duration_s / len(points), 0.4)
        for x, y, z in points:
            self._goto(head_xyz_mm=(x, y, z), duration_s=step, method="linear")

    def _motion_convection_wave(self, duration_s: float) -> None:
        points = [(0, 0, 12), (6, 0, 8), (0, 0, 2), (-6, 0, 6)]
        step = max(duration_s / len(points), 0.5)
        for x, y, z in points:
            self._goto(head_xyz_mm=(x, y, z), duration_s=step)

    def _motion_magnetic_twist(self, duration_s: float) -> None:
        swings = [(-8, 0, 6), (8, 0, 6), (-8, 0, 6), (8, 0, 6)]
        step = max(duration_s / len(swings), 0.4)
        for i, (x, y, z) in enumerate(swings):
            antennas = (25.0, -25.0) if i % 2 == 0 else (-25.0, 25.0)
            self._goto(head_xyz_mm=(x, y, z), antennas_deg=antennas, duration_s=step)

    def _motion_solar_wind_shiver(self, duration_s: float) -> None:
        points = [(2, 0, 6), (-2, 0, 6), (0, 2, 6), (0, -2, 6)]
        step = max(duration_s / len(points), 0.2)
        for x, y, z in points:
            self._goto(head_xyz_mm=(x, y, z), duration_s=step, method="linear")


# ----------------------------
# Lesson data model
# ----------------------------

@dataclass
class LessonLevel:
    title: str
    goal: str
    physics: str
    reachy_asks: str
    correct_answer: str
    accepted_answers: List[str]
    motion_id: str
    motion_cue: str
    motion_duration_s: float = 2.0
    extra_facts: List[str] = field(default_factory=list)


# ----------------------------
# Lesson content
# ----------------------------

LEVELS: List[LessonLevel] = [
    LessonLevel(
        title="Level 1: The Foundation (Chemistry & Density)",
        goal="Understand that the Sun is a pressurized ball of gas, not a solid object.",
        physics=(
            "The Sun is a plasma. On Earth we have solids, liquids, and gases. "
            "Plasma is the 'fourth state' -- a gas so hot that electrons are stripped "
            "from atoms."
        ),
        reachy_asks="Is the Sun a solid rock like Earth, or a giant cloud of glowing soup?",
        correct_answer="Glowing soup (plasma).",
        accepted_answers=["plasma", "glowing soup", "hot gas", "ionized gas", "soup", "gas"],
        motion_id="gas_spin",
        motion_cue=(
            "Slow, fluid circular head motion to mimic a spinning ball of gas; "
            "wiggle antennas quickly for vibrating atoms."
        ),
        motion_duration_s=3.0,
        extra_facts=[
            "Plasma is made of charged particles (ions and free electrons).",
        ],
    ),
    LessonLevel(
        title="Level 2: The Core (Nuclear Physics)",
        goal="Explain the strong nuclear force and fusion.",
        physics=(
            "At the core, gravity creates immense pressure. This overcomes the "
            "electrostatic repulsion between hydrogen protons, forcing them to fuse."
        ),
        reachy_asks=(
            "The Sun is heavy! If I squeeze two tiny pieces of Hydrogen together "
            "really hard, do they bounce away or become one big piece?"
        ),
        correct_answer="They become one (nuclear fusion).",
        accepted_answers=["fuse", "become one", "nuclear fusion", "they combine", "combine", "big piece", "one piece"],
        motion_id="fusion_snap",
        motion_cue=(
            "Head tilted back, then a sharp nod forward once -- like a hammer hitting a nail."
        ),
        motion_duration_s=1.5,
        extra_facts=[
            "Fusion reaction: 4 hydrogen nuclei become 1 helium nucleus plus energy.",
        ],
    ),
    LessonLevel(
        title="Level 3: The Radiative Zone (Photon Physics)",
        goal="Explain how energy moves through matter.",
        physics=(
            "Light particles (photons) try to leave the core but keep hitting dense "
            "atoms. This is a 'random walk.' It can take a photon 100,000 plus years "
            "to move just a few miles."
        ),
        reachy_asks="Light is fast, but the Sun is crowded! Does light move straight or zig-zag?",
        correct_answer="A crazy zig-zag (random walk).",
        accepted_answers=["zig zag", "zig-zag", "zigzag", "zig", "zag", "bounce around", "crazy"],
        motion_id="random_walk",
        motion_cue=(
            "Jerky head moves left/right/up/down in a confused sequence."
        ),
        motion_duration_s=2.5,
        extra_facts=[
            "Photons are constantly absorbed and re-emitted.",
        ],
    ),
    LessonLevel(
        title="Level 4: The Convection Zone (Thermodynamics)",
        goal="Explain heat transfer through fluid movement.",
        physics=(
            "Closer to the surface, the Sun acts like a lava lamp. Hot plasma rises, "
            "cools down, and sinks. This is convection."
        ),
        reachy_asks=(
            "Like bubbles in boiling pasta, does hot Sun-stuff move up or down?"
        ),
        correct_answer="Both. It rises, cools, and sinks.",
        accepted_answers=["both", "up and down", "rise and sink", "up then down", "down and up", "sink and rise"],
        motion_id="convection_wave",
        motion_cue=(
            "Vertical wave: up then forward then down then back to simulate rolling bubbles."
        ),
        motion_duration_s=3.0,
        extra_facts=[
            "Convection is a heat engine driven by temperature differences.",
        ],
    ),
    LessonLevel(
        title="Level 5: The Atmosphere & Magnetism (Electromagnetism)",
        goal="Explain why the Sun has 'weather' at all.",
        physics=(
            "Because the Sun is plasma (charged), its movement creates magnetic fields. "
            "The Sun rotates faster at the equator than at the poles, twisting magnetic "
            "lines like a rope."
        ),
        reachy_asks="The Sun acts like a giant magnet. What happens to a rope if you twist it?",
        correct_answer="It knots up and can snap (sunspots and flares).",
        accepted_answers=["knot", "snap", "twist too much", "tangle"],
        motion_id="magnetic_twist",
        motion_cue=(
            "Head tilts side-to-side while antennas spin in opposite directions."
        ),
        motion_duration_s=2.5,
        extra_facts=[
            "Sunspots are cooler, darker regions with strong magnetic fields.",
        ],
    ),
    LessonLevel(
        title="Level 6: The Solar Wind (Plasma Dynamics)",
        goal="Explain how the Sun's 'weather' reaches Earth.",
        physics=(
            "The corona is so hot that particles escape the Sun's gravity. This creates "
            "the heliosphere, the bubble of space the Sun controls."
        ),
        reachy_asks=(
            "Does the Sun's wind blow cold like winter, or is it made of electric fire?"
        ),
        correct_answer="Electric particles (a plasma wind).",
        accepted_answers=["electric particles", "charged particles", "plasma wind", "electric fire", "fire", "electric"],
        motion_id="solar_wind_shiver",
        motion_cue=(
            "Look directly at the group and shiver with rapid, tiny head shakes."
        ),
        motion_duration_s=2.0,
        extra_facts=[
            "Solar wind can trigger auroras when it hits Earth's magnetosphere.",
        ],
    ),
]


# ----------------------------
# Q&A and interactive layer
# ----------------------------

@dataclass
class QAEntry:
    keywords: List[str]
    response: str


FAQ_ENTRIES: List[QAEntry] = [
    QAEntry(
        keywords=["plasma", "ionized", "charged particles"],
        response="Plasma is a super-hot gas where electrons are freed from atoms.",
    ),
    QAEntry(
        keywords=["shine", "light", "energy", "fusion"],
        response="Fusion in the core releases energy that slowly escapes as light and heat.",
    ),
    QAEntry(
        keywords=["sunspot", "spot", "dark"],
        response="A sunspot is a cooler, darker area with very strong magnetic fields.",
    ),
    QAEntry(
        keywords=["solar wind", "wind", "heliosphere"],
        response="The solar wind is a stream of charged particles flowing out from the Sun.",
    ),
    QAEntry(
        keywords=["age", "old", "formed"],
        response="The Sun is about 4.6 billion years old.",
    ),
    QAEntry(
        keywords=["magnetic", "magnetism", "flare", "eruption"],
        response="Moving plasma twists magnetic fields, which can snap and release flares.",
    ),
    QAEntry(
        keywords=["core", "gravity", "pressure"],
        response="In the core, gravity creates huge pressure that makes fusion possible.",
    ),
    QAEntry(
        keywords=["convection", "rise", "sink"],
        response="Hot plasma rises, cools, and sinks in a rolling convection cycle.",
    ),
    QAEntry(
        keywords=["radiative", "photon", "zig"],
        response="Photons bounce around in a random walk before escaping the Sun.",
    ),
    QAEntry(
        keywords=["how big", "size", "diameter", "sun"],
        response="The Sun is huge -- about 1.39 million kilometers wide.",
    ),
    QAEntry(
        keywords=["how big", "size", "diameter", "earth"],
        response="Earth is about 12,742 kilometers wide.",
    ),
    QAEntry(
        keywords=["distance", "far", "sun", "earth", "away"],
        response="The Sun is about 150 million kilometers away from Earth.",
    ),
    QAEntry(
        keywords=["hot", "temperature", "surface"],
        response="The Sun's surface is about 5,500 degrees Celsius.",
    ),
    QAEntry(
        keywords=["hot", "temperature", "core"],
        response="The Sun's core is about 15 million degrees Celsius.",
    ),
    QAEntry(
        keywords=["light", "travel", "sun", "earth", "time", "minutes"],
        response="Light from the Sun reaches Earth in about 8 minutes 20 seconds.",
    ),
    QAEntry(
        keywords=["how fast", "speed", "light"],
        response="Light travels about 300,000 kilometers per second.",
    ),
]

SUGGESTED_TOPICS = [
    "plasma",
    "fusion",
    "sunspots",
    "solar wind",
    "magnetic fields",
    "convection",
    "Sun size",
    "Earth size",
    "distance to Sun",
    "Sun temperature",
    "light travel time",
]


def normalize(text: str) -> str:
    return "".join(ch.lower() for ch in text if ch.isalnum() or ch.isspace()).strip()


def tokenize(text: str) -> List[str]:
    return [t for t in normalize(text).split() if t]


# Mapping spoken number words to digits
SPOKEN_NUMBERS: Dict[str, str] = {
    "one": "1", "won": "1", "want": "1",
    "two": "2", "to": "2", "too": "2",
    "three": "3", "tree": "3", "free": "3",
    "four": "4", "for": "4", "fore": "4",
    "five": "5",
    "six": "6", "sex": "6", "sits": "6",
}


def parse_menu_choice(raw: str, option_keywords: Dict[str, str]) -> Optional[str]:
    """
    Parse typed or spoken input into a menu choice number.

    Checks in order:
      1. Exact digit string ("1", "2", ...)
      2. Spoken number word ("one", "two", ...)
      3. Keyword phrases ("full lesson", "single level", "question", "exit", ...)

    Args:
        raw: The raw user input (typed or from STT).
        option_keywords: Mapping of keyword phrase -> choice number.

    Returns:
        The choice number as a string, or None if not recognised.
    """
    text = normalize(raw)
    if not text:
        return None

    # 1. Exact digit
    if text in option_keywords.values():
        return text

    # 2. Spoken number words (check each word in the input)
    for word in text.split():
        if word in SPOKEN_NUMBERS:
            digit = SPOKEN_NUMBERS[word]
            if digit in option_keywords.values():
                return digit

    # 3. Keyword phrases
    for phrase, choice in option_keywords.items():
        if phrase in text:
            return choice

    return None


# Keywords for the main menu (maps phrase -> choice number)
MAIN_MENU_KEYWORDS: Dict[str, str] = {
    "full lesson": "1",
    "all levels": "1",
    "run full": "1",
    "start lesson": "1",
    "all six": "1",
    "single level": "2",
    "pick a level": "2",
    "choose a level": "2",
    "one level": "2",
    "select level": "2",
    "ask a question": "3",
    "question": "3",
    "ask": "3",
    "exit": "4",
    "quit": "4",
    "bye": "4",
    "goodbye": "4",
    "done": "4",
}

# Keywords for level selection (maps phrase -> level number)
LEVEL_KEYWORDS: Dict[str, str] = {
    "foundation": "1",
    "chemistry": "1",
    "density": "1",
    "core": "2",
    "nuclear": "2",
    "fusion": "2",
    "radiative": "3",
    "photon": "3",
    "random walk": "3",
    "convection": "4",
    "thermodynamics": "4",
    "lava lamp": "4",
    "magnetism": "5",
    "atmosphere": "5",
    "electromagnetism": "5",
    "magnetic": "5",
    "solar wind": "6",
    "plasma dynamics": "6",
    "heliosphere": "6",
}


def match_faq(question: str) -> Optional[str]:
    tokens = set(tokenize(question))
    best: Optional[QAEntry] = None
    best_score = 0
    for entry in FAQ_ENTRIES:
        score = 0
        for kw in entry.keywords:
            kw_tokens = set(tokenize(kw))
            if kw_tokens.issubset(tokens):
                score += 2
            elif kw in normalize(question):
                score += 1
        if score > best_score:
            best_score = score
            best = entry
    if best and best_score >= 2:
        return best.response
    return None


def is_correct_answer(user: str, accepted_answers: List[str]) -> bool:
    user_tokens = set(tokenize(user))
    user_text = normalize(user)
    for ans in accepted_answers:
        ans_text = normalize(ans)
        if ans_text and ans_text in user_text:
            return True
        ans_tokens = set(tokenize(ans))
        if ans_tokens and ans_tokens.issubset(user_tokens):
            return True
    return False


def get_user_text(
    voice: Optional[OfflineVoiceIO],
    adapter: Optional[ReachyAdapter],
    voice_prompt: str = "",
    terminal_prompt: str = "> ",
) -> str:
    """
    Get input from the user -- typed text, or speech if they press Enter.

    Args:
        voice: OfflineVoiceIO instance (or None for text-only).
        adapter: ReachyAdapter to speak the voice_prompt aloud.
        voice_prompt: What Reachy says out loud before waiting for input.
        terminal_prompt: What appears in the terminal input line.
    """
    if voice_prompt and adapter:
        adapter.say(voice_prompt)
    typed = input(terminal_prompt).strip()
    if typed:
        return typed
    if not voice:
        return ""
    try:
        if adapter:
            adapter.say("I'm listening.")
        return voice.listen()
    except Exception as exc:
        print(f"  [STT Warning] {exc}")
        return ""


def ask_and_answer(
    adapter: ReachyAdapter,
    voice: Optional[OfflineVoiceIO],
    prompt: str,
    correct: str,
    accepted: List[str],
) -> None:
    adapter.say(prompt)
    user = get_user_text(
        voice, adapter,
        voice_prompt="What do you think?",
        terminal_prompt="Your answer > ",
    )
    if not user:
        adapter.say(f"The answer is: {correct}")
        return
    if is_correct_answer(user, accepted):
        adapter.say("Nice! You got it.")
        return
    adapter.say("Not quite. Try one more time.")
    user_retry = get_user_text(
        voice, adapter,
        voice_prompt="Give it another try.",
        terminal_prompt="Your answer > ",
    )
    if user_retry and is_correct_answer(user_retry, accepted):
        adapter.say("Nice! You got it.")
    else:
        adapter.say(f"The answer is: {correct}")


def deliver_level(adapter: ReachyAdapter, voice: Optional[OfflineVoiceIO], level: LessonLevel) -> None:
    adapter.say(level.title)
    adapter.say(level.goal)
    adapter.say(level.physics)
    ask_and_answer(adapter, voice, level.reachy_asks, level.correct_answer, level.accepted_answers)
    adapter.motion(level.motion_id, level.motion_duration_s)
    for fact in level.extra_facts:
        adapter.say(f"Bonus fact: {fact}")


# ----------------------------
# Program flow
# ----------------------------

def program_menu(adapter: ReachyAdapter) -> None:
    adapter.say("What would you like to do?")
    adapter.say("Option 1: Run full lesson, levels 1 through 6.")
    adapter.say("Option 2: Run a single level.")
    adapter.say("Option 3: Ask a question.")
    adapter.say("Option 4: Exit.")


def select_level(adapter: ReachyAdapter, voice: Optional[OfflineVoiceIO]) -> Optional[LessonLevel]:
    adapter.say("Pick a level:")
    for i, lvl in enumerate(LEVELS, start=1):
        adapter.say(f"Level {i}: {lvl.title}")
    raw = get_user_text(
        voice, adapter,
        voice_prompt="Which level would you like?",
        terminal_prompt="Level number > ",
    )
    if not raw:
        return None
    choice = parse_menu_choice(raw, LEVEL_KEYWORDS)
    if choice is None:
        # Try as a plain digit
        cleaned = normalize(raw)
        if cleaned.isdigit():
            choice = cleaned
        else:
            return None
    idx = int(choice)
    if 1 <= idx <= len(LEVELS):
        return LEVELS[idx - 1]
    return None


def question_loop(adapter: ReachyAdapter, voice: Optional[OfflineVoiceIO]) -> None:
    adapter.say("Ask me anything about the Sun or the solar system!")
    adapter.say("Say 'topics' for suggestions, or 'back' to return to the menu.")
    first = True
    while True:
        if first:
            prompt = "Go ahead, ask me something!"
            first = False
        else:
            prompt = "Any other questions?"
        question = get_user_text(
            voice, adapter,
            voice_prompt=prompt,
            terminal_prompt="Your question > ",
        )
        if normalize(question) in {"back", "exit", "quit", "menu"}:
            adapter.say("Okay, let's go back to the menu.")
            break
        if normalize(question) in {"topics", "help"}:
            adapter.say("Here are some topics you can ask about: " + ", ".join(SUGGESTED_TOPICS))
            continue
        if not question:
            adapter.say("I didn't hear anything. Try again, or say 'back' to return to the menu.")
            continue

        answer = match_faq(question)
        if answer:
            adapter.say(answer)
        else:
            adapter.say(
                "I'm not sure about that one. Try asking about: "
                + ", ".join(SUGGESTED_TOPICS[:5])
            )


def build_voice(
    input_device: Optional[int] = None,
    output_device: Optional[int] = None,
) -> Optional[OfflineVoiceIO]:
    """Try to initialise offline voice; fall back to text-only gracefully."""
    try:
        voice = OfflineVoiceIO(
            input_device=input_device,
            output_device=output_device,
        )
        if input_device is not None or output_device is not None:
            parts = []
            if input_device is not None:
                parts.append(f"mic=device {input_device}")
            if output_device is not None:
                parts.append(f"speaker=device {output_device}")
            print(f"[Voice] Using Reachy audio: {', '.join(parts)}")
        print("[Voice] Offline TTS + STT ready.")
        return voice
    except Exception as exc:
        print(f"[Voice Warning] Offline voice disabled: {exc}")
        print("[Voice] Falling back to text-only mode (type your answers).")
        return None


def run() -> None:
    print("""
    =============================================
      Reachy Mini Lite  --  Solar System Courseware
      USB Connection + Offline Voice (TTS & STT)
    =============================================

    Make sure your Reachy Mini Lite is connected
    via USB before continuing.
    """)

    # Auto-detect Reachy's built-in mic and speaker
    input_dev, output_dev = detect_reachy_audio()

    # Quick mic test so we know immediately if it's working
    test_microphone(input_dev)

    voice = build_voice(input_device=input_dev, output_device=output_dev)

    # Connect to the physical Reachy Mini Lite via USB (default connection)
    with ReachyMini() as mini:
        adapter = ReachyLiteVoiceAdapter(mini, voice)
        adapter.say(
            "Hello! I'm Reachy. Let's explore the Sun, from the core to the solar wind."
        )

        while True:
            program_menu(adapter)
            raw = get_user_text(
                voice, adapter,
                voice_prompt="Pick a number, or tell me what you'd like to do.",
                terminal_prompt="Your choice > ",
            )
            choice = parse_menu_choice(raw, MAIN_MENU_KEYWORDS)

            if choice is None:
                adapter.say("I didn't catch that. Please say a number from 1 to 4, or describe what you'd like to do.")
                continue

            if choice == "1":
                adapter.say("Great! Let's run through all six levels.")
                for level in LEVELS:
                    deliver_level(adapter, voice, level)
                    adapter.wait(0.5)
                adapter.say("Great job completing all six levels!")
            elif choice == "2":
                level = select_level(adapter, voice)
                if level:
                    deliver_level(adapter, voice, level)
                else:
                    adapter.say("I didn't recognise that level. Let's go back to the menu.")
            elif choice == "3":
                question_loop(adapter, voice)
            elif choice == "4":
                adapter.say("Thanks for learning with me. See you next time!")
                break


if __name__ == "__main__":
    run()
