from film_lab.project import Project
from film_lab.scene_context import SceneContextStore
from film_lab.ui_handlers import director_home_plan_ui, director_home_apply_ui


def test_home_plan_is_review_only(tmp_path, monkeypatch):
    monkeypatch.setenv("FILM_LAB_DATA", str(tmp_path))
    project = Project.create("director-home")
    plan_id, md, status = director_home_plan_ui(project.name, "At night, run and hide while camera orbits", "scene-a", "shot-a")
    assert plan_id.startswith("cmd_")
    assert "Production Plan" in md and "orbit" in md
    assert "ready for review" in status
    assert SceneContextStore(project).get("scene-a").director_instructions == ""


def test_home_apply_updates_real_production_state(tmp_path, monkeypatch):
    monkeypatch.setenv("FILM_LAB_DATA", str(tmp_path))
    project = Project.create("director-apply")
    plan_id, _, _ = director_home_plan_ui(project.name, "Night rain. Run and hide. Camera orbits.", "scene-b", "shot-b")
    md, status = director_home_apply_ui(project.name, plan_id)
    project = Project.load(project.name)
    shot = project.load_shot("shot-b")
    scene = SceneContextStore(project).get("scene-b")
    assert shot.camera_move == "orbit"
    assert "Run and hide" in shot.director_intent
    assert scene.time_of_day == "night"
    assert scene.weather == "rain"
    assert "APPLIED" in md
    assert "Applied Director plan" in status


def test_home_apply_requires_reviewed_plan(tmp_path, monkeypatch):
    monkeypatch.setenv("FILM_LAB_DATA", str(tmp_path))
    Project.create("director-empty")
    md, status = director_home_apply_ui("director-empty", "")
    assert "Create a plan first" in md
    assert "No Director plan" in status
