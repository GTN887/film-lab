from pathlib import Path
from PIL import Image,ImageDraw
from film_lab.visual_target_recognition import VisualTarget,VisualTargetStore
from film_lab.full_take_continuity_scanning import scan_frame_sequences,_times

class P:
    def __init__(self,p): self.root=p
    def ensure_dirs(self): self.root.mkdir(parents=True,exist_ok=True)

def frame(path,x=20,extra=False):
    im=Image.new("RGB",(200,100),"black"); d=ImageDraw.Draw(im); d.rectangle((x,30,x+29,69),fill="white"); d.line((x,30,x+29,69),fill="gray",width=3)
    if extra: d.rectangle((110,5,195,95),fill="white")
    im.save(path)

def seq(tmp,prefix,xs,extras=None):
    out=[]; extras=extras or set()
    for i,x in enumerate(xs):
        p=tmp/f"{prefix}{i}.png"; frame(p,x,i in extras); out.append(p)
    return out

def test_full_take_scan_passes_stable_sequence(tmp_path):
    p=P(tmp_path); s=seq(tmp_path,"s",[20,25,30]); c=seq(tmp_path,"c",[20,25,30])
    r=scan_frame_sequences(p,source_frames=s,candidate_frames=c,times_s=[0,1,2])
    assert r["status"]=="PASS" and r["sample_count"]==3 and not r["events"]

def test_full_take_scan_reports_time_of_visual_drift(tmp_path):
    p=P(tmp_path); s=seq(tmp_path,"s",[20,20,20]); c=seq(tmp_path,"c",[20,20,20],{1})
    r=scan_frame_sequences(p,source_frames=s,candidate_frames=c,times_s=[0,1.5,3])
    assert r["status"] in {"PARTIAL","FAIL"}
    assert any(e["time_s"]==1.5 and e["domain"]=="global_frame_similarity" for e in r["events"])

def test_full_take_scan_tracks_registered_target(tmp_path):
    p=P(tmp_path); VisualTargetStore(p).save(VisualTarget("sarah","character","Sarah",(.1,.3,.25,.7),character_id="char-sarah"))
    s=seq(tmp_path,"s",[20,25,30]); c=seq(tmp_path,"c",[20,25,30])
    r=scan_frame_sequences(p,source_frames=s,candidate_frames=c,times_s=[0,1,2])
    assert r["targets"][0]["target"]["character_id"]=="char-sarah"
    assert r["targets"][0]["candidate_track"]["status"]=="PASS"
    assert "does not prove biometric identity" in r["truth"]

def test_sample_times_cover_take_without_exact_eof():
    t=_times(8.0,5)
    assert t[0]==0 and len(t)==5 and 7.9<t[-1]<8.0
