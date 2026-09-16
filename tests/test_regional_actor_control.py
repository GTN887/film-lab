from pathlib import Path
from types import SimpleNamespace
from PIL import Image

from film_lab.advanced_conditioning_bridge import inject_advanced_conditioning
from film_lab.generator_capabilities import requirements_from_conditioning
from film_lab.mark import ProjectMarks, RegionMark, save_marks
from film_lab.project import Project
from film_lab.regional_actor_control import build_regional_actor_controls


def _project(tmp_path):
    p=Project.create("regional", data_root=tmp_path)
    p.ensure_dirs(); return p


def test_region_resolves_by_stable_character_id(tmp_path):
    p=_project(tmp_path); d=p.stills_dir/"mark_masks"; d.mkdir(parents=True,exist_ok=True)
    Image.new("L",(16,16),255).save(d/"m.png")
    save_marks(p, ProjectMarks([RegionMark("r1", target="face emotion", note="more afraid", mask_name="m.png", character_id="char_sarah")]))
    c=SimpleNamespace(characters=(SimpleNamespace(character_id="char_sarah"),), metadata={})
    out=build_regional_actor_controls(p,c)
    assert out[0].character_id=="char_sarah" and out[0].status=="REQUESTED" and Path(out[0].mask_path).is_file()


def test_legacy_unbound_mark_is_not_actor_isolated(tmp_path):
    p=_project(tmp_path); save_marks(p, ProjectMarks([RegionMark("r1", note="change")]))
    c=SimpleNamespace(characters=(SimpleNamespace(character_id="char_sarah"),), metadata={})
    assert build_regional_actor_controls(p,c)==()


def test_explicit_actor_mask_slot_wires_only_with_inpaint_node(tmp_path):
    mask=tmp_path/"mask.png"; Image.new("L",(8,8),255).save(mask)
    c=SimpleNamespace(characters=(), camera={}, blocking=(), objects=(), metadata={"regional_actor_controls":[{"character_id":"char_sarah","mask_path":str(mask),"instruction":"more afraid","status":"REQUESTED"}]})
    graph={"1":{"class_type":"LoadImage","inputs":{"image":""},"_meta":{"title":"film_lab_actor_mask:char_sarah"}},"2":{"class_type":"VAEEncodeForInpaint","inputs":{}},"3":{"class_type":"TextNode","inputs":{"text":""},"_meta":{"title":"film_lab_actor_region_prompt:char_sarah"}}}
    ev=inject_advanced_conditioning(graph,c,lambda p:"uploaded-mask.png")
    assert "mask_regeneration" in ev["wired_capabilities"]
    assert graph["1"]["inputs"]["image"]=="uploaded-mask.png"
    assert graph["3"]["inputs"]["text"]=="more afraid"


def test_regional_control_requests_mask_capability():
    c=SimpleNamespace(end_image="", characters=(), camera={}, blocking=(), objects=(), metadata={"regional_actor_controls":[{"character_id":"c"}]})
    req={r.name:r.required for r in requirements_from_conditioning(c)}
    assert req["mask_regeneration"] is False
