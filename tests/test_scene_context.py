from film_lab.scene_context import SceneContextStore, generation_prompt
from film_lab.project import Project


def project(tmp_path, name):
    return Project.create(name, data_root=tmp_path / "projects")


def test_scene_world_survives_restart(tmp_path):
    p = project(tmp_path, "world")
    store = SceneContextStore(p)
    store.update("scene_001", location="abandoned warehouse", time_of_day="night", weather="rain", lighting="blue moonlight", continuity_notes="coat remains wet")
    again = SceneContextStore(p).get("scene_001")
    assert again.location == "abandoned warehouse"
    assert again.weather == "rain"
    assert again.continuity_notes == "coat remains wet"


def test_scene_world_is_composed_into_generation_prompt(tmp_path):
    p = project(tmp_path, "world-prompt")
    SceneContextStore(p).update("scene_007", location="train platform", lighting="warm practical lights", characters=[{"id":"char_maya","name":"Maya"}], camera={"lens":"50mm","move":"slow push"})
    prompt = generation_prompt(p, "scene_007", "Maya turns and runs")
    assert "train platform" in prompt
    assert "warm practical lights" in prompt
    assert "Maya" in prompt
    assert "50mm" in prompt
    assert "Maya turns and runs" in prompt


def test_scene_world_rejects_unknown_fields(tmp_path):
    p = project(tmp_path, "world-fields")
    try:
        SceneContextStore(p).update("scene_001", imaginary_switch=True)
    except ValueError:
        pass
    else:
        raise AssertionError("unknown Scene World fields must be rejected")
