"""Independent R95-native replay for the two initially colour-conflated relations.

The preliminary broad colour masks are deliberately not read.  This replay
uses direct R95 text operators, direct native pixels, the extracted blue
vector path and a narrowly classified dashed teal line to distinguish text
from an identically coloured graphic.
"""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path

import fitz
import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import distance_transform_edt, binary_dilation, label, find_objects


ROOT = Path(__file__).resolve().parent
PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r95_fullbook\main_full.pdf")
RASTER = ROOT / "raw" / "r95_page_625_300dpi.png"
OUT = ROOT / "critical_TG304_TG317_R95"


def pbox(rect, sx, sy, w, h):
    x0, y0, x1, y1 = map(float, rect)
    return max(0, math.floor(x0*sx)), max(0, math.floor(y0*sy)), min(w, math.ceil(x1*sx)), min(h, math.ceil(y1*sy))


def cmask(arr: np.ndarray, rgb: tuple[int, int, int]) -> np.ndarray:
    white = np.asarray((255., 255., 255.))
    a = arr.astype(float); target = np.asarray(rgb, dtype=float); d = white-target
    pr = ((white-a)*d).sum(2)/float(d@d)
    rec = white-pr[...,None]*d
    return (pr >= 20/255) & (pr <= 1.02) & (np.linalg.norm(a-rec, axis=2) <= 4.0) & (np.max(abs(white-a), axis=2) >= 20)


def chars(page, predicate, sx, sy, w, h):
    got=[]
    for block in page.get_text('rawdict')['blocks']:
        for line in block.get('lines',[]):
            for span in line.get('spans',[]):
                rgb=((span['color']>>16)&255,(span['color']>>8)&255,span['color']&255)
                for char in span.get('chars',[]):
                    b=tuple(map(float,char['bbox'])); cx=(b[0]+b[2])/2; cy=(b[1]+b[3])/2
                    if predicate(cx,cy,char['c']) and char['c'].strip(): got.append({'char':char['c'],'pdf':b,'px':pbox(b,sx,sy,w,h),'rgb':rgb})
    # Math fractions put numerator and denominator at distinct baselines; x
    # ordering preserves the source reading sequence for this legend.
    return sorted(got,key=lambda r:(r['pdf'][0],r['pdf'][1]))


def union_text(arr, records):
    m=np.zeros(arr.shape[:2],bool)
    for r in records:
        x0,y0,x1,y1=r['px']; m[y0:y1,x0:x1] |= cmask(arr[y0:y1,x0:x1],r['rgb'])
    return m


def save(im, name):
    im.save(OUT/f'{name}_1x.png')
    im.resize((im.width*8,im.height*8),Image.Resampling.NEAREST).save(OUT/f'{name}_8x_nearest.png')


def relation_artifacts(name, arr, text, graphic, roi, threshold, text_object, graphic_object):
    x0,y0,x1,y1=roi
    if not text.any() or not graphic.any(): raise RuntimeError(name+' empty mask')
    d,ind=distance_transform_edt(~graphic,return_indices=True)
    ty,tx=np.where(text); k=int(np.argmin(d[ty,tx])); yy,xx=int(ty[k]),int(tx[k]); gy,gx=int(ind[0,yy,xx]),int(ind[1,yy,xx])
    dist=float(d[yy,xx]); overlap=int(np.count_nonzero(text&graphic)); decision='PASS' if overlap==0 and dist>=threshold else 'FAIL'
    crop=arr[y0:y1,x0:x1]
    over=crop.copy(); over[text[y0:y1,x0:x1]]=(255,0,0) # red target only
    target=np.full_like(crop,255);target[text[y0:y1,x0:x1]]=(0,0,0)
    graph=np.full_like(crop,255);graph[graphic[y0:y1,x0:x1]]=(0,0,0)
    near=over.copy();near[yy-y0,xx-x0]=(255,0,0);near[gy-y0,gx-x0]=(255,165,0)
    save(Image.fromarray(crop),name+'_original')
    save(Image.fromarray(over),name+'_target_overlay_unique_red')
    save(Image.fromarray(target),name+'_target_mask_only')
    save(Image.fromarray(graph),name+'_graphic_mask_only')
    save(Image.fromarray(near),name+'_nearest_points_overlay')
    return {'RELATION_ID':name,'TEXT_OBJECT':text_object,'GRAPHIC_OBJECT':graphic_object,'THRESHOLD_PX':threshold,'RAW_MASK_OVERLAP_PX':overlap,'MIN_DISTANCE_PX':f'{dist:.3f}','NEAREST_TEXT_XY':f'{xx},{yy}','NEAREST_GRAPHIC_XY':f'{gx},{gy}','DECISION':decision,'METHOD':'direct R95 native300dpi; strict source-colour projection; geometry-constrained graphic mask'}


def main():
    OUT.mkdir(exist_ok=True)
    doc=fitz.open(PDF);page=doc[624];arr=np.asarray(Image.open(RASTER).convert('RGB'),dtype=np.uint8);h,w,_=arr.shape;sx,sy=w/page.rect.width,h/page.rect.height
    # TG304: blue legend, direct R95 text operators.
    blue_text=chars(page,lambda x,y,c:200<x<260 and 200<y<222,sx,sy,w,h)
    if ''.join(x['char'] for x in blue_text)!='实线𝑝(𝑦)': raise RuntimeError(blue_text)
    blue=union_text(arr,blue_text)
    drawlist=page.get_drawings(extended=True)
    curve=next(d for d in drawlist if d['type']=='s' and d.get('color') and abs(d['rect'].x0-121.7232)<.05 and len(d['items'])==300)
    curve_color=tuple(int(round(v*255)) for v in curve['color'])
    # Rasterise exactly the R95 extracted 300-segment path, then retain only
    # matching visible blue pixels. The later opaque white legend underlay is
    # explicitly removed, preserving the actual final visible curve.
    path=Image.new('L',(w,h),0);pd=ImageDraw.Draw(path);lw=max(1,round(float(curve['width'])*sx))
    for item in curve['items']:
        if item[0]=='l': pd.line([(round(item[1].x*sx),round(item[1].y*sy)),(round(item[2].x*sx),round(item[2].y*sy))],fill=255,width=lw)
    curve_geo=binary_dilation(np.asarray(path)>0,iterations=1)
    curve_mask=cmask(arr,curve_color)&curve_geo
    white_label=next(d for d in drawlist if d['type']=='f' and d.get('fill')==(1.0,1.0,1.0) and abs(d['rect'].x0-213.67218)<.05)
    ux0,uy0,ux1,uy1=pbox(tuple(white_label['rect']),sx,sy,w,h);curve_mask[max(0,uy0-2):min(h,uy1+2),max(0,ux0-2):min(w,ux1+2)]=False
    row304=relation_artifacts('TG304',arr,blue,curve_mask,(860,830,1090,945),3,'P_LEGEND_BLUE','G01_P_CURVE')
    # TG317: strict teal text. Its lower fraction digit bbox contains a
    # separate dash; the dash is classified as a horizontal component and
    # removed from the text-object mask before measurement.
    teal_text=chars(page,lambda x,y,c:360<x<460 and 165<y<200,sx,sy,w,h)
    if ''.join(x['char'] for x in teal_text)!='虚线𝑐𝑞(𝑦)=85': raise RuntimeError(teal_text)
    teal=tuple(teal_text[0]['rgb']);allteal=cmask(arr,teal)
    # The translucent rejection fill shares the teal hue and joins individual
    # dashes at the 20/255 text threshold.  A graphic line is opaque here, so
    # retain only >=0.50 source-colour coverage for the cq line object.
    white=np.asarray((255.,255.,255.)); direction=white-np.asarray(teal,dtype=float)
    teal_coverage=((white-arr.astype(float))*direction).sum(2)/float(direction@direction)
    # In R95 the final opaque dashes begin at native row 803.  The translucent
    # fill begins below them; limiting the band to rows 803--811 gives the
    # stroke-only line, including its real antialias edge but not the fill.
    cq=np.zeros_like(allteal);cq[803:812,500:1920]=(allteal & (teal_coverage >= .50))[803:812,500:1920]
    labelteal=union_text(arr,teal_text)
    # The lower 5's PDF advance bbox extends below its visible contour. Its
    # separate dash is a graphic, not a text contour, so exclude rows at and
    # below the first real dash from that one glyph box.
    labelteal[803:809,1836:1856]=False
    row317=relation_artifacts('TG317',arr,labelteal,cq,(1560,700,1890,830),3,'P_LEGEND_TEAL','G02_CQ_ENVELOPE')
    rows=[row304,row317]
    with (OUT/'TG304_TG317_measurements.csv').open('w',encoding='utf-8-sig',newline='') as f:
        wri=csv.DictWriter(f,fieldnames=list(rows[0]));wri.writeheader();wri.writerows(rows)
    (OUT/'TG304_TG317_measurements.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
    (OUT/'TG304_TG317_MANUAL_REVIEW.md').write_text(
        '# R95 replay of initially colour-conflated required relations\n\n'
        'Both relation bundles were opened at native 1× and 8× nearest. The preliminary broad colour mask is superseded: it merged text of the same colour into the graphic. This replay uses R95 text-operator bboxes and graphic-specific geometry. Results are in the CSV/JSON and each relation has original, unique-red target overlay, two independent masks, and nearest-points images.\n',encoding='utf-8')
    print(json.dumps(rows,ensure_ascii=False))

if __name__=='__main__': main()
