from pathlib import Path
from film_lab.project import Project
from film_lab.production import ProductionStore
from film_lab.take_quality_control import diagnose_take, TakeQualityControlStore

def mk(tmp_path,events):
 p=Project('p',tmp_path/'p'); p.ensure_dirs(); media=tmp_path/'x.mp4'; media.write_bytes(b'x')
 t=ProductionStore(p).add_take(media,shot_id='shot_1',copy_media=False,metadata={'full_take_continuity_scan':{'events':events}}); return p,t

def test_target_loss_selects_regional_repair(tmp_path):
 p,t=mk(tmp_path,[{'time_s':4.2,'domain':'registered_visual_target','target_id':'prop_bag','severity':'HIGH','message':'bag lost'}])
 d=diagnose_take(p,t.id); assert d.strategy=='REGIONAL_TARGET_REPAIR'; assert d.event_index==0; assert d.time_s==4.2; assert d.requires_creator_approval
 assert TakeQualityControlStore(p).load().candidate_take_id==t.id

def test_multiple_severe_domains_recommend_full_regeneration(tmp_path):
 ev=[{'time_s':1,'domain':'camera','severity':'HIGH'},{'time_s':2,'domain':'registered_visual_target','severity':'HIGH'},{'time_s':3,'domain':'camera','severity':'HIGH'}]
 p,t=mk(tmp_path,ev); d=diagnose_take(p,t.id); assert d.strategy=='REGENERATE_TAKE'; assert d.automatic_action=='FORK_FULL_CANDIDATE'

def test_no_events_passes_without_repair(tmp_path):
 p,t=mk(tmp_path,[]); d=diagnose_take(p,t.id); assert d.status=='PASS'; assert d.automatic_action=='NO_REPAIR'

def test_untimed_track_event_does_not_fake_localization(tmp_path):
 p,t=mk(tmp_path,[{'time_s':None,'domain':'target_position_track','severity':'MEDIUM'}]); d=diagnose_take(p,t.id)
 assert d.automatic_action=='MANUAL_REVIEW'; assert d.event_index is None
