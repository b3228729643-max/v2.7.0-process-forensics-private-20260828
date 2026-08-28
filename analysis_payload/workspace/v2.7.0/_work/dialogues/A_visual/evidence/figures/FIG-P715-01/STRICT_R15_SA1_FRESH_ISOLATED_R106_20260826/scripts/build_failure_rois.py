from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np
from PIL import Image
from scipy.spatial import cKDTree


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P715-01\STRICT_R15_SA1_FRESH_ISOLATED_R106_20260826")


def read_csv(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader(); w.writerows(rows)


def load_object_mask(obj: dict) -> tuple[np.ndarray, tuple[int, int, int, int], np.ndarray]:
    box = tuple(int(x) for x in obj["bbox_px"])
    sub = "glyphs" if obj["kind"] == "TEXT_GLYPH" else "drawings"
    mask = np.array(Image.open(ROOT / "masks" / sub / obj["safe_filename"]).convert("L")) >= 128
    ys, xs = np.nonzero(mask)
    coords = np.column_stack((xs + box[0], ys + box[1])).astype(np.int32)
    return mask, box, coords


def paint_local(target: np.ndarray, mask: np.ndarray, box: tuple[int,int,int,int], roi: tuple[int,int,int,int]) -> np.ndarray:
    out = np.zeros(target.shape[:2], bool)
    x0=max(box[0],roi[0]); y0=max(box[1],roi[1]); x1=min(box[2],roi[2]); y1=min(box[3],roi[3])
    if x1>x0 and y1>y0:
        out[y0-roi[1]:y1-roi[1],x0-roi[0]:x1-roi[0]] = mask[y0-box[1]:y1-box[1],x0-box[0]:x1-box[0]]
    return out


def main() -> None:
    objects = {o["element_id"]: o for o in json.loads((ROOT/"machine/object_manifest.json").read_text(encoding="utf-8"))}
    pairs = read_csv(ROOT/"machine/all_unordered_pairs.csv")
    selected=[]
    for p in pairs:
        req = None if p["protocol_min_clearance_px"] == "" else float(p["protocol_min_clearance_px"])
        gap = None if p["white_gap_px"] == "" else float(p["white_gap_px"])
        if req is not None and gap is not None and gap < req and p["relation_category"] in {"TEXT_TEXT","TEXT_FORMULA_NODE_BORDER","TEXT_FORMULA_PANEL_BORDER","TEXT_FORMULA_CELL_BORDER"}:
            selected.append(p)
    page = Image.open(ROOT/"views/full_page_300dpi_native.png").convert("RGB")
    page_np=np.array(page)
    out_rows=[]
    for p in selected:
        a=objects[p["object_a"]]; b=objects[p["object_b"]]
        ma,ba,ca=load_object_mask(a); mb,bb,cb=load_object_mask(b)
        la=ca[:,1].astype(np.int64)*page.width+ca[:,0]; lb=cb[:,1].astype(np.int64)*page.width+cb[:,0]
        common=np.intersect1d(la,lb)
        if len(common):
            ys=(common//page.width).astype(int); xs=(common%page.width).astype(int)
            cx=int(np.median(xs)); cy=int(np.median(ys))
        else:
            tree=cKDTree(cb); dist,idx=tree.query(ca,k=1,p=np.inf); k=int(np.argmin(dist)); q=cb[int(idx[k])]
            cx=int(round((int(ca[k,0])+int(q[0]))/2)); cy=int(round((int(ca[k,1])+int(q[1]))/2))
        half_w,half_h=90,70
        roi=(max(0,cx-half_w),max(0,cy-half_h),min(page.width,cx+half_w),min(page.height,cy+half_h))
        original=page_np[roi[1]:roi[3],roi[0]:roi[2]].copy()
        loca=paint_local(original,ma,ba,roi); locb=paint_local(original,mb,bb,roi)
        inter=loca&locb
        overlay=original.copy(); overlay[loca]=(255,0,0); overlay[locb]=(0,80,255); overlay[inter]=(255,215,0)
        araw=np.zeros(original.shape[:2],np.uint8); araw[loca]=255
        braw=np.zeros(original.shape[:2],np.uint8); braw[locb]=255
        iraw=np.zeros(original.shape[:2],np.uint8); iraw[inter]=255
        folder=ROOT/"rois"/p["pair_id"]
        folder.mkdir(parents=True,exist_ok=True)
        Image.fromarray(original).save(folder/"original_native1x.png")
        Image.fromarray(overlay).save(folder/"overlay_native1x.png")
        Image.fromarray(araw).save(folder/"object_a_raw_mask_native1x.png")
        Image.fromarray(braw).save(folder/"object_b_raw_mask_native1x.png")
        Image.fromarray(iraw).save(folder/"intersection_raw_mask_native1x.png")
        Image.fromarray(overlay).resize((overlay.shape[1]*8,overlay.shape[0]*8),Image.Resampling.NEAREST).save(folder/"overlay_8x_nearest.png")
        Image.fromarray(iraw).resize((iraw.shape[1]*8,iraw.shape[0]*8),Image.Resampling.NEAREST).save(folder/"intersection_8x_nearest.png")
        out_rows.append({
            "pair_id":p["pair_id"],"relation_category":p["relation_category"],"object_a":p["object_a"],"object_b":p["object_b"],
            "raw_intersection_px":p["raw_intersection_px"],"white_gap_px":p["white_gap_px"],"protocol_min_clearance_px":p["protocol_min_clearance_px"],
            "roi_fullpage_px":",".join(map(str,roi)),"original_native1x":str(Path("rois")/p["pair_id"]/"original_native1x.png"),
            "overlay_native1x":str(Path("rois")/p["pair_id"]/"overlay_native1x.png"),"object_a_raw_mask":str(Path("rois")/p["pair_id"]/"object_a_raw_mask_native1x.png"),
            "object_b_raw_mask":str(Path("rois")/p["pair_id"]/"object_b_raw_mask_native1x.png"),"intersection_raw_mask":str(Path("rois")/p["pair_id"]/"intersection_raw_mask_native1x.png"),
            "overlay_8x_nearest":str(Path("rois")/p["pair_id"]/"overlay_8x_nearest.png"),"intersection_8x_nearest":str(Path("rois")/p["pair_id"]/"intersection_8x_nearest.png"),
        })
    write_csv(ROOT/"machine/failure_roi_index.csv",out_rows)
    print(json.dumps({"selected_pair_count":len(selected),"roi_file_count":len(selected)*7},indent=2))


if __name__ == "__main__":
    main()
