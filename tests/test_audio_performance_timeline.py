from pathlib import Path
from types import SimpleNamespace
import pytest
from film_lab.audio_performance_timeline import build_audio_performance_timeline, move_dialogue_beat, timeline_sync_status
from film_lab.dialogue_performance import DialogueBeat, DialoguePerformance, DialoguePerformanceStore
from film_lab.voice_acting import VoiceActingBeat, VoiceActingPerformance, VoiceActingStore
from film_lab.performance_timeline import ActorPerformanceTimeline, PerformanceKeyframe, PerformanceTimelineStore


def project(tmp_path): return SimpleNamespace(root=tmp_path)

def test_unified_timeline_keeps_character_lanes_independent(tmp_path):
    p=project(tmp_path)
    DialoguePerformanceStore(p).save(DialoguePerformance("s1","sh1",(DialogueBeat(0,"sarah","Hi",end_s=1),DialogueBeat(1.2,"michael","Wait",end_s=2))))
    VoiceActingStore(p).save(VoiceActingPerformance("s1","sh1",(VoiceActingBeat(0,"sarah",emotion="afraid"),VoiceActingBeat(1.2,"michael",emotion="concerned"))))
    t=build_audio_performance_timeline(p,"s1","sh1")
    assert t.character_ids == ("michael","sarah")
    assert len(t.for_character("sarah")) == 2
    assert {e.character_id for e in t.lane("dialogue")} == {"sarah","michael"}

def test_performance_keyframes_share_same_time_axis(tmp_path):
    p=project(tmp_path)
    PerformanceTimelineStore(p).save(ActorPerformanceTimeline("s","sh","sarah","Sarah",(PerformanceKeyframe(2.5,emotion="fear"),)))
    t=build_audio_performance_timeline(p,"s","sh")
    assert t.events[0].lane == "performance" and t.events[0].start_s == 2.5

def test_move_dialogue_preserves_duration_and_identity(tmp_path):
    p=project(tmp_path); store=DialoguePerformanceStore(p)
    store.save(DialoguePerformance("s","sh",(DialogueBeat(1,"sarah","Run",end_s=2.5),)))
    move_dialogue_beat(p,"s","sh",0,4)
    b=store.get("s","sh").beats[0]
    assert (b.character_id,b.start_s,b.end_s)==("sarah",4,5.5)

def test_sync_truth_gate_requires_all_renderer_paths(tmp_path):
    p=project(tmp_path)
    DialoguePerformanceStore(p).save(DialoguePerformance("s","sh",(DialogueBeat(0,"sarah","Hi",end_s=1),)))
    t=build_audio_performance_timeline(p,"s","sh")
    assert timeline_sync_status(t)["status"] == "PARTIAL"
    assert timeline_sync_status(t,lip_sync_wired=True,performance_time_wired=True)["status"] == "ENFORCED"
