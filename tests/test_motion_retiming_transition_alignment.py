from pathlib import Path
from types import SimpleNamespace
import film_lab.motion_retiming_transition_alignment as m


def test_retiming_plan_detects_early_late_alignment(monkeypatch,tmp_path):
    project=SimpleNamespace(root=tmp_path)
    monkeypatch.setattr(m,"_sample_frame",lambda *a,**k: None)
    # Best entry at +.10 and exit at -.05.
    def fake_score(a,b):
        name=b.name
        idx=int(name.rsplit("_",1)[1].split(".")[0])
        boundary="entry" if "entry" in name else "exit"
        target=8 if boundary=="entry" else 5  # steps radius .30/.05 => center 6
        return 1.0-abs(idx-target)*.05
    monkeypatch.setattr(m,"_score",fake_score)
    p=m.analyze_motion_retiming(project,Path("s.mp4"),Path("r.mp4"),window_start_s=2,window_end_s=5,repair_duration_s=8)
    assert p.entry.offset_s == .1
    assert p.exit.offset_s == -.05
    assert p.speed_factor != 1.0
    assert p.enforcement == "AVAILABLE"


def test_retiming_failure_is_truthful(monkeypatch,tmp_path):
    project=SimpleNamespace(root=tmp_path)
    monkeypatch.setattr(m,"_sample_frame",lambda *a,**k: (_ for _ in ()).throw(RuntimeError("decoder")))
    p=m.analyze_motion_retiming(project,Path("s"),Path("r"),window_start_s=1,window_end_s=2)
    assert p.status == "NOT_TESTED"
    assert p.enforcement == "NOT_ENFORCED"


def test_retiming_guardrail_blocks_extreme_speed(monkeypatch,tmp_path):
    project=SimpleNamespace(root=tmp_path)
    monkeypatch.setattr(m,"_align_boundary",lambda project,source,repair,name,source_t,**k:
        m.BoundaryAlignment(name,source_t,0.0 if name=="entry" else 3.0,0,1.0,"PASS"))
    p=m.analyze_motion_retiming(project,Path("s"),Path("r"),window_start_s=1,window_end_s=2,repair_duration_s=4)
    assert p.enforcement == "UNSAFE_RETIME"
    assert p.status == "FAIL"

def test_motion_aligned_reassembly_uses_retime_filter(monkeypatch,tmp_path):
    import film_lab.intelligent_seam_blending as s
    src=tmp_path/"src.mp4"; rep=tmp_path/"rep.mp4"; src.write_bytes(b"x"); rep.write_bytes(b"y")
    take1=SimpleNamespace(id="s",media_path=str(src),scene_id="sc",shot_id="sh",name="Source",duration=6)
    take2=SimpleNamespace(id="r",media_path=str(rep),scene_id="sc",shot_id="sh",name="Repair",duration=6)
    class Store:
        def __init__(self,p): self.p=p
        def get_take(self,i): return take1 if i=="s" else take2
        def add_take(self,path,**kw): return SimpleNamespace(id="a",media_path=str(path),scene_id="sc",shot_id="sh")
        def _load(self): return {"takes":{"a":{"metadata":{"motion_retiming_transition_alignment":{}}}}}
        def _save(self,d): pass
    project=SimpleNamespace(root=tmp_path,takes_dir=tmp_path/"takes")
    monkeypatch.setattr(s,"ProductionStore",Store); monkeypatch.setattr(s,"probe_has_audio",lambda p: True); monkeypatch.setattr(s,"probe_duration_seconds",lambda p: 6.0)
    monkeypatch.setattr(s,"analyze_motion_seams",lambda *a,**k: SimpleNamespace(recommended_blend_s=.1,to_dict=lambda:{"status":"PASS"}))
    import film_lab.motion_retiming_transition_alignment as mr
    monkeypatch.setattr(mr,"analyze_motion_retiming",lambda *a,**k: mr.MotionRetimingPlan(2,4,2.1,3.9,.9,None,None,"PASS","AVAILABLE","ok"))
    monkeypatch.setattr(s,"_certify_assembled_boundaries",lambda *a,**k:{"status":"PASS","checks":{}})
    seen={}
    def ff(args):
        seen["args"]=args; Path(args[-1]).parent.mkdir(parents=True,exist_ok=True); Path(args[-1]).write_bytes(b"z")
    monkeypatch.setattr(s,"run_ffmpeg",ff)
    assembled,meta=s.reassemble_motion_aligned_blended_audio_visual_segment(project,source_take_id="s",repair_take_id="r",window_start_s=2,window_end_s=4,blend_duration_s=.1)
    filt=seen["args"][seen["args"].index("-filter_complex")+1]
    assert "atempo=" in filt and "setpts=(PTS-STARTPTS)/" in filt
    assert meta["retiming_status"] == "ENFORCED"
