"""
Reachy Mini Solar System Program (Simulation-first)

This module defines a complete, lesson-driven experience that teaches
solar physics using scripted prompts, interactive Q&A, and motion cues.
It targets Simulation now, with a clean adapter layer for Lite/Wireless later.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Tuple
import textwrap
import time


# ----------------------------
# Platform adapter interface
# ----------------------------

class ReachyAdapter:
    """
    Minimal interface for Reachy motion and speech.
    Replace with SDK calls for Lite/Wireless later.
    """

    def say(self, text: str) -> None:
        raise NotImplementedError()

    def motion(self, name: str, duration_s: float = 2.0) -> None:
        raise NotImplementedError()

    def wait(self, seconds: float) -> None:
        time.sleep(seconds)


class SimulationAdapter(ReachyAdapter):
    """
    Simulation adapter: prints text and motion cues.
    Replace with real SDK calls when ready.
    """

    def say(self, text: str) -> None:
        print(f"\nReachy: {text}")

    def motion(self, name: str, duration_s: float = 2.0) -> None:
        print(f"[Motion] {name} ({duration_s:.1f}s)")
        self.wait(duration_s)


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

FAQ: Dict[str, str] = {
    "what is plasma": "Plasma is a super-hot gas where electrons are freed from atoms.",
    "why does the sun shine": "Fusion in the core releases energy that slowly escapes as light and heat.",
    "what is a sunspot": "A cooler, darker area with very strong magnetic fields.",
    "what is the solar wind": "A stream of charged particles flowing out from the Sun.",
    "how old is the sun": "About 4.6 billion years old.",
}


def normalize(text: str) -> str:
    return "".join(ch.lower() for ch in text if ch.isalnum() or ch.isspace()).strip()


def match_faq(question: str) -> Optional[str]:
    key = normalize(question)
    for k, v in FAQ.items():
        if k in key:
            return v
    return None


def ask_and_answer(adapter: ReachyAdapter, prompt: str, correct: str) -> None:
    adapter.say(prompt)
    user = input("Your answer: ").strip()
    if not user:
        adapter.say(f"The answer is: {correct}")
        return
    if normalize(user) in normalize(correct):
        adapter.say("Nice! You got it.")
    else:
        adapter.say(f"Close! The answer is: {correct}")


def deliver_level(adapter: ReachyAdapter, level: LessonLevel) -> None:
    adapter.say(level.title)
    adapter.say(level.goal)
    adapter.say(level.physics)
    ask_and_answer(adapter, level.reachy_asks, level.correct_answer)
    adapter.motion(level.motion_cue, level.motion_duration_s)
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
    while True:
        question = input("Question (or 'back'): ").strip()
        if normalize(question) in {"back", "exit", "quit"}:
            break
        answer = match_faq(question)
        if answer:
            adapter.say(answer)
        else:
            adapter.say(
                "Great question! I don't have that answer yet, but I can learn it."
            )


def run() -> None:
    adapter = SimulationAdapter()
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
