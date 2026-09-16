from types import SimpleNamespace
from film_lab.multi_character_conditioning import assign_character_profiles

def _c(cid,name): return SimpleNamespace(character_id=cid,name=name,reference_images=(),identity_reference="")
def test_stable_ids_get_distinct_identity_slots():
    g={
      "1":{"class_type":"LoadImage","inputs":{"image":"a.png"}},
      "2":{"class_type":"InstantIDApply","inputs":{"image":["1",0]}},
      "3":{"class_type":"LoadImage","inputs":{"image":"b.png"}},
      "4":{"class_type":"PuLIDApply","inputs":{"image":["3",0]}},
    }
    c=SimpleNamespace(characters=(_c("char_sarah","Sarah"),_c("char_michael","Michael")))
    r=assign_character_profiles(g,c)
    assert r["status"]=="PASS"
    assert g["1"]["_meta"]["title"]=="film_lab_identity_image:char_sarah"
    assert g["3"]["_meta"]["title"]=="film_lab_identity_image:char_michael"

def test_insufficient_identity_slots_is_truthful_partial():
    g={"1":{"class_type":"LoadImage","inputs":{"image":"a.png"}},"2":{"class_type":"InstantIDApply","inputs":{"image":["1",0]}}}
    c=SimpleNamespace(characters=(_c("char_a","A"),_c("char_b","B")))
    r=assign_character_profiles(g,c)
    assert r["status"]=="PARTIAL"
    assert [a["status"] for a in r["assignments"]]==["BOUND","UNSUPPORTED"]
