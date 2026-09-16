from pathlib import Path
from types import SimpleNamespace
from film_lab.lip_sync_bridge import inject_lip_sync, update_dialogue_enforcement


def cond(tmp_path, two=False):
    a=tmp_path/'sarah.wav'; a.write_bytes(b'RIFFfake')
    beats=[{"start_s":0.0,"character_id":"char_sarah","text":"Run!","audio_path":str(a),"end_s":1.0,"emotion":"afraid","intention":"urgent","cue_id":"","reaction_to":""}]
    if two:
        b=tmp_path/'michael.wav'; b.write_bytes(b'RIFFfake')
        beats.append({"start_s":1.0,"character_id":"char_michael","text":"Wait!","audio_path":str(b),"end_s":2.0,"emotion":"calm","intention":"firm","cue_id":"","reaction_to":""})
    return SimpleNamespace(scene_id='s1',shot_id='sh1',metadata={"dialogue_performance":{"scene_id":"s1","shot_id":"sh1","status":"TIMED_AUDIO","beats":beats}})


def test_character_audio_slot_enforces_only_proven_lip_path(tmp_path):
    c=cond(tmp_path)
    g={"1":{"class_type":"MuseTalkLipSync","inputs":{}},"2":{"class_type":"LoadAudio","inputs":{"audio":""},"_meta":{"title":"film_lab_dialogue_audio:char_sarah"}}}
    ev=inject_lip_sync(g,c)
    assert ev['lip_sync_enforced_character_ids']==['char_sarah']
    assert Path(g['2']['inputs']['audio']).name=='sarah.wav'
    assert update_dialogue_enforcement(c,ev)['status']=='ENFORCED'


def test_lip_node_without_explicit_character_slot_is_not_enforced(tmp_path):
    c=cond(tmp_path); g={"1":{"class_type":"Wav2Lip","inputs":{"audio":""}}}
    ev=inject_lip_sync(g,c)
    assert not ev['wired']
    assert update_dialogue_enforcement(c,ev)['status']=='PARTIAL'


def test_two_characters_require_separate_audio_slots(tmp_path):
    c=cond(tmp_path,True)
    g={"1":{"class_type":"MuseTalkLipSync","inputs":{}},"2":{"class_type":"LoadAudio","inputs":{"audio":""},"_meta":{"title":"film_lab_dialogue_audio:char_sarah"}},"3":{"class_type":"LoadAudio","inputs":{"audio":""},"_meta":{"title":"film_lab_dialogue_audio:char_michael"}}}
    ev=inject_lip_sync(g,c)
    assert set(ev['lip_sync_enforced_character_ids'])=={'char_sarah','char_michael'}
    assert update_dialogue_enforcement(c,ev)['status']=='ENFORCED'


def test_facial_direction_does_not_equal_lip_sync(tmp_path):
    c=cond(tmp_path)
    g={"1":{"class_type":"LivePortraitExpression","inputs":{}},"2":{"class_type":"TextInput","inputs":{"text":""},"_meta":{"title":"film_lab_facial_performance:char_sarah"}}}
    ev=inject_lip_sync(g,c)
    assert ev['facial_bound_character_ids']==['char_sarah']
    assert not ev['wired']
    assert update_dialogue_enforcement(c,ev)['status']=='PARTIAL'
