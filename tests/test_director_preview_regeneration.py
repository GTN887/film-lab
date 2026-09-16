from pathlib import Path
from film_lab.project import Project
from film_lab.production import ProductionStore
from film_lab.shot_card import ShotCard
from film_lab.performance_timeline import PerformanceTimelineStore, ActorPerformanceTimeline, PerformanceKeyframe
from film_lab.camera_timeline import CameraTimelineStore, CameraTimeline, CameraKeyframe
from film_lab.playback_sync import PlaybackSyncStore
from film_lab.director_preview_regeneration import capture_preview_context, regenerate_preview, DirectorPreviewStore, accept_candidate

class FakeGenerator:
    id="fake-preview"; label="Fake Preview"; model="fake-v1"
    def generate(self,job): job.output_path.parent.mkdir(parents=True,exist_ok=True); job.output_path.write_bytes(b"new-video"); return job.output_path

def setup(tmp_path):
    p=Project.create("preview",data_root=tmp_path/"projects"); p.save_shot(ShotCard(id="q",name="Shot",scene_id="s"))
    src=tmp_path/"source.mp4"; src.write_bytes(b"video")
    t=ProductionStore(p).add_take(src,scene_id="s",shot_id="q",copy_media=False,duration=6); ProductionStore(p).set_status(t.id,"selected")
    return p,t

def test_capture_context_at_playhead_keeps_character_and_camera_state(tmp_path):
    p,t=setup(tmp_path)
    PerformanceTimelineStore(p).save(ActorPerformanceTimeline("s","q","char_sarah","Sarah",(PerformanceKeyframe(2,emotion="afraid",action="backs away"),),"PROMPT_ONLY"))
    CameraTimelineStore(p).save(CameraTimeline("s","q",(CameraKeyframe(1,move="push in",follow_character_id="char_sarah"),),"DIRECTED"))
    c=capture_preview_context(p,"s","q",2)
    assert c.source_take_id==t.id and c.playhead_s==2
    assert c.performance_state[0]["character_id"]=="char_sarah" and c.camera_state["move"]=="push in"

def test_regeneration_forks_take_and_persists_ab_review_same_playhead(tmp_path,monkeypatch):
    p,source=setup(tmp_path); PlaybackSyncStore(p).save_playhead("s","q",3)
    def still(src,dst): dst.parent.mkdir(parents=True,exist_ok=True); dst.write_bytes(b"png"); return dst
    monkeypatch.setattr("film_lab.mark_direct_regenerate.still_from_source",still)
    r=regenerate_preview(p,scene_id="s",shot_id="q",generator=FakeGenerator(),director_instruction="Sarah becomes suspicious",playhead_s=3)
    assert r.source_take_id==source.id and r.candidate_take_id!=source.id and r.playhead_s==3
    assert Path(r.candidate_media_path).is_file() and DirectorPreviewStore(p).load().candidate_take_id==r.candidate_take_id
    assert ProductionStore(p).get_take(r.candidate_take_id).metadata["preview_playhead_s"]==3

def test_candidate_does_not_replace_selected_source_until_creator_accepts(tmp_path,monkeypatch):
    p,source=setup(tmp_path)
    monkeypatch.setattr("film_lab.mark_direct_regenerate.still_from_source",lambda s,d: (d.parent.mkdir(parents=True,exist_ok=True),d.write_bytes(b"png"),d)[-1])
    r=regenerate_preview(p,scene_id="s",shot_id="q",generator=FakeGenerator(),director_instruction="change",playhead_s=1)
    assert [t.id for t in ProductionStore(p).selected_takes()]==[source.id]
    chosen=accept_candidate(p,r)
    assert chosen.id==r.candidate_take_id and [t.id for t in ProductionStore(p).selected_takes()]==[r.candidate_take_id]

def test_capture_requires_real_selected_take(tmp_path):
    p=Project.create("empty",data_root=tmp_path/"projects")
    try: capture_preview_context(p,"s","q",1)
    except ValueError as e: assert "Selected Take" in str(e)
    else: raise AssertionError("expected truth gate")

def test_regeneration_persists_continuity_contract_and_candidate_report(tmp_path,monkeypatch):
    p,source=setup(tmp_path)
    monkeypatch.setattr("film_lab.mark_direct_regenerate.still_from_source",lambda s,d: (d.parent.mkdir(parents=True,exist_ok=True),d.write_bytes(b"png"),d)[-1])
    r=regenerate_preview(p,scene_id="s",shot_id="q",generator=FakeGenerator(),director_instruction="Sarah becomes suspicious",playhead_s=2)
    meta=ProductionStore(p).get_take(r.candidate_take_id).metadata
    assert meta["continuity_contract"]["source_take_id"]==source.id
    assert meta["continuity_report"]["candidate_take_id"]==r.candidate_take_id
    assert meta["continuity_report"]["visual_certification"]=="NOT_TESTED"
