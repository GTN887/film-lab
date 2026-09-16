"""Automatic Creator-facing preflight gate for real motion generation."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from film_lab.runtime_preflight import PreflightReport, run_preflight

@dataclass(frozen=True)
class GenerationGate:
    allowed: bool
    report: PreflightReport
    message: str


def requested_capabilities_for_shot(shot) -> tuple[str, ...]:
    """Translate visible Shot intent into truthful optional workflow capabilities."""
    requested = {"text_prompt", "start_image"}
    if getattr(shot, "end_frame", ""):
        requested.add("end_image")
    if getattr(shot, "character_ids", None):
        requested.add("reference_images")
    camera = str(getattr(shot, "camera_move", "") or "").strip().lower()
    if camera and camera not in {"static", "locked", "none"}:
        requested.add("camera_control")
    return tuple(sorted(requested))


def preflight_generation(shot, *, endpoint: str = "http://127.0.0.1:8188", workflow_dir: Path | str = "workflows") -> GenerationGate:
    report = run_preflight(endpoint=endpoint, workflow_dir=workflow_dir,
                           requested_capabilities=requested_capabilities_for_shot(shot))
    if report.ready:
        msg = "Ready to Generate"
        if report.selected_workflow:
            msg += f" · {report.selected_workflow}"
        if report.gpu_devices:
            msg += " · " + ", ".join(report.gpu_devices)
        if report.unsupported_capabilities:
            msg += "\nWarning: unsupported optional controls: " + ", ".join(report.unsupported_capabilities)
        return GenerationGate(True, report, msg)
    details = list(report.blockers)
    if report.missing_models:
        details.append("Missing models: " + ", ".join(report.missing_models))
    if report.missing_nodes:
        details.append("Missing nodes: " + ", ".join(report.missing_nodes))
    return GenerationGate(False, report, "Generation blocked by Preflight. " + (" ".join(details) or "Machine is not ready."))
