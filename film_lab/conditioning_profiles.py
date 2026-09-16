"""Evidence-based conditioning profiles for known ComfyUI graph layouts.

Profiles do not invent capabilities. They only annotate an existing graph when a
known conditioning consumer is already connected to a LoadImage node. The normal
advanced conditioning bridge then performs the actual upload/injection and records
evidence. Unknown/custom layouts remain untouched and therefore not enforced.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ConditioningProfile:
    id: str
    capability: str
    consumer_node: str
    image_node: str
    strength: int
    reason: str


IDENTITY_TERMS = ("instantid", "faceid", "pulid")
REFERENCE_TERMS = ("ipadapter", "reference")
IMAGE_INPUT_KEYS = ("image", "face_image", "reference_image", "ref_image")


def _linked_node(value: Any) -> str | None:
    if isinstance(value, list) and len(value) >= 1 and isinstance(value[0], (str, int)):
        return str(value[0])
    return None


def _find_connected_load_image(graph: dict[str, Any], consumer: dict[str, Any]) -> str | None:
    inputs = consumer.get("inputs") or {}
    if not isinstance(inputs, dict):
        return None
    for key in IMAGE_INPUT_KEYS:
        source = _linked_node(inputs.get(key))
        node = graph.get(source) if source is not None else None
        if isinstance(node, dict) and str(node.get("class_type", "")).lower() == "loadimage":
            return source
    return None


def discover_conditioning_profiles(graph: dict[str, Any]) -> tuple[ConditioningProfile, ...]:
    """Return only profiles proven by concrete graph connections."""
    found: list[ConditioningProfile] = []
    for node_id, node in graph.items():
        if not isinstance(node, dict):
            continue
        class_name = str(node.get("class_type", "")).lower()
        image_node = _find_connected_load_image(graph, node)
        if not image_node:
            continue
        if any(term in class_name for term in IDENTITY_TERMS):
            found.append(ConditioningProfile(
                id=f"identity:{node_id}", capability="identity_conditioning",
                consumer_node=str(node_id), image_node=image_node, strength=100,
                reason="Known identity consumer is directly connected to LoadImage.",
            ))
        elif any(term in class_name for term in REFERENCE_TERMS):
            found.append(ConditioningProfile(
                id=f"reference:{node_id}", capability="reference_images",
                consumer_node=str(node_id), image_node=image_node, strength=70,
                reason="Known reference-image consumer is directly connected to LoadImage.",
            ))
    return tuple(sorted(found, key=lambda p: (-p.strength, p.id)))


def apply_best_conditioning_profiles(graph: dict[str, Any]) -> dict[str, Any]:
    """Annotate strongest proven image-conditioning slots without replacing explicit slots."""
    profiles = discover_conditioning_profiles(graph)
    applied: list[dict[str, Any]] = []
    claimed_images: set[str] = set()
    for profile in profiles:
        if profile.image_node in claimed_images:
            continue
        node = graph.get(profile.image_node)
        if not isinstance(node, dict):
            continue
        meta = node.setdefault("_meta", {})
        existing = str(meta.get("title") or "").strip()
        # Workflow-authored Film Lab slots always win over auto-profiling.
        if existing.lower().startswith("film_lab_"):
            continue
        slot = "film_lab_identity_image" if profile.capability == "identity_conditioning" else "film_lab_reference_image"
        meta["title"] = slot
        claimed_images.add(profile.image_node)
        applied.append({
            "profile_id": profile.id, "capability": profile.capability,
            "consumer_node": profile.consumer_node, "image_node": profile.image_node,
            "slot": slot, "strength": profile.strength, "reason": profile.reason,
        })
    return {"version": 1, "applied": applied, "available_profiles": [p.__dict__ for p in profiles]}
