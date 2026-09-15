"""Adapter profile that exposes only capabilities discovered from local ComfyUI."""
from __future__ import annotations
from dataclasses import dataclass
from film_lab.comfyui_discovery import discover_comfyui

@dataclass
class ComfyUIGeneratorProfile:
    endpoint: str="http://127.0.0.1:8188"
    id: str="comfyui-local"
    label: str="Local ComfyUI"
    _discovery: object|None=None
    def refresh(self): self._discovery=discover_comfyui(self.endpoint); return self._discovery
    @property
    def discovery(self): return self._discovery or self.refresh()
    @property
    def capabilities(self): return self.discovery.capabilities
    @property
    def available(self): return bool(self.discovery.available)
    def capability_report(self):
        d=self.discovery
        return {"available":d.available,"endpoint":d.endpoint,"node_count":d.node_count,"capabilities":d.capabilities.to_dict(),"evidence":d.evidence or {},"error":d.error}
