from pathlib import Path
import subprocess

from film_lab.production import ProductionStore
from film_lab.project import Project
from film_lab.render_certification import certify_generated_output
from film_lab.runtime_preflight import PreflightReport


def _mp4(path: Path):
    subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "color=size=64x64:rate=10:duration=0.3", "-pix_fmt", "yuv420p", str(path)], check=True, capture_output=True)


def _ready():
    return PreflightReport(ready=True, comfyui_connected=True, endpoint="http://127.0.0.1:8188", gpu_devices=("AMD test",), ffmpeg_ready=True, selected_workflow="svd")


def test_exact_generated_output_auto_certifies_real_route(tmp_path):
    p = Project.create("auto-cert", data_root=tmp_path)
    output = tmp_path / "render.mp4"; _mp4(output)
    ProductionStore(p).add_take(output, scene_id="s1", shot_id="sh1", generator="amd_i2v", metadata={"generation_output_path": str(output.resolve()), "generator_route": {"validated": True}})
    cert = certify_generated_output(p, output_path=output, preflight=_ready())
    assert cert.status == "PASS" and cert.certified_real_render
    assert Path(cert.cinema_export).is_file()


def test_unvalidated_route_cannot_receive_real_render_pass(tmp_path):
    p = Project.create("auto-cert-unvalidated", data_root=tmp_path)
    output = tmp_path / "render.mp4"; _mp4(output)
    ProductionStore(p).add_take(output, shot_id="sh1", generator="amd_i2v", metadata={"generation_output_path": str(output.resolve()), "generator_route": {"validated": False}})
    cert = certify_generated_output(p, output_path=output, preflight=_ready())
    assert cert.status == "PARTIAL" and not cert.certified_real_render


def test_missing_generation_take_is_recorded_as_failure(tmp_path):
    p = Project.create("auto-cert-missing", data_root=tmp_path)
    output = tmp_path / "render.mp4"; _mp4(output)
    cert = certify_generated_output(p, output_path=output, preflight=_ready())
    assert cert.status == "FAIL" and not cert.certified_real_render
    assert (p.root / "certifications" / f"{cert.id}.json").is_file()
