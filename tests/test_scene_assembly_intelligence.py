from film_lab.project import Project
from film_lab.production import ProductionStore
from film_lab.scene_assembly_intelligence import evaluate_scene, evaluate_cut
import film_lab.scene_assembly_intelligence as sai


def _p(tmp_path):
    p=Project('p',tmp_path/'p'); p.ensure_dirs(); return p

def _selected(p,shot,name,events=None):
    media=p.root/f'{name}.mp4'; media.write_bytes(b'video')
    meta={'full_take_continuity_scan':{'events':events or []}}
    t=ProductionStore(p).add_take(media,scene_id='scene_1',shot_id=shot,copy_media=False,metadata=meta,duration=2.0)
    return ProductionStore(p).set_status(t.id,'selected')

def test_scene_fails_when_a_shot_has_no_selected_take(tmp_path):
    p=_p(tmp_path); _selected(p,'shot_1','a'); store=ProductionStore(p); store.ensure_shot('shot_2',scene_id='scene_1')
    r=evaluate_scene(p,'scene_1')
    assert r.status=='FAIL' and r.missing_selected_shots==('shot_2',) and not r.cinema_ready

def test_single_selected_shot_is_structurally_ready(tmp_path):
    p=_p(tmp_path); t=_selected(p,'shot_1','a')
    r=evaluate_scene(p,'scene_1')
    assert r.status=='PASS' and r.cinema_ready and r.selected_take_ids==(t.id,)

def test_cut_does_not_change_selected_takes(tmp_path,monkeypatch):
    p=_p(tmp_path); a=_selected(p,'shot_1','a'); b=_selected(p,'shot_2','b')
    monkeypatch.setattr(sai,'_sample_frame',lambda media,dest,seconds: dest)
    class M:
        def to_dict(self): return {'perceptual_similarity':.95}
    monkeypatch.setattr(sai,'_metrics',lambda a,b:M()); monkeypatch.setattr(sai,'_global_status',lambda m:'PASS')
    r=evaluate_scene(p,'scene_1')
    assert r.status=='REVIEW' and r.cinema_ready and len(r.cut_reports)==1
    assert ProductionStore(p).get_take(a.id).status=='selected' and ProductionStore(p).get_take(b.id).status=='selected'

def test_severe_persisted_event_marks_cut_for_review(tmp_path,monkeypatch):
    p=_p(tmp_path); a=_selected(p,'shot_1','a',[{'severity':'HIGH','domain':'camera'}]); b=_selected(p,'shot_2','b')
    monkeypatch.setattr(sai,'_sample_frame',lambda media,dest,seconds: dest)
    class M:
        def to_dict(self): return {}
    monkeypatch.setattr(sai,'_metrics',lambda a,b:M()); monkeypatch.setattr(sai,'_global_status',lambda m:'PASS')
    c=evaluate_cut(p,a,b)
    assert c.status=='REVIEW' and any(x['domain']=='persisted_continuity' for x in c.issues)
