"""Creator-facing acceptance view for real-render certification.

This module is deliberately read-only with respect to rendering. Generation creates
certifications automatically; this view turns the saved evidence into a simple studio
PASS/PARTIAL/FAIL report without asking the Creator to inspect developer logs.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from film_lab.project import Project


@dataclass(frozen=True)
class AcceptanceView:
    status: str
    headline: str
    certification_id: str = ""
    scene_id: str = ""
    shot_id: str = ""
    take_id: str = ""
    cinema_export: str = ""
    certified_real_render: bool = False
    stages: tuple[dict[str, Any], ...] = ()

    @property
    def creator_ready(self) -> bool:
        return self.status == "PASS" and self.certified_real_render


def certification_files(project: Project) -> list[Path]:
    folder = project.root / "certifications"
    if not folder.is_dir():
        return []
    return sorted(folder.glob("cert_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)


def latest_acceptance(project: Project) -> AcceptanceView:
    files = certification_files(project)
    if not files:
        return AcceptanceView(
            status="NOT TESTED",
            headline="No real-render certification has been recorded for this project yet.",
        )
    try:
        data = json.loads(files[0].read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return AcceptanceView(status="FAIL", headline=f"Latest certification record could not be read: {exc}")

    stages = tuple(s for s in data.get("stages", ()) if isinstance(s, dict))
    status = str(data.get("status") or "FAIL").upper()
    real = bool(data.get("certified_real_render"))
    if status == "PASS" and not real:
        status = "PARTIAL"  # never show a pipeline-only pass as real-render acceptance
    if status == "PASS" and real:
        headline = "REAL RENDER CERTIFIED — Film Lab proved the complete production slice."
    elif status == "PARTIAL":
        headline = "PARTIAL — the pipeline ran, but real-render certification is incomplete."
    else:
        headline = "FAIL — Film Lab found a blocking or failed certification stage."
    return AcceptanceView(
        status=status,
        headline=headline,
        certification_id=str(data.get("id") or files[0].stem),
        scene_id=str(data.get("scene_id") or ""),
        shot_id=str(data.get("shot_id") or ""),
        take_id=str(data.get("take_id") or ""),
        cinema_export=str(data.get("cinema_export") or ""),
        certified_real_render=real,
        stages=stages,
    )


def creator_markdown(view: AcceptanceView) -> str:
    icon = {"PASS": "✅", "PARTIAL": "⚠️", "FAIL": "❌", "NOT TESTED": "○"}.get(view.status, "○")
    lines = [f"## {icon} Creator Acceptance: {view.status}", view.headline]
    if view.certification_id:
        lines.append(f"**Certificate:** `{view.certification_id}`  ")
        lines.append(f"**Scene / Shot / Take:** `{view.scene_id or '—'}` / `{view.shot_id or '—'}` / `{view.take_id or '—'}`")
    if view.stages:
        lines.append("\n### Certification stages")
        for stage in view.stages:
            name = stage.get("name", "Stage")
            status = stage.get("status", "NOT TESTED")
            message = stage.get("message", "")
            lines.append(f"- **{name}: {status}** — {message}")
    if view.cinema_export:
        lines.append(f"\n**Cinema output:** `{view.cinema_export}`")
    if view.status == "NOT TESTED":
        lines.append("\nGenerate a real shot from Motion. Film Lab will run Preflight and create this certification automatically.")
    return "\n".join(lines)
