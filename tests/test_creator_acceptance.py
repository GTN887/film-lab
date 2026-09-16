import json
from pathlib import Path

from film_lab.creator_acceptance import latest_acceptance, creator_markdown
from film_lab.project import Project


def project(tmp_path):
    return Project.create("acceptance-test", data_root=tmp_path)


def write_cert(p, **overrides):
    folder = p.root / "certifications"; folder.mkdir(parents=True, exist_ok=True)
    data = {
        "id": "cert_abc", "status": "PASS", "certified_real_render": True,
        "scene_id": "scene-1", "shot_id": "shot-1", "take_id": "take-1",
        "cinema_export": str(p.outputs_dir / "final.mp4"),
        "stages": [{"name": "Preflight", "status": "PASS", "message": "Ready."}],
    }
    data.update(overrides)
    (folder / "cert_abc.json").write_text(json.dumps(data), encoding="utf-8")


def test_no_certificate_is_not_tested(tmp_path):
    view = latest_acceptance(project(tmp_path))
    assert view.status == "NOT TESTED"
    assert "Generate a real shot" in creator_markdown(view)


def test_real_pass_is_creator_ready(tmp_path):
    p = project(tmp_path); write_cert(p)
    view = latest_acceptance(p)
    assert view.status == "PASS" and view.creator_ready
    assert "REAL RENDER CERTIFIED" in creator_markdown(view)


def test_non_real_pass_is_downgraded(tmp_path):
    p = project(tmp_path); write_cert(p, certified_real_render=False)
    view = latest_acceptance(p)
    assert view.status == "PARTIAL" and not view.creator_ready


def test_corrupt_certificate_fails_truthfully(tmp_path):
    p = project(tmp_path); folder = p.root / "certifications"; folder.mkdir(parents=True)
    (folder / "cert_bad.json").write_text("not json", encoding="utf-8")
    assert latest_acceptance(p).status == "FAIL"
