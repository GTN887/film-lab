"""Explicit, evidence-based conditioning bridge for ComfyUI API workflows.

Film Lab only calls a rich conditioning channel wired when the workflow exposes an
explicit Film Lab slot.  We do not guess custom-node schemas from names alone.
Workflow authors opt in with `_meta.title` values such as:
  film_lab_reference_image[:character-id-or-name]
  film_lab_identity_image[:character-id-or-name]
  film_lab_camera
  film_lab_blocking
  film_lab_objects
Image slots must be LoadImage nodes already connected to the intended graph path.
Text/control slots must expose a scalar `text`, `value`, `camera`, `blocking`, or
`objects` input.  This keeps capability claims tied to a concrete graph injection.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

UploadFn = Callable[[Path], str]


def _title(node: dict[str, Any]) -> str:
    return str((node.get("_meta") or {}).get("title") or "").strip()


def _slot(title: str) -> tuple[str, str]:
    if ":" in title:
        base, target = title.split(":", 1)
        return base.strip().lower(), target.strip().lower()
    return title.strip().lower(), ""


def _character(conditioning, target: str):
    chars = tuple(getattr(conditioning, "characters", ()) or ())
    if not chars:
        return None
    if not target:
        return chars[0]
    for char in chars:
        if target in {str(getattr(char, "character_id", "")).lower(), str(getattr(char, "name", "")).lower()}:
            return char
    return None


def _reference_path(char, *, identity: bool) -> Path | None:
    candidates: list[str] = []
    if identity:
        ref = str(getattr(char, "identity_reference", "") or "")
        if ref:
            candidates.append(ref)
    candidates.extend(str(p) for p in (getattr(char, "reference_images", ()) or ()) if p)
    for value in candidates:
        p = Path(value).expanduser()
        if p.is_file():
            return p.resolve()
    return None


def _set_scalar(inputs: dict[str, Any], preferred: tuple[str, ...], value: str) -> bool:
    for key in preferred:
        if key in inputs and not isinstance(inputs[key], (list, dict)):
            inputs[key] = value
            return True
    return False


def inject_advanced_conditioning(graph: dict[str, Any], conditioning, upload: UploadFn) -> dict[str, Any]:
    """Inject only explicit Film Lab slots and return auditable bridge evidence."""
    wired: set[str] = set()
    slots: list[dict[str, Any]] = []
    identity_node_present = any(
        any(term in str(node.get("class_type", "")).lower() for term in ("instantid", "faceid", "pulid"))
        for node in graph.values() if isinstance(node, dict)
    )

    inpaint_node_present = any(
        any(term in str(node.get("class_type", "")).lower() for term in ("inpaint", "noisemask", "noise_mask"))
        for node in graph.values() if isinstance(node, dict)
    )
    regional = list((getattr(conditioning, "metadata", {}) or {}).get("regional_actor_controls") or [])

    def regional_for(target: str):
        for item in regional:
            if str(item.get("character_id") or "").lower() == target and item.get("status") == "REQUESTED":
                return item
        return None

    for node_id, node in graph.items():
        if not isinstance(node, dict):
            continue
        base, target = _slot(_title(node))
        inputs = node.setdefault("inputs", {})
        if base in {"film_lab_reference_image", "film_lab_identity_image"}:
            char = _character(conditioning, target)
            path = _reference_path(char, identity=base.endswith("identity_image")) if char else None
            ok = False
            if path and node.get("class_type") == "LoadImage" and "image" in inputs:
                inputs["image"] = upload(path)
                capability = "identity_conditioning" if base.endswith("identity_image") else "reference_images"
                # Identity requires both an explicit identity slot and an identity-capable graph node.
                if capability != "identity_conditioning" or identity_node_present:
                    wired.add(capability)
                    ok = True
            slots.append({"node_id": str(node_id), "slot": base, "target": target, "wired": ok, "source": str(path or "")})
            continue

        if base == "film_lab_actor_mask":
            item = regional_for(target)
            path = Path(str((item or {}).get("mask_path") or "")).expanduser() if item else None
            ok = False
            if item and path and path.is_file() and node.get("class_type") == "LoadImage" and "image" in inputs and inpaint_node_present:
                inputs["image"] = upload(path.resolve())
                wired.add("mask_regeneration")
                ok = True
            slots.append({"node_id": str(node_id), "slot": base, "target": target, "wired": ok, "source": str(path or "")})
            continue
        if base == "film_lab_actor_region_prompt":
            item = regional_for(target)
            value = str((item or {}).get("instruction") or "").strip()
            ok = bool(value) and _set_scalar(inputs, ("text", "value", "prompt"), value)
            slots.append({"node_id": str(node_id), "slot": base, "target": target, "wired": ok})
            continue

        value = None
        capability = ""
        preferred: tuple[str, ...] = ()
        if base == "film_lab_camera" and getattr(conditioning, "camera", None):
            capability, value, preferred = "camera_control", json.dumps(conditioning.camera, sort_keys=True), ("camera", "text", "value")
        elif base == "film_lab_blocking" and getattr(conditioning, "blocking", None):
            capability, value, preferred = "blocking", json.dumps(conditioning.blocking, sort_keys=True), ("blocking", "text", "value")
        elif base == "film_lab_objects" and getattr(conditioning, "objects", None):
            capability, value, preferred = "objects", json.dumps(conditioning.objects, sort_keys=True), ("objects", "text", "value")
        if capability:
            ok = _set_scalar(inputs, preferred, value)
            if ok:
                wired.add(capability)
            slots.append({"node_id": str(node_id), "slot": base, "target": target, "wired": ok})

    return {"version": 1, "wired_capabilities": sorted(wired), "slots": slots}
