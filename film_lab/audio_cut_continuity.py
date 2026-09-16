"""Dialogue & Audio Cut Continuity for Scene Assembly.

Deterministic boundary analysis only. It measures decoded PCM level/silence and uses
explicit Director edit intent for J/L cuts. It does not infer semantic dialogue,
room acoustics, speaker identity, or artistic correctness.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any
import math, struct, subprocess

from film_lab.ffmpeg_support import find_ffmpeg, probe_has_audio, probe_duration_seconds

@dataclass(frozen=True)
class AudioBoundaryMetrics:
    rms_db: float
    peak_db: float
    silence_ratio: float
    sample_count: int
    def to_dict(self): return asdict(self)

@dataclass(frozen=True)
class AudioCutReport:
    status: str
    outgoing: dict[str, Any]
    incoming: dict[str, Any]
    level_jump_db: float | None
    silence_gap_risk: bool
    room_tone_status: str
    dialogue_handoff_status: str
    edit_style: str
    issues: tuple[dict[str, Any], ...]
    truth: str
    def to_dict(self):
        d=asdict(self); d['issues']=[dict(x) for x in self.issues]; return d

def analyze_pcm_samples(samples:list[int], *, silence_threshold:int=400)->AudioBoundaryMetrics:
    if not samples: return AudioBoundaryMetrics(-120.0,-120.0,1.0,0)
    scale=32768.0
    rms=math.sqrt(sum(float(x)*float(x) for x in samples)/len(samples))/scale
    peak=max(abs(int(x)) for x in samples)/scale
    silence=sum(1 for x in samples if abs(int(x)) <= silence_threshold)/len(samples)
    db=lambda x: 20.0*math.log10(max(x,1e-6))
    return AudioBoundaryMetrics(round(db(rms),2),round(db(peak),2),round(silence,4),len(samples))

def _decode_window(path:Path,start_s:float,duration_s:float=0.6,sample_rate:int=16000)->AudioBoundaryMetrics:
    exe=find_ffmpeg()
    proc=subprocess.run([exe,'-hide_banner','-loglevel','error','-ss',f'{max(0,start_s):.4f}','-t',f'{duration_s:.4f}','-i',str(path),'-vn','-ac','1','-ar',str(sample_rate),'-f','s16le','pipe:1'],capture_output=True)
    if proc.returncode != 0: raise RuntimeError((proc.stderr or b'ffmpeg audio decode failed').decode('utf-8','replace').strip())
    raw=proc.stdout[:len(proc.stdout)//2*2]
    samples=list(struct.unpack('<'+'h'*(len(raw)//2),raw)) if raw else []
    return analyze_pcm_samples(samples)

def _intent(take)->dict[str,Any]:
    meta=take.metadata if isinstance(take.metadata,dict) else {}
    x=meta.get('audio_cut_intent') or {}
    return x if isinstance(x,dict) else {}

def _dialogue_near_boundary(take,side:str,duration:float|None)->bool|None:
    meta=take.metadata if isinstance(take.metadata,dict) else {}
    # Persisted timeline formats vary; conservatively inspect timed events only.
    candidates=[]
    for key in ('audio_performance_timeline','dialogue_voice_sync'):
        x=meta.get(key)
        if isinstance(x,dict): candidates += list(x.get('events') or x.get('cues') or x.get('lines') or [])
    timed=[]
    for e in candidates:
        if not isinstance(e,dict): continue
        try:
            s=float(e.get('start_s',e.get('start',0))); en=float(e.get('end_s',e.get('end',s)))
            timed.append((s,en))
        except (TypeError,ValueError): pass
    if not timed: return None
    if side=='outgoing' and duration is not None: return any(en >= max(0,duration-0.75) for s,en in timed)
    if side=='incoming': return any(s <= 0.75 for s,en in timed)
    return None

def evaluate_audio_cut(a,b,window_s:float=0.6)->AudioCutReport:
    issues=[]; edit='HARD_CUT'
    ai,bi=_intent(a),_intent(b)
    if ai.get('l_cut') or bi.get('l_cut'): edit='L_CUT'
    if ai.get('j_cut') or bi.get('j_cut'): edit='J_CUT' if edit=='HARD_CUT' else 'J_L_CUT'
    ah,bh=probe_has_audio(Path(a.media_path)),probe_has_audio(Path(b.media_path))
    if ah is not True or bh is not True:
        missing=[]
        if ah is not True: missing.append('outgoing')
        if bh is not True: missing.append('incoming')
        return AudioCutReport('NOT_TESTED',{}, {},None,False,'NOT_TESTED','NOT_TESTED',edit,({'domain':'audio_stream','severity':'REVIEW','message':f'Proven audio stream unavailable for {" and ".join(missing)} Take(s).'},),'Audio continuity is not guessed when both audio streams cannot be proven by ffprobe.')
    ad=probe_duration_seconds(Path(a.media_path)); bd=probe_duration_seconds(Path(b.media_path))
    if ad is None or bd is None:
        return AudioCutReport('NOT_TESTED',{}, {},None,False,'NOT_TESTED','NOT_TESTED',edit,({'domain':'audio_duration','severity':'REVIEW','message':'Media duration could not be proven for boundary audio sampling.'},),'Audio boundary analysis requires proven media duration.')
    try:
        out=_decode_window(Path(a.media_path),max(0,ad-window_s),min(window_s,ad))
        inc=_decode_window(Path(b.media_path),0,min(window_s,bd))
    except Exception as exc:
        return AudioCutReport('NOT_TESTED',{}, {},None,False,'NOT_TESTED','NOT_TESTED',edit,({'domain':'audio_decode','severity':'REVIEW','message':f'Boundary PCM decode failed: {exc}'},),'No audible-continuity claim is made when PCM decoding fails.')
    jump=round(abs(out.rms_db-inc.rms_db),2)
    allow_level=bool(ai.get('allow_level_change') or bi.get('allow_level_change'))
    if jump >= 10 and not allow_level: issues.append({'domain':'audio_level','severity':'HIGH','message':f'Large boundary loudness proxy jump ({jump:.1f} dB RMS). Review gain/room tone.'})
    elif jump >= 6 and not allow_level: issues.append({'domain':'audio_level','severity':'MEDIUM','message':f'Noticeable boundary loudness proxy jump ({jump:.1f} dB RMS).'})
    silence_risk=(out.silence_ratio < .55 and inc.silence_ratio > .92) or (out.silence_ratio > .92 and inc.silence_ratio < .55)
    allow_silence=bool(ai.get('allow_silence_change') or bi.get('allow_silence_change'))
    if silence_risk and not allow_silence: issues.append({'domain':'silence_gap','severity':'MEDIUM','message':'Abrupt speech/ambience-to-near-silence boundary detected; review for an unintended gap or room-tone drop.'})
    # PCM amplitude cannot certify room-tone identity; report proxy only.
    room='REVIEW' if jump>=6 or silence_risk else 'PASS_PROXY'
    da=_dialogue_near_boundary(a,'outgoing',ad); db=_dialogue_near_boundary(b,'incoming',bd)
    if edit in {'J_CUT','L_CUT','J_L_CUT'}: dialogue='REVIEW'
    elif da is None and db is None: dialogue='NOT_TESTED'
    else: dialogue='PASS_PROXY' if not (da is True and db is True) else 'REVIEW'
    if da is True and db is True and edit=='HARD_CUT': issues.append({'domain':'dialogue_handoff','severity':'REVIEW','message':'Persisted dialogue cues reach both sides of this hard cut; review for clipped/stacked dialogue or choose explicit J/L-cut intent.'})
    severe=any(str(x.get('severity')).upper()=='HIGH' for x in issues)
    status='REVIEW' if issues or dialogue in {'REVIEW','NOT_TESTED'} or room=='REVIEW' else 'PASS'
    if severe: status='REVIEW'
    truth='REAL deterministic PCM boundary analysis measures RMS/peak level and near-silence ratio. Room-tone status is only a level/silence proxy. J/L cuts and intentional level/silence changes require explicit Director metadata; semantic dialogue, speaker identity, acoustics and artistic quality are not inferred.'
    return AudioCutReport(status,out.to_dict(),inc.to_dict(),jump,silence_risk,room,dialogue,edit,tuple(issues),truth)
