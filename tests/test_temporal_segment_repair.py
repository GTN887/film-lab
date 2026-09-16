from pathlib import Path
from film_lab.project import Project
from film_lab.production import ProductionStore
import film_lab.temporal_segment_repair as tsr


def _project(tmp_path):
    p=Project("p",tmp_path/"p"); p.ensure_dirs(); return p

def _take(store,tmp_path,name):
    f=tmp_path/f"{name}.mp4"; f.write_bytes(b"video")
    return store.add_take(f,scene_id="s1",shot_id="sh1",name=name,duration=10.0)

def test_segment_reassembly_preserves_source_outside_window_and_audio_truth(tmp_path,monkeypatch):
    p=_project(tmp_path); store=ProductionStore(p); src=_take(store,tmp_path,"source"); rep=_take(store,tmp_path,"repair")
    calls=[]
    def fake_ffmpeg(args,**kw):
        calls.append(args); Path(args[-1]).write_bytes(b"assembled")
    monkeypatch.setattr(tsr,"run_ffmpeg",fake_ffmpeg)
    monkeypatch.setattr(tsr,"probe_duration_seconds",lambda path:10.0)
    monkeypatch.setattr(tsr,"_boundary_evidence",lambda *a,**k:{"status":"PASS","checks":{},"method":"test"})
    take,res=tsr.reassemble_visual_segment(p,source_take_id=src.id,repair_take_id=rep.id,window_start_s=3.5,window_end_s=4.5)
    assert Path(take.media_path).is_file(); assert res.video_patch_status=="ENFORCED"
    assert res.audio_patch_status=="SOURCE_AUDIO_PRESERVED"
    joined=" ".join(calls[0]); assert "trim=start=0:end=3.500000" in joined and "trim=start=4.500000" in joined
    assert "0:a?" in calls[0]

def test_segment_window_is_clamped_to_source_duration(tmp_path,monkeypatch):
    p=_project(tmp_path); store=ProductionStore(p); src=_take(store,tmp_path,"source"); rep=_take(store,tmp_path,"repair")
    monkeypatch.setattr(tsr,"run_ffmpeg",lambda args,**kw: Path(args[-1]).write_bytes(b"x"))
    monkeypatch.setattr(tsr,"probe_duration_seconds",lambda path:5.0)
    monkeypatch.setattr(tsr,"_boundary_evidence",lambda *a,**k:{"status":"PASS","checks":{},"method":"test"})
    _,res=tsr.reassemble_visual_segment(p,source_take_id=src.id,repair_take_id=rep.id,window_start_s=4.0,window_end_s=8.0)
    assert res.window_end_s==5.0

def test_invalid_segment_window_rejected(tmp_path,monkeypatch):
    p=_project(tmp_path); store=ProductionStore(p); src=_take(store,tmp_path,"source"); rep=_take(store,tmp_path,"repair")
    monkeypatch.setattr(tsr,"probe_duration_seconds",lambda path:10.0)
    try: tsr.reassemble_visual_segment(p,source_take_id=src.id,repair_take_id=rep.id,window_start_s=5,window_end_s=4)
    except ValueError: pass
    else: raise AssertionError("invalid window should fail")

def test_boundary_evidence_can_require_review(tmp_path,monkeypatch):
    p=_project(tmp_path); a=tmp_path/"a.mp4"; b=tmp_path/"b.mp4"; a.write_bytes(b"a"); b.write_bytes(b"b")
    monkeypatch.setattr(tsr,"_sample_frame",lambda media,dest,seconds: (dest.write_bytes(b"x") or dest))
    class M:
        perceptual_similarity=.5; histogram_similarity=.5
        def to_dict(self): return {"perceptual_similarity":.5,"histogram_similarity":.5}
    monkeypatch.setattr(tsr,"_metrics",lambda a,b:M())
    ev=tsr._boundary_evidence(p,a,b,2,3); assert ev["status"]=="REVIEW"

def test_av_segment_repair_replaces_only_localized_audio_and_video(tmp_path,monkeypatch):
    p=_project(tmp_path); store=ProductionStore(p); src=_take(store,tmp_path,"sourceav"); rep=_take(store,tmp_path,"repairav")
    calls=[]
    monkeypatch.setattr(tsr,"probe_has_audio",lambda path: True)
    monkeypatch.setattr(tsr,"probe_duration_seconds",lambda path:10.0)
    monkeypatch.setattr(tsr,"_boundary_evidence",lambda *a,**k:{"status":"PASS","checks":{},"method":"test"})
    monkeypatch.setattr(tsr,"run_ffmpeg",lambda args,**kw:(calls.append(args),Path(args[-1]).write_bytes(b"av")))
    take,res=tsr.reassemble_audio_visual_segment(p,source_take_id=src.id,repair_take_id=rep.id,window_start_s=2.0,window_end_s=3.0)
    assert Path(take.media_path).is_file(); assert res.audio_patch_status=="ENFORCED"
    joined=" ".join(calls[0]); assert "atrim=start=0:end=2.000000" in joined and "[1:a]atrim=start=2.000000:end=3.000000" in joined

def test_av_segment_repair_refuses_unproven_repair_audio(tmp_path,monkeypatch):
    p=_project(tmp_path); store=ProductionStore(p); src=_take(store,tmp_path,"source-noa"); rep=_take(store,tmp_path,"repair-noa")
    monkeypatch.setattr(tsr,"probe_has_audio",lambda path: path.name.startswith("source"))
    try: tsr.reassemble_audio_visual_segment(p,source_take_id=src.id,repair_take_id=rep.id,window_start_s=2,end=3)
    except TypeError: pass
    else: raise AssertionError("bad call should not pass")
    try: tsr.reassemble_audio_visual_segment(p,source_take_id=src.id,repair_take_id=rep.id,window_start_s=2,window_end_s=3)
    except ValueError as exc: assert "proven audio" in str(exc)
    else: raise AssertionError("missing repair audio must fail")
