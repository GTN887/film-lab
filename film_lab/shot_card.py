"""Shot card dataclass and JSON persistence."""

from __future__ import annotations

import json
import re
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from film_lab.constants import (
    ASPECT_RATIOS,
    CAMERA_MOVES,
    DEFAULT_ASPECT,
    normalize_aspect,
    DEFAULT_DURATION,
    DEFAULT_LIGHTING,
    INTIMACY_MODES,
    MAX_DURATION,
    MIN_DURATION,
    SCHEMA_VERSION,
)
from film_lab.intensity import (
    DEFAULT_INTENSITY,
    clamp_content_intensity,
    intensity_shot_bits,
)
from film_lab.intimacy import intimacy_shot_bits

_SAFE_NAME = re.compile(r"[^a-zA-Z0-9._-]+")


def new_shot_id() -> str:
    return uuid.uuid4().hex[:10]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def slugify(name: str) -> str:
    slug = _SAFE_NAME.sub("-", name.strip().lower()).strip("-")
    return slug or "shot"


@dataclass
class ShotCard:
    """One flexible shot: stills + camera + body notes + intimacy label."""

    id: str = field(default_factory=new_shot_id)
    name: str = "Untitled shot"
    start_frame: str | None = None
    end_frame: str | None = None
    start_frame_hint: str = ""
    end_frame_hint: str = ""
    duration: float = DEFAULT_DURATION
    aspect_ratio: str = DEFAULT_ASPECT
    camera_move: str = "slow push-in"
    subject_motion_strength: float = 0.35
    body_motion_notes: str = ""
    intimacy_mode: str = "covered sheets"
    content_intensity: float = DEFAULT_INTENSITY
    intensity_preset: str = ""
    character_tags: list[str] = field(default_factory=list)
    lighting: str = DEFAULT_LIGHTING
    negative_prompt: str | None = None
    seed: int | None = None
    director_intent: str = ""
    scene_id: str | None = None
    character_ids: list[str] = field(default_factory=list)
    face_lock_strength: float = 0.55
    resolution: str = "720p"
    dialogue_wav: str | None = None
    dialogue_cue: str = ""
    dialogue_start_s: float = 0.0
    music_cue_id: str | None = None
    schema_version: int = SCHEMA_VERSION
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        self.duration = float(min(MAX_DURATION, max(MIN_DURATION, self.duration)))
        self.subject_motion_strength = float(
            min(1.0, max(0.0, self.subject_motion_strength))
        )
        self.aspect_ratio = normalize_aspect(self.aspect_ratio)
        if self.aspect_ratio not in ASPECT_RATIOS:
            raise ValueError(f"aspect_ratio must be one of {ASPECT_RATIOS}")
        if self.camera_move not in CAMERA_MOVES:
            raise ValueError(f"camera_move must be one of {CAMERA_MOVES}")
        if self.intimacy_mode not in INTIMACY_MODES:
            raise ValueError(f"intimacy_mode must be one of {INTIMACY_MODES}")
        self.content_intensity = clamp_content_intensity(self.content_intensity)
        tags: list[str] = []
        for tag in self.character_tags:
            text = str(tag).strip()
            if text and text not in tags:
                tags.append(text)
        self.character_tags = tags
        ids: list[str] = []
        for cid in self.character_ids:
            text = str(cid).strip()
            if text and text not in ids:
                ids.append(text)
        self.character_ids = ids
        if self.negative_prompt == "":
            self.negative_prompt = None
        if self.start_frame == "":
            self.start_frame = None
        if self.end_frame == "":
            self.end_frame = None
        if self.scene_id == "":
            self.scene_id = None
        if self.dialogue_wav == "":
            self.dialogue_wav = None
        if self.music_cue_id == "":
            self.music_cue_id = None
        if self.seed is not None:
            self.seed = int(self.seed)
        self.dialogue_start_s = float(self.dialogue_start_s or 0.0)
        try:
            self.face_lock_strength = float(self.face_lock_strength)
        except (TypeError, ValueError):
            self.face_lock_strength = 0.55
        self.face_lock_strength = min(1.0, max(0.0, self.face_lock_strength))
        from film_lab.quality import normalize_quality

        self.resolution = normalize_quality(self.resolution)

    def touch(self) -> None:
        self.updated_at = utc_now()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self, path: Path) -> None:
        self.touch()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(self.to_dict(), indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ShotCard:
        known = {k: data[k] for k in cls.__dataclass_fields__ if k in data}
        return cls(**known)

    @classmethod
    def from_json(cls, path: Path) -> ShotCard:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError(f"Shot card {path} is not a JSON object")
        return cls.from_dict(payload)

    def local_prompt(self) -> str:
        """Compose a local I2V / ComfyUI prompt from desk fields. Never sent off-box."""
        tags = ", ".join(self.character_tags) if self.character_tags else "adult couple"
        from film_lab.lighting import lighting_prompt_bit

        parts = (
            intimacy_shot_bits(self.intimacy_mode)
            + intensity_shot_bits(self.content_intensity, intimacy_mode=self.intimacy_mode)
            + [
                tags,
                lighting_prompt_bit(self.lighting),
                f"camera: {self.camera_move}",
                f"quality {self.resolution}",
            ]
        )
        if self.body_motion_notes.strip():
            parts.append(f"body: {self.body_motion_notes.strip()}")
        if self.director_intent.strip():
            parts.append(self.director_intent.strip())
        parts.append("late-20s adults, film still, private local use")
        return ", ".join(p for p in parts if p)
