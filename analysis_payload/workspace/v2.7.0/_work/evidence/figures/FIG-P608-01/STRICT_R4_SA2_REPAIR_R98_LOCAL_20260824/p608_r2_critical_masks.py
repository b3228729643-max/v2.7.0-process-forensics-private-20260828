#!/usr/bin/env python3
"""Native 300-dpi critical-relation masks for FIG-P608-01 R2.

The only counting raster is the supplied final direct 300-dpi page.  Isolated
vector replays provide object identity for drawing paths; all final-visible
counts are sampled from that direct page without morphology or resizing.
"""
from __future__ import annotations

import argparse
import csv
import importlib.util
import math
from pathlib import Path

import fitz
import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import distance_transform_edt


DPI = 300
S = DPI / 72.0


def pxbox(rect, image, pad=0):
    r = fitz.Rect(rect)
    return (max(0, math.floor(r.x0*S)-pad), max(0, math.floor(r.y0*S)-pad),
            min(image.width, math.ceil(r.x1*S)+pad), min(image.height, math.ceil(r.y1*S)+pad))


def cropmask(mask, outer):
    return Image.fromarray(np.where(mask[outer[1]:outer[3], outer[0]:outer[2]], 0, 255).astype(np.uint8), "L")


def write_csv(path, rows):
    with path.open("w", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)


def fullmask_from_glyphs(image, glyphs, ids, glyph_card_dir):
    """Rebuild full-page text support from provenance-sealed glyph masks.

    It deliberately does not threshold the source page inside a text bbox:
    a curve, hatch, or neighbouring glyph there would be foreign ink.  The
    card coordinates come from the same native integer box used by the glyph
    review package, and a dimension mismatch is a hard script error.
    """
    result = np.zeros((image.height, image.width), dtype=bool)
    for gid in ids:
        row = glyphs[gid]
        x0,y0,x1,y1 = pxbox((float(row["x0_pt"]),float(row["y0_pt"]),float(row["x1_pt"]),float(row["y1_pt"])), image)
        card = glyph_card_dir / f"{gid}_sealed_unique_mask_1x.png"
        if not card.is_file():
            raise FileNotFoundError(card)
        target = np.asarray(Image.open(card).convert("L")) < 128
        if target.shape != (y1-y0, x1-x0):
            raise RuntimeError(f"{gid} card shape {target.shape} != native target {(y1-y0,x1-x0)}")
        result[y0:y1, x0:x1] |= target
    return result


def min_clearance(a, b):
    if not a.any() or not b.any():
        return "MASK_EMPTY", 0
    overlap = int((a & b).sum())
    if overlap:
        return "OVERLAP", 0
    # For each A pixel, distance to closest B pixel; no inflated geometry.
    dist = distance_transform_edt(~b)
    return "SEPARATE", float(dist[a].min())


def component_card(name, full, region_pt, out, masks, colors):
    outer = pxbox(region_pt, full, pad=3)
    original = full.crop(outer).convert("RGB")
    original.save(out / f"{name}_original_1x.png")
    original.resize((original.width*8, original.height*8), Image.Resampling.NEAREST).save(out / f"{name}_original_8x_nearest.png")
    overlay = original.copy(); draw = ImageDraw.Draw(overlay, "RGBA")
    for label, mask in masks.items():
        local = mask[outer[1]:outer[3], outer[0]:outer[2]]
        rgba = np.zeros((local.shape[0], local.shape[1], 4), dtype=np.uint8)
        rgba[local] = colors[label]
        overlay = Image.alpha_composite(overlay.convert("RGBA"), Image.fromarray(rgba, "RGBA"))
        cropmask(mask, outer).save(out / f"{name}_{label}_mask_1x.png")
    overlay.convert("RGB").save(out / f"{name}_relationship_overlay_1x.png")
    return outer


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--pdf',type=Path,required=True); ap.add_argument('--png',type=Path,required=True); ap.add_argument('--glyph-csv',type=Path,required=True); ap.add_argument('--glyph-card-dir',type=Path,required=True); ap.add_argument('--tool',type=Path,required=True); ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args(); a.out.mkdir(parents=True,exist_ok=True)
    spec=importlib.util.spec_from_file_location('tools_r2',a.tool); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    full=Image.open(a.png).convert('RGB'); raw=np.asarray(full); page=fitz.open(a.pdf)[0]; draws=page.get_drawings()
    with a.glyph_csv.open('r',newline='',encoding='utf-8-sig') as fh: glyphs={r['glyph_id']:r for r in csv.DictReader(fh)}
    cache={}
    def dmask(indices, force_black_fill=False):
        ans=np.zeros((full.height,full.width),dtype=bool)
        for ix in indices:
            key=(ix,force_black_fill)
            if key not in cache:
                drawing=dict(draws[ix])
                if force_black_fill:
                    # A white opaque/semitransparent fill is visually a background
                    # layer, but its geometric alpha support must not become an
                    # empty mask merely because it is white on a white test page.
                    drawing['fill']=(0.0,0.0,0.0)
                    drawing['color']=None
                im=mod.replay_drawing_mask(drawing,page.rect)
                cache[key]=np.asarray(im).min(axis=2)<230
            ans |= cache[key]
        return ans
    # D010 (index 9) is the actual white .86-opacity label underlay. It is
    # separately retained from the text and from the blue pre-occlusion trace.
    cases=[
      ('CR001_warmup_label_vs_blue', (186,120,243,152), list(range(7,8))+list(range(14,19)), 9, [f'G{i:03d}' for i in range(4,16)], 'track+markers vs semiopaque label background vs warmup text'),
      ('CR002_retained_label_vs_blue', (302,96,402,120), list(range(7,8))+list(range(19,34)), None, [f'G{i:03d}' for i in range(16,30)], 'track+markers vs retained-sample text'),
      ('CR003_target_label_vs_lower_plot', (404,172,455,192), list(range(41,44))+list(range(44,59)), None, [f'G{i:03d}' for i in range(54,58)], 'target label vs lower curve/reference/markers'),
      ('CR004_upper_axis_vs_lower_title', (258,148,375,174), [2,0], None, [f'G{i:03d}' for i in range(63,75)], 'upper axis+ticks vs lower title/formula/overbar'),
      ('CR005_rotated_script_pair', (138,114,168,224), [], None, ['G030','G031','G059','G060','G061','G062'], 'both rotated y labels and their glyph components'),
      ('CR006_eq_warmup', (186,136,216,151), [10,11], None, ['G007','G008','G009','G011','G013','G015'], 'two explicit MATH_RULE paths with neighbouring formula glyphs'),
      ('CR007_eq_retained', (344,101,374,116), [12,13], None, ['G020','G021','G022','G024','G026','G028','G029'], 'two explicit MATH_RULE paths with neighbouring formula glyphs'),
    ]
    rows=[]
    colors={'pre_blue':(0,80,255,135),'text':(255,0,0,135),'background':(0,180,0,95),'final_blue':(255,128,0,150),'math_rule':(150,0,255,135),'axis_or_tick':(0,0,0,150)}
    for name,region,blue_ix,bg_ix,text_ids,relation in cases:
        pre=dmask(blue_ix) if blue_ix else np.zeros((full.height,full.width),bool)
        text=fullmask_from_glyphs(full,glyphs,text_ids,a.glyph_card_dir)
        background=dmask([bg_ix], force_black_fill=True) if bg_ix is not None else np.zeros((full.height,full.width),bool)
        # This is the actual final raster test: source blue geometry that remains
        # at >=20/255 contrast to white after compositing, not a paint-order guess.
        final_blue=pre & ((255-raw.min(axis=2)) >= 20)
        # Name rules/axis masks separately for human interpretation.
        mname='math_rule' if name.startswith('CR006') or name.startswith('CR007') else 'axis_or_tick' if name.startswith('CR004') else 'pre_blue'
        masks={mname:pre,'text':text,'background':background,'final_blue':final_blue}
        outer=component_card(name,full,region,a.out,masks,colors)
        state_pre,clear_pre=min_clearance(pre,text)
        state_final,clear_final=min_clearance(final_blue,text)
        regionmask=np.zeros_like(pre); regionmask[outer[1]:outer[3],outer[0]:outer[2]]=True
        rows.append({
          'relation_id':name,'relation':relation,'native_roi_px':str(outer),
          'pre_mask_px':int(pre[regionmask].sum()),'text_mask_px':int(text[regionmask].sum()),'background_mask_px':int(background[regionmask].sum()),
          'pre_under_background_px':int((pre&background&regionmask).sum()),'final_blue_under_background_px':int((final_blue&background&regionmask).sum()),
          'pre_text_intersection_px':int((pre&text&regionmask).sum()),'pre_text_state':state_pre,'pre_text_clearance_px':clear_pre if isinstance(clear_pre,str) else f'{clear_pre:.3f}',
          'final_blue_px':int((final_blue&regionmask).sum()),'final_blue_text_intersection_px':int((final_blue&text&regionmask).sum()),'final_text_state':state_final,'final_text_clearance_px':clear_final if isinstance(clear_final,str) else f'{clear_final:.3f}',
          'manual_required':'TRUE','status':'PENDING_MANUAL_OPEN',
        })
    write_csv(a.out/'critical_pixel_measurements_machine.csv',rows)
    print('\n'.join(str(r) for r in rows))

if __name__=='__main__': main()
