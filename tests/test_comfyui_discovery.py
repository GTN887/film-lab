from film_lab.comfyui_discovery import infer_capabilities
from film_lab.comfyui_generator_profile import ComfyUIGeneratorProfile

def test_identity_and_inpaint_require_node_evidence():
    caps,evidence=infer_capabilities(["LoadImage","KSampler","ApplyInstantID","VAEEncodeForInpaint","CameraCtrlApply"])
    assert caps.identity_conditioning and caps.reference_images
    assert caps.mask_regeneration and caps.camera_control
    assert not caps.voice
    assert evidence["identity_conditioning"]

def test_plain_comfyui_does_not_claim_advanced_features():
    caps,evidence=infer_capabilities(["LoadImage","KSampler","SaveImage","CheckpointLoaderSimple"])
    assert caps.text_prompt and caps.start_image
    assert not caps.identity_conditioning
    assert not caps.mask_regeneration
    assert not caps.camera_control
    assert not caps.voice

def test_profile_uses_discovered_capabilities(monkeypatch):
    import film_lab.comfyui_generator_profile as module
    class D:
        available=True; endpoint="http://local"; node_count=1; evidence={"identity_conditioning":("InstantID",)}; error=""
        from film_lab.generator_capabilities import GeneratorCapabilities
        capabilities=GeneratorCapabilities(identity_conditioning=True,start_image=True)
    monkeypatch.setattr(module,"discover_comfyui",lambda endpoint:D())
    profile=ComfyUIGeneratorProfile(endpoint="http://local")
    assert profile.available
    assert profile.capabilities.identity_conditioning
    assert profile.capability_report()["evidence"]["identity_conditioning"]==("InstantID",)
