"""Truthful continuity enforcement plan for generation.

Turns continuity state into concrete conditioning channels while distinguishing
what Film Lab can actually enforce from what is only requested or prompt-guided.
This module never claims model-level identity/reference control unless the render
adapter has a wired conditioning channel for it.
"""
from __future__ import annotations
from typing import Any


def build_enforcement_plan(conditioning, *, route_metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    route = dict(route_metadata or {})
    route_caps = set(route.get("workflow_capabilities") or [])
    validated = bool(route.get("validated"))
    wired_caps = set(route.get("wired_capabilities") or (route.get("conditioning_bridge") or {}).get("wired_capabilities") or [])
    chars = tuple(getattr(conditioning, "characters", ()) or ())

    prompt_locks = []
    for c in chars:
        prompt_locks.append({
            "character_id": getattr(c, "character_id", ""),
            "name": getattr(c, "name", ""),
            "method": "production_prompt",
            "status": "ENFORCED",
        })

    channels = [{
        "name": "start_frame",
        "requested": bool(getattr(conditioning, "start_image", "")),
        "status": "ENFORCED" if getattr(conditioning, "start_image", "") else "NOT_REQUESTED",
        "method": "img2vid_start_image" if getattr(conditioning, "start_image", "") else "",
    }]

    refs = [p for c in chars for p in (getattr(c, "reference_images", ()) or ()) if p]
    identity = [c for c in chars if getattr(c, "identity_adapter", "") or getattr(c, "identity_reference", "")]
    camera = bool(getattr(conditioning, "camera", {}))
    blocking = bool(getattr(conditioning, "blocking", ()))
    objects = bool(getattr(conditioning, "objects", ()))

    # Current ComfyUI I2V adapter injects start image + production prompt.  These
    # richer controls are routed/capability-checked but do not yet have a generic
    # graph-injection bridge, so never label them enforced merely because nodes exist.
    for name, requested, available in (
        ("reference_images", bool(refs), "reference_images" in route_caps),
        ("identity_conditioning", bool(identity), "identity_conditioning" in route_caps),
        ("camera_control", camera, "camera_control" in route_caps),
        ("blocking", blocking, "blocking" in route_caps),
        ("objects", objects, "objects" in route_caps),
    ):
        if not requested:
            status = "NOT_REQUESTED"
        elif validated and name in wired_caps:
            status = "ENFORCED"
        elif validated and available:
            status = "AVAILABLE_NOT_WIRED"
        else:
            status = "PROMPT_ONLY" if name in {"camera_control", "blocking", "objects"} else "UNSUPPORTED"
        channels.append({"name": name, "requested": requested, "status": status, "workflow_available": bool(validated and available), "bridge_wired": bool(validated and name in wired_caps)})

    prior = list((getattr(conditioning, "metadata", {}) or {}).get("prior_take_ids", []) or [])
    unenforced = [c["name"] for c in channels if c["requested"] and c["status"] not in {"ENFORCED", "PROMPT_ONLY"}]
    prompt_only = [c["name"] for c in channels if c["requested"] and c["status"] == "PROMPT_ONLY"]
    return {
        "version": 2,
        "prompt_locks": prompt_locks,
        "channels": channels,
        "prior_take_ids": prior,
        "unenforced_controls": unenforced,
        "prompt_only_controls": prompt_only,
        "fully_enforced": not unenforced and not prompt_only,
        "truth": "Continuity is enforced only through channels explicitly marked ENFORCED; PROMPT_ONLY is guidance, not a model lock.",
    }
