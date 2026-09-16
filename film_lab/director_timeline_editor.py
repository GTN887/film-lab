"""Creator-facing Director Timeline edit model.

Every edit in this module mutates persistent production state. UI code can therefore
remain thin and cannot claim a drag/edit succeeded unless the underlying store changed.
"""
from __future__ import annotations
from dataclasses import replace
from typing import Any
from film_lab.audio_performance_timeline import build_audio_performance_timeline
from film_lab.camera_timeline import CameraKeyframe, CameraTimeline, CameraTimelineStore

LANES=("dialogue","voice_acting","performance","reaction","camera")

def timeline_rows(project,scene_id:str,shot_id:str)->list[list[Any]]:
    rows=[]
    t=build_audio_performance_timeline(project,scene_id,shot_id)
    for e in t.events:
        rows.append([e.lane,e.character_id,e.event_id,round(float(e.start_s),3),"" if e.end_s is None else round(float(e.end_s),3),e.label])
    cam=CameraTimelineStore(project).get(scene_id,shot_id)
    if cam:
        for i,k in enumerate(cam.keyframes): rows.append(["camera",k.follow_character_id,f"camera_{i:03d}",round(float(k.time_s),3),"",k.move or k.framing or k.note])
    return sorted(rows,key=lambda r:(float(r[3]),r[0],r[1],r[2]))

def move_event(project,scene_id:str,shot_id:str,lane:str,index:int,new_start_s:float):
    start=float(new_start_s)
    if start < 0: raise ValueError("Timeline time cannot be negative.")
    if lane=="dialogue":
        from film_lab.audio_performance_timeline import move_dialogue_beat
        return move_dialogue_beat(project,scene_id,shot_id,index,start)
    if lane=="voice_acting":
        from film_lab.voice_acting import VoiceActingStore, VoiceActingPerformance
        s=VoiceActingStore(project); p=s.get(scene_id,shot_id)
        if p is None or not 0<=index<len(p.beats): raise IndexError("Voice beat index out of range.")
        b=p.beats[index]; dur=(b.end_s-b.start_s) if b.end_s is not None else None
        beats=list(p.beats); beats[index]=replace(b,start_s=start,end_s=(start+dur if dur is not None else None)); return s.save(VoiceActingPerformance(scene_id,shot_id,tuple(beats)))
    if lane=="reaction":
        from film_lab.performance_choreography import PerformanceChoreographyStore, PerformanceChoreography
        s=PerformanceChoreographyStore(project); p=s.get(scene_id,shot_id)
        if p is None or not 0<=index<len(p.cues): raise IndexError("Reaction cue index out of range.")
        cues=list(p.cues); cues[index]=replace(cues[index],time_s=start); return s.save(PerformanceChoreography(scene_id,shot_id,tuple(cues),p.status))
    if lane=="camera":
        s=CameraTimelineStore(project); p=s.get(scene_id,shot_id)
        if p is None or not 0<=index<len(p.keyframes): raise IndexError("Camera keyframe index out of range.")
        keys=list(p.keyframes); keys[index]=replace(keys[index],time_s=start); return s.save(CameraTimeline(scene_id,shot_id,tuple(keys),p.status))
    raise ValueError("Performance events require Character-specific editing via move_performance_keyframe().")

def move_performance_keyframe(project,scene_id:str,shot_id:str,character_id:str,index:int,new_time_s:float):
    from film_lab.performance_timeline import PerformanceTimelineStore, ActorPerformanceTimeline
    start=float(new_time_s)
    if start<0: raise ValueError("Timeline time cannot be negative.")
    s=PerformanceTimelineStore(project); p=s.get(scene_id,shot_id,character_id)
    if p is None or not 0<=index<len(p.keyframes): raise IndexError("Performance keyframe index out of range.")
    keys=list(p.keyframes); keys[index]=replace(keys[index],time_s=start); return s.save(ActorPerformanceTimeline(scene_id,shot_id,character_id,p.character_name,tuple(keys),p.status))

def add_performance_beat(project,scene_id,shot_id,character_id,character_name,time_s,*,emotion="",expression="",gaze="",posture="",gesture="",action="",intensity=None):
    from film_lab.performance_timeline import PerformanceTimelineStore, ActorPerformanceTimeline, PerformanceKeyframe
    s=PerformanceTimelineStore(project); old=s.get(scene_id,shot_id,character_id); keys=list(old.keyframes if old else ())
    keys.append(PerformanceKeyframe(float(time_s),emotion,expression,gaze,posture,gesture,action,intensity))
    return s.save(ActorPerformanceTimeline(scene_id,shot_id,character_id,character_name or character_id,tuple(keys),old.status if old else "PROMPT_ONLY"))

def add_camera_beat(project,scene_id,shot_id,time_s,*,move="",framing="",lens="",focus_target="",follow_character_id="",speed=None,note=""):
    s=CameraTimelineStore(project); old=s.get(scene_id,shot_id); keys=list(old.keyframes if old else ())
    keys.append(CameraKeyframe(float(time_s),move,framing,lens,focus_target,follow_character_id,speed,note))
    return s.save(CameraTimeline(scene_id,shot_id,tuple(keys),old.status if old else "DIRECTED"))

def inspector(project,scene_id,shot_id)->dict[str,Any]:
    rows=timeline_rows(project,scene_id,shot_id)
    return {"scene_id":scene_id,"shot_id":shot_id,"rows":len(rows),"characters":sorted({r[1] for r in rows if r[1]}),"lanes":sorted({r[0] for r in rows}),"persistent":True}

def draggable_items(project, scene_id: str, shot_id: str) -> list[dict[str, Any]]:
    """Return persisted events with the exact store index required for a drag-save."""
    items: list[dict[str, Any]] = []
    from film_lab.dialogue_performance import DialoguePerformanceStore
    d = DialoguePerformanceStore(project).get(scene_id, shot_id)
    if d:
        for i, b in enumerate(d.beats):
            items.append({"lane":"dialogue","character_id":b.character_id,"index":i,"start_s":float(b.start_s),"end_s":None if b.end_s is None else float(b.end_s),"label":b.text})
    from film_lab.voice_acting import VoiceActingStore
    v = VoiceActingStore(project).get(scene_id, shot_id)
    if v:
        for i, b in enumerate(v.beats):
            items.append({"lane":"voice_acting","character_id":b.character_id,"index":i,"start_s":float(b.start_s),"end_s":None if b.end_s is None else float(b.end_s),"label":b.delivery or b.emotion})
    from film_lab.performance_timeline import PerformanceTimelineStore
    for tl in PerformanceTimelineStore(project).for_shot(scene_id, shot_id):
        for i, k in enumerate(tl.keyframes):
            items.append({"lane":"performance","character_id":tl.character_id,"index":i,"start_s":float(k.time_s),"end_s":None,"label":k.action or k.expression or k.emotion})
    from film_lab.performance_choreography import PerformanceChoreographyStore
    c = PerformanceChoreographyStore(project).get(scene_id, shot_id)
    if c:
        for i, cue in enumerate(c.cues):
            items.append({"lane":"reaction","character_id":cue.actor_id,"index":i,"start_s":float(cue.time_s),"end_s":None,"label":cue.action or cue.reaction or cue.dialogue_beat})
    cam = CameraTimelineStore(project).get(scene_id, shot_id)
    if cam:
        for i, k in enumerate(cam.keyframes):
            items.append({"lane":"camera","character_id":k.follow_character_id,"index":i,"start_s":float(k.time_s),"end_s":None,"label":k.move or k.framing or k.note})
    return sorted(items, key=lambda x:(x["start_s"],x["lane"],x["character_id"],x["index"]))


def visual_timeline_html(project, scene_id: str, shot_id: str, playhead_s: float | None = None) -> str:
    """Render a creator-facing draggable timeline. Dragging writes through the hidden save bridge."""
    import html, json
    items = draggable_items(project, scene_id, shot_id)
    lanes = ["dialogue","voice_acting","performance","reaction","camera"]
    duration = max([6.0] + [float(x["end_s"] if x["end_s"] is not None else x["start_s"] + .6) for x in items])
    lane_labels={"dialogue":"Dialogue","voice_acting":"Voice","performance":"Performance","reaction":"Reaction","camera":"Camera"}
    cursor=max(0.0,min(100.0,(float(playhead_s or 0)/duration)*100.0))
    parts=['<div class="fl-dt-shell" data-duration="%.3f">' % duration,
           '<div class="fl-dt-ruler"><span>0s</span><span>%.1fs</span></div>' % duration,
           '<div class="fl-dt-playhead" style="left:%.3f%%" title="Playhead %.3fs"></div>' % (cursor,float(playhead_s or 0))]
    for lane in lanes:
        parts.append('<div class="fl-dt-row"><div class="fl-dt-label">%s</div><div class="fl-dt-track">' % lane_labels[lane])
        for x in [q for q in items if q["lane"]==lane]:
            left=max(0,min(98,(x["start_s"]/duration)*100)); width=max(2, ((x["end_s"]-x["start_s"])/duration*100) if x["end_s"] is not None else 4)
            payload=json.dumps({"lane":x["lane"],"character_id":x["character_id"],"index":x["index"]},separators=(",",":"))
            title=(x["character_id"]+" · " if x["character_id"] else "")+(x["label"] or lane_labels[lane])
            parts.append('<div class="fl-dt-beat" draggable="true" data-payload=\'%s\' style="left:%.3f%%;width:%.3f%%" title="Drag to retime">%s</div>' % (html.escape(payload,quote=True),left,width,html.escape(title)))
        parts.append('</div></div>')
    parts.append('<div class="fl-dt-help">Drag a beat left or right to retime it. Drop commits the new time to persistent Film Lab production state.</div></div>')
    return ''.join(parts)

DRAG_TIMELINE_JS = r"""
(element) => {
  const shell = element.querySelector('.fl-dt-shell');
  if (!shell) return;
  const duration = Number(shell.dataset.duration || 6);
  shell.querySelectorAll('.fl-dt-beat').forEach((beat) => {
    beat.addEventListener('dragstart', (ev) => { ev.dataTransfer.setData('text/plain', beat.dataset.payload); beat.classList.add('fl-dt-dragging'); });
    beat.addEventListener('dragend', () => beat.classList.remove('fl-dt-dragging'));
  });
  shell.querySelectorAll('.fl-dt-track').forEach((track) => {
    track.addEventListener('dragover', (ev) => ev.preventDefault());
    track.addEventListener('drop', (ev) => {
      ev.preventDefault();
      let meta; try { meta = JSON.parse(ev.dataTransfer.getData('text/plain')); } catch (_) { return; }
      const r = track.getBoundingClientRect();
      const frac = Math.max(0, Math.min(1, (ev.clientX-r.left)/r.width));
      meta.new_time_s = Math.round(frac * duration * 1000) / 1000;
      const host = document.querySelector('#fl-timeline-drag-payload');
      const input = host && host.querySelector('textarea,input');
      if (!input) return;
      const setter = Object.getOwnPropertyDescriptor(Object.getPrototypeOf(input), 'value')?.set;
      if (setter) setter.call(input, JSON.stringify(meta)); else input.value = JSON.stringify(meta);
      input.dispatchEvent(new Event('input', {bubbles:true})); input.dispatchEvent(new Event('change', {bubbles:true}));
      setTimeout(() => document.querySelector('#fl-timeline-drag-save button')?.click(), 20);
    });
  });
}
"""
