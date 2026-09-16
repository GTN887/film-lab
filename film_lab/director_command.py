"""Persistent, deterministic Director Command planning for Creator-first Film Lab.

This is the local orchestration layer, not an LLM.  It turns a Creator instruction
into explicit Scene World + Shot changes that can be reviewed before generation.
"""
from __future__ import annotations

import json
import re
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from film_lab.constants import CAMERA_MOVES
from film_lab.scene_context import SceneContextStore
from film_lab.shot_card import ShotCard


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@dataclass
class DirectorPlan:
    id: str
    instruction: str
    scene_id: str
    shot_id: str
    camera_move: str = "slow push-in"
    shot_direction: str = ""
    scene_changes: dict[str, Any] = field(default_factory=dict)
    requested_actions: list[str] = field(default_factory=list)
    production_context: dict[str, Any] = field(default_factory=dict)
    continuity_warnings: list[str] = field(default_factory=list)
    capability_warnings: list[str] = field(default_factory=list)
    continuity_report: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_utc_now)
    applied_at: str = ""

    @property
    def applied(self) -> bool:
        return bool(self.applied_at)

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "DirectorPlan":
        known = {k: raw[k] for k in cls.__dataclass_fields__ if k in raw}
        return cls(**known)


_CAMERA_PATTERNS = (
    (r"\b(orbits?|circle around)\b", "orbit"),
    (r"\b(aerial|overhead)\b", "aerial"),
    (r"\bdrone\b", "drone"),
    (r"\b(push[ -]?in|dolly in|move closer)\b", "slow push-in"),
    (r"\b(pull[ -]?out|dolly out|move back)\b", "pull-out"),
    (r"\bpan left\b", "pan L"),
    (r"\bpan right\b", "pan R"),
    (r"\b(low angle|from below)\b", "low"),
    (r"\b(high angle|from above)\b", "high"),
    (r"\b(over[- ]the[- ]shoulder|\bots\b)\b", "OTS"),
    (r"\b(static|locked camera|tripod)\b", "static"),
    (r"\bwide outdoor\b", "wide outdoor"),
)


def _camera_from_instruction(text: str) -> str:
    lower = text.lower()
    for pattern, camera in _CAMERA_PATTERNS:
        if re.search(pattern, lower):
            return camera
    return "slow push-in"


def _scene_changes(text: str) -> dict[str, Any]:
    lower = text.lower()
    changes: dict[str, Any] = {"director_instructions": text.strip()}
    for token, value in (("night", "night"), ("sunset", "sunset"), ("sunrise", "sunrise"), ("daytime", "day"), ("daylight", "day")):
        if token in lower:
            changes["time_of_day"] = value
            break
    for token, value in (("rain", "rain"), ("snow", "snow"), ("fog", "fog"), ("storm", "storm"), ("sunny", "clear")):
        if token in lower:
            changes["weather"] = value
            break
    for token, value in (("neon", "neon"), ("candle", "candlelight"), ("moonlight", "moonlight"), ("golden hour", "golden hour"), ("low key", "low key")):
        if token in lower:
            changes["lighting"] = value
            break
    return changes


def _requested_actions(text: str) -> list[str]:
    lower = text.lower()
    actions = ["direct"]
    if any(x in lower for x in ("run", "walk", "hide", "turn", "dance", "fight", "move", "jump")):
        actions.append("performance")
    if any(re.search(p, lower) for p, _ in _CAMERA_PATTERNS):
        actions.append("camera")
    if any(x in lower for x in ("rain", "snow", "fog", "storm", "night", "sunset", "lighting", "neon")):
        actions.append("scene_world")
    return actions


class DirectorCommandStore:
    def __init__(self, project):
        self.project = project
        project.ensure_dirs()
        self.path: Path = project.root / "director_commands.json"

    def _load(self) -> dict[str, Any]:
        if not self.path.exists():
            return {"version": 1, "plans": []}
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {"version": 1, "plans": []}
        raw.setdefault("version", 1)
        raw.setdefault("plans", [])
        return raw

    def _save(self, raw: dict[str, Any]) -> None:
        temp = self.path.with_suffix(".json.tmp")
        temp.write_text(json.dumps(raw, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        temp.replace(self.path)

    def list(self) -> list[DirectorPlan]:
        return [DirectorPlan.from_dict(x) for x in self._load()["plans"] if isinstance(x, dict)]

    def get(self, plan_id: str) -> DirectorPlan:
        for plan in self.list():
            if plan.id == plan_id:
                return plan
        raise KeyError(plan_id)

    def plan(self, instruction: str, *, scene_id: str, shot_id: str) -> DirectorPlan:
        text = (instruction or "").strip()
        if not text:
            raise ValueError("Director instruction is required.")
        if not scene_id.strip() or not shot_id.strip():
            raise ValueError("Scene and Shot are required for a Director command.")
        camera = _camera_from_instruction(text)
        if camera not in CAMERA_MOVES:
            camera = "slow push-in"
        production_context, continuity_warnings, capability_warnings = self._production_awareness(text, scene_id.strip(), shot_id.strip())
        from film_lab.continuity_intelligence import build_continuity_report
        continuity_report = build_continuity_report(self.project, scene_id=scene_id.strip(), shot_id=shot_id.strip(), instruction=text, scene_changes=_scene_changes(text))
        plan = DirectorPlan(
            id=f"cmd_{uuid.uuid4().hex[:10]}",
            instruction=text,
            scene_id=scene_id.strip(),
            shot_id=shot_id.strip(),
            camera_move=camera,
            shot_direction=text,
            scene_changes=_scene_changes(text),
            requested_actions=_requested_actions(text),
            production_context=production_context,
            continuity_warnings=continuity_warnings,
            capability_warnings=capability_warnings,
            continuity_report=continuity_report,
        )
        raw = self._load()
        raw["plans"].append(asdict(plan))
        self._save(raw)
        return plan

    def _production_awareness(self, instruction: str, scene_id: str, shot_id: str) -> tuple[dict[str, Any], list[str], list[str]]:
        """Snapshot existing movie state for review. Never mutates production state."""
        from film_lab.character_state import CharacterStore
        from film_lab.production import ProductionStore
        from film_lab.generators import GENERATORS, FALLBACK_GENERATOR_ID
        from film_lab.generator_capabilities import capabilities_for

        world = SceneContextStore(self.project).get(scene_id)
        characters = CharacterStore(self.project).resolve_scene_characters(world.characters)
        selected = [t for t in ProductionStore(self.project).selected_takes(existing_media_only=False) if t.scene_id == scene_id]
        selected.sort(key=lambda t: t.created_at)
        prior = selected[-1] if selected else None
        lower = instruction.lower()
        mentioned = [c for c in characters if c.name and re.search(r"\b" + re.escape(c.name.lower()) + r"\b", lower)]
        unresolved_names = []
        # Preserve explicit Scene World bindings; do not invent a character ID from prose.
        for ref in world.characters or []:
            if isinstance(ref, dict) and ref.get("name") and not ref.get("id"):
                unresolved_names.append(str(ref["name"]))

        caps = {}
        for gid, gen in GENERATORS.items():
            if gid == FALLBACK_GENERATOR_ID:
                continue
            caps[gid] = capabilities_for(gen).to_dict()
        capability_warnings=[]
        if any(x in lower for x in ("same face", "same appearance", "keep her appearance", "keep his appearance", "identity")):
            if not any(v.get("identity_conditioning") for v in caps.values()):
                capability_warnings.append("Identity consistency was requested, but no configured generative engine currently declares identity conditioning.")
        if any(x in lower for x in ("orbit", "camera", "pan ", "dolly", "push in", "pull out")):
            if not any(v.get("camera_control") for v in caps.values()):
                capability_warnings.append("Camera direction is preserved in the plan, but no configured generative engine currently declares explicit camera control.")

        continuity=[]
        if prior:
            continuity.append(f"Previous selected Take: {prior.id} ({prior.shot_id}).")
        if world.continuity_notes:
            continuity.append("Existing Scene continuity notes will be preserved unless the Creator applies an explicit change.")
        if unresolved_names:
            continuity.append("Some Scene characters are not bound to stable Character IDs: " + ", ".join(unresolved_names) + ".")
        context={
            "scene_world": {"set_id": world.set_id, "location": world.location, "time_of_day": world.time_of_day, "weather": world.weather, "lighting": world.lighting, "continuity_notes": world.continuity_notes},
            "characters": [{"id": c.id, "name": c.name, "wardrobe": c.wardrobe, "appearance": c.appearance, "emotional_state": c.emotional_state, "reference_images": list(c.reference_images)} for c in characters],
            "mentioned_character_ids": [c.id for c in mentioned],
            "previous_selected_take": ({"id": prior.id, "shot_id": prior.shot_id, "director_notes": prior.director_notes, "tags": list(prior.tags)} if prior else None),
            "generator_capabilities": caps,
        }
        return context, continuity, capability_warnings

    def apply(self, plan_id: str) -> tuple[DirectorPlan, ShotCard]:
        raw = self._load()
        index = next((i for i, item in enumerate(raw["plans"]) if item.get("id") == plan_id), None)
        if index is None:
            raise KeyError(plan_id)
        plan = DirectorPlan.from_dict(raw["plans"][index])
        try:
            shot = self.project.load_shot(plan.shot_id)
        except (OSError, FileNotFoundError):
            shot = ShotCard(id=plan.shot_id, name=f"Shot {plan.shot_id}", scene_id=plan.scene_id)
        shot.scene_id = plan.scene_id
        shot.camera_move = plan.camera_move
        shot.director_intent = plan.shot_direction
        self.project.save_shot(shot)
        SceneContextStore(self.project).update(plan.scene_id, **plan.scene_changes)
        from film_lab.continuity_intelligence import apply_continuity_anchor
        apply_continuity_anchor(self.project, scene_id=plan.scene_id, report=plan.continuity_report)
        plan.applied_at = _utc_now()
        raw["plans"][index] = asdict(plan)
        self._save(raw)
        return plan, shot
