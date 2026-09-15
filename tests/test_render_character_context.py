from film_lab.character_state import CharacterStore
from film_lab.project import Project
from film_lab.render_service import generate_take
from film_lab.scene_context import SceneContextStore
from film_lab.shot_card import ShotCard

class CaptureGenerator:
    id="capture-character"; label="Capture Character"
    def __init__(self): self.prompt=""
    def generate(self,job):
        self.prompt=job.shot.prompt; job.output_path.write_bytes(b"video"); return job.output_path

def test_character_record_flows_into_generation_and_take(tmp_path):
    p=Project.create("character-render",base_dir=tmp_path)
    still=p.stills_dir/"start.png"; still.write_bytes(b"image")
    chars=CharacterStore(p)
    maya=chars.create("Maya",appearance="brown eyes and short dark hair",wardrobe="black raincoat",performance="restrained panic",emotional_state="afraid",continuity_notes="raincoat remains soaked",identity_adapter="future-face-adapter",identity_reference="maya_ref.png")
    SceneContextStore(p).update("scene_003",location="alley",characters=[{"id":maya.id,"name":"Maya"}])
    shot=ShotCard(id="shot_003",name="Escape",prompt="Maya looks behind her",scene_id="scene_003")
    gen=CaptureGenerator(); result=generate_take(p,shot,still,gen)
    assert maya.id in gen.prompt
    assert "brown eyes and short dark hair" in gen.prompt
    assert "black raincoat" in gen.prompt
    assert "restrained panic" in gen.prompt
    assert "raincoat remains soaked" in gen.prompt
    assert result.take.metadata["character_ids"]==[maya.id]
    snapshot=result.take.metadata["characters"][0]
    assert snapshot["id"]==maya.id
    assert snapshot["identity_adapter"]=="future-face-adapter"
    assert snapshot["identity_reference"]=="maya_ref.png"

def test_old_take_keeps_character_snapshot_after_character_changes(tmp_path):
    p=Project.create("character-snapshot",base_dir=tmp_path)
    still=p.stills_dir/"start.png"; still.write_bytes(b"image")
    chars=CharacterStore(p); maya=chars.create("Maya",wardrobe="red coat")
    SceneContextStore(p).update("scene_001",characters=[{"id":maya.id}])
    shot=ShotCard(id="shot_001",name="One",prompt="stand still",scene_id="scene_001")
    take=generate_take(p,shot,still,CaptureGenerator()).take
    chars.update(maya.id,wardrobe="blue coat")
    assert take.metadata["characters"][0]["wardrobe"]=="red coat"
    assert chars.get(maya.id).wardrobe=="blue coat"
