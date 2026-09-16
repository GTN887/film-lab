from PIL import Image
from film_lab.project import Project
from film_lab.production import ProductionStore
from film_lab.visual_continuity_certification import certify_visual_continuity, certify_candidate_take


def setup(tmp_path,a=(30,40,50),b=(30,40,50)):
    p=Project.create("visual-cert",data_root=tmp_path/"projects")
    sm=tmp_path/"source.mp4"; cm=tmp_path/"candidate.mp4"; sm.write_bytes(b"video"); cm.write_bytes(b"video")
    Image.new("RGB",(96,64),a).save(tmp_path/"source_frame.png"); Image.new("RGB",(96,64),b).save(tmp_path/"candidate_frame.png")
    s=ProductionStore(p).add_take(sm,scene_id="s",shot_id="q",copy_media=False)
    c=ProductionStore(p).add_take(cm,scene_id="s",shot_id="q",copy_media=False)
    contract={"source_take_id":s.id,"preserve":{"characters":[{"character_id":"char_sarah"}],"location":"room","objects":[{"name":"mug"}],"lighting":"warm"}}
    return p,s,c,contract

def fake_sampler(tmp_path):
    def sample(media,dest,seconds):
        src=tmp_path/("source_frame.png" if "source" in media.name else "candidate_frame.png")
        dest.parent.mkdir(parents=True,exist_ok=True); Image.open(src).save(dest); return dest
    return sample

def test_identical_frames_pass_global_check_but_semantics_stay_review_required(tmp_path,monkeypatch):
    p,s,c,contract=setup(tmp_path); monkeypatch.setattr("film_lab.visual_continuity_certification._sample_frame",fake_sampler(tmp_path))
    r=certify_visual_continuity(p,source_take_id=s.id,candidate_take_id=c.id,contract=contract)
    assert r["domains"]["global_frame_similarity"]["status"]=="PASS"
    assert r["status"]=="PARTIAL" and r["domains"]["character_identity"]["status"]=="REVIEW_REQUIRED"

def test_large_visual_drift_is_flagged(tmp_path,monkeypatch):
    p,s,c,contract=setup(tmp_path,(0,0,0),(255,255,255)); monkeypatch.setattr("film_lab.visual_continuity_certification._sample_frame",fake_sampler(tmp_path))
    r=certify_visual_continuity(p,source_take_id=s.id,candidate_take_id=c.id,contract=contract)
    assert r["status"]=="FAIL" and r["visual_drift"][0]["severity"]=="HIGH"

def test_certification_persists_into_take_and_continuity_report(tmp_path,monkeypatch):
    p,s,c,contract=setup(tmp_path); monkeypatch.setattr("film_lab.visual_continuity_certification._sample_frame",fake_sampler(tmp_path))
    data=ProductionStore(p)._load(); data["takes"][c.id]["metadata"]={"continuity_contract":contract,"preview_playhead_s":1.25,"continuity_report":{"visual_certification":"NOT_TESTED"}}; ProductionStore(p)._save(data)
    r=certify_candidate_take(p,c.id); meta=ProductionStore(p).get_take(c.id).metadata
    assert meta["visual_continuity_certification"]["status"]==r["status"] and meta["continuity_report"]["visual_certification"]=="PARTIAL"

def test_missing_media_returns_not_tested_not_fake_pass(tmp_path):
    p,s,c,contract=setup(tmp_path); (tmp_path/"candidate.mp4").unlink()
    r=certify_visual_continuity(p,source_take_id=s.id,candidate_take_id=c.id,contract=contract)
    assert r["status"]=="NOT_TESTED" and "no visual continuity claim" in r["truth"]
