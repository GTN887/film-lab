from pathlib import Path
from film_lab.project import Project
from film_lab.production import ProductionStore
from film_lab.shot_readiness import score_take,evaluate_shot

def _p(tmp_path):
    p=Project('p',tmp_path/'p'); p.ensure_dirs(); return p

def _take(p,name,events=None,selected=False):
    media=p.root/f'{name}.mp4'; media.write_bytes(b'video')
    meta={} if events is None else {'full_take_continuity_scan':{'events':events}}
    t=ProductionStore(p).add_take(media,scene_id='scene_1',shot_id='shot_1',copy_media=False,metadata=meta)
    if selected: t=ProductionStore(p).set_status(t.id,'selected')
    return t

def test_score_penalizes_severe_events(tmp_path):
    p=_p(tmp_path); clean=_take(p,'clean',[]); bad=_take(p,'bad',[{'severity':'HIGH','domain':'camera'}])
    assert score_take(clean).score > score_take(bad).score
    assert score_take(bad).severe_events==1

def test_missing_scan_is_not_tested(tmp_path):
    p=_p(tmp_path); t=_take(p,'unknown',None,True); r=evaluate_shot(p,'scene_1','shot_1')
    assert r.status=='NOT TESTED' and r.selected_take_id==t.id

def test_recommends_better_take_without_selecting_it(tmp_path):
    p=_p(tmp_path); selected=_take(p,'selected',[{'severity':'HIGH','domain':'camera'}],True); better=_take(p,'better',[])
    r=evaluate_shot(p,'scene_1','shot_1'); assert r.status=='REVIEW'; assert r.recommended_take_id==better.id
    assert ProductionStore(p).get_take(selected.id).status=='selected'
    assert ProductionStore(p).get_take(better.id).status=='review'

def test_pass_requires_selected_media_and_clean_scan(tmp_path):
    p=_p(tmp_path); t=_take(p,'clean',[],True); r=evaluate_shot(p,'scene_1','shot_1')
    assert r.status=='PASS' and r.selected_take_id==t.id and r.recommendation_requires_creator_approval
