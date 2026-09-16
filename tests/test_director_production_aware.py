from pathlib import Path
from film_lab.project import Project
from film_lab.character_state import CharacterStore
from film_lab.scene_context import SceneContextStore
from film_lab.production import ProductionStore
from film_lab.director_command import DirectorCommandStore


def test_director_plan_reads_character_and_scene_without_mutation(tmp_path):
    p=Project.create("aware", data_root=tmp_path)
    c=CharacterStore(p).create("Sarah", appearance="short dark hair", wardrobe="red coat")
    SceneContextStore(p).update("scene-a", location="warehouse", time_of_day="night", characters=[{"id":c.id,"name":"Sarah"}], continuity_notes="coat stays dry")
    plan=DirectorCommandStore(p).plan("Sarah runs outside; keep her appearance the same", scene_id="scene-a", shot_id="shot-2")
    assert plan.production_context["characters"][0]["id"] == c.id
    assert plan.production_context["mentioned_character_ids"] == [c.id]
    assert plan.production_context["scene_world"]["location"] == "warehouse"
    # planning is review-only
    assert SceneContextStore(p).get("scene-a").director_instructions == ""


def test_director_plan_uses_previous_selected_take_for_continuity(tmp_path):
    p=Project.create("aware-take", data_root=tmp_path)
    media=tmp_path/"clip.mp4"; media.write_bytes(b"real-test-file")
    store=ProductionStore(p)
    t=store.add_take(media, scene_id="scene-a", shot_id="shot-1")
    store.update_notes(t.id, director_notes="Sarah exits frame left")
    store.set_status(t.id,"selected")
    plan=DirectorCommandStore(p).plan("Continue into the next shot", scene_id="scene-a", shot_id="shot-2")
    assert plan.production_context["previous_selected_take"]["id"] == t.id
    assert any("Previous selected Take" in x for x in plan.continuity_warnings)


def test_director_plan_persists_production_snapshot(tmp_path):
    p=Project.create("aware-persist", data_root=tmp_path)
    SceneContextStore(p).update("scene-a", location="street")
    first=DirectorCommandStore(p).plan("Camera orbits", scene_id="scene-a", shot_id="shot-1")
    loaded=DirectorCommandStore(p).get(first.id)
    assert loaded.production_context["scene_world"]["location"] == "street"
    assert isinstance(loaded.capability_warnings, list)
