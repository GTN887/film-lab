from pathlib import Path
import subprocess

from film_lab.production import ProductionStore
from film_lab.project import Project
from film_lab.render_certification import certify_take
from film_lab.runtime_preflight import PreflightReport


def _project(tmp_path):
    return Project.create("cert-test", data_root=tmp_path)


def _mp4(path: Path):
    subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "color=size=64x64:rate=10:duration=0.3", "-pix_fmt", "yuv420p", str(path)], check=True, capture_output=True)


def _preflight(ready=True):
    return PreflightReport(ready=ready, comfyui_connected=ready, endpoint="http://127.0.0.1:8188", gpu_devices=("AMD test device",) if ready else (), ffmpeg_ready=True, selected_workflow="test-flow", blockers=() if ready else ("not ready",))


def test_real_certification_proves_take_cinema_and_reload(tmp_path):
    p = _project(tmp_path); src = tmp_path / "real.mp4"; _mp4(src)
    take = ProductionStore(p).add_take(src, scene_id="scene_1", shot_id="shot_1", generator="comfyui", model="test-model", metadata={"generator_route":{"validated": True}})
    cert = certify_take(p, take_id=take.id, preflight=_preflight(), real_generative_render=True)
    assert cert.status == "PASS" and cert.certified_real_render
    assert Path(cert.cinema_export).is_file()
    assert ProductionStore(p).get_take(take.id).status == "selected"
    assert (p.root / "certifications" / f"{cert.id}.json").is_file()


def test_import_or_mock_cannot_be_real_render_pass(tmp_path):
    p = _project(tmp_path); src = tmp_path / "mock.mp4"; _mp4(src)
    take = ProductionStore(p).add_take(src, shot_id="shot_1", generator="mock")
    cert = certify_take(p, take_id=take.id, preflight=_preflight(), real_generative_render=False)
    assert cert.status == "PARTIAL"
    assert not cert.certified_real_render
    assert next(s for s in cert.stages if s.name == "Generative render").status == "NOT TESTED"


def test_failed_preflight_cannot_certify_real_render(tmp_path):
    p = _project(tmp_path); src = tmp_path / "real.mp4"; _mp4(src)
    take = ProductionStore(p).add_take(src, shot_id="shot_1", generator="comfyui")
    cert = certify_take(p, take_id=take.id, preflight=_preflight(False), real_generative_render=True)
    assert cert.status == "FAIL" and not cert.certified_real_render


def test_missing_take_is_failure_and_recorded(tmp_path):
    p = _project(tmp_path)
    cert = certify_take(p, take_id="take_missing", preflight=_preflight(), real_generative_render=True)
    assert cert.status == "FAIL"
    assert (p.root / "certifications" / f"{cert.id}.json").is_file()
