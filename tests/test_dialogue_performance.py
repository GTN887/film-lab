from pathlib import Path
from film_lab.dialogue_performance import DialogueBeat, DialoguePerformance, DialoguePerformanceStore, dialogue_enforcement
from film_lab.project import Project


def project(tmp_path): return Project.create("voice-sync", data_root=tmp_path)

def test_dialogue_is_stably_character_bound_and_sorted(tmp_path):
    p=project(tmp_path); d=DialoguePerformance("s1","sh1",(DialogueBeat(2,"char_b","Reply"),DialogueBeat(1,"char_a","Hello")))
    DialoguePerformanceStore(p).save(d); got=DialoguePerformanceStore(p).get("s1","sh1")
    assert [x.character_id for x in got.beats]==["char_a","char_b"]
    assert got.character_ids==("char_a","char_b")

def test_lip_sync_never_claimed_from_audio_timing_alone():
    d=DialoguePerformance("s","sh",(DialogueBeat(0,"char_a","Hello"),))
    result=dialogue_enforcement(d,audio_timing_wired=True,lip_sync_wired=False,character_audio_wired=False)
    assert result["status"]=="PARTIAL" and result["lip_sync_enforced"] is False

def test_lip_sync_requires_both_lip_and_character_audio_bridge():
    d=DialoguePerformance("s","sh",(DialogueBeat(0,"char_a","Hello"),))
    assert dialogue_enforcement(d,lip_sync_wired=True,character_audio_wired=False)["status"]!="ENFORCED"
    assert dialogue_enforcement(d,lip_sync_wired=True,character_audio_wired=True)["status"]=="ENFORCED"

def test_dialogue_prompt_keeps_speakers_separate():
    d=DialoguePerformance("s","sh",(DialogueBeat(0,"char_a","Run",emotion="afraid"),DialogueBeat(1,"char_b","Wait",reaction_to="char_a")))
    text=d.prompt({"char_a":"Sarah","char_b":"Michael"})
    assert "Sarah [char_a]" in text and 'line: "Run"' in text
    assert "Michael [char_b]" in text and 'line: "Wait"' in text
