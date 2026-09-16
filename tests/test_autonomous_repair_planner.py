from film_lab.project import Project
from film_lab.production import ProductionStore
from film_lab.director_preview_regeneration import DirectorPreviewStore, ABReview
from film_lab.autonomous_repair_planner import run_multi_pass_repair, qc_penalty, MultiPassRepairStore

def setup(tmp_path, events, selected=False):
    p=Project('p',tmp_path/'p'); p.ensure_dirs(); media=tmp_path/'a.mp4'; media.write_bytes(b'x'); s=ProductionStore(p)
    src=s.add_take(media,shot_id='shot_1',copy_media=False); cand=s.add_take(media,shot_id='shot_1',copy_media=False,metadata={'full_take_continuity_scan':{'events':events}})
    if selected: s.set_status(src.id,'selected')
    DirectorPreviewStore(p).save(ABReview(src.scene_id,src.shot_id,src.id,cand.id,src.media_path,cand.media_path,0,{},status='READY'))
    return p,src,cand

def executor_with(events_by_pass):
    state={'i':0}
    def ex(project,generator,decision):
        s=ProductionStore(project); src=s.get_take(decision.candidate_take_id); media=src.media_path
        ev=events_by_pass[state['i']]; state['i']+=1
        new=s.add_take(media,shot_id=src.shot_id,scene_id=src.scene_id,copy_media=False,metadata={'continuity_repair_scan':{'events':ev}})
        return new,{'status':'REVIEW' if ev else 'PASS'}
    return ex

def test_qc_penalty_weights_severity():
    assert qc_penalty([{'severity':'LOW'},{'severity':'HIGH'}])==8.0

def test_multi_pass_promotes_only_improvements(tmp_path):
    p,_,c=setup(tmp_path,[{'time_s':1,'domain':'camera','severity':'HIGH'}])
    plan=run_multi_pass_repair(p,generator=None,max_passes=3,repair_executor=executor_with([[]]))
    assert plan.status=='PASS' and plan.best_take_id!=c.id and plan.passes[0].outcome=='IMPROVED'

def test_regression_is_not_promoted(tmp_path):
    p,_,c=setup(tmp_path,[{'time_s':1,'domain':'camera','severity':'HIGH'}])
    worse=[{'time_s':1,'domain':'camera','severity':'HIGH'},{'time_s':2,'domain':'registered_visual_target','target_id':'bag','severity':'HIGH'}]
    plan=run_multi_pass_repair(p,generator=None,repair_executor=executor_with([worse]))
    assert plan.best_take_id==c.id and plan.passes[0].outcome=='REJECTED_REGRESSION'

def test_repair_budget_stops_loop(tmp_path):
    ev=[{'time_s':1,'domain':'camera','severity':'HIGH'},{'time_s':2,'domain':'camera','severity':'MEDIUM'}]
    p,_,_=setup(tmp_path,ev)
    one=[{'time_s':2,'domain':'camera','severity':'MEDIUM'}]
    two=[{'time_s':3,'domain':'camera','severity':'LOW'}]
    plan=run_multi_pass_repair(p,generator=None,max_passes=2,min_improvement=.5,repair_executor=executor_with([one,two]))
    assert len(plan.passes)==2 and 'budget' in plan.stop_reason.lower()

def test_never_changes_selected_take_and_persists_history(tmp_path):
    p,src,_=setup(tmp_path,[{'time_s':1,'domain':'camera','severity':'HIGH'}],selected=True)
    plan=run_multi_pass_repair(p,generator=None,repair_executor=executor_with([[]]))
    assert ProductionStore(p).selected_takes(existing_media_only=False)[0].id==src.id
    loaded=MultiPassRepairStore(p).load(); assert loaded.best_take_id==plan.best_take_id and not loaded.selected_take_changed
