from film_lab.generators.comfyui_i2v import _installed_models_from_object_info, _kind_for_workflow


def test_installed_models_are_read_from_comfyui_choice_inputs():
    info={"CheckpointLoaderSimple":{"input":{"required":{"ckpt_name":[["a.safetensors","b.safetensors"]]}}}}
    assert _installed_models_from_object_info(info)=={"a.safetensors","b.safetensors"}


def test_unknown_model_inventory_stays_unknown():
    assert _installed_models_from_object_info({"LoadImage":{"input":{"required":{}}}}) is None


def test_workflow_id_maps_to_real_backend_kind():
    assert _kind_for_workflow("svd_xt_i2v_api")=="svd"
    assert _kind_for_workflow("amd_ltx_i2v_api")=="ltx"
    assert _kind_for_workflow("amd_animatediff_i2v_api")=="animatediff"
