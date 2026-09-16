from pathlib import Path
from PIL import Image, ImageDraw
from film_lab.visual_target_recognition import VisualTarget,VisualTargetStore,compare_target_regions,certify_visual_targets

class P:
    def __init__(self,p): self.root=p
    def ensure_dirs(self): self.root.mkdir(parents=True,exist_ok=True)

def img(path,left="white",right="black"):
    im=Image.new("RGB",(200,100),right); ImageDraw.Draw(im).rectangle((0,0,99,99),fill=left); im.save(path)

def test_target_store_stable_character_id(tmp_path):
    p=P(tmp_path); t=VisualTarget("sarah-face","character","Sarah",(.05,.1,.45,.9),character_id="char_sarah")
    VisualTargetStore(p).save(t); got=VisualTargetStore(p).list()[0]
    assert got.character_id=="char_sarah" and got.bbox==(.05,.1,.45,.9)

def test_region_passes_when_registered_target_is_preserved(tmp_path):
    a=tmp_path/"a.png"; b=tmp_path/"b.png"; img(a); img(b,right="red")
    t=VisualTarget("sarah","character","Sarah",(0,0,.5,1),character_id="char_sarah")
    assert compare_target_regions(a,b,t)["status"]=="PASS"

def test_region_fails_on_large_target_drift(tmp_path):
    a=tmp_path/"a.png"; b=tmp_path/"b.png"; img(a,"white"); img(b,"black")
    t=VisualTarget("prop","object","Bag",(0,0,.5,1),object_id="bag")
    assert compare_target_regions(a,b,t)["status"]=="FAIL"

def test_certification_keeps_targets_independent(tmp_path):
    p=P(tmp_path); a=tmp_path/"a.png"; b=tmp_path/"b.png"; img(a,"white","black"); img(b,"white","white")
    s=VisualTargetStore(p); s.save(VisualTarget("actor","character","Sarah",(0,0,.5,1),character_id="c1")); s.save(VisualTarget("lamp","object","Lamp",(.5,0,1,1),object_id="o1"))
    r=certify_visual_targets(p,source_frame=a,candidate_frame=b)
    by={x["target"]["id"]:x["status"] for x in r["targets"]}
    assert by["actor"]=="PASS" and by["lamp"]=="FAIL" and r["status"]=="FAIL"

def test_invalid_bbox_rejected(tmp_path):
    p=P(tmp_path)
    try: VisualTargetStore(p).save(VisualTarget("x","object","x",(.8,0,.2,1)))
    except ValueError: pass
    else: raise AssertionError("invalid bbox accepted")
