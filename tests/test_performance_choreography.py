from film_lab.performance_choreography import InteractionCue, PerformanceChoreography, PerformanceChoreographyStore, choreography_enforcement
from film_lab.project import Project
from film_lab.shot_card import ShotCard
from film_lab.conditioning import build_conditioning
from film_lab.character_state import CharacterStore
from film_lab.scene_context import SceneContextStore


def _project(tmp_path):
    return Project.create("choreo-test", data_root=tmp_path)


def test_choreography_uses_stable_ids_and_orders_cues(tmp_path):
    p=_project(tmp_path)
    c=PerformanceChoreography("scene_1","shot_1",(
        InteractionCue(2.0,"char_b","char_a",reaction="looks back"),
        InteractionCue(0.5,"char_a","char_b",action="approaches",gaze="eye contact"),
    ))
    PerformanceChoreographyStore(p).save(c)
    got=PerformanceChoreographyStore(p).get("scene_1","shot_1")
    assert [x.actor_id for x in got.cues] == ["char_a","char_b"]
    assert got.character_ids == ("char_a","char_b")


def test_choreography_rejects_self_target():
    import pytest
    with pytest.raises(ValueError):
        InteractionCue(1.0,"char_a","char_a",action="approach")


def test_choreography_truthful_enforcement():
    c=PerformanceChoreography("s","q",(InteractionCue(0,"a","b",action="handoff"),))
    assert choreography_enforcement(c)["status"] == "PROMPT_ONLY"
    assert choreography_enforcement(c,temporal_wired=True)["status"] == "PARTIAL"
    assert choreography_enforcement(c,temporal_wired=True,multi_actor_spatial_wired=True)["status"] == "ENFORCED"


def test_conditioning_carries_choreography_and_prompt(tmp_path):
    p=_project(tmp_path)
    cs=CharacterStore(p)
    a=cs.create("Sarah"); b=cs.create("Michael")
    SceneContextStore(p).update("scene_1", characters=[{"id":a.id,"name":"Sarah"},{"id":b.id,"name":"Michael"}])
    PerformanceChoreographyStore(p).save(PerformanceChoreography("scene_1","shot_1",(
        InteractionCue(1.0,a.id,b.id,action="backs away",reaction="hesitates",gaze="looks at Michael",spacing="keeps two meters"),
    )))
    start=tmp_path/"start.png"; start.write_bytes(b"x")
    shot=ShotCard(id="shot_1", scene_id="scene_1")
    cond=build_conditioning(p,shot,start)
    assert cond.metadata["performance_choreography"]["cues"][0]["actor_id"] == a.id
    assert "Sarah" in cond.prompt and "Michael" in cond.prompt and "Actor choreography:" in cond.prompt
    assert cond.metadata["performance_choreography_enforcement"]["status"] == "PROMPT_ONLY"
