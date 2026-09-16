# Effects Desk custom graphs

Drop a **ComfyUI API-format** JSON here named `<preset_id>.json` (see `film_lab/effects.py`).

Until a file contains real `class_type` nodes, Effects Desk **Generate** uses the shared local **SVD-XT** img2vid graph plus that preset’s motion prompt.

Start the sidecar:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run_comfyui_amd.ps1
```

`http://127.0.0.1:8188` · `--cuda-device 1` · `svd_xt.safetensors`

Zero Film Lab credits. Adults 18+.
