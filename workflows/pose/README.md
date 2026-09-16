# Pose Desk optional graph

Drop a **ComfyUI API-format** JSON here named `openpose_still.json` with real `class_type` nodes (OpenPose / DW preprocessor → ControlNet on the **still**).

Until then, **Apply pose** is the local skeleton overlay. Film Lab does **not** pretend ControlNet rewrote the body. Face pixels stay. Then Motion Desk **Animate** (SVD-XT).

Start the sidecar:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run_comfyui_amd.ps1
```

`http://127.0.0.1:8188` · `--cuda-device 1` · `svd_xt.safetensors`

Still-first. Not video puppeting. Zero Film Lab credits. Adults 18+.
