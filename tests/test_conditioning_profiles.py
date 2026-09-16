from film_lab.conditioning_profiles import discover_conditioning_profiles, apply_best_conditioning_profiles


def test_instantid_connected_loadimage_becomes_identity_profile():
    graph={"1":{"class_type":"LoadImage","inputs":{"image":"x.png"}},"2":{"class_type":"ApplyInstantID","inputs":{"image":["1",0]}}}
    profiles=discover_conditioning_profiles(graph)
    assert profiles[0].capability == "identity_conditioning"
    evidence=apply_best_conditioning_profiles(graph)
    assert graph["1"]["_meta"]["title"] == "film_lab_identity_image"
    assert evidence["applied"][0]["strength"] == 100


def test_ipadapter_connected_loadimage_becomes_reference_profile():
    graph={"1":{"class_type":"LoadImage","inputs":{"image":"x.png"}},"2":{"class_type":"IPAdapterAdvanced","inputs":{"image":["1",0]}}}
    evidence=apply_best_conditioning_profiles(graph)
    assert graph["1"]["_meta"]["title"] == "film_lab_reference_image"
    assert evidence["applied"][0]["capability"] == "reference_images"


def test_unknown_or_unconnected_nodes_are_not_profiled():
    graph={"1":{"class_type":"LoadImage","inputs":{"image":"x.png"}},"2":{"class_type":"MysteryIdentity","inputs":{"image":["1",0]}},"3":{"class_type":"ApplyInstantID","inputs":{}}}
    assert discover_conditioning_profiles(graph) == ()
    assert apply_best_conditioning_profiles(graph)["applied"] == []
    assert "_meta" not in graph["1"]


def test_explicit_film_lab_slot_is_never_overwritten():
    graph={"1":{"class_type":"LoadImage","inputs":{"image":"x.png"},"_meta":{"title":"film_lab_reference_image:maya"}},"2":{"class_type":"ApplyInstantID","inputs":{"image":["1",0]}}}
    evidence=apply_best_conditioning_profiles(graph)
    assert graph["1"]["_meta"]["title"] == "film_lab_reference_image:maya"
    assert evidence["applied"] == []
