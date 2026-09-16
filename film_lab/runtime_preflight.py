"""Creator-facing runtime preflight for real Film Lab generation.

Preflight never renders. It reports whether the current machine can truthfully attempt
one requested Shot using local ComfyUI + a validated workflow + ffmpeg.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from film_lab.comfyui_discovery import discover_comfyui
from film_lab.ffmpeg_support import ffmpeg_available
from film_lab.workflow_router import choose_workflow, discover_workflows


@dataclass(frozen=True)
class PreflightReport:
    ready: bool
    comfyui_connected: bool
    endpoint: str
    gpu_devices: tuple[str, ...] = ()
    node_count: int = 0
    ffmpeg_ready: bool = False
    ffmpeg_message: str = ""
    selected_workflow: str = ""
    selected_workflow_path: str = ""
    required_models: tuple[str, ...] = ()
    missing_models: tuple[str, ...] = ()
    requested_capabilities: tuple[str, ...] = ()
    unsupported_capabilities: tuple[str, ...] = ()
    missing_nodes: tuple[str, ...] = ()
    blockers: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    evidence: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def summary(self) -> str:
        status = "READY" if self.ready else "NOT READY"
        lines = [f"Film Lab preflight: {status}"]
        lines.append(f"ComfyUI: {'connected' if self.comfyui_connected else 'unavailable'} ({self.endpoint})")
        lines.append("GPU/device: " + (", ".join(self.gpu_devices) if self.gpu_devices else "not reported"))
        lines.append(f"ffmpeg: {'ready' if self.ffmpeg_ready else 'not ready'}")
        lines.append("Workflow: " + (self.selected_workflow or "none"))
        if self.required_models: lines.append("Required models: " + ", ".join(self.required_models))
        if self.missing_models: lines.append("Missing models: " + ", ".join(self.missing_models))
        if self.unsupported_capabilities: lines.append("Unsupported optional controls: " + ", ".join(self.unsupported_capabilities))
        if self.blockers: lines.append("Blockers: " + " | ".join(self.blockers))
        return "\n".join(lines)


def _get_json(endpoint: str, path: str, timeout: float = 3.0) -> Any:
    with urlopen(Request(endpoint.rstrip("/") + path, headers={"Accept": "application/json"}), timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def _device_names(system_stats: Any) -> tuple[str, ...]:
    if not isinstance(system_stats, dict): return ()
    devices = system_stats.get("devices") or system_stats.get("device") or ()
    if isinstance(devices, dict): devices = [devices]
    names = []
    if isinstance(devices, list):
        for d in devices:
            if isinstance(d, dict):
                name = d.get("name") or d.get("device_name") or d.get("type")
                if name: names.append(str(name))
            elif d: names.append(str(d))
    return tuple(names)


def _installed_model_choices(object_info: dict[str, Any]) -> tuple[str, ...]:
    """Collect ComfyUI combo choices that look like model/checkpoint filenames."""
    values: set[str] = set()
    model_keys = {"ckpt_name", "model_name", "motion_model", "motion_model_name", "vae_name", "clip_name"}
    for node in object_info.values() if isinstance(object_info, dict) else ():
        inputs = node.get("input") if isinstance(node, dict) else None
        if not isinstance(inputs, dict): continue
        for section in ("required", "optional"):
            fields = inputs.get(section) or {}
            if not isinstance(fields, dict): continue
            for key, spec in fields.items():
                if key not in model_keys or not isinstance(spec, (list, tuple)) or not spec: continue
                choices = spec[0]
                if isinstance(choices, (list, tuple)):
                    values.update(str(v) for v in choices if isinstance(v, str) and v)
    return tuple(sorted(values))


def run_preflight(*, endpoint: str = "http://127.0.0.1:8188", workflow_dir: Path | str = "workflows", requested_capabilities: Iterable[str] = (), timeout: float = 3.0) -> PreflightReport:
    requested = tuple(sorted(set(map(str, requested_capabilities))))
    discovery = discover_comfyui(endpoint, timeout=timeout)
    ff_ok, ff_msg = ffmpeg_available()
    blockers: list[str] = []; warnings: list[str] = []
    if not discovery.available:
        blockers.append(discovery.error or "ComfyUI is not reachable.")
        return PreflightReport(False, False, endpoint.rstrip("/"), ffmpeg_ready=ff_ok, ffmpeg_message=ff_msg, requested_capabilities=requested, blockers=tuple(blockers), evidence={"comfyui": discovery.to_dict()})

    try: object_info = _get_json(endpoint, "/object_info", timeout)
    except (URLError, HTTPError, TimeoutError, OSError, json.JSONDecodeError) as exc:
        object_info = {}; blockers.append(f"Could not read ComfyUI node inventory: {exc}")
    try: stats = _get_json(endpoint, "/system_stats", timeout)
    except (URLError, HTTPError, TimeoutError, OSError, json.JSONDecodeError): stats = {}
    devices = _device_names(stats)
    if not devices: warnings.append("ComfyUI did not report a GPU/device name; rendering capability is not hardware-certified yet.")

    installed = _installed_model_choices(object_info)
    workflows = discover_workflows(workflow_dir, object_info, installed_models=installed)
    route = choose_workflow(workflows, requested)
    selected = route.workflow
    if selected is None: blockers.append(route.reason or "No runnable workflow is available.")
    if not ff_ok: blockers.append("ffmpeg is not ready; Film Lab cannot certify MP4/Cinema output.")
    if route.unsupported_capabilities:
        warnings.append("Some requested optional controls will not be honored by the selected workflow.")

    missing_models = selected.missing_models if selected else ()
    missing_nodes = selected.missing_nodes if selected else ()
    if missing_models: blockers.append("Selected workflow is missing required models.")
    if missing_nodes: blockers.append("Selected workflow is missing required ComfyUI nodes.")
    ready = discovery.available and ff_ok and selected is not None and selected.runnable and not blockers
    evidence = {
        "comfyui": discovery.to_dict(),
        "system_stats": stats,
        "installed_model_choices": installed,
        "workflow_count": len(workflows),
        "route_reason": route.reason,
    }
    return PreflightReport(ready, True, endpoint.rstrip("/"), devices, discovery.node_count, ff_ok, ff_msg,
        selected.id if selected else "", selected.path if selected else "", selected.model_requirements if selected else (),
        missing_models, requested, route.unsupported_capabilities, missing_nodes, tuple(blockers), tuple(warnings), evidence)
