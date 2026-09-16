from pathlib import Path
import numpy as np
from PIL import Image
from film_lab.project import Project
import film_lab.motion_aware_seam_matching as ms


def _img(path, x):
    a=np.zeros((80,120),dtype=np.uint8); a[25:55,x:x+20]=220; Image.fromarray(a).save(path)

def test_translation_estimator_follows_motion(tmp_path):
    a=tmp_path/'a.png'; b=tmp_path/'b.png'; _img(a,30); _img(b,34)
    dx,dy=ms._estimate_translation(a,b)
    assert dx > 0 and abs(dy) < .02

def test_motion_plan_pass_for_matching_vectors(tmp_path,monkeypatch):
    p=Project('p',tmp_path/'p'); p.ensure_dirs(); src=p.root/'s.mp4'; rep=p.root/'r.mp4'; src.write_bytes(b'x'); rep.write_bytes(b'x')
    monkeypatch.setattr(ms,'_boundary',lambda project,s,r,name,t,d: ms.MotionBoundaryEvidence(name,t,(.02,0),(.021,0),.001,.99,'PASS'))
    plan=ms.analyze_motion_seams(p,src,rep,window_start_s=2,window_end_s=4,requested_blend_s=.12)
    assert plan.status=='PASS' and plan.recommended_blend_s==.12

def test_motion_plan_increases_blend_for_review(tmp_path,monkeypatch):
    p=Project('p',tmp_path/'p'); p.ensure_dirs(); src=p.root/'s.mp4'; rep=p.root/'r.mp4'; src.write_bytes(b'x'); rep.write_bytes(b'x')
    monkeypatch.setattr(ms,'_boundary',lambda project,s,r,name,t,d: ms.MotionBoundaryEvidence(name,t,(.01,0),(.05,0),.04,1.0,'REVIEW'))
    plan=ms.analyze_motion_seams(p,src,rep,window_start_s=2,window_end_s=4,requested_blend_s=.1)
    assert plan.status=='REVIEW' and plan.recommended_blend_s>.1
