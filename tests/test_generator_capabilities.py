from types import SimpleNamespace
from film_lab.generator_capabilities import GeneratorCapabilities, GeneratorRequirement, capabilities_for, choose_generator, evaluate, requirements_from_conditioning

class Legacy:
    id="legacy"
class Basic:
    id="basic"; capabilities=GeneratorCapabilities(text_prompt=True,start_image=True,structured_conditioning=True)
class Identity:
    id="identity"; capabilities=GeneratorCapabilities(text_prompt=True,start_image=True,reference_images=True,identity_conditioning=True,camera_control=True,structured_conditioning=True)

def test_legacy_generator_is_conservative():
    caps=capabilities_for(Legacy()); assert caps.text_prompt and caps.start_image
    assert not caps.identity_conditioning and not caps.mask_regeneration and not caps.camera_control

def test_router_prefers_engine_with_requested_optional_controls():
    req=(GeneratorRequirement("text_prompt"),GeneratorRequirement("start_image"),GeneratorRequirement("identity_conditioning",False),GeneratorRequirement("camera_control",False))
    best,all_decisions=choose_generator([Basic(),Identity()],req)
    assert best.generator_id=="identity"; assert best.usable

def test_required_capability_can_block_engine():
    decision=evaluate(Basic(),(GeneratorRequirement("mask_regeneration",True),))
    assert not decision.usable; assert decision.missing_required==("mask_regeneration",)

def test_conditioning_builds_optional_identity_and_camera_requirements():
    char=SimpleNamespace(reference_images=("face.png",),identity_adapter="instantid",identity_reference="face.png")
    c=SimpleNamespace(end_image="",characters=(char,),camera={"lens":"35mm"},blocking=(),objects=())
    req={r.name:r.required for r in requirements_from_conditioning(c)}
    assert req["text_prompt"] and req["start_image"]
    assert req["identity_conditioning"] is False and req["reference_images"] is False and req["camera_control"] is False
