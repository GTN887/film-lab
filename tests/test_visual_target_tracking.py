from pathlib import Path
from PIL import Image,ImageDraw
from film_lab.visual_target_recognition import VisualTarget
from film_lab.visual_target_tracking import track_target_frames,VisualTrackStore,compare_tracks

class P:
    def __init__(self,p): self.root=p
    def ensure_dirs(self): self.root.mkdir(parents=True,exist_ok=True)

def frame(path,x):
    im=Image.new("RGB",(200,100),"black"); d=ImageDraw.Draw(im); d.rectangle((x,30,x+29,69),fill="white"); d.line((x,30,x+29,69),fill="gray",width=3); im.save(path)

def test_tracker_follows_moving_registered_target(tmp_path):
    fs=[]
    for i,x in enumerate((20,30,40,50)):
        p=tmp_path/f"f{i}.png"; frame(p,x); fs.append(p)
    t=VisualTarget("sarah","character","Sarah",(.10,.30,.25,.70),character_id="char_sarah")
    tr=track_target_frames(t,fs,search_radius=.08,steps=9)
    assert tr.status=="PASS" and all(p.status=="TRACKED" for p in tr.points)
    assert tr.points[-1].bbox[0] > tr.points[0].bbox[0]

def test_tracks_persist_by_stable_target_id(tmp_path):
    p=P(tmp_path); a=tmp_path/"a.png"; frame(a,20); t=VisualTarget("bag","object","Bag",(.1,.3,.25,.7),object_id="bag-1")
    tr=track_target_frames(t,[a]); VisualTrackStore(p).save(tr); saved=VisualTrackStore(p).get("bag")
    assert saved["target_id"]=="bag" and saved["points"][0]["status"]=="TRACKED"

def test_tracker_reports_lost_target_without_identity_claim(tmp_path):
    a=tmp_path/"a.png"; b=tmp_path/"b.png"; frame(a,20); Image.new("RGB",(200,100),"black").save(b)
    t=VisualTarget("actor","character","Actor",(.1,.3,.25,.7),character_id="c1")
    tr=track_target_frames(t,[a,b],search_radius=.1,lost_threshold=.7)
    assert tr.points[-1].status=="LOST" and "does not certify biometric identity" in tr.to_dict()["truth"]

def test_track_comparison_detects_position_drift(tmp_path):
    src=[]; cand=[]
    for i,(x,y) in enumerate(zip((20,30,40),(20,70,100))):
        a=tmp_path/f"s{i}.png"; b=tmp_path/f"c{i}.png"; frame(a,x); frame(b,y); src.append(a); cand.append(b)
    t=VisualTarget("actor","character","Actor",(.1,.3,.25,.7),character_id="c1")
    s=track_target_frames(t,src,search_radius=.12,steps=11); c=track_target_frames(t,cand,search_radius=.4,steps=17)
    r=compare_tracks(s,c,center_tolerance=.08)
    assert r["status"] in {"REVIEW","FAIL"} and r["samples_compared"]>=2
