"""Evidence-based certification for Film Lab's real production slice.

A certification never manufactures success.  It consumes a real preflight report and
an existing generated Take, then proves persistence, selection and Cinema export.
Hardware rendering itself is certified only when the caller marks the Take as coming
from a real generative engine and the preflight was ready.
"""
from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from film_lab.cinema_export import export_selected
from film_lab.ffmpeg_support import probe_duration_seconds
from film_lab.production import ProductionStore
from film_lab.project import Project, utc_now
from film_lab.runtime_preflight import PreflightReport


@dataclass(frozen=True)
class CertificationStage:
    name: str
    status: str  # PASS | PARTIAL | FAIL | NOT TESTED
    message: str
    evidence: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RenderCertification:
    id: str
    created_at: str
    project: str
    scene_id: str
    shot_id: str
    take_id: str
    status: str
    certified_real_render: bool
    stages: tuple[CertificationStage, ...]
    cinema_export: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def summary(self) -> str:
        lines = [f"Real-render certification: {self.status}"]
        lines.extend(f"{s.name}: {s.status} — {s.message}" for s in self.stages)
        return "\n".join(lines)


def _save(project: Project, cert: RenderCertification) -> Path:
    folder = project.root / "certifications"
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{cert.id}.json"
    path.write_text(json.dumps(cert.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def certify_take(
    project: Project,
    *,
    take_id: str,
    preflight: PreflightReport,
    real_generative_render: bool,
    export_path: Path | str | None = None,
) -> RenderCertification:
    """Certify Preflight -> MP4 -> Take -> selection -> Cinema -> restart persistence.

    ``real_generative_render`` must be supplied by the actual generation boundary. A
    mock/import/fallback Take can exercise the pipeline but cannot earn real-render PASS.
    """
    stages: list[CertificationStage] = []
    stages.append(CertificationStage(
        "Preflight", "PASS" if preflight.ready else "FAIL",
        "Machine reported ready before generation." if preflight.ready else "Machine was not ready before generation.",
        {"workflow": preflight.selected_workflow, "devices": list(preflight.gpu_devices), "blockers": list(preflight.blockers)},
    ))

    store = ProductionStore(project)
    try:
        take = store.get_take(take_id)
    except KeyError:
        stages.append(CertificationStage("Persistent Take", "FAIL", "Take ID does not exist in production state."))
        cert = _finish(project, "", "", take_id, stages, False, "")
        _save(project, cert); return cert

    media = Path(take.media_path)
    duration = probe_duration_seconds(media) if media.is_file() else None
    mp4_ok = media.is_file() and media.suffix.lower() == ".mp4" and media.stat().st_size > 0 and bool(duration and duration > 0)
    stages.append(CertificationStage("MP4 validation", "PASS" if mp4_ok else "FAIL",
        f"Validated real MP4 ({duration:.2f}s)." if mp4_ok else "Take media is missing, empty, not MP4, or not probeable.",
        {"media_path": str(media), "duration": duration}))
    stages.append(CertificationStage("Persistent Take", "PASS", "Take exists in Project → Scene → Shot production state.",
        {"take_id": take.id, "scene_id": take.scene_id, "shot_id": take.shot_id, "generator": take.generator, "model": take.model}))

    if real_generative_render and preflight.ready and mp4_ok:
        stages.append(CertificationStage("Generative render", "PASS", "Generation boundary identified this Take as a real generative render.",
            {"generator": take.generator, "model": take.model, "route": take.metadata.get("generator_route", {})}))
    else:
        stages.append(CertificationStage("Generative render", "NOT TESTED" if mp4_ok else "FAIL",
            "Pipeline media exists, but this run is not certified as a real generative render."))

    cinema = ""
    if mp4_ok:
        store.set_status(take.id, "selected")
        selected = ProductionStore(project).get_take(take.id)
        selection_ok = selected.status == "selected"
        stages.append(CertificationStage("Take Board selection", "PASS" if selection_ok else "FAIL",
            "Selected Take persisted." if selection_ok else "Selected state did not persist."))
        try:
            out = Path(export_path) if export_path else project.outputs_dir / f"certification_{take.id}.mp4"
            cinema_path = export_selected(project, out)
            cinema_ok = cinema_path.is_file() and cinema_path.stat().st_size > 0
            cinema = str(cinema_path.resolve()) if cinema_ok else ""
            stages.append(CertificationStage("Cinema export", "PASS" if cinema_ok else "FAIL",
                "Cinema produced a real output file." if cinema_ok else "Cinema did not produce a real output file.", {"path": cinema}))
        except Exception as exc:  # truthful certification boundary
            stages.append(CertificationStage("Cinema export", "FAIL", str(exc)))

        restarted = ProductionStore(project)
        try:
            persisted = restarted.get_take(take.id)
            restart_ok = persisted.status == "selected" and Path(persisted.media_path).is_file()
        except KeyError:
            restart_ok = False
        stages.append(CertificationStage("Restart persistence", "PASS" if restart_ok else "FAIL",
            "Take, media reference, and Selected state survived store reload." if restart_ok else "Production state did not survive reload."))
    else:
        for name in ("Take Board selection", "Cinema export", "Restart persistence"):
            stages.append(CertificationStage(name, "NOT TESTED", "Blocked by invalid Take media."))

    real_ok = real_generative_render and preflight.ready and all(s.status == "PASS" for s in stages)
    cert = _finish(project, take.scene_id, take.shot_id, take.id, stages, real_ok, cinema)
    _save(project, cert)
    return cert



def certify_generated_output(
    project: Project,
    *,
    output_path: Path | str,
    preflight: PreflightReport,
    expected_generator: str = "amd_i2v",
    export_path: Path | str | None = None,
) -> RenderCertification:
    """Certify the exact Take created for one generation output.

    This is the automatic Generate -> Certification bridge.  It deliberately
    requires an exact generation-output provenance match, the expected real
    ComfyUI generator, and a validated generator route before it can assert that
    the render boundary was genuinely generative.
    """
    wanted = str(Path(output_path).resolve())
    matches = [
        take for take in ProductionStore(project).list_takes(existing_media_only=True)
        if str(take.metadata.get("generation_output_path", "")) == wanted
    ]
    if not matches:
        stages = [CertificationStage(
            "Persistent Take", "FAIL",
            "No persistent Take is linked to the generated output.",
            {"generation_output_path": wanted},
        )]
        cert = _finish(project, "", "", "", stages, False, "")
        _save(project, cert)
        return cert

    take = matches[0]
    route = take.metadata.get("generator_route", {})
    route_validated = isinstance(route, dict) and route.get("validated") is True
    real_boundary = (
        take.generator == expected_generator
        and route_validated
        and preflight.ready
    )
    return certify_take(
        project, take_id=take.id, preflight=preflight,
        real_generative_render=real_boundary, export_path=export_path,
    )


def _finish(project: Project, scene_id: str, shot_id: str, take_id: str, stages: list[CertificationStage], real_ok: bool, cinema: str) -> RenderCertification:
    if real_ok:
        status = "PASS"
    elif any(s.status == "FAIL" for s in stages):
        status = "FAIL"
    else:
        status = "PARTIAL"
    return RenderCertification(
        id=f"cert_{uuid.uuid4().hex[:12]}", created_at=utc_now(), project=project.name,
        scene_id=scene_id, shot_id=shot_id, take_id=take_id, status=status,
        certified_real_render=real_ok, stages=tuple(stages), cinema_export=cinema,
    )
