"""Discover bundled ComfyUI workflows and choose only routes supported by local nodes.

This module is deliberately conservative: a workflow is runnable only when every
class_type it references is present in ComfyUI's /object_info response. Model
filenames are reported as requirements when they can be read from workflow inputs;
they are not claimed installed unless the caller supplies installed_models.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable


@dataclass(frozen=True)
class WorkflowProfile:
    id: str
    path: str
    node_types: tuple[str, ...]
    missing_nodes: tuple[str, ...] = ()
    model_requirements: tuple[str, ...] = ()
    missing_models: tuple[str, ...] = ()
    capabilities: tuple[str, ...] = ()
    runnable: bool = False
    error: str = ""


@dataclass(frozen=True)
class WorkflowRoute:
    workflow: WorkflowProfile | None
    requested_capabilities: tuple[str, ...]
    unsupported_capabilities: tuple[str, ...] = ()
    reason: str = ""


CAPABILITY_NODES = {
    "identity_conditioning": ("instantid", "faceid", "pulid"),
    "reference_images": ("ipadapter", "instantid", "reference"),
    "camera_control": ("cameractrl", "cameracontrol", "motionctrl"),
    "mask_regeneration": ("inpaint", "noisemask", "mask"),
    "audio": ("audio", "videocombine"),
    "voice": ("tts", "texttospeech", "kokoro", "xtts", "f5tts"),
    "performance_timeline_control": ("keyframe", "timeline", "promptschedule", "animatediff", "temporal", "schedule"),
}


def _workflow_capabilities(node_types: Iterable[str]) -> tuple[str, ...]:
    names = tuple(str(n).lower() for n in node_types)
    found = {"text_prompt", "start_image"}
    for capability, terms in CAPABILITY_NODES.items():
        if any(term in name for name in names for term in terms):
            found.add(capability)
    if any("img2video" in n or "img2vid" in n or "animatediff" in n for n in names):
        found.add("video_generation")
    return tuple(sorted(found))


def _model_requirements(graph: dict[str, Any]) -> tuple[str, ...]:
    values: set[str] = set()
    model_keys = {"ckpt_name", "model_name", "motion_model", "motion_model_name", "vae_name", "clip_name"}
    for node in graph.values():
        if not isinstance(node, dict):
            continue
        inputs = node.get("inputs") or {}
        if not isinstance(inputs, dict):
            continue
        for key, value in inputs.items():
            if key in model_keys and isinstance(value, str) and value and "{{" not in value:
                values.add(value)
    return tuple(sorted(values))


def inspect_workflow(path: Path | str, object_info: dict[str, Any], installed_models: Iterable[str] | None = None) -> WorkflowProfile:
    p = Path(path)
    try:
        graph = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return WorkflowProfile(p.stem, str(p), (), runnable=False, error=f"Unreadable workflow: {exc}")
    if not isinstance(graph, dict) or graph.get("nodes") is not None:
        return WorkflowProfile(p.stem, str(p), (), runnable=False, error="Workflow is not ComfyUI API format")
    node_types = tuple(sorted({str(n.get("class_type")) for n in graph.values() if isinstance(n, dict) and n.get("class_type")}))
    available = set(map(str, object_info.keys()))
    missing_nodes = tuple(sorted(n for n in node_types if n not in available))
    required_models = _model_requirements(graph)
    installed = None if installed_models is None else set(map(str, installed_models))
    missing_models = () if installed is None else tuple(sorted(m for m in required_models if m not in installed))
    return WorkflowProfile(
        id=p.stem,
        path=str(p),
        node_types=node_types,
        missing_nodes=missing_nodes,
        model_requirements=required_models,
        missing_models=missing_models,
        capabilities=_workflow_capabilities(node_types),
        runnable=not missing_nodes and not missing_models,
    )


def discover_workflows(workflow_dir: Path | str, object_info: dict[str, Any], installed_models: Iterable[str] | None = None) -> tuple[WorkflowProfile, ...]:
    root = Path(workflow_dir)
    if not root.is_dir():
        return ()
    return tuple(inspect_workflow(p, object_info, installed_models) for p in sorted(root.glob("*.json")))


def choose_workflow(workflows: Iterable[WorkflowProfile], requested_capabilities: Iterable[str] = ()) -> WorkflowRoute:
    requested = tuple(sorted(set(map(str, requested_capabilities))))
    runnable = [w for w in workflows if w.runnable]
    if not runnable:
        return WorkflowRoute(None, requested, requested, "No locally runnable workflow was discovered.")
    def score(w: WorkflowProfile):
        supported = len(set(requested) & set(w.capabilities))
        return (supported, len(w.capabilities), w.id)
    best = max(runnable, key=score)
    unsupported = tuple(sorted(set(requested) - set(best.capabilities)))
    reason = "Selected best locally runnable workflow."
    if unsupported:
        reason += " Some requested optional controls are unsupported."
    return WorkflowRoute(best, requested, unsupported, reason)
