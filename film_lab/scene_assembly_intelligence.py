"""Scene Assembly Intelligence for consecutive Selected Takes.

Evaluates whether selected shots in one scene are technically ready to cut together.
It is advisory and non-destructive: it never changes Take selection or renders Cinema.
Automated visual evidence is boundary-frame evidence, not semantic identity proof.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any
import json

from film_lab.production import ProductionStore, Take
from film_lab.ffmpeg_support import probe_duration_seconds
from film_lab.visual_continuity_certification import _sample_frame, _metrics, _global_status
from film_lab.cross_shot_spatial_continuity import evaluate_cross_shot_spatial
from film_lab.camera_geography import evaluate_camera_geography
from film_lab.lighting_color_continuity import evaluate_lighting_color_frames
from film_lab.audio_cut_continuity import evaluate_audio_cut
from film_lab.room_tone import RoomToneStore

@dataclass(frozen=True)
class CutReport:
    from_shot_id: str
    to_shot_id: str
    from_take_id: str
    to_take_id: str
    status: str
    visual_status: str
    semantic_status: str
    audio_status: str
    spatial_status: str
    metrics: dict[str, Any]
    issues: tuple[dict[str, Any], ...]
    truth: str
    def to_dict(self):
        d=asdict(self); d['issues']=[dict(x) for x in self.issues]; return d

@dataclass(frozen=True)
class SceneAssemblyReport:
    scene_id: str
    status: str
    selected_take_ids: tuple[str, ...]
    cut_reports: tuple[CutReport, ...]
    missing_selected_shots: tuple[str, ...]
    cinema_ready: bool
    requires_creator_approval: bool
    reasons: tuple[str, ...]
    truth: str
    room_tone_status: str = 'NOT TESTED'
    room_tone_path: str = ''
    def to_dict(self):
        d=asdict(self); d['selected_take_ids']=list(self.selected_take_ids); d['cut_reports']=[x.to_dict() for x in self.cut_reports]; d['missing_selected_shots']=list(self.missing_selected_shots); d['reasons']=list(self.reasons); return d

class SceneAssemblyStore:
    def __init__(self, project):
        self.project=project; project.ensure_dirs(); self.path=project.root/'scene_assembly.json'
    def save(self, report:SceneAssemblyReport):
        data={}
        if self.path.exists():
            try: data=json.loads(self.path.read_text(encoding='utf-8'))
            except (OSError,json.JSONDecodeError): data={}
        data[report.scene_id]=report.to_dict()
        tmp=self.path.with_suffix('.json.tmp'); tmp.write_text(json.dumps(data,indent=2,sort_keys=True)+'\n',encoding='utf-8'); tmp.replace(self.path); return report

def _scene_shots(store:ProductionStore, scene_id:str)->list[dict[str,Any]]:
    raw=store._load()
    shots=[x for x in raw.get('shots',{}).values() if str(x.get('scene_id'))==scene_id]
    return sorted(shots,key=lambda x:(str(x.get('created_at','')),str(x.get('id',''))))

def _selected_for(store:ProductionStore, scene_id:str, shot_id:str)->Take|None:
    return next((t for t in store.list_takes(shot_id=shot_id,existing_media_only=False) if t.scene_id==scene_id and t.status=='selected'),None)

def _semantic_boundary_evidence(a:Take,b:Take)->tuple[str,list[dict[str,Any]]]:
    """Use persisted machine evidence conservatively; never infer semantics from pixels."""
    issues=[]
    for take,label in ((a,'outgoing'),(b,'incoming')):
        meta=take.metadata if isinstance(take.metadata,dict) else {}
        scan=meta.get('full_take_continuity_scan') or meta.get('continuity_repair_scan') or {}
        events=list(scan.get('events',[]) or []) if isinstance(scan,dict) else []
        severe=[e for e in events if str(e.get('severity','')).upper() in {'HIGH','CRITICAL'}]
        if severe: issues.append({'domain':'persisted_continuity','severity':'HIGH','message':f'{label.title()} Take has {len(severe)} HIGH/CRITICAL continuity event(s).','take_id':take.id})
    if issues: return 'REVIEW',issues
    return 'REVIEW_REQUIRED',[{'domain':'semantic_continuity','severity':'REVIEW','message':'Character identity, wardrobe, props, blocking, lighting, camera intent and story continuity require specialized evidence or Director review across this cut.'}]

def _audio_boundary_evidence(a:Take,b:Take)->tuple[str,list[dict[str,Any]],dict[str,Any]]:
    report=evaluate_audio_cut(a,b)
    return report.status,list(report.issues),report.to_dict()

def evaluate_cut(project,a:Take,b:Take)->CutReport:
    issues=[]; metrics={}
    if not Path(a.media_path).is_file() or not Path(b.media_path).is_file():
        missing=[t.id for t in (a,b) if not Path(t.media_path).is_file()]
        return CutReport(a.shot_id,b.shot_id,a.id,b.id,'FAIL','NOT_TESTED','NOT_TESTED','NOT_TESTED','NOT_TESTED',{},({'domain':'media','severity':'CRITICAL','message':f'Missing Take media: {", ".join(missing)}'},),'Cut cannot be evaluated or assembled when selected media is missing.')
    root=project.root/'scene_assembly_frames'/f'{a.id}__{b.id}'; root.mkdir(parents=True,exist_ok=True)
    duration=a.duration if a.duration and a.duration>0 else probe_duration_seconds(Path(a.media_path))
    if duration is None:
        visual='NOT_TESTED'; issues.append({'domain':'visual_boundary','severity':'REVIEW','message':'Outgoing Take duration could not be proven, so its end frame was not sampled.'})
    else:
        try:
            af=_sample_frame(Path(a.media_path),root/'outgoing.png',max(0.0,float(duration)-0.08))
            bf=_sample_frame(Path(b.media_path),root/'incoming.png',0.04)
            m=_metrics(af,bf); metrics=m.to_dict(); visual=_global_status(m)
            if visual=='FAIL': issues.append({'domain':'visual_boundary','severity':'HIGH','message':'Large whole-frame change detected across the cut. This may be intentional, but requires Director review.'})
            elif visual=='REVIEW': issues.append({'domain':'visual_boundary','severity':'MEDIUM','message':'Meaningful whole-frame change detected across the cut; review composition/motion continuity.'})
        except Exception as exc:
            visual='NOT_TESTED'; issues.append({'domain':'visual_boundary','severity':'REVIEW','message':f'Boundary frames could not be certified: {exc}'})
    semantic,sem_issues=_semantic_boundary_evidence(a,b); issues.extend(sem_issues)
    audio,aud_issues,audio_report=_audio_boundary_evidence(a,b); issues.extend(aud_issues); metrics['audio_cut_continuity']=audio_report
    spatial_report=evaluate_cross_shot_spatial(a,b); spatial=spatial_report.status; issues.extend(spatial_report.issues)
    metrics['cross_shot_spatial']=spatial_report.to_dict()
    geography_report=evaluate_camera_geography(a,b); issues.extend(geography_report.issues)
    metrics['camera_geography']=geography_report.to_dict()
    am=a.metadata if isinstance(a.metadata,dict) else {}; bm=b.metadata if isinstance(b.metadata,dict) else {}
    ali=am.get('lighting_continuity_intent') or {}; bli=bm.get('lighting_continuity_intent') or {}
    allow_light_change=bool((isinstance(ali,dict) and ali.get('allow_change')) or (isinstance(bli,dict) and bli.get('allow_change')))
    lighting_report=None
    if visual != 'NOT_TESTED' and Path(af).is_file() and Path(bf).is_file():
        try:
            lighting_report=evaluate_lighting_color_frames(af,bf,allow_change=allow_light_change)
        except Exception as exc:
            metrics['lighting_color_continuity']={'status':'NOT_TESTED','truth':f'Lighting/color boundary analysis could not run: {exc}'}
    if lighting_report:
        issues.extend(lighting_report.issues); metrics['lighting_color_continuity']=lighting_report.to_dict()
    elif 'lighting_color_continuity' not in metrics:
        metrics['lighting_color_continuity']={'status':'NOT_TESTED','truth':'Boundary frame files were unavailable; lighting/color continuity was not guessed.'}
    if visual=='FAIL' or any(str(x.get('severity')).upper() in {'HIGH','CRITICAL'} for x in issues): status='REVIEW'
    elif visual=='NOT_TESTED': status='NOT_TESTED'
    else: status='REVIEW'  # semantic/audio cut approval remains human/specialized
    truth='Visual status measures adjacent boundary-frame similarity; lighting/color analysis measures luminance, contrast and coarse RGB balance; camera geography uses explicit Scene/Director intent; audio-cut analysis measures decoded PCM level/silence proxies plus explicit J/L-cut intent. These do not prove Character identity, gaze, semantic 180-degree compliance, action match, prop state, room-tone identity, semantic dialogue flow, speaker identity, or artistic correctness.'
    return CutReport(a.shot_id,b.shot_id,a.id,b.id,status,visual,semantic,audio,spatial,metrics,tuple(issues),truth)

def evaluate_scene(project,scene_id:str)->SceneAssemblyReport:
    store=ProductionStore(project); shots=_scene_shots(store,scene_id)
    if not shots:
        r=SceneAssemblyReport(scene_id,'FAIL',(),(),(),False,True,('No Shots exist in this Scene.',),'Scene Assembly is advisory and never changes Take selection.')
        return SceneAssemblyStore(project).save(r)
    selected=[]; missing=[]
    for shot in shots:
        sid=str(shot.get('id','')); t=_selected_for(store,scene_id,sid)
        if t is None: missing.append(sid)
        else: selected.append(t)
    cuts=tuple(evaluate_cut(project,a,b) for a,b in zip(selected,selected[1:]))
    reasons=[]
    if missing:
        status='FAIL'; reasons.append(f'{len(missing)} Shot(s) have no Selected Take: {", ".join(missing)}.')
    elif any(c.status=='FAIL' for c in cuts): status='FAIL'; reasons.append('At least one cut cannot be evaluated because required media/evidence is missing.')
    elif any(c.status=='NOT_TESTED' for c in cuts): status='NOT TESTED'; reasons.append('At least one cut lacks sufficient automated boundary evidence.')
    elif cuts:
        status='REVIEW'; reasons.append('All Shots have Selected Takes; consecutive cuts were analyzed and require Director/semantic review before Cinema.')
    else:
        status='PASS'; reasons.append('The Scene contains one Shot with a Selected Take; there are no inter-shot cuts to evaluate.')
    cinema_ready=not missing and all(Path(t.media_path).is_file() for t in selected) and status in {'PASS','REVIEW'}
    truth='Cinema-ready means the selected media set is structurally assemblable. REVIEW is expected until semantic, action-match and audible cut quality are approved; Film Lab does not auto-select Takes or export the Scene from this check.'
    tone=RoomToneStore(project).get(scene_id)
    if tone is None:
        tone_status='NOT TESTED'; tone_path=''; reasons.append('No room-tone bed is assigned; room tone remains optional and was not guessed.')
    elif not tone.enabled:
        tone_status='REVIEW'; tone_path=tone.media_path; reasons.append('The Director explicitly disabled the assigned room-tone bed for this Scene.')
    elif Path(tone.media_path).is_file():
        tone_status='PASS'; tone_path=tone.media_path; reasons.append('A persistent room-tone bed is available for Cinema; audible artistic approval remains with the Director.')
    else:
        tone_status='FAIL'; tone_path=tone.media_path; reasons.append('The assigned room-tone media file is missing; Cinema cannot enforce that bed.')
        status='FAIL'; cinema_ready=False
    r=SceneAssemblyReport(scene_id,status,tuple(t.id for t in selected),cuts,tuple(missing),cinema_ready,True,tuple(reasons),truth,tone_status,tone_path)
    return SceneAssemblyStore(project).save(r)

def format_scene_assembly(report:SceneAssemblyReport)->str:
    lines=[f'### Scene Assembly — {report.status}',f'**Scene:** `{report.scene_id}`',f'**Cinema structurally ready:** {"YES" if report.cinema_ready else "NO"}',f'**Selected Takes:** {len(report.selected_take_ids)}',f'**Room tone:** {report.room_tone_status}']
    if report.missing_selected_shots: lines.append(f'**Shots missing Selected Takes:** {", ".join(report.missing_selected_shots)}')
    for c in report.cut_reports:
        lines.append(f'- `{c.from_shot_id}` → `{c.to_shot_id}` · **{c.status}** · visual {c.visual_status} · semantic {c.semantic_status} · spatial {c.spatial_status} · audio {c.audio_status}')
        ar=c.metrics.get('audio_cut_continuity',{}) if isinstance(c.metrics,dict) else {}
        if ar: lines.append(f'  - Audio cut: {ar.get("edit_style","HARD_CUT")} · level jump {ar.get("level_jump_db")} dB · room tone {ar.get("room_tone_status","NOT_TESTED")} · dialogue {ar.get("dialogue_handoff_status","NOT_TESTED")}')
    lines.append(f'**Reason:** {" ".join(report.reasons)}'); lines.append(f'**Truth:** {report.truth}'); lines.append('**Automatic Take selection/export: NO.**')
    return '\n'.join(lines)
