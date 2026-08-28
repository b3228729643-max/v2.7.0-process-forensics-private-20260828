from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P583-01\STRICT_R1_SA1_FRESH_R103_R168_20260825")
PAIR_ID = "PAIR-088-089"


def coords(obj: dict) -> np.ndarray:
    mask = np.asarray(Image.open(ROOT / obj["mask_path"])) > 0
    y, x = np.nonzero(mask)
    x0, y0, _, _ = obj["tight_bbox_page_px"]
    return np.column_stack([y + y0, x + x0])


def font() -> ImageFont.ImageFont:
    p = Path(r"C:\Windows\Fonts\consola.ttf")
    return ImageFont.truetype(str(p), 18) if p.exists() else ImageFont.load_default()


def main() -> None:
    objects = {o["element_id"]: o for o in json.loads((ROOT / "machine" / "object_inventory.json").read_text(encoding="utf-8"))}
    with (ROOT / "pairs" / "all_unordered_pairs.csv").open("r", encoding="utf-8-sig", newline="") as f:
        row = next(r for r in csv.DictReader(f) if r["pair_id"] == PAIR_ID)
    a, b = objects[row["a_id"]], objects[row["b_id"]]
    ac, bc = coords(a), coords(b)
    ax0, ay0, ax1, ay1 = a["tight_bbox_page_px"]
    bx0, by0, bx1, by1 = b["tight_bbox_page_px"]
    pad = 12
    roi = (min(ax0, bx0)-pad, min(ay0, by0)-pad, max(ax1, bx1)+pad, max(ay1, by1)+pad)
    page = Image.open(ROOT / "views" / "full_page_300dpi.png").convert("RGB")
    orig = np.asarray(page.crop(roi)).copy()
    ma = np.zeros(orig.shape[:2], bool); mb = np.zeros(orig.shape[:2], bool)
    for cc, mm in ((ac, ma), (bc, mb)):
        yy = cc[:, 0]-roi[1]; xx = cc[:, 1]-roi[0]
        ok = (yy>=0)&(yy<mm.shape[0])&(xx>=0)&(xx<mm.shape[1]); mm[yy[ok], xx[ok]] = True
    overlay = orig.copy(); overlay[ma] = [255,0,0]; overlay[mb] = [0,80,255]; overlay[ma&mb] = [255,0,255]
    only_a = np.full_like(orig, 255); only_a[ma] = [0,0,0]
    only_b = np.full_like(orig, 255); only_b[mb] = [0,0,0]
    panel = Image.new("RGB", (orig.shape[1]*4, orig.shape[0]+36), "white")
    for i, arr in enumerate((orig, only_a, only_b, overlay)):
        panel.paste(Image.fromarray(arr), (i*orig.shape[1], 36))
    ImageDraw.Draw(panel).text((4,6), f"{PAIR_ID} {a['element_id']}/{b['element_id']} intentional rate construction intersection={row['intersection_px']} px", fill="black", font=font())
    p1 = ROOT / "critical" / f"{PAIR_ID}_1x.png"
    p8 = ROOT / "critical" / f"{PAIR_ID}_8x_nearest.png"
    panel.save(p1)
    panel.resize((panel.width*8, panel.height*8), Image.Resampling.NEAREST).save(p8)
    print(json.dumps({"pair_id":PAIR_ID,"a":a["element_id"],"b":b["element_id"],"intersection_px":int(row["intersection_px"]),"one_x":str(p1.relative_to(ROOT)),"eight_x":str(p8.relative_to(ROOT)),"manual_fields_generated_by_script":False}, indent=2))


if __name__ == "__main__":
    main()
