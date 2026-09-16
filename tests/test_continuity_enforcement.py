from film_lab.project import Project
from film_lab.character_state import CharacterStore
from film_lab.scene_context import SceneContextStore
from film_lab.shot_card import ShotCard
from film_lab.conditioning import build_conditioning
from film_lab.continuity_enforcement import build_enforcement_plan


def _conditioning(tmp_path):
    p=Project.create("enforce", data_root=tmp_path)
    ref=tmp_path/"maya.png"; ref.write_bytes(b"img")
    c=CharacterStore(p).create("Maya", appearance="brown eyes", wardrobe="black coat", reference_images=[str(ref)], identity_adapter="faceid")
    SceneContextStore(p).update("s1", characters=[{"id":c.id,"name":"Maya"}], camera={"move":"orbit"}, blocking=[{"Maya":"door"}], prior_take_ids=["take_old"])
    start=tmp_path/"start.png"; start.write_bytes(b"img")
    shot=ShotCard(id="shot2", name="Next", scene_id="s1", start_frame=str(start))
    return build_conditioning(p, shot, start)


def test_enforcement_truthfully_separates_prompt_and_model_locks(tmp_path):
    c=_conditioning(tmp_path)
    r=build_enforcement_plan(c)
    assert next(x for x in r["channels"] if x["name"]=="start_frame")["status"] == "ENFORCED"
    assert next(x for x in r["channels"] if x["name"]=="identity_conditioning")["status"] == "UNSUPPORTED"
    assert next(x for x in r["channels"] if x["name"]=="camera_control")["status"] == "PROMPT_ONLY"
    assert r["prior_take_ids"] == ["take_old"]
    assert r["fully_enforced"] is False


def test_workflow_capability_is_not_mislabeled_as_wired(tmp_path):
    c=_conditioning(tmp_path)
    route={"validated":True,"workflow_capabilities":["reference_images","identity_conditioning","camera_control"]}
    r=build_enforcement_plan(c, route_metadata=route)
    assert next(x for x in r["channels"] if x["name"]=="identity_conditioning")["status"] == "AVAILABLE_NOT_WIRED"
    assert "identity_conditioning" in r["unenforced_controls"]


def test_character_locks_are_present_in_production_prompt(tmp_path):
    c=_conditioning(tmp_path)
    assert "Wardrobe: black coat" in c.prompt
    assert "Appearance: brown eyes" in c.prompt
    r=build_enforcement_plan(c)
    assert r["prompt_locks"][0]["character_id"].startswith("char_")
