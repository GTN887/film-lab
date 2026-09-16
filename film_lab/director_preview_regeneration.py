"""Director Preview & Regeneration Loop.

Captures the exact directing context at a persisted playhead, forks a new Take through
Mark & Direct, and stores an A/B review session without replacing the source Take.
Renderer truth remains owned by the generator/conditioning evidence.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
import json
from pathlib import Path
from typing import Any

from film_lab.playback_sync import PlaybackSyncStore, resolve_playback
from film_lab.production import ProductionStore, Take
from film_lab.mark_direct_regenerate import regenerate_take
from film_lab.shot_continuity_intelligence import build_regeneration_contract, audit_candidate

@dataclass(frozen=True)
class PreviewContext:
    scene_id: str
    shot_id: str
    source_take_id: str
    playhead_s: float
    active_events: tuple[dict[str, Any], ...]
    camera_state: dict[str, Any]
    dialogue_state: tuple[dict[str, Any], ...]
    performance_state: tuple[dict[str, Any], ...]
    continuity_prior_take_ids: tuple[str, ...]
    def to_dict(self): return asdict(self)

@dataclass(frozen=True)
class ABReview:
    scene_id: str
    shot_id: str
    source_take_id: str
    candidate_take_id: str
    source_media_path: str
    candidate_media_path: str
    playhead_s: float
    context: dict[str, Any]
    status: str = "READY_FOR_AB_REVIEW"
    def to_dict(self): return asdict(self)

class DirectorPreviewStore:
    def __init__(self, project):
        self.project=project; project.ensure_dirs(); self.path=project.root/"director_preview_review.json"
    def save(self, review: ABReview):
        tmp=self.path.with_suffix(".json.tmp"); tmp.write_text(json.dumps(review.to_dict(),indent=2,sort_keys=True)+"\n",encoding="utf-8"); tmp.replace(self.path); return review
    def load(self):
        if not self.path.exists(): return None
        try: return ABReview(**json.loads(self.path.read_text(encoding="utf-8")))
        except (OSError,json.JSONDecodeError,TypeError): return None

def _at(start, end, t):
    start=float(start or 0); return start <= t <= (float(end) if end is not None else start+.35)

def capture_preview_context(project, scene_id: str, shot_id: str, playhead_s: float | None=None) -> PreviewContext:
    from film_lab.director_timeline_editor import draggable_items
    from film_lab.camera_timeline import CameraTimelineStore
    from film_lab.scene_context import SceneContextStore
    state=resolve_playback(project,scene_id,shot_id,requested_s=playhead_s)
    if not state.take_id: raise ValueError("A real Selected Take is required before preview regeneration.")
    t=state.playhead_s
    active=[]; dialogue=[]; performance=[]
    for item in draggable_items(project,scene_id,shot_id):
        if _at(item["start_s"],item.get("end_s"),t):
            snap=dict(item); active.append(snap)
            if item["lane"] in {"dialogue","voice_acting"}: dialogue.append(snap)
            if item["lane"] in {"performance","reaction"}: performance.append(snap)
    camera={}
    tl=CameraTimelineStore(project).get(scene_id,shot_id)
    if tl and tl.keyframes:
        prior=[k for k in tl.keyframes if float(k.time_s)<=t]
        if prior:
            k=max(prior,key=lambda x:float(x.time_s)); camera=k.to_dict()
    world=SceneContextStore(project).get(scene_id)
    return PreviewContext(scene_id,shot_id,state.take_id,t,tuple(active),camera,tuple(dialogue),tuple(performance),tuple(world.prior_take_ids))

def regenerate_preview(project, *, scene_id: str, shot_id: str, generator, director_instruction: str, playhead_s: float | None=None, character_id: str="", region_id: str="") -> ABReview:
    ctx=capture_preview_context(project,scene_id,shot_id,playhead_s)
    source=ProductionStore(project).get_take(ctx.source_take_id)
    contract=build_regeneration_contract(project,scene_id=scene_id,shot_id=shot_id,source_take_id=source.id,instruction=director_instruction,character_id=character_id)
    new=regenerate_take(project,source_take_id=source.id,generator=generator,director_instruction=director_instruction,character_id=character_id,region_id=region_id)
    store=ProductionStore(project); data=store._load(); raw=data["takes"][new.id]; meta=raw.setdefault("metadata",{})
    meta["director_preview_context"]=ctx.to_dict(); meta["preview_playhead_s"]=ctx.playhead_s; meta["ab_source_take_id"]=source.id
    meta["continuity_contract"]=contract
    store._save(data)
    audit=audit_candidate(project,candidate_take_id=new.id,contract=contract)
    data=store._load(); data["takes"][new.id].setdefault("metadata",{})["continuity_report"]=audit; store._save(data)
    # Run conservative sampled-frame visual QA. Invalid/unavailable media returns NOT_TESTED
    # rather than blocking regeneration or inventing a continuity claim.
    from film_lab.visual_continuity_certification import certify_candidate_take
    certify_candidate_take(project,new.id)
    # Temporal QA samples the full Take and reports when drift/lost targets occur.
    # Missing ffmpeg/media degrades truthfully to NOT_TESTED and never blocks A/B review.
    from film_lab.full_take_continuity_scanning import scan_candidate_take
    scan_candidate_take(project,new.id)
    PlaybackSyncStore(project).save_playhead(scene_id,shot_id,ctx.playhead_s)
    review=ABReview(scene_id,shot_id,source.id,new.id,source.media_path,new.media_path,ctx.playhead_s,ctx.to_dict())
    return DirectorPreviewStore(project).save(review)

def accept_candidate(project, review: ABReview | None=None) -> Take:
    review=review or DirectorPreviewStore(project).load()
    if review is None: raise ValueError("No Director A/B review is ready.")
    take=ProductionStore(project).set_status(review.candidate_take_id,"selected")
    PlaybackSyncStore(project).save_playhead(review.scene_id,review.shot_id,review.playhead_s)
    return take
