#!/usr/bin/env python3
"""Build pure native raw-ownership masks for each extracted PDF drawing.

An isolated vector replay gives only geometric support.  It is therefore
intersected with the final direct 300-dpi raster's source-colour line before
being used for pair analysis.  This prevents an adjacent blue/gold/gray object
inside a card from becoming part of a target path merely because it shares the
card rectangle.  Same-colour geometric contacts remain represented in both
objects' support masks and are reported as explicit pair contacts later.
"""
from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import math
from pathlib import Path

import fitz
import numpy as np
from PIL import Image, ImageDraw


DPI = 300
S = DPI / 72.0


def pxbox(rect, image, pad=3):
    r = fitz.Rect(rect)
    return (max(0, math.floor(r.x0*S)-pad), max(0, math.floor(r.y0*S)-pad),
            min(image.width, math.ceil(r.x1*S)+pad), min(image.height, math.ceil(r.y1*S)+pad))


def rgb(value):
    if value is None:
        return None
    return np.rint(np.asarray(value, dtype=float) * 255.0).astype(float)


def visible_colourline(raw, support, colour):
    if colour is None:
        return np.zeros(support.shape, dtype=bool)
    arr = raw.astype(float)
    d = 255.0 - colour
    displacement = arr - colour
    denom = float(np.dot(d, d))
    t = (displacement * d).sum(axis=2) / denom
    residual = np.sqrt(((displacement - t[..., None] * d) ** 2).sum(axis=2))
    # White may be a later opaque cover; do not turn it into visible target ink.
    contrast = (255.0 - arr).max(axis=2)
    return support & (t >= -0.03) & (t <= 1.04) & (residual <= 3.0) & (contrast >= 5.0)


def save_mask_panel(name, original, outer, support, final, out):
    native = original.crop(outer).convert("RGB")
    overlay = native.copy()
    draw = ImageDraw.Draw(overlay)
    draw.rectangle((3, 3, max(3, native.width - 4), max(3, native.height - 4)), outline=(255, 0, 0), width=1)
    native.save(out / f"{name}_original_1x.png")
    overlay.save(out / f"{name}_target_overlay_1x.png")
    native.resize((native.width * 8, native.height * 8), Image.Resampling.NEAREST).save(out / f"{name}_original_8x_nearest.png")
    pieces = []
    for title, mask in (("pre_vector_support", support), ("final_raw_ownership", final)):
        crop = mask[outer[1]:outer[3], outer[0]:outer[2]]
        pure = Image.fromarray(np.where(crop, 0, 255).astype(np.uint8), "L")
        if title == "final_raw_ownership":
            pure.save(out / f"{name}_sealed_raw_ownership_mask_1x.png")
        else:
            pure.save(out / f"{name}_pre_vector_support_mask_1x.png")
        im = pure.convert("RGB")
        ImageDraw.Draw(im).text((1, 1), title, fill="red")
        pieces.append(im)
    panel = Image.new("RGB", (sum(i.width for i in pieces), max(i.height for i in pieces)), "white")
    x = 0
    for im in pieces:
        panel.paste(im, (x, 0)); x += im.width
    panel.save(out / f"{name}_masks_panel_1x.png")


def contacts(cards, out, suffix, title):
    out.mkdir(parents=True, exist_ok=True)
    cols, per, pad, label = 3, 6, 12, 24
    for start in range(0, len(cards), per):
        part = cards[start:start+per]
        ims = [Image.open(p).convert("RGB") for p in part]
        cw = max(i.width for i in ims)+2*pad; ch=max(i.height for i in ims)+2*pad+label
        sheet=Image.new("RGB", (cols*cw,36+math.ceil(len(ims)/cols)*ch),"white")
        draw=ImageDraw.Draw(sheet); draw.text((pad,8),title,fill="black")
        for n,(im,p) in enumerate(zip(ims,part)):
            c,r=n%cols,n//cols; x=c*cw+pad; y=36+r*ch+label+pad
            sheet.paste(im,(x,y)); draw.text((x,y-label),p.name.split("_")[0],fill="black")
            draw.rectangle((c*cw,36+r*ch,(c+1)*cw-1,36+(r+1)*ch-1),outline="gray")
        sheet.save(out / f"{suffix}_sheet_{start//per+1:02d}.png")


def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--pdf",type=Path,required=True); ap.add_argument("--png",type=Path,required=True); ap.add_argument("--tool",type=Path,required=True); ap.add_argument("--out",type=Path,required=True)
    a=ap.parse_args(); cards=a.out/"sealed_drawing_cards"; cards.mkdir(parents=True,exist_ok=True)
    spec=importlib.util.spec_from_file_location("drawtool",a.tool); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    full=Image.open(a.png).convert("RGB"); raw=np.asarray(full); page=fitz.open(a.pdf)[0]; drawings=page.get_drawings()
    rows=[]
    special_math={11,12,13,14,60,61}
    for i,drawing in enumerate(drawings,1):
        oid=f"D{i:03d}"; outer=pxbox(drawing["rect"],full,3)
        replay=dict(drawing)
        background=(i==10)
        if background:
            replay["fill"]=(0.0,0.0,0.0); replay["color"]=None
        iso=mod.replay_drawing_mask(replay,page.rect)
        support=np.asarray(iso).min(axis=2)<230
        colour=rgb(drawing.get("color"))
        if colour is None:
            colour=rgb(drawing.get("fill"))
        final=visible_colourline(raw,support,colour) if not background else np.zeros_like(support)
        save_mask_panel(oid,full,outer,support,final,cards)
        if i in (7,41): category="OUT_OF_SCOPE_PAGE_DECORATION"
        elif background: category="OCCLUSION_BACKGROUND"
        elif i in special_math: category="GRAPHIC_MATH_RULE"
        else: category="SEMANTIC_GRAPHIC"
        rows.append({
            "object_id":oid,"drawing_index_zero_based":i-1,"category":category,
            "bbox_pt":str(tuple(round(v,5) for v in drawing["rect"])),"native_outer_px":str(outer),
            "source_colour_rgb": "" if colour is None else ";".join(str(int(v)) for v in colour),
            "pre_vector_support_area_px":int(support.sum()),"final_raw_ownership_area_px":int(final.sum()),
            "pre_minus_final_px":int(support.sum()-final.sum()),
            "final_mask_file":f"{oid}_sealed_raw_ownership_mask_1x.png",
            "pre_mask_file":f"{oid}_pre_vector_support_mask_1x.png",
            "identity_method":"isolated_vector_geometry INTERSECT direct_native_RGB_colourline; no_bbox_threshold; no_morphology",
            "manual_decision":"PENDING_MANUAL_LEDGER",
        })
    with (a.out/"drawing_mask_seal_machine.csv").open("w",newline="",encoding="utf-8-sig") as fh:
        w=csv.DictWriter(fh,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    for suffix,title in (("_original_1x.png","drawing ownership original native 1x"),("_target_overlay_1x.png","drawing ownership target overlay native 1x"),("_masks_panel_1x.png","drawing ownership pre/final masks native 1x"),("_original_8x_nearest.png","drawing ownership original 8x nearest")):
        paths=sorted(cards.glob(f"*{suffix}")); contacts(paths,a.out/f"sealed_drawing_contacts_{suffix[1:].split('.')[0]}",suffix[1:].split('.')[0],title)
    (a.out/"drawing_mask_seal_method.json").write_text(json.dumps({
        "foreground_path_count":sum(r["category"] in ("SEMANTIC_GRAPHIC","GRAPHIC_MATH_RULE") for r in rows),
        "occlusion_background_count":sum(r["category"]=="OCCLUSION_BACKGROUND" for r in rows),
        "page_decoration_exclusion_count":sum(r["category"]=="OUT_OF_SCOPE_PAGE_DECORATION" for r in rows),
        "manual": "No machine PASS; every path card must be visually reviewed.",
    },indent=2),encoding="utf-8")
    print(json.dumps({"drawings":len(rows),"foreground":sum(r["category"] in ("SEMANTIC_GRAPHIC","GRAPHIC_MATH_RULE") for r in rows),"zero_foreground":sum(r["category"] in ("SEMANTIC_GRAPHIC","GRAPHIC_MATH_RULE") and r["final_raw_ownership_area_px"]==0 for r in rows)},ensure_ascii=False))


if __name__=="__main__": main()
