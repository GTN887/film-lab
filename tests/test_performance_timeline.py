from types import SimpleNamespace
from film_lab.performance_timeline import PerformanceKeyframe, ActorPerformanceTimeline, PerformanceTimelineStore, timeline_enforcement
from film_lab.project import Project
from film_lab.shot_card import ShotCard
from film_lab.conditioning import build_conditioning


def test_timeline_is_stable_character_bound_and_sorted(tmp_path):
    p=Project.create("movie",data_root=tmp_path)
    t=ActorPerformanceTimeline("scene_1","shot_1","char_sarah","Sarah",(
        PerformanceKeyframe(2.0,emotion="terrified"), PerformanceKeyframe(0.0,emotion="uneasy")))
    PerformanceTimelineStore(p).save(t)
    got=PerformanceTimelineStore(p).get("scene_1","shot_1","char_sarah")
    assert got.character_id=="char_sarah" and [k.time_s for k in got.keyframes]==[0.0,2.0]


def test_timeline_rejects_invalid_time_and_intensity():
    try: PerformanceKeyframe(-1,emotion="afraid")
    except ValueError: pass
    else: assert False
    try: PerformanceKeyframe(0,intensity=1.5)
    except ValueError: pass
    else: assert False


def test_timeline_is_prompt_only_without_proven_time_bridge():
    t=ActorPerformanceTimeline("s","x","char_a","Sarah",(PerformanceKeyframe(0,emotion="calm"),))
    assert timeline_enforcement(t)["status"]=="PROMPT_ONLY"
    assert timeline_enforcement(t,time_control_wired=True)["status"]=="ENFORCED"


def test_conditioning_carries_timeline_and_temporal_prompt(tmp_path):
    p=Project.create("movie",data_root=tmp_path)
    img=p.stills_dir/"start.png"; img.write_bytes(b"image")
    shot=ShotCard(id="shot_1",scene_id="scene_1",start_frame=str(img))
    PerformanceTimelineStore(p).save(ActorPerformanceTimeline("scene_1","shot_1","char_sarah","Sarah",(
        PerformanceKeyframe(0,emotion="calm",gaze="door"),PerformanceKeyframe(2.5,emotion="afraid",action="backs away",intensity=.8))))
    c=build_conditioning(p,shot,img)
    assert c.metadata["performance_timelines"][0]["character_id"]=="char_sarah"
    assert c.metadata["performance_timeline_enforcement"][0]["status"]=="PROMPT_ONLY"
    assert "2.50s" in c.prompt and "backs away" in c.prompt
