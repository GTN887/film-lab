from film_lab.character_state import CharacterStore
from film_lab.project import Project


def test_character_identity_survives_restart(tmp_path):
    p=Project.create("characters",base_dir=tmp_path)
    store=CharacterStore(p)
    maya=store.create("Maya",appearance="oval face, brown eyes",wardrobe="black raincoat",voice_id="voice_maya")
    again=CharacterStore(p).get(maya.id)
    assert again.id==maya.id
    assert again.name=="Maya"
    assert again.wardrobe=="black raincoat"
    assert again.voice_id=="voice_maya"


def test_character_updates_keep_stable_id(tmp_path):
    p=Project.create("character-update",base_dir=tmp_path)
    store=CharacterStore(p); maya=store.create("Maya")
    updated=store.update(maya.id,emotional_state="terrified but controlled",continuity_notes="coat remains wet")
    assert updated.id==maya.id
    assert "terrified" in updated.prompt_context()
    assert "coat remains wet" in updated.prompt_context()


def test_scene_character_refs_resolve_by_id(tmp_path):
    p=Project.create("character-resolve",base_dir=tmp_path)
    store=CharacterStore(p); maya=store.create("Maya",appearance="brown eyes")
    resolved=store.resolve_scene_characters([{"id":maya.id,"name":"Wrong display name"}])
    assert len(resolved)==1
    assert resolved[0].id==maya.id
    assert resolved[0].name=="Maya"
    assert resolved[0].appearance=="brown eyes"
