from film_lab.voice_acting import VoiceActingBeat,VoiceActingPerformance,VoiceActingStore,voice_acting_enforcement
from film_lab.voice_acting_bridge import inject_voice_acting,update_voice_acting_enforcement
from film_lab.conditioning import GenerationConditioning

class P:
    def __init__(self,root): self.root=root

def test_voice_acting_persists_by_character(tmp_path):
    p=P(tmp_path); perf=VoiceActingPerformance("s1","sh1",(VoiceActingBeat(0,"char_sarah",emotion="fear",pace="slow",intensity=.7),VoiceActingBeat(2,"char_mike",delivery="whisper")))
    VoiceActingStore(p).save(perf); got=VoiceActingStore(p).get("s1","sh1")
    assert got.character_ids==("char_mike","char_sarah") and got.beats[0].emotion=="fear"

def test_voice_acting_defaults_prompt_only():
    p=VoiceActingPerformance("s","h",(VoiceActingBeat(0,"char_a",emotion="sad"),))
    assert voice_acting_enforcement(p)["status"]=="PROMPT_ONLY"

def test_bridge_requires_explicit_character_slot_and_expressive_renderer():
    c=GenerationConditioning("s","h","p","x",metadata={"voice_acting":{"scene_id":"s","shot_id":"h","beats":[VoiceActingBeat(0,"char_a",emotion="fear").to_dict()]}})
    graph={"1":{"class_type":"ExpressiveProsodyTTS","inputs":{"style":""},"_meta":{"title":"film_lab_voice_performance:char_a"}}}
    e=inject_voice_acting(graph,c); assert e["wired"] and e["enforced_character_ids"]==["char_a"]
    assert "char_a" in graph["1"]["inputs"]["style"]

def test_multi_character_voice_never_binds_ambiguous_global_slot():
    beats=[VoiceActingBeat(0,"char_a",emotion="fear").to_dict(),VoiceActingBeat(1,"char_b",emotion="calm").to_dict()]
    c=GenerationConditioning("s","h","p","x",metadata={"voice_acting":{"scene_id":"s","shot_id":"h","beats":beats}})
    graph={"1":{"class_type":"ExpressiveProsodyTTS","inputs":{"style":""},"_meta":{"title":"film_lab_voice_performance"}}}
    e=inject_voice_acting(graph,c); assert not e["wired"]
    r=update_voice_acting_enforcement(c,e); assert r["status"]=="PROMPT_ONLY"
