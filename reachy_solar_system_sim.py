"""
Reachy Mini Solar System Program (Simulation movement enabled)

This is a simulator-ready version that uses the Reachy Mini Python SDK
to move the robot in the Control Dashboard Simulation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional
import time

import numpy as np
from reachy_mini import ReachyMini
from reachy_mini.utils import create_head_pose


# ----------------------------
# Platform adapter interface
# ----------------------------

class ReachyAdapter:
    """
    Minimal interface for Reachy motion and speech.
    """

    def say(self, text: str) -> None:
        raise NotImplementedError()

    def motion(self, motion_id: str, duration_s: float = 2.0) -> None:
        raise NotImplementedError()

    def wait(self, seconds: float) -> None:
        time.sleep(seconds)


class ReachyMiniAdapter(ReachyAdapter):
    """
    Reachy Mini SDK adapter for the Simulation.
    """

    def __init__(self, mini: ReachyMini) -> None:
        self.mini = mini
        self._neutral()

    def say(self, text: str) -> None:
        # Keep speech in terminal for now (TTS can be added later).
        print(f"\nReachy: {text}")

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
            "Plasma is the 'fourth state'—a gas so hot that electrons are stripped "
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
            "Head tilted back, then a sharp nod forward once—like a hammer hitting a nail."
        ),
        motion_duration_s=1.5,
        extra_facts=[
            "Fusion reaction: 4 hydrogen nuclei → 1 helium nucleus + energy.",
        ],
    ),
    LessonLevel(
        title="Level 3: The Radiative Zone (Photon Physics)",
        goal="Explain how energy moves through matter.",
        physics=(
            "Light particles (photons) try to leave the core but keep hitting dense "
            "atoms. This is a 'random walk.' It can take a photon 100,000+ years "
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
            "Vertical wave: up → forward → down → back to simulate rolling bubbles."
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
        response="The Sun is huge—about 1.39 million kilometers wide.",
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
        response="The Sun’s surface is about 5,500°C (10,000°F).",
    ),
    QAEntry(
        keywords=["hot", "temperature", "core"],
        response="The Sun’s core is about 15 million°C.",
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


def build_knowledge_base(levels: List[LessonLevel]) -> str:
    lines: List[str] = []
    for level in levels:
        lines.append(level.title)
        lines.append(f"Goal: {level.goal}")
        lines.append(f"Physics: {level.physics}")
        if level.extra_facts:
            for fact in level.extra_facts:
                lines.append(f"Fact: {fact}")
        lines.append("")
    lines.append("Q&A Facts:")
    for entry in FAQ_ENTRIES:
        lines.append(f"- {entry.response}")
    return "\n".join(lines).strip()


def ask_and_answer(adapter: ReachyAdapter, prompt: str, correct: str, accepted: List[str]) -> None:
    adapter.say(prompt)
    user = input("Your answer: ").strip()
    if not user:
        adapter.say(f"The answer is: {correct}")
        return
    if is_correct_answer(user, accepted):
        adapter.say("Nice! You got it.")
        return
    adapter.say("Not quite. Try one more time.")
    user_retry = input("Your answer (second try): ").strip()
    if user_retry and is_correct_answer(user_retry, accepted):
        adapter.say("Nice! You got it.")
    else:
        adapter.say(f"The answer is: {correct}")


def deliver_level(adapter: ReachyAdapter, level: LessonLevel) -> None:
    adapter.say(level.title)
    adapter.say(level.goal)
    adapter.say(level.physics)
    ask_and_answer(adapter, level.reachy_asks, level.correct_answer, level.accepted_answers)
    adapter.motion(level.motion_id, level.motion_duration_s)
    for fact in level.extra_facts:
        adapter.say(f"Bonus fact: {fact}")


# ----------------------------
# Program flow
# ----------------------------

def program_menu() -> None:
    print("\nSolar System Courseware")
    print("1) Run full lesson (levels 1-6)")
    print("2) Run a single level")
    print("3) Ask a question")
    print("4) Exit")


def select_level() -> Optional[LessonLevel]:
    print("\nPick a level:")
    for i, lvl in enumerate(LEVELS, start=1):
        print(f"{i}) {lvl.title}")
    raw = input("Level number: ").strip()
    if not raw.isdigit():
        return None
    idx = int(raw)
    if 1 <= idx <= len(LEVELS):
        return LEVELS[idx - 1]
    return None


def question_loop(adapter: ReachyAdapter) -> None:
    adapter.say("Ask me anything about the Sun or the solar system!")
    off_topic_mode = False
    while True:
        question = input("Question (or 'topics'/'back'): ").strip()
        if normalize(question) in {"back", "exit", "quit"}:
            break
        if normalize(question) in {"course", "lesson"}:
            off_topic_mode = False
            adapter.say("Back to the lesson. Ask me a Sun or solar system question!")
            continue
        if normalize(question) in {"topics", "help"}:
            adapter.say("Try: " + ", ".join(SUGGESTED_TOPICS))
            continue
        if off_topic_mode:
            adapter.say(
                "I can only chat about the Sun and solar system right now. "
                "Type 'course' to return to the lesson."
            )
            continue

        answer = match_faq(question)
        if answer:
            adapter.say(answer)
            continue

        adapter.say(
            "That sounds off-topic. Want to keep learning about the Sun or chat freely?"
        )
        choice = input("Type 'course' or 'chat': ").strip().lower()
        if choice == "chat":
            off_topic_mode = True
            adapter.say(
                "Off-topic chat isn't available offline. "
                "Ask a Sun question or type 'topics'."
            )
        else:
            adapter.say("Great! Try: " + ", ".join(SUGGESTED_TOPICS))


def run() -> None:
    with ReachyMini(connection_mode="localhost_only") as mini:
        adapter = ReachyMiniAdapter(mini)
        adapter.say(
            "Hello! I'm Reachy. Let's explore the Sun, from the core to the solar wind."
        )

        while True:
            program_menu()
            choice = input("Choose: ").strip()
            if choice == "1":
                for level in LEVELS:
                    deliver_level(adapter, level)
                    adapter.wait(0.5)
            elif choice == "2":
                level = select_level()
                if level:
                    deliver_level(adapter, level)
                else:
                    print("Invalid level.")
            elif choice == "3":
                question_loop(adapter)
            elif choice == "4":
                adapter.say("Thanks for learning with me. See you next time!")
                break
            else:
                print("Invalid choice.")


if __name__ == "__main__":
    run()
