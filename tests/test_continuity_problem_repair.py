from film_lab.project import Project
from film_lab.production import ProductionStore
from film_lab.continuity_problem_repair import localize_candidate_problem, execute_repair
from film_lab.visual_target_recognition import VisualTarget,VisualTargetStore
from film_lab.shot_card import ShotCard

class FakeGenerator:
    id="repair-fake"; label="Repair Fake"; model="fake"
    def generate(self,job): job.output_path.parent.mkdir(parents=True,exist_ok=True); job.output_path.write_bytes(b"new"); return job.output_path

def setup(tmp_path):
    p=Project.create("repair",data_root=tmp_path/"projects"); p.save_shot(ShotCard(id="q",name="Q",scene_id="s"))
    a=tmp_path/"a.mp4"; b=tmp_path/"b.mp4"; a.write_bytes(b"a"); b.write_bytes(b"b")
    src=ProductionStore(p).add_take(a,scene_id="s",shot_id="q",copy_media=False)
    cand=ProductionStore(p).add_take(b,scene_id="s",shot_id="q",copy_media=False)
    d=ProductionStore(p)._load(); d["takes"][cand.id]["metadata"]={"ab_source_take_id":src.id,"full_take_continuity_scan":{"events":[{"time_s":4.2,"domain":"registered_visual_target","target_id":"bag","severity":"HIGH","status":"LOST"}],"targets":[]}}; ProductionStore(p)._save(d)
    VisualTargetStore(p).save(VisualTarget("bag","object","Red handbag",(.4,.4,.6,.7),object_id="prop-bag"))
    return p,src,cand

def test_localizes_timed_problem_and_registered_region(tmp_path):
    p,src,cand=setup(tmp_path); plan=localize_candidate_problem(p,cand.id,padding_s=.6)
    assert plan.time_s==4.2 and plan.window_start_s==3.6 and plan.window_end_s==4.8
    assert plan.target_id=="bag" and plan.bbox==(.4,.4,.6,.7) and plan.original_source_take_id==src.id

def test_localization_does_not_claim_temporal_splice(tmp_path):
    p,_,cand=setup(tmp_path); plan=localize_candidate_problem(p,cand.id)
    assert plan.temporal_status=="LOCALIZED_NOT_SPLICED"

def test_no_timed_event_refuses_fake_repair(tmp_path):
    p,_,cand=setup(tmp_path); d=ProductionStore(p)._load(); d["takes"][cand.id]["metadata"]["full_take_continuity_scan"]["events"]=[{"time_s":None,"domain":"track"}]; ProductionStore(p)._save(d)
    try: localize_candidate_problem(p,cand.id)
    except ValueError as e: assert "time-localized" in str(e)
    else: raise AssertionError("expected truth gate")

def test_execute_repair_forks_candidate_preserves_source_and_records_truth(tmp_path,monkeypatch):
    p,src,cand=setup(tmp_path); plan=localize_candidate_problem(p,cand.id)
    def still(s,d,seconds=0): d.parent.mkdir(parents=True,exist_ok=True); d.write_bytes(b"png"); return d
    monkeypatch.setattr("film_lab.mark_direct_regenerate.still_from_source",still)
    monkeypatch.setattr("film_lab.continuity_problem_repair.scan_take_continuity",lambda *a,**k:{"status":"NOT_TESTED","events":[],"truth":"test"})
    new,report=execute_repair(p,generator=FakeGenerator(),plan=plan)
    assert new.id not in {src.id,cand.id} and ProductionStore(p).get_take(cand.id).id==cand.id
    meta=ProductionStore(p).get_take(new.id).metadata
    assert meta["continuity_repair"]["source_candidate_preserved"] is True
    assert meta["continuity_repair"]["temporal_enforcement"]=="NOT_ENFORCED"
    assert meta["localized_repair_source"]["time_s"]==4.2 and report["status"]=="NOT_TESTED"
