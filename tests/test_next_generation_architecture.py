from film_lab.project import Project
from film_lab.shot_card import ShotCard
from film_lab.scene_context import SceneContextStore
from film_lab.character_state import CharacterStore
from film_lab.conditioning import build_conditioning
from film_lab.generator_capabilities import GeneratorCapabilities,GeneratorRequirement,choose_generator
from film_lab.comfyui_discovery import infer_capabilities

def test_conditioning_uses_real_project_api(tmp_path):
    p=Project.create("next",data_root=tmp_path); still=p.stills_dir/"a.png"; still.write_bytes(b"x")
    c=CharacterStore(p).create("Maya",reference_images=["maya.png"],identity_adapter="instantid")
    SceneContextStore(p).update("scene_1",set_id="station",camera={"lens":"35mm"},characters=[{"id":c.id}])
    shot=ShotCard(name="Run",scene_id="scene_1",director_intent="Maya runs")
    pkg=build_conditioning(p,shot,still)
    assert pkg.set_id=="station" and pkg.characters[0].character_id==c.id and "35mm" in pkg.prompt

def test_router_prefers_capable_generator():
    class A: id="a"; capabilities=GeneratorCapabilities(text_prompt=True,start_image=True)
    class B: id="b"; capabilities=GeneratorCapabilities(text_prompt=True,start_image=True,identity_conditioning=True)
    best,_=choose_generator([A(),B()],[GeneratorRequirement("text_prompt"),GeneratorRequirement("start_image"),GeneratorRequirement("identity_conditioning",False)])
    assert best.generator_id=="b"

def test_comfyui_capabilities_require_node_evidence():
    caps,_=infer_capabilities(["KSampler","ApplyInstantID","VAEEncodeForInpaint"])
    assert caps.identity_conditioning and caps.mask_regeneration and not caps.voice
