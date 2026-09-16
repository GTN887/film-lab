from film_lab.project import Project
from film_lab.character_state import CharacterStore
from film_lab.scene_context import SceneContextStore
from film_lab.production import ProductionStore
from film_lab.continuity_intelligence import build_continuity_report
from film_lab.director_command import DirectorCommandStore


def test_continuity_report_preserves_character_and_scene_state(tmp_path):
    p=Project.create("continuity", data_root=tmp_path)
    c=CharacterStore(p).create("Maya", appearance="brown eyes", wardrobe="black coat", hair="braid")
    SceneContextStore(p).update("s1", location="warehouse", lighting="blue practicals", characters=[{"id":c.id,"name":"Maya"}], blocking=[{"Maya":"door"}])
    r=build_continuity_report(p, scene_id="s1", shot_id="shot2", instruction="Maya runs", scene_changes={"director_instructions":"Maya runs"})
    assert r["character_locks"][0]["id"] == c.id
    assert r["character_locks"][0]["wardrobe"] == "black coat"
    assert any(x["field"] == "location" and x["value"] == "warehouse" for x in r["preserve"])
    assert r["creator_review_required"] is True


def test_continuity_report_anchors_previous_selected_take(tmp_path):
    p=Project.create("anchor", data_root=tmp_path)
    media=tmp_path/"take.mp4"; media.write_bytes(b"video")
    ps=ProductionStore(p); t=ps.add_take(media, scene_id="s1", shot_id="shot1", metadata={"conditioning":{"camera":{"move":"orbit"}}}); ps.set_status(t.id,"selected")
    r=build_continuity_report(p, scene_id="s1", shot_id="shot2", instruction="continue", scene_changes={})
    assert r["anchor_take"]["take_id"] == t.id
    assert r["anchor_take"]["conditioning"]["camera"]["move"] == "orbit"


def test_director_plan_shows_changes_before_apply_and_apply_pins_anchor(tmp_path):
    p=Project.create("review", data_root=tmp_path)
    SceneContextStore(p).update("s1", time_of_day="day")
    media=tmp_path/"take.mp4"; media.write_bytes(b"video")
    ps=ProductionStore(p); t=ps.add_take(media, scene_id="s1", shot_id="shot1"); ps.set_status(t.id,"selected")
    store=DirectorCommandStore(p); plan=store.plan("Make it night and run", scene_id="s1", shot_id="shot2")
    assert SceneContextStore(p).get("s1").time_of_day == "day"
    assert any(x["field"] == "time_of_day" and x["to"] == "night" for x in plan.continuity_report["requested_changes"])
    store.apply(plan.id)
    world=SceneContextStore(p).get("s1")
    assert world.time_of_day == "night"
    assert t.id in world.prior_take_ids


def test_planning_never_rewrites_character_bible(tmp_path):
    p=Project.create("no-rewrite", data_root=tmp_path)
    c=CharacterStore(p).create("Sarah", wardrobe="red coat")
    SceneContextStore(p).update("s1", characters=[{"id":c.id,"name":"Sarah"}])
    plan=DirectorCommandStore(p).plan("Sarah changes clothes and runs", scene_id="s1", shot_id="shot2")
    assert plan.continuity_report["character_locks"][0]["wardrobe"] == "red coat"
    assert CharacterStore(p).get(c.id).wardrobe == "red coat"
