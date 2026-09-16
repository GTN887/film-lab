from types import SimpleNamespace
import pytest
from film_lab.director_timeline_editor import timeline_rows, move_event, move_performance_keyframe, add_performance_beat, add_camera_beat, inspector
from film_lab.dialogue_performance import DialogueBeat, DialoguePerformance, DialoguePerformanceStore
from film_lab.voice_acting import VoiceActingBeat, VoiceActingPerformance, VoiceActingStore
from film_lab.performance_choreography import InteractionCue, PerformanceChoreography, PerformanceChoreographyStore
from film_lab.performance_timeline import PerformanceTimelineStore
from film_lab.camera_timeline import CameraTimelineStore, camera_enforcement

def p(tmp_path): return SimpleNamespace(root=tmp_path)

def test_director_rows_merge_actor_and_camera_tracks(tmp_path):
    x=p(tmp_path); DialoguePerformanceStore(x).save(DialoguePerformance("s","sh",(DialogueBeat(1,"sarah","Wait",end_s=2),)))
    add_camera_beat(x,"s","sh",0,move="push in",follow_character_id="sarah")
    rows=timeline_rows(x,"s","sh")
    assert {r[0] for r in rows}=={"dialogue","camera"} and inspector(x,"s","sh")["persistent"] is True

def test_add_and_move_performance_beat_is_character_specific(tmp_path):
    x=p(tmp_path); add_performance_beat(x,"s","sh","sarah","Sarah",1,emotion="calm"); add_performance_beat(x,"s","sh","michael","Michael",1,emotion="afraid")
    move_performance_keyframe(x,"s","sh","sarah",0,3)
    assert PerformanceTimelineStore(x).get("s","sh","sarah").keyframes[0].time_s==3
    assert PerformanceTimelineStore(x).get("s","sh","michael").keyframes[0].time_s==1

def test_move_voice_preserves_duration_and_character(tmp_path):
    x=p(tmp_path); VoiceActingStore(x).save(VoiceActingPerformance("s","sh",(VoiceActingBeat(1,"sarah",end_s=2.5),)))
    move_event(x,"s","sh","voice_acting",0,4); b=VoiceActingStore(x).get("s","sh").beats[0]
    assert (b.start_s,b.end_s,b.character_id)==(4,5.5,"sarah")

def test_move_reaction_persists(tmp_path):
    x=p(tmp_path); PerformanceChoreographyStore(x).save(PerformanceChoreography("s","sh",(InteractionCue(1,"sarah","michael",reaction="startled"),)))
    move_event(x,"s","sh","reaction",0,2.25)
    assert PerformanceChoreographyStore(x).get("s","sh").cues[0].time_s==2.25

def test_camera_timeline_persists_and_moves(tmp_path):
    x=p(tmp_path); add_camera_beat(x,"s","sh",1,move="orbit",framing="wide",follow_character_id="sarah")
    move_event(x,"s","sh","camera",0,2)
    k=CameraTimelineStore(x).get("s","sh").keyframes[0]; assert (k.time_s,k.move,k.follow_character_id)==(2,"orbit","sarah")

def test_camera_truth_gate(tmp_path):
    x=p(tmp_path); t=add_camera_beat(x,"s","sh",0,move="dolly")
    assert camera_enforcement(t)["status"]=="PROMPT_ONLY"
    assert camera_enforcement(t,temporal_camera_wired=True)["status"]=="ENFORCED"

def test_negative_editor_time_rejected(tmp_path):
    x=p(tmp_path); add_camera_beat(x,"s","sh",0,move="pan")
    with pytest.raises(ValueError): move_event(x,"s","sh","camera",0,-1)

def test_timeline_rows_keep_stable_character_ids(tmp_path):
    x=p(tmp_path); add_performance_beat(x,"s","sh","char-123","Sarah",1,action="turn")
    assert any(r[1]=="char-123" for r in timeline_rows(x,"s","sh"))

def test_draggable_items_preserve_store_indexes(tmp_path):
    from film_lab.director_timeline_editor import draggable_items
    x=p(tmp_path)
    DialoguePerformanceStore(x).save(DialoguePerformance("s","sh",(DialogueBeat(4,"sarah","Later"),DialogueBeat(1,"michael","Earlier"))))
    items=draggable_items(x,"s","sh")
    by_text={q["label"]:q for q in items if q["lane"]=="dialogue"}
    assert by_text["Earlier"]["index"]==0 and by_text["Later"]["index"]==1


def test_visual_timeline_contains_real_drag_metadata(tmp_path):
    from film_lab.director_timeline_editor import visual_timeline_html
    x=p(tmp_path); add_performance_beat(x,"s","sh","char-123","Sarah",1.5,action="turn")
    html=visual_timeline_html(x,"s","sh")
    assert 'draggable="true"' in html and 'char-123' in html and 'performance' in html and 'turn' in html


def test_drag_javascript_commits_through_hidden_save_bridge():
    from film_lab.director_timeline_editor import DRAG_TIMELINE_JS
    assert "new_time_s" in DRAG_TIMELINE_JS
    assert "#fl-timeline-drag-payload" in DRAG_TIMELINE_JS
    assert "#fl-timeline-drag-save button" in DRAG_TIMELINE_JS


def test_visual_timeline_includes_all_creator_lanes(tmp_path):
    from film_lab.director_timeline_editor import visual_timeline_html
    html=visual_timeline_html(p(tmp_path),"s","sh")
    for label in ("Dialogue","Voice","Performance","Reaction","Camera"):
        assert label in html
