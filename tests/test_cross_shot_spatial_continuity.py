from film_lab.production import Take
from film_lab.cross_shot_spatial_continuity import evaluate_cross_shot_spatial

def _take(tid, points, *, eye_out='', eye_in=''):
    target={'target':{'id':'char_sarah'},'candidate_track':{'points':[{'bbox':b,'status':'TRACKED'} for b in points]}}
    meta={'full_take_continuity_scan':{'targets':[target]},'cross_shot_spatial_intent':{'eyeline_out':eye_out,'eyeline_in':eye_in}}
    return Take(tid,'scene','shot','/tmp/x.mp4',metadata=meta)

def test_matching_motion_direction_passes_screen_direction():
    a=_take('a',[(.1,.3,.3,.7),(.2,.3,.4,.7)])
    b=_take('b',[(.2,.3,.4,.7),(.3,.3,.5,.7)])
    r=evaluate_cross_shot_spatial(a,b)
    assert r.screen_direction_status=='PASS' and r.position_status=='PASS'

def test_reversed_motion_is_review_not_automatic_failure():
    a=_take('a',[(.1,.3,.3,.7),(.2,.3,.4,.7)])
    b=_take('b',[(.2,.3,.4,.7),(.1,.3,.3,.7)])
    r=evaluate_cross_shot_spatial(a,b)
    assert r.screen_direction_status=='REVIEW'
    assert any(x['domain']=='screen_direction' for x in r.issues)

def test_explicit_opposed_eyelines_pass():
    a=_take('a',[(.1,.3,.3,.7),(.2,.3,.4,.7)],eye_out='RIGHT')
    b=_take('b',[(.2,.3,.4,.7),(.3,.3,.5,.7)],eye_in='LEFT')
    assert evaluate_cross_shot_spatial(a,b).eyeline_status=='PASS'

def test_missing_tracking_and_eyeline_remains_not_tested_or_review():
    a=Take('a','scene','shot','/tmp/a.mp4'); b=Take('b','scene','shot2','/tmp/b.mp4')
    r=evaluate_cross_shot_spatial(a,b)
    assert r.status=='NOT_TESTED'
    assert r.screen_direction_status=='NOT_TESTED' and r.eyeline_status=='NOT_TESTED'
