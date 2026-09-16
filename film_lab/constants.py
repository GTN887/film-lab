"""Shared enums and defaults for the shot desk."""

from __future__ import annotations

from typing import Final, Literal

SCHEMA_VERSION: Final[int] = 1

ASPECT_SCOPE: Final[str] = "2.39:1 cinema scope"
ASPECT_FLAT: Final[str] = "1.85:1"

ASPECT_RATIOS: Final[tuple[str, ...]] = (
    "16:9",
    "9:16",
    "1:1",
    "4:5",
    "3:2",
    "2:3",
    "4:3",
    "3:4",
    "21:9",
    ASPECT_SCOPE,
    ASPECT_FLAT,
)
AspectRatio = str
DEFAULT_ASPECT: Final[str] = "16:9"

# 720p-class desk pixels (Ken Burns / prompt card). Quality module owns export sizes.
ASPECT_SIZES: Final[dict[str, tuple[int, int]]] = {
    "9:16": (720, 1280),
    "16:9": (1280, 720),
    "1:1": (720, 720),
    "4:5": (720, 900),
    "3:2": (1080, 720),
    "2:3": (720, 1080),
    "4:3": (960, 720),
    "3:4": (720, 960),
    "21:9": (1680, 720),
    ASPECT_SCOPE: (1720, 720),
    ASPECT_FLAT: (1332, 720),
}

_ASPECT_ALIASES: Final[dict[str, str]] = {
    "9/16": "9:16",
    "16/9": "16:9",
    "1/1": "1:1",
    "4/5": "4:5",
    "3/2": "3:2",
    "2/3": "2:3",
    "4/3": "4:3",
    "3/4": "3:4",
    "21/9": "21:9",
    "2.39:1": ASPECT_SCOPE,
    "2.39": ASPECT_SCOPE,
    "239:100": ASPECT_SCOPE,
    "scope": ASPECT_SCOPE,
    "cinema scope": ASPECT_SCOPE,
    "1.85": ASPECT_FLAT,
    "185:100": ASPECT_FLAT,
    "widescreen": "16:9",
    "vertical": "9:16",
    "square": "1:1",
    "ultrawide": "21:9",
    "portrait": "9:16",
}


# Dropdown frame icons — square / tall / landscape / ultrawide.
FRAME_SQUARE: Final[str] = "▢"
FRAME_TALL: Final[str] = "▯"
FRAME_LANDSCAPE: Final[str] = "▭"
FRAME_ULTRAWIDE: Final[str] = "▬"

ASPECT_FRAME_KIND: Final[dict[str, str]] = {
    "1:1": "square",
    "9:16": "tall",
    "4:5": "tall",
    "2:3": "tall",
    "3:4": "tall",
    "16:9": "landscape",
    "3:2": "landscape",
    "4:3": "landscape",
    ASPECT_FLAT: "landscape",
    "21:9": "ultrawide",
    ASPECT_SCOPE: "ultrawide",
}

ASPECT_FRAME_ICON: Final[dict[str, str]] = {
    "square": FRAME_SQUARE,
    "tall": FRAME_TALL,
    "landscape": FRAME_LANDSCAPE,
    "ultrawide": FRAME_ULTRAWIDE,
}


def aspect_frame_kind(ratio: str | None) -> str:
    key = (ratio or "").strip()
    if key in ASPECT_FRAME_KIND:
        return ASPECT_FRAME_KIND[key]
    return ASPECT_FRAME_KIND.get(normalize_aspect(key), "landscape")


def aspect_frame_icon(ratio: str | None) -> str:
    return ASPECT_FRAME_ICON[aspect_frame_kind(ratio)]


def aspect_choice_label(ratio: str) -> str:
    return f"{aspect_frame_icon(ratio)}  {ratio}"


def aspect_dropdown_choices() -> list[tuple[str, str]]:
    """Gradio choices: visible frame + label, stored value is the ratio."""
    return [(aspect_choice_label(ratio), ratio) for ratio in ASPECT_RATIOS]


def _strip_aspect_frame(text: str) -> str:
    raw = text.strip()
    for icon in (FRAME_ULTRAWIDE, FRAME_LANDSCAPE, FRAME_TALL, FRAME_SQUARE):
        if raw.startswith(icon):
            return raw[len(icon) :].strip()
    return raw


def normalize_aspect(value: str | None) -> str:
    text = _strip_aspect_frame(value or "")
    if text in ASPECT_RATIOS:
        return text
    return _ASPECT_ALIASES.get(text, _ASPECT_ALIASES.get(text.lower(), DEFAULT_ASPECT))

CAMERA_MOVES: Final[tuple[str, ...]] = (
    "static",
    "slow push-in",
    "pull-out",
    "pan L",
    "pan R",
    "low",
    "high",
    "OTS",
    "orbit",
    "aerial",
    "drone",
    "wide outdoor",
)
CameraMove = Literal[
    "static",
    "slow push-in",
    "pull-out",
    "pan L",
    "pan R",
    "low",
    "high",
    "OTS",
    "orbit",
    "aerial",
    "drone",
    "wide outdoor",
]

EXPLICIT_INTIMACY: Final[str] = "explicit / pornographic (adult study)"
STORY_INTIMACY: Final[str] = "none (story)"

INTIMACY_MODES: Final[tuple[str, ...]] = (
    STORY_INTIMACY,
    "covered sheets",
    "artistic nude",
    "intimate sex",
    EXPLICIT_INTIMACY,
)
IntimacyMode = Literal[
    "none (story)",
    "covered sheets",
    "artistic nude",
    "intimate sex",
    "explicit / pornographic (adult study)",
]

CHARACTER_TAGS: Final[tuple[str, ...]] = (
    "Alison (blonde late-20s)",
    "Bradley (dark hair athletic late-20s)",
    "wedding bands",
)

DEFAULT_LIGHTING: Final[str] = "warm lamp bedroom"
DEFAULT_DURATION: Final[float] = 5.0
MIN_DURATION: Final[float] = 2.0
MAX_DURATION: Final[float] = 30.0
DEFAULT_FPS: Final[int] = 24

DEFAULT_PROJECT: Final[str] = "alison-bradley-study"

# Local-only banner copy shown in the UI and README.
LOCAL_BANNER: Final[str] = (
    "Film-school studio on this machine. Personal study only — not a commercial SaaS. "
    "Nothing is uploaded. Regular / story filming may include family roles "
    "(non-sexual). Adult explicit / pornographic sex is allowed only in "
    "18+ Explicit with adults 18+. Content intensity is a director dial, not an MPAA certificate. "
    "No subscriptions, no Film Lab credits, no quotas, no paywalls. "
    "Works offline for local generation. "
    "Optional writing APIs use keys you own."
)
