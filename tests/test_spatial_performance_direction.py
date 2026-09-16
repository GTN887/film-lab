from types import SimpleNamespace
from film_lab.spatial_control import build_spatial_assignments
from film_lab.performance_direction import build_performance_directions

def test_spatial_binding_uses_character_id_not_order():
    a=SimpleNamespace(character_id="char_a",name="Sarah",performance="backs away",emotional_state="afraid")
    b=SimpleNamespace(character_id="char_b",name="Michael",performance="watches",emotional_state="calm")
    c=SimpleNamespace(characters=(b,a),blocking=({"character_id":"char_a","region":"left"},{"character_id":"char_b","region":"right"}))
    out={x.character_id:x for x in build_spatial_assignments(c)}
    assert out["char_a"].region=="left" and out["char_b"].region=="right"
    assert out["char_a"].status=="PROMPT_ONLY"

def test_performance_is_per_character_and_directed_not_claimed_enforced():
    a=SimpleNamespace(character_id="char_a",name="Sarah",performance="backs away",emotional_state="afraid")
    b=SimpleNamespace(character_id="char_b",name="Michael",performance="watches",emotional_state="calm")
    out={x.character_id:x for x in build_performance_directions(SimpleNamespace(characters=(a,b)))}
    assert out["char_a"].emotion=="afraid"
    assert out["char_b"].performance=="watches"
    assert all(x.status=="DIRECTED" for x in out.values())
