from pathlib import Path
from types import SimpleNamespace

from film_lab.advanced_conditioning_bridge import inject_advanced_conditioning
from film_lab.continuity_enforcement import build_enforcement_plan


def _conditioning(tmp_path):
    ref = tmp_path / "maya.png"; ref.write_bytes(b"image")
    char = SimpleNamespace(character_id="char_maya", name="Maya", reference_images=(str(ref),), identity_reference=str(ref))
    return SimpleNamespace(characters=(char,), camera={"move":"orbit"}, blocking=({"Maya":"door"},), objects=({"name":"bag"},), start_image="start.png", metadata={})


def test_explicit_reference_and_identity_slots_are_wired(tmp_path):
    c = _conditioning(tmp_path)
    graph = {
        "1":{"class_type":"LoadImage","inputs":{"image":"old.png"},"_meta":{"title":"film_lab_reference_image:char_maya"}},
        "2":{"class_type":"LoadImage","inputs":{"image":"old2.png"},"_meta":{"title":"film_lab_identity_image:Maya"}},
        "3":{"class_type":"ApplyInstantID","inputs":{"image":["2",0]}},
    }
    uploaded=[]
    evidence=inject_advanced_conditioning(graph,c,lambda p: uploaded.append(p) or f"uploaded-{p.name}")
    assert graph["1"]["inputs"]["image"] == "uploaded-maya.png"
    assert graph["2"]["inputs"]["image"] == "uploaded-maya.png"
    assert set(evidence["wired_capabilities"]) == {"reference_images","identity_conditioning"}
    assert len(uploaded) == 2


def test_identity_slot_without_identity_node_is_not_claimed_wired(tmp_path):
    c=_conditioning(tmp_path)
    graph={"1":{"class_type":"LoadImage","inputs":{"image":"old"},"_meta":{"title":"film_lab_identity_image:Maya"}}}
    evidence=inject_advanced_conditioning(graph,c,lambda p:"maya.png")
    assert "identity_conditioning" not in evidence["wired_capabilities"]


def test_explicit_control_slots_bridge_structured_state(tmp_path):
    c=_conditioning(tmp_path)
    graph={
        "4":{"class_type":"PrimitiveString","inputs":{"text":""},"_meta":{"title":"film_lab_camera"}},
        "5":{"class_type":"PrimitiveString","inputs":{"value":""},"_meta":{"title":"film_lab_blocking"}},
        "6":{"class_type":"PrimitiveString","inputs":{"objects":""},"_meta":{"title":"film_lab_objects"}},
    }
    evidence=inject_advanced_conditioning(graph,c,lambda p:p.name)
    assert set(evidence["wired_capabilities"]) == {"camera_control","blocking","objects"}
    assert 'orbit' in graph["4"]["inputs"]["text"]
    assert 'door' in graph["5"]["inputs"]["value"]
    assert 'bag' in graph["6"]["inputs"]["objects"]


def test_enforcement_upgrades_only_explicit_wired_channels(tmp_path):
    c=_conditioning(tmp_path)
    route={"validated":True,"workflow_capabilities":["reference_images","identity_conditioning","camera_control"],"wired_capabilities":["reference_images","identity_conditioning"]}
    result=build_enforcement_plan(c,route_metadata=route)
    by={x["name"]:x for x in result["channels"]}
    assert by["reference_images"]["status"] == "ENFORCED"
    assert by["identity_conditioning"]["status"] == "ENFORCED"
    assert by["camera_control"]["status"] == "AVAILABLE_NOT_WIRED"
    assert result["fully_enforced"] is False
