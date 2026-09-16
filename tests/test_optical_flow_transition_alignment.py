from pathlib import Path
from types import SimpleNamespace
import film_lab.optical_flow_transition_alignment as o


def test_capability_available_only_when_filter_proven(monkeypatch):
    monkeypatch.setattr(o,"ffmpeg_filter_available",lambda n:(True,"minterpolate evidence"))
    c=o.inspect_optical_flow_capability()
    assert c.status == "PASS" and c.enforcement == "AVAILABLE"
    assert c.filter_name == "minterpolate"


def test_capability_truthful_when_filter_missing(monkeypatch):
    monkeypatch.setattr(o,"ffmpeg_filter_available",lambda n:(False,"missing"))
    c=o.inspect_optical_flow_capability()
    assert c.enforcement == "NOT_ENFORCED"
    assert c.status == "NOT_TESTED"


def test_minterpolate_filter_has_motion_compensation():
    f=o.minterpolate_filter(60)
    assert "minterpolate=fps=60.000" in f and "mi_mode=mci" in f and "me_mode=bidir" in f


def test_optical_flow_reassembly_requires_and_executes_filter(monkeypatch,tmp_path):
    import film_lab.intelligent_seam_blending as s
    import film_lab.motion_retiming_transition_alignment as mr
    src=tmp_path/"src.mp4"; rep=tmp_path/"rep.mp4"; src.write_bytes(b"x"); rep.write_bytes(b"y")
    take1=SimpleNamespace(id="s",media_path=str(src),scene_id="sc",shot_id="sh",name="Source",duration=6)
    take2=SimpleNamespace(id="r",media_path=str(rep),scene_id="sc",shot_id="sh",name="Repair",duration=6)
    class Store:
        def __init__(self,p): pass
        def get_take(self,i): return take1 if i=="s" else take2
        def add_take(self,path,**kw): return SimpleNamespace(id="a",media_path=str(path),scene_id="sc",shot_id="sh")
        def _load(self): return {"takes":{"a":{"metadata":{"optical_flow_transition_alignment":{}}}}}
        def _save(self,d): pass
    project=SimpleNamespace(root=tmp_path,takes_dir=tmp_path/"takes")
    monkeypatch.setattr(s,"ProductionStore",Store); monkeypatch.setattr(s,"probe_has_audio",lambda p:True); monkeypatch.setattr(s,"probe_duration_seconds",lambda p:6.0)
    monkeypatch.setattr(s,"analyze_motion_seams",lambda *a,**k:SimpleNamespace(recommended_blend_s=.1,to_dict=lambda:{"status":"PASS"}))
    monkeypatch.setattr(mr,"analyze_motion_retiming",lambda *a,**k:mr.MotionRetimingPlan(2,4,2.1,3.9,.9,None,None,"PASS","AVAILABLE","ok"))
    monkeypatch.setattr(o,"ffmpeg_filter_available",lambda n:(True,"proven"))
    monkeypatch.setattr(s,"_certify_assembled_boundaries",lambda *a,**k:{"status":"PASS","checks":{}})
    seen={}
    def ff(args):
        seen["args"]=args; Path(args[-1]).parent.mkdir(parents=True,exist_ok=True); Path(args[-1]).write_bytes(b"z")
    monkeypatch.setattr(s,"run_ffmpeg",ff)
    assembled,meta=s.reassemble_optical_flow_aligned_audio_visual_segment(project,source_take_id="s",repair_take_id="r",window_start_s=2,window_end_s=4)
    filt=seen["args"][seen["args"].index("-filter_complex")+1]
    assert "minterpolate=" in filt
    assert meta["optical_flow_status"] == "ENFORCED"
