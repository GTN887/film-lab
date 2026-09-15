from film_lab.character_state import CharacterStore
from film_lab.conditioning import build_conditioning
from film_lab.project import Project
from film_lab.render_service import generate_take
from film_lab.scene_context import SceneContextStore
from film_lab.shot_card import ShotCard

class StructuredGenerator:
    id="structured"; label="Structured Generator"
    def __init__(self): self.conditioning=None
    def generate(self,job):
        self.conditioning=getattr(job,"conditioning",None)
        job.output_path.write_bytes(b"video"); return job.output_path

def setup(tmp_path):
    p=Project.create("conditioning",base_dir=tmp_path); still=p.stills_dir/"start.png"; still.write_bytes(b"image")
    chars=CharacterStore(p); maya=chars.create("Maya",reference_images=["maya_front.png","maya_side.png"],identity_adapter="instantid",identity_reference="maya_front.png",performance="controlled fear",voice_id="maya_voice")
    SceneContextStore(p).update("scene_009",set_id="set_station",location="station",camera={"lens":"50mm","move":"push in"},blocking=[{"character_id":maya.id,"position":"platform edge"}],objects=[{"id":"bag","position":"left hand"}],characters=[{"id":maya.id}],continuity_notes="bag stays in left hand",director_instructions="keep performance subtle")
    shot=ShotCard(id="shot_009",name="Platform",prompt="Maya hears a noise",scene_id="scene_009")
    return p,still,maya,shot

def test_build_conditioning_contains_non_text_inputs(tmp_path):
    p,still,maya,shot=setup(tmp_path); c=build_conditioning(p,shot,still)
    assert c.set_id=="set_station"; assert c.camera["lens"]=="50mm"; assert c.blocking[0]["character_id"]==maya.id
    assert c.characters[0].reference_images==("maya_front.png","maya_side.png")
    assert c.characters[0].identity_adapter=="instantid"; assert c.characters[0].identity_reference=="maya_front.png"
    assert c.continuity_notes=="bag stays in left hand"

def test_capable_generator_receives_structured_conditioning_and_take_records_it(tmp_path):
    p,still,maya,shot=setup(tmp_path); gen=StructuredGenerator(); result=generate_take(p,shot,still,gen)
    assert gen.conditioning is not None; assert gen.conditioning.characters[0].character_id==maya.id
    assert gen.conditioning.camera["move"]=="push in"
    saved=result.take.metadata["conditioning"]
    assert saved["set_id"]=="set_station"; assert saved["characters"][0]["identity_adapter"]=="instantid"
