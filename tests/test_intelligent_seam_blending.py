from pathlib import Path
import pytest
from film_lab.project import Project
from film_lab.production import ProductionStore
import film_lab.intelligent_seam_blending as sb

def _project(tmp_path):
    p=Project("p",tmp_path/"p"); p.ensure_dirs(); return p

def mk_take(p, name):
    f=p.root/f"{name}.mp4"; f.write_bytes(b"media")
    return ProductionStore(p).add_take(f,scene_id="s1",shot_id="sh1",name=name,duration=10)

def test_seam_blend_uses_xfade_and_acrossfade(tmp_path,monkeypatch):
    p=_project(tmp_path); src=mk_take(p,"src"); rep=mk_take(p,"rep"); seen={}
    monkeypatch.setattr(sb,"probe_has_audio",lambda x: True); monkeypatch.setattr(sb,"probe_duration_seconds",lambda x:10.0)
    class MP:
        recommended_blend_s=.1
        def to_dict(self): return {"status":"PASS","recommended_blend_s":.1}
    monkeypatch.setattr(sb,"analyze_motion_seams",lambda *a,**k: MP())
    monkeypatch.setattr(sb,"_certify_assembled_boundaries",lambda *a,**k:{"status":"PASS","checks":{},"method":"test"})
    def run(args):
        seen["args"]=args; Path(args[-1]).write_bytes(b"assembled")
    monkeypatch.setattr(sb,"run_ffmpeg",run)
    take,res=sb.reassemble_blended_audio_visual_segment(p,source_take_id=src.id,repair_take_id=rep.id,window_start_s=3,window_end_s=5,blend_duration_s=.1)
    fc=seen["args"][seen["args"].index("-filter_complex")+1]
    assert "xfade=" in fc and "acrossfade=" in fc
    assert res.visual_blend_status=="ENFORCED" and res.audio_blend_status=="ENFORCED"
    assert res.boundary_certification_status=="PASS" and take.id!=src.id

def test_seam_blend_refuses_unproven_audio(tmp_path,monkeypatch):
    p=_project(tmp_path); src=mk_take(p,"src"); rep=mk_take(p,"rep")
    monkeypatch.setattr(sb,"probe_has_audio",lambda x: False)
    with pytest.raises(ValueError,match="proven audio"):
        sb.reassemble_blended_audio_visual_segment(p,source_take_id=src.id,repair_take_id=rep.id,window_start_s=3,window_end_s=5)

def test_seam_blend_clamps_requested_blend(tmp_path,monkeypatch):
    p=_project(tmp_path); src=mk_take(p,"src"); rep=mk_take(p,"rep"); seen={}
    monkeypatch.setattr(sb,"probe_has_audio",lambda x: True); monkeypatch.setattr(sb,"probe_duration_seconds",lambda x:10.0)
    class MP:
        recommended_blend_s=.1
        def to_dict(self): return {"status":"PASS","recommended_blend_s":.1}
    monkeypatch.setattr(sb,"analyze_motion_seams",lambda *a,**k: MP())
    monkeypatch.setattr(sb,"_certify_assembled_boundaries",lambda *a,**k:{"status":"REVIEW","checks":{},"method":"test"})
    def run(args): seen["fc"]=args[args.index("-filter_complex")+1]; Path(args[-1]).write_bytes(b"x")
    monkeypatch.setattr(sb,"run_ffmpeg",run)
    _,res=sb.reassemble_blended_audio_visual_segment(p,source_take_id=src.id,repair_take_id=rep.id,window_start_s=.2,window_end_s=.6,blend_duration_s=2)
    assert res.blend_duration_s <= .1 and res.boundary_certification_status=="REVIEW"

def test_boundary_certification_truth_status(tmp_path,monkeypatch):
    p=_project(tmp_path); a=p.root/"a.mp4"; b=p.root/"b.mp4"; a.write_bytes(b"a"); b.write_bytes(b"b")
    class M:
        perceptual_similarity=.95; histogram_similarity=.95
        def to_dict(self): return {"perceptual_similarity":.95,"histogram_similarity":.95}
    monkeypatch.setattr(sb,"_sample_frame",lambda src,out,t: out.write_bytes(b"frame"))
    monkeypatch.setattr(sb,"_metrics",lambda a,b:M())
    ev=sb._certify_assembled_boundaries(p,a,b,3,5,.1)
    assert ev["status"]=="PASS" and set(ev["checks"])=={"entry","exit"}
