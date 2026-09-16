from film_lab.director_command import DirectorCommandStore
from film_lab.project import Project
from film_lab.scene_context import SceneContextStore, generation_prompt
from film_lab.shot_card import ShotCard


def test_director_command_plans_without_mutating_scene(tmp_path):
    project = Project.create("director-plan", data_root=tmp_path)
    project.save_shot(ShotCard(id="shot-1", name="Escape", scene_id="scene-1"))
    store = DirectorCommandStore(project)
    plan = store.plan("At night, have them run and hide while the camera orbits", scene_id="scene-1", shot_id="shot-1")
    assert plan.camera_move == "orbit"
    assert "performance" in plan.requested_actions
    assert "scene_world" in plan.requested_actions
    assert SceneContextStore(project).get("scene-1").time_of_day == ""


def test_apply_director_command_updates_scene_and_shot_persistently(tmp_path):
    project = Project.create("director-apply", data_root=tmp_path)
    project.save_shot(ShotCard(id="shot-2", name="Alley", scene_id="scene-2"))
    store = DirectorCommandStore(project)
    plan = store.plan("Rain at night. Pan right as they run and hide.", scene_id="scene-2", shot_id="shot-2")
    applied, shot = store.apply(plan.id)
    assert applied.applied
    assert shot.camera_move == "pan R"
    assert project.load_shot("shot-2").director_intent.startswith("Rain at night")
    scene = SceneContextStore(project).get("scene-2")
    assert scene.weather == "rain"
    assert scene.time_of_day == "night"
    assert "Rain at night" in generation_prompt(project, "scene-2", "escape through the alley")


def test_director_command_history_survives_reload(tmp_path):
    project = Project.create("director-history", data_root=tmp_path)
    store = DirectorCommandStore(project)
    plan = store.plan("Slow push-in while the subject turns", scene_id="scene-a", shot_id="shot-a")
    reloaded = DirectorCommandStore(Project.load("director-history", data_root=tmp_path)).get(plan.id)
    assert reloaded.instruction == plan.instruction
    assert reloaded.camera_move == "slow push-in"
    assert not reloaded.applied


def test_director_command_rejects_empty_instruction(tmp_path):
    project = Project.create("director-empty", data_root=tmp_path)
    store = DirectorCommandStore(project)
    try:
        store.plan("   ", scene_id="scene", shot_id="shot")
    except ValueError as exc:
        assert "instruction" in str(exc).lower()
    else:
        raise AssertionError("empty Director instruction must fail")
