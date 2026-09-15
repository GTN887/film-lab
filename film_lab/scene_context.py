"""Scene World context used to keep generation direction consistent across Takes."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class SceneContext:
    scene_id: str
    set_id: str = ""
    location: str = ""
    time_of_day: str = ""
    weather: str = ""
    lighting: str = ""
    camera: dict[str, Any] = field(default_factory=dict)
    characters: list[dict[str, Any]] = field(default_factory=list)
    objects: list[dict[str, Any]] = field(default_factory=list)
    blocking: list[dict[str, Any]] = field(default_factory=list)
    continuity_notes: str = ""
    director_instructions: str = ""
    prior_take_ids: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "SceneContext":
        data = dict(raw or {})
        return cls(**{k: data[k] for k in cls.__dataclass_fields__ if k in data})

    def prompt_context(self) -> str:
        parts = []
        if self.location: parts.append(f"Location: {self.location}")
        if self.time_of_day: parts.append(f"Time: {self.time_of_day}")
        if self.weather: parts.append(f"Weather: {self.weather}")
        if self.lighting: parts.append(f"Lighting: {self.lighting}")
        if self.characters:
            parts.append("Characters: " + ", ".join(str(x.get("name") or x.get("id") or "character") for x in self.characters))
        if self.blocking: parts.append("Blocking: " + json.dumps(self.blocking, ensure_ascii=False))
        if self.camera: parts.append("Camera: " + json.dumps(self.camera, ensure_ascii=False))
        if self.continuity_notes: parts.append(f"Continuity: {self.continuity_notes}")
        if self.director_instructions: parts.append(f"Director: {self.director_instructions}")
        return ". ".join(parts)


class SceneContextStore:
    def __init__(self, project):
        self.project = project
        project.ensure_dirs()
        self.path = project.root / "scene_world.json"

    def _load(self) -> dict[str, Any]:
        if not self.path.exists(): return {"version": 1, "scenes": {}}
        try: raw = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError): return {"version": 1, "scenes": {}}
        raw.setdefault("version", 1); raw.setdefault("scenes", {})
        return raw

    def _save(self, data: dict[str, Any]) -> None:
        tmp = self.path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        tmp.replace(self.path)

    def get(self, scene_id: str) -> SceneContext:
        raw = self._load()["scenes"].get(scene_id)
        return SceneContext.from_dict(raw) if raw else SceneContext(scene_id=scene_id)

    def save(self, context: SceneContext) -> SceneContext:
        data = self._load(); data["scenes"][context.scene_id] = asdict(context); self._save(data); return context

    def update(self, scene_id: str, **changes: Any) -> SceneContext:
        context = self.get(scene_id)
        for key, value in changes.items():
            if key not in SceneContext.__dataclass_fields__ or key == "scene_id": raise ValueError(f"Unknown Scene World field: {key}")
            setattr(context, key, value)
        return self.save(context)


def generation_prompt(project, scene_id: str, shot_prompt: str) -> str:
    """Compose the Shot request with persistent Scene World continuity."""
    world = SceneContextStore(project).get(scene_id).prompt_context()
    shot = (shot_prompt or "").strip()
    if world and shot: return f"{world}. Shot direction: {shot}"
    return world or shot
