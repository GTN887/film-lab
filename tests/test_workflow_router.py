import json
from pathlib import Path
from film_lab.workflow_router import inspect_workflow, discover_workflows, choose_workflow


def write_api(path, nodes):
    graph={str(i):{"class_type":node,"inputs":{}} for i,node in enumerate(nodes,1)}
    path.write_text(json.dumps(graph),encoding="utf-8")


def test_workflow_requires_every_referenced_node(tmp_path):
    p=tmp_path/"svd.json"; write_api(p,["LoadImage","SVD_img2vid_Conditioning","SaveVideo"])
    profile=inspect_workflow(p,{"LoadImage":{},"SaveVideo":{}})
    assert not profile.runnable
    assert profile.missing_nodes==("SVD_img2vid_Conditioning",)


def test_workflow_reports_model_requirements_without_claiming_install(tmp_path):
    p=tmp_path/"model.json"
    p.write_text(json.dumps({"1":{"class_type":"CheckpointLoaderSimple","inputs":{"ckpt_name":"movie.safetensors"}}}),encoding="utf-8")
    unknown=inspect_workflow(p,{"CheckpointLoaderSimple":{}})
    assert unknown.runnable and unknown.model_requirements==("movie.safetensors",)
    checked=inspect_workflow(p,{"CheckpointLoaderSimple":{}},installed_models=[])
    assert not checked.runnable and checked.missing_models==("movie.safetensors",)


def test_router_prefers_runnable_workflow_matching_requested_control(tmp_path):
    basic=tmp_path/"basic.json"; identity=tmp_path/"identity.json"
    write_api(basic,["LoadImage","KSampler"])
    write_api(identity,["LoadImage","KSampler","ApplyInstantID"])
    info={"LoadImage":{},"KSampler":{},"ApplyInstantID":{}}
    route=choose_workflow(discover_workflows(tmp_path,info),["identity_conditioning"])
    assert route.workflow is not None and route.workflow.id=="identity"
    assert route.unsupported_capabilities==()


def test_router_refuses_to_call_missing_node_workflow_runnable(tmp_path):
    p=tmp_path/"broken.json"; write_api(p,["ImaginaryNode"])
    route=choose_workflow(discover_workflows(tmp_path,{}),["video_generation"])
    assert route.workflow is None
    assert "No locally runnable workflow" in route.reason
