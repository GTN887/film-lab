from film_lab.project import Project
from film_lab.scene_context import SceneContextStore,generation_prompt
from film_lab.character_state import CharacterStore

def test_scene_and_character_context_persist_and_compose(tmp_path):
    p=Project.create("world",data_root=tmp_path/"projects")
    c=CharacterStore(p).create("Maya",appearance="brown eyes",wardrobe="black raincoat",continuity_notes="coat stays wet")
    SceneContextStore(p).update("scene_1",location="station",weather="rain",camera={"lens":"50mm"},characters=[{"id":c.id}])
    text=generation_prompt(p,"scene_1","Maya runs")
    assert all(x in text for x in ("station","rain","50mm","brown eyes","black raincoat","coat stays wet","Maya runs"))
    assert SceneContextStore(p).get("scene_1").location=="station"
    assert CharacterStore(p).get(c.id).id==c.id

def test_scene_context_rejects_unknown_field(tmp_path):
    p=Project.create("bad",data_root=tmp_path/"projects")
    try: SceneContextStore(p).update("s",imaginary=True)
    except ValueError: pass
    else: raise AssertionError("unknown fields must fail")
