"""Shot-to-shot lighting and color continuity from boundary-frame evidence.

Measures exposure/luminance, contrast and coarse RGB color balance. This is an
advisory image-statistics check: it does not infer artistic lighting intent,
physical color temperature, skin tone, or semantic scene illumination.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any
import numpy as np
from PIL import Image

@dataclass(frozen=True)
class LightingColorReport:
    status: str
    exposure_status: str
    contrast_status: str
    color_status: str
    issues: tuple[dict[str, Any], ...]
    metrics: dict[str, Any]
    truth: str
    def to_dict(self):
        d=asdict(self); d['issues']=[dict(x) for x in self.issues]; return d

def _stats(path: Path) -> dict[str,float]:
    a=np.asarray(Image.open(path).convert('RGB').resize((160,90)),dtype=np.float32)/255.0
    lum=.2126*a[:,:,0]+.7152*a[:,:,1]+.0722*a[:,:,2]
    means=a.mean(axis=(0,1)); total=float(means.sum()) or 1.0
    return {'luminance':float(lum.mean()),'contrast':float(lum.std()),
            'red_balance':float(means[0]/total),'green_balance':float(means[1]/total),'blue_balance':float(means[2]/total)}

def evaluate_lighting_color_frames(outgoing:Path,incoming:Path, *, allow_change:bool=False,
                                   exposure_review:float=.16, contrast_review:float=.12,
                                   color_review:float=.10) -> LightingColorReport:
    a,b=_stats(outgoing),_stats(incoming); issues=[]
    exposure=abs(a['luminance']-b['luminance']); contrast=abs(a['contrast']-b['contrast'])
    color=max(abs(a[k]-b[k]) for k in ('red_balance','green_balance','blue_balance'))
    def judge(delta,threshold,domain,label):
        if delta<=threshold:return 'PASS'
        sev='REVIEW' if allow_change else 'MEDIUM'
        issues.append({'domain':domain,'severity':sev,'message':f'{label} changes across the cut (Δ {delta:.3f}).'+(' Director intent explicitly allows a lighting/color change.' if allow_change else ' Confirm this is intentional.')})
        return 'REVIEW'
    es=judge(exposure,exposure_review,'lighting_exposure','Boundary luminance')
    cs=judge(contrast,contrast_review,'lighting_contrast','Boundary contrast')
    cols=judge(color,color_review,'color_balance','Coarse RGB color balance')
    status='PASS' if es==cs==cols=='PASS' else 'REVIEW'
    metrics={'outgoing':a,'incoming':b,'luminance_delta':round(exposure,6),'contrast_delta':round(contrast,6),'color_balance_delta':round(color,6),'intentional_change_allowed':bool(allow_change)}
    truth='This check measures boundary-frame luminance, contrast and coarse RGB balance. It does not measure physical color temperature, prove lighting direction/quality, identify skin tones, or decide whether an artistic lighting change is correct.'
    return LightingColorReport(status,es,cs,cols,tuple(issues),metrics,truth)
