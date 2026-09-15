from film_lab.character_state import CharacterStore
from film_lab.project import Project

def project(tmp_path,name): return Project.create(name,data_root=tmp_path/"projects")

def test_character_identity_survives_restart(tmp_path):
    p=project(tmp_path,"characters"); store=CharacterStore(p)
    maya=store.create("Maya",appearance="oval face, brown eyes",wardrobe="black raincoat",voice_id="voice_maya")
    again=CharacterStore(p).get(maya.id)
    assert again.id==maya.id and again.name=="Maya" and again.wardrobe=="black raincoat" and again.voice_id=="voice_maya"

def test_character_updates_keep_stable_id(tmp_path):
    p=project(tmp_path,"character-update"); store=CharacterStore(p); maya=store.create("Maya")
    updated=store.update(maya.id,emotional_state="terrified but controlled",continuity_notes="coat remains wet")
    assert updated.id==maya.id and "terrified" in updated.prompt_context() and "coat remains wet" in updated.prompt_context()

def test_scene_character_refs_resolve_by_id(tmp_path):
    p=project(tmp_path,"character-resolve"); store=CharacterStore(p); maya=store.create("Maya",appearance="brown eyes")
    resolved=store.resolve_scene_characters([{"id":maya.id,"name":"Wrong display name"}])
    assert len(resolved)==1 and resolved[0].id==maya.id and resolved[0].name=="Maya" and resolved[0].appearance=="brown eyes"
