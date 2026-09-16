from pathlib import Path
from PIL import Image
from film_lab.lighting_color_continuity import evaluate_lighting_color_frames

def _img(p:Path,c): Image.new('RGB',(80,50),c).save(p); return p

def test_matching_lighting_and_color_pass(tmp_path):
    a=_img(tmp_path/'a.png',(120,110,100)); b=_img(tmp_path/'b.png',(122,112,102))
    r=evaluate_lighting_color_frames(a,b)
    assert r.status=='PASS' and r.exposure_status=='PASS' and r.color_status=='PASS'

def test_large_exposure_jump_requires_review(tmp_path):
    a=_img(tmp_path/'a.png',(30,30,30)); b=_img(tmp_path/'b.png',(230,230,230))
    r=evaluate_lighting_color_frames(a,b)
    assert r.status=='REVIEW' and r.exposure_status=='REVIEW'
    assert any(x['domain']=='lighting_exposure' for x in r.issues)

def test_large_color_balance_jump_requires_review(tmp_path):
    a=_img(tmp_path/'a.png',(220,40,40)); b=_img(tmp_path/'b.png',(40,40,220))
    r=evaluate_lighting_color_frames(a,b)
    assert r.color_status=='REVIEW' and r.metrics['color_balance_delta']>.1

def test_intentional_change_is_recorded_not_silently_passed(tmp_path):
    a=_img(tmp_path/'a.png',(25,25,25)); b=_img(tmp_path/'b.png',(240,180,120))
    r=evaluate_lighting_color_frames(a,b,allow_change=True)
    assert r.status=='REVIEW' and r.metrics['intentional_change_allowed'] is True
    assert all(x['severity']!='HIGH' for x in r.issues)
