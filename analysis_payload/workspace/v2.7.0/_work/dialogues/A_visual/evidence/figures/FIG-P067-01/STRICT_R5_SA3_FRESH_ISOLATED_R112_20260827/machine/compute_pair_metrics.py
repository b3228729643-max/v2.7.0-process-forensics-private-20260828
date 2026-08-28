from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path

import numpy as np
from PIL import Image
from scipy.ndimage import distance_transform_edt


ROOT=Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P067-01\STRICT_R5_SA3_FRESH_ISOLATED_R112_20260827")
MACHINE=ROOT/"machine"
elements=json.loads((MACHINE/"visible_elements.json").read_text(encoding="utf-8"))
pairs=json.loads((MACHINE/"all_unordered_pairs.json").read_text(encoding="utf-8"))
by_id={e["element_id"]:e for e in elements}


def load_global(e: dict) -> np.ndarray:
    x0,y0,x1,y1=e["bbox_crop_px"]
    local=np.asarray(Image.open(ROOT/e["mask"]).convert("L"))>0
    if local.shape != (y1-y0,x1-x0):
        raise RuntimeError(f"mask dimension mismatch for {e['element_id']}: {local.shape} vs {(y1-y0,x1-x0)}")
    return local


local_masks={e["element_id"]:load_global(e) for e in elements}


def candidate_metrics(a: dict,b: dict) -> tuple[int,float|None]:
    ax0,ay0,ax1,ay1=a["bbox_crop_px"]
    bx0,by0,bx1,by1=b["bbox_crop_px"]
    ux0=min(ax0,bx0); uy0=min(ay0,by0); ux1=max(ax1,bx1); uy1=max(ay1,by1)
    aa=np.zeros((uy1-uy0,ux1-ux0),dtype=bool)
    bb=np.zeros_like(aa)
    aa[ay0-uy0:ay1-uy0,ax0-ux0:ax1-ux0]=local_masks[a["element_id"]]
    bb[by0-uy0:by1-uy0,bx0-ux0:bx1-ux0]=local_masks[b["element_id"]]
    inter=int(np.count_nonzero(aa & bb))
    if inter:
        return inter,0.0
    if not np.any(aa) or not np.any(bb):
        return inter,None
    dt=distance_transform_edt(~bb)
    return inter,float(dt[aa].min())


candidate_count=0
for pair in pairs:
    if pair["bbox_intersects"] or pair["bbox_clearance_px"] <= 20.0:
        candidate_count+=1
        a=by_id[pair["element_a"]]; b=by_id[pair["element_b"]]
        inter,clearance=candidate_metrics(a,b)
        pair["raw_mask_intersection_px"]=inter
        pair["min_ink_center_distance_px"]=None if clearance is None else round(clearance,3)
        pair["metric_scope"]="native_300dpi_candidate"
    else:
        pair["raw_mask_intersection_px"]=0
        pair["min_ink_center_distance_px"]=None
        pair["metric_scope"]="bbox_clearance_gt20px"

(MACHINE/"all_unordered_pairs.json").write_text(json.dumps(pairs,ensure_ascii=False,indent=2),encoding="utf-8")
with (MACHINE/"all_unordered_pairs.csv").open("w",newline="",encoding="utf-8-sig") as f:
    writer=csv.DictWriter(f,fieldnames=list(pairs[0].keys()))
    writer.writeheader(); writer.writerows(pairs)

intersecting=[p for p in pairs if p["raw_mask_intersection_px"]>0]
summary={
    "visible_denominator":len(elements),
    "all_unordered_pairs":len(pairs),
    "pair_formula":len(elements)*(len(elements)-1)//2,
    "candidate_pairs_measured":candidate_count,
    "raw_mask_intersecting_pair_count":len(intersecting),
    "raw_mask_intersection_pixels_total":sum(p["raw_mask_intersection_px"] for p in intersecting),
    "intersecting_pair_class_counts":dict(Counter(p["pair_class"] for p in intersecting)),
    "intersecting_pairs":intersecting,
}
(MACHINE/"pair_metrics_summary.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding="utf-8")
print(json.dumps(summary,ensure_ascii=True))
