from types import SimpleNamespace
from film_lab.performance_timeline_bridge import inject_performance_timelines, inspect_performance_controls, update_timeline_enforcement


def c():
    return SimpleNamespace(metadata={"performance_timelines":[{"character_id":"char_sarah","character_name":"Sarah","keyframes":[{"time_s":0,"emotion":"calm"},{"time_s":2,"emotion":"afraid"}]}],"performance_timeline_enforcement":[]})

def test_timeline_slot_requires_time_aware_consumer():
    graph={"1":{"class_type":"PrimitiveString","inputs":{"text":""},"_meta":{"title":"film_lab_performance_timeline:char_sarah"}}}
    ev=inject_performance_timelines(graph,c())
    assert ev["wired"] is False and graph["1"]["inputs"]["text"]==""

def test_timeline_slot_wires_with_time_aware_consumer():
    graph={"1":{"class_type":"PrimitiveString","inputs":{"text":""},"_meta":{"title":"film_lab_performance_timeline:char_sarah"}},"2":{"class_type":"PromptSchedule","inputs":{"schedule":["1",0]}}}
    cc=c(); ev=inject_performance_timelines(graph,cc); states=update_timeline_enforcement(cc,ev)
    assert ev["wired"] is True and 'afraid' in graph["1"]["inputs"]["text"]
    assert states[0]["status"]=="ENFORCED"

def test_pose_expression_discovery_is_evidence_only():
    graph={"1":{"class_type":"DWPreprocessor","inputs":{}},"2":{"class_type":"LivePortraitExpression","inputs":{}}}
    ev=inspect_performance_controls(graph)
    assert ev["pose_control"] is True and ev["expression_control"] is True and ev["time_aware"] is False

def test_unmatched_character_timeline_is_not_wired():
    graph={"1":{"class_type":"PrimitiveString","inputs":{"timeline":""},"_meta":{"title":"film_lab_performance_timeline:char_michael"}},"2":{"class_type":"TimelineKeyframe","inputs":{}}}
    assert inject_performance_timelines(graph,c())["wired"] is False
