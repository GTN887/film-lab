"""Emotion, sensory, and environment desk for Writing Studio.

Genre is story shape. This module is how actors feel the room:
emotion → senses → environment, then the page.
"""

from __future__ import annotations

from dataclasses import dataclass, field

EMOTIONS: tuple[str, ...] = (
    "tenderness",
    "longing",
    "desire",
    "warmth",
    "safety",
    "playfulness",
    "amusement",
    "tension",
    "irritation",
    "anger",
    "grief",
    "shame",
    "fear",
    "dread",
    "relief",
    "guilt",
    "jealousy",
    "awe",
    "loneliness",
    "hope",
    "numbness",
    "pride",
    "vulnerability",
    "none / unspecified",
)

RELATIONSHIP_TEMPS: tuple[str, ...] = (
    "newlywed tenderness",
    "easy familiarity",
    "playful heat",
    "quiet aftercare",
    "tension under courtesy",
    "cold argument",
    "grief in the same bed",
    "repair after a fight",
    "distance in the same room",
    "protective",
    "charged silence",
    "custom",
)

SENSE_KEYS: tuple[str, ...] = ("touch", "smell", "taste", "hearing", "sight")

SENSE_LABELS: dict[str, str] = {
    "touch": "Touch / tactile",
    "smell": "Smell / scent",
    "taste": "Taste",
    "hearing": "Hearing / soundscape",
    "sight": "Sight (balanced)",
}

SENSE_CHOICES: tuple[str, ...] = tuple(SENSE_LABELS[k] for k in SENSE_KEYS)
LABEL_TO_SENSE: dict[str, str] = {label: key for key, label in SENSE_LABELS.items()}

SENSE_CUES: dict[str, str] = {
    "touch": "skin, fabric, temperature, pressure, weight — what the body registers",
    "smell": "scent in the room: skin, rain, coffee, laundry, dust, heat",
    "taste": "mouth: toothpaste, whiskey, coffee, salt on a lip — only if it belongs here",
    "hearing": "soundscape: rain, kettle, radiator, breath, a street, the bed frame",
    "sight": "keep sight present but do not let it dominate the other enabled senses",
}

TIMES_OF_DAY: tuple[str, ...] = (
    "pre-dawn",
    "morning",
    "late morning",
    "noon",
    "afternoon",
    "golden hour",
    "dusk",
    "night",
    "late night",
)

WEATHERS: tuple[str, ...] = (
    "clear",
    "humid",
    "rain",
    "storm",
    "wind",
    "snow",
    "heat",
    "cold",
)

LIGHTS: tuple[str, ...] = (
    "warm lamp",
    "cool moonlight",
    "harsh noon",
    "neon",
    "overcast window",
    "candle",
    "fluorescent kitchen",
    "golden hour",
    "practical TV glow",
    "wet street light",
)

DEFAULT_SENSES: tuple[str, ...] = ("touch", "hearing", "sight")


def clamp_intensity(value: float | int | None) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return 0.55
    return max(0.0, min(1.0, number))


def parse_enabled_senses(raw: list[str] | None) -> list[str]:
    found: list[str] = []
    for item in raw or []:
        key = LABEL_TO_SENSE.get(str(item).strip(), str(item).strip())
        if key in SENSE_KEYS and key not in found:
            found.append(key)
    return found


def sense_labels_for(keys: list[str] | None) -> list[str]:
    return [SENSE_LABELS[k] for k in (keys or []) if k in SENSE_LABELS]


@dataclass
class SensoryBrief:
    primary_emotion: str = "tenderness"
    secondary_emotion: str = "longing"
    intensity: float = 0.55
    inner_state: str = ""
    outer_behavior: str = ""
    relationship_temp: str = "newlywed tenderness"
    enabled_senses: list[str] = field(default_factory=lambda: list(DEFAULT_SENSES))
    touch_notes: str = ""
    smell_notes: str = ""
    taste_notes: str = ""
    hearing_notes: str = ""
    sight_notes: str = ""
    sensory_pass: bool = False
    location: str = "INT. BEDROOM - NIGHT"
    time_of_day: str = "night"
    weather: str = "clear"
    light: str = "warm lamp"
    ambient_sound: str = ""
    blocking: str = ""
    props: str = ""

    def __post_init__(self) -> None:
        self.intensity = clamp_intensity(self.intensity)
        self.enabled_senses = parse_enabled_senses(self.enabled_senses) or list(DEFAULT_SENSES)

    def notes_for(self, key: str) -> str:
        return {
            "touch": self.touch_notes,
            "smell": self.smell_notes,
            "taste": self.taste_notes,
            "hearing": self.hearing_notes,
            "sight": self.sight_notes,
        }.get(key, "")


@dataclass(frozen=True)
class SenseEnvPreset:
    id: str
    label: str
    brief: SensoryBrief


def _preset(gid: str, label: str, **kwargs: object) -> SenseEnvPreset:
    return SenseEnvPreset(gid, label, SensoryBrief(**kwargs))  # type: ignore[arg-type]


SENSE_PRESETS: tuple[SenseEnvPreset, ...] = (
    _preset(
        "warm_bedroom_newlywed",
        "Warm bedroom newlywed",
        primary_emotion="tenderness",
        secondary_emotion="longing",
        intensity=0.6,
        inner_state="Wants to stay. The hard thing is already said; the body has not caught up.",
        outer_behavior="Still. Small practical talk. A hand finds the sheet, not a speech.",
        relationship_temp="newlywed tenderness",
        enabled_senses=["touch", "smell", "hearing", "sight"],
        touch_notes="Cotton sheet, warm lamp on skin, wedding-band metal, the weight of another adult in the bed.",
        smell_notes="Clean laundry, skin, a little heat from the lamp.",
        hearing_notes="Street hush, radiator click, two people breathing in one room.",
        sight_notes="Lamp pool. Do not light the whole room. Faces and bands first.",
        sensory_pass=True,
        location="INT. BEDROOM - NIGHT",
        time_of_day="night",
        weather="clear",
        light="warm lamp",
        ambient_sound="street hush, radiator, breath",
        blocking="They share the bed. Faces close. One could leave and does not.",
        props="sheets, wedding bands, lamp, his shirt on the chair",
    ),
    _preset(
        "cold_argument_kitchen",
        "Cold argument kitchen",
        primary_emotion="irritation",
        secondary_emotion="tenderness",
        intensity=0.72,
        inner_state="Afraid this is the fight that counts. Still in love, which makes it worse.",
        outer_behavior="Busy with the kettle. Will not look. Voice stays even.",
        relationship_temp="cold argument",
        enabled_senses=["touch", "smell", "hearing", "sight"],
        touch_notes="Cold counter, mug handle, the space of the island between them.",
        smell_notes="Coffee gone a little burnt. Morning kitchen.",
        hearing_notes="Kettle, fridge hum, a mug set down too carefully.",
        sight_notes="Harsh morning. Keep the island in frame. Do not beautify the fight.",
        sensory_pass=True,
        location="INT. KITCHEN - MORNING",
        time_of_day="morning",
        weather="clear",
        light="fluorescent kitchen",
        ambient_sound="kettle, fridge, street starting",
        blocking="Island between them. She faces the window. He faces her back.",
        props="two mugs, cold coffee, keys, the second chair unused",
    ),
    _preset(
        "rain_outside_window",
        "Rain outside window",
        primary_emotion="longing",
        secondary_emotion="grief",
        intensity=0.5,
        inner_state="A day they will not name sits in the room with them.",
        outer_behavior="One watches the glass. The other stays on the bed.",
        relationship_temp="charged silence",
        enabled_senses=["touch", "smell", "hearing", "sight"],
        touch_notes="Cold pane. Warm sheet behind them. Rain-sound in the fingers.",
        smell_notes="Wet air under the sash. The room still smells like sleep.",
        hearing_notes="Rain on the glass is the scene. Let it work between lines.",
        sight_notes="Street shine through wet glass. Interior stays darker than the rain.",
        sensory_pass=True,
        location="INT. BEDROOM - NIGHT (rain on the glass)",
        time_of_day="night",
        weather="rain",
        light="wet street light",
        ambient_sound="rain on the pane, a car, then nothing",
        blocking="One at the window, one on the bed. The gap is the blocking.",
        props="wet glass, sheet, street shine, a glass of water",
    ),
    _preset(
        "aftercare_lamp",
        "Aftercare lamp",
        primary_emotion="relief",
        secondary_emotion="tenderness",
        intensity=0.42,
        inner_state="Still in the body. Not ready for the next sentence of the day.",
        outer_behavior="A hand on a back. Quiet. Water, then the lamp stays on.",
        relationship_temp="quiet aftercare",
        enabled_senses=["touch", "smell", "hearing", "sight"],
        touch_notes="Skin cooling. Sheet weight. The ordinary kindness of a palm.",
        smell_notes="Heat leaving the room. Clean sweat, laundry.",
        hearing_notes="Breath settling. A glass. No performance.",
        sight_notes="Lamp only. Aftercare is a held wide, not a cutaway.",
        sensory_pass=True,
        location="INT. BEDROOM - NIGHT",
        time_of_day="late night",
        weather="clear",
        light="warm lamp",
        ambient_sound="settling building, distant traffic",
        blocking="They stay in the same bed. No one reaches for a phone.",
        props="sheets, water glass, lamp, wedding bands",
    ),
)

PRESET_BY_LABEL: dict[str, SenseEnvPreset] = {p.label: p for p in SENSE_PRESETS}
PRESET_LABELS: tuple[str, ...] = tuple(p.label for p in SENSE_PRESETS)
DEFAULT_SENSE_PRESET = "Warm bedroom newlywed"


def preset_brief(label: str | None) -> SensoryBrief:
    spec = PRESET_BY_LABEL.get((label or "").strip())
    if not spec:
        return SensoryBrief()
    src = spec.brief
    return SensoryBrief(
        primary_emotion=src.primary_emotion,
        secondary_emotion=src.secondary_emotion,
        intensity=src.intensity,
        inner_state=src.inner_state,
        outer_behavior=src.outer_behavior,
        relationship_temp=src.relationship_temp,
        enabled_senses=list(src.enabled_senses),
        touch_notes=src.touch_notes,
        smell_notes=src.smell_notes,
        taste_notes=src.taste_notes,
        hearing_notes=src.hearing_notes,
        sight_notes=src.sight_notes,
        sensory_pass=src.sensory_pass,
        location=src.location,
        time_of_day=src.time_of_day,
        weather=src.weather,
        light=src.light,
        ambient_sound=src.ambient_sound,
        blocking=src.blocking,
        props=src.props,
    )


def _mode_craft(mode: str, sensory_pass: bool) -> str:
    if mode == "screenplay":
        craft = (
            "SCREENPLAY CRAFT: Keep dialogue playable, short, and subtextual. "
            "Put sensory and environment detail in ACTION LINES and sluglines — "
            "never stuff novel paragraphs into dialogue. Parentheticals stay small."
        )
    elif mode == "novel":
        craft = (
            "NOVEL CRAFT: Full sensory immersion. Let the room work on the body "
            "before the thought. Close third or limited. Do not inventory senses; braid them."
        )
    elif mode == "book_to_screenplay":
        craft = (
            "ADAPTATION CRAFT: Translate novel senses into shootable action and blocking. "
            "Preserve the feeling of the room. Dialogue stays speakable; the environment "
            "lands in action, not monologue."
        )
    elif mode == "roleplay":
        craft = (
            "ROLEPLAY CRAFT: Answer in-character. React through body and senses to this "
            "environment — temperature, sound, distance — then the line. Short takes, playable aloud."
        )
    elif mode == "director_rewrite":
        craft = (
            "REWRITE CRAFT: Restage the existing scene so the actors feel the room. "
            "Keep voices. Move sensory load into action if this is Fountain; into prose if it is novel."
        )
    else:
        craft = "Write so the environment is felt, not described as a tourist."
    if sensory_pass:
        craft += (
            " SENSORY PASS is ON: mandatory multi-sense detail grounded in the chosen "
            "environment. Every beat should be felt in the body and the room. "
            "Do not invent a different set."
        )
    return craft


def sensory_system_addendum(brief: SensoryBrief, mode: str) -> str:
    return (
        f"Direct as if the actors feel the room. "
        f"Primary feeling: {brief.primary_emotion} (intensity {brief.intensity:.2f}). "
        f"{_mode_craft(mode, brief.sensory_pass)}"
    )


def sensory_prompt_block(
    brief: SensoryBrief,
    *,
    mode: str,
    intimacy_mode: str = "",
    content_intensity: float | None = None,
) -> str:
    """Compose emotion + senses + environment for the local prompt pack."""
    enabled = brief.enabled_senses or list(DEFAULT_SENSES)
    lines = [
        "DIRECTOR BRIEF (emotion → senses → environment → genre → page)",
        "",
        "Emotion & feeling",
        f"- Primary: {brief.primary_emotion or 'unspecified'} (intensity {brief.intensity:.2f} on 0–1)",
        f"- Secondary / conflicting: {brief.secondary_emotion or 'none'}",
        f"- Relationship temperature: {brief.relationship_temp or 'unspecified'}",
    ]
    if (brief.inner_state or "").strip():
        lines.append(f"- Inner state: {brief.inner_state.strip()}")
    if (brief.outer_behavior or "").strip():
        lines.append(f"- Outer behavior: {brief.outer_behavior.strip()}")
    if (brief.inner_state or "").strip() or (brief.outer_behavior or "").strip():
        lines.append(
            "- Subtext: play the gap between inner state and outer behavior. Do not explain it."
        )
    lines.append("")
    lines.append("Senses (enabled — write these; skip the rest unless the room forces them)")
    for key in SENSE_KEYS:
        if key not in enabled:
            continue
        note = (brief.notes_for(key) or "").strip() or SENSE_CUES[key]
        lines.append(f"- {SENSE_LABELS[key]}: {note}")
    skipped = [SENSE_LABELS[k] for k in SENSE_KEYS if k not in enabled]
    if skipped:
        lines.append(f"- Not required this pass: {', '.join(skipped)}")
    if "sight" in enabled:
        lines.append(
            "- Sight stays in the mix but must not crowd out touch, smell, taste, or sound when those are on."
        )
    lines.extend(
        [
            "",
            "Environment (couple every enabled sense to this set — do not change rooms)",
            f"- Location / set: {brief.location or 'unspecified'}",
            f"- Time of day: {brief.time_of_day or 'unspecified'}",
            f"- Weather: {brief.weather or 'unspecified'}",
            f"- Light quality: {brief.light or 'unspecified'}",
        ]
    )
    if (brief.ambient_sound or "").strip():
        lines.append(f"- Ambient sound: {brief.ambient_sound.strip()}")
    if (brief.blocking or "").strip():
        lines.append(f"- Spatial blocking: {brief.blocking.strip()}")
    if (brief.props or "").strip():
        lines.append(f"- Props that trigger senses: {brief.props.strip()}")
    lines.extend(["", _mode_craft(mode, brief.sensory_pass)])
    if intimacy_mode:
        from film_lab.intimacy import intimacy_sensory_addendum

        extra = intimacy_sensory_addendum(intimacy_mode, brief.sensory_pass)
        if extra:
            lines.append(extra)
    if content_intensity is not None:
        from film_lab.intensity import intensity_sensory_addendum

        lines.append(intensity_sensory_addendum(content_intensity, intimacy_mode=intimacy_mode))
    return "\n".join(lines)
