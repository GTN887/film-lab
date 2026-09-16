from film_lab.project import Project
from film_lab.production import ProductionStore
from film_lab.scene_context import SceneContextStore
from film_lab.character_state import CharacterStore
from film_lab.shot_continuity_intelligence import infer_change_scope, build_regeneration_contract, audit_candidate


def setup(tmp_path):
    p=Project.create("continuity-shot",data_root=tmp_path/"projects")
    c=CharacterStore(p).create("Sarah",appearance="freckles",wardrobe="blue coat",hair="brown bob")
    SceneContextStore(p).update("s",set_id="set_house",location="kitchen",lighting="warm",camera={"framing":"medium"},objects=[{"name":"red mug"}],characters=[{"id":c.id,"name":"Sarah"}])
    f=tmp_path/"source.mp4"; f.write_bytes(b"video")
    t=ProductionStore(p).add_take(f,scene_id="s",shot_id="q",copy_media=False); ProductionStore(p).set_status(t.id,"selected")
    return p,c,t


def test_instruction_scope_changes_performance_without_unlocking_world(tmp_path):
    p,c,t=setup(tmp_path)
    contract=build_regeneration_contract(p,scene_id="s",shot_id="q",source_take_id=t.id,instruction="Make Sarah more suspicious",character_id=c.id)
    assert contract["requested_change_scopes"]==["performance"]
    assert contract["preserve"]["location"]=="kitchen" and contract["preserve"]["camera"]["framing"]=="medium"
    assert contract["preserve"]["characters"][0]["wardrobe"]=="blue coat"


def test_explicit_camera_change_unlocks_camera_only(tmp_path):
    p,c,t=setup(tmp_path)
    contract=build_regeneration_contract(p,scene_id="s",shot_id="q",source_take_id=t.id,instruction="Push in camera while Sarah reacts",character_id=c.id)
    assert "camera" in contract["requested_change_scopes"] and "camera" not in contract["preserve"]
    assert contract["preserve"]["lighting"]=="warm" and contract["preserve"]["objects"][0]["name"]=="red mug"


def test_unknown_character_cannot_be_silently_targeted(tmp_path):
    p,c,t=setup(tmp_path)
    try: build_regeneration_contract(p,scene_id="s",shot_id="q",source_take_id=t.id,instruction="react",character_id="char_wrong")
    except ValueError as e: assert "not bound" in str(e)
    else: raise AssertionError("expected stable Character truth gate")


def test_candidate_audit_never_claims_visual_continuity_from_renderer_metadata(tmp_path):
    p,c,t=setup(tmp_path); f=tmp_path/"candidate.mp4"; f.write_bytes(b"new")
    cand=ProductionStore(p).add_take(f,scene_id="s",shot_id="q",copy_media=False,metadata={"continuity_enforcement":{"channels":[{"name":"start_frame","status":"ENFORCED"},{"name":"identity_conditioning","status":"ENFORCED"}]}})
    contract=build_regeneration_contract(p,scene_id="s",shot_id="q",source_take_id=t.id,instruction="Sarah looks afraid",character_id=c.id)
    report=audit_candidate(p,candidate_take_id=cand.id,contract=contract)
    assert report["renderer_evidence"]["identity"]=="ENFORCED"
    assert report["visual_certification"]=="NOT_TESTED" and "does not prove visual" in report["truth"]
