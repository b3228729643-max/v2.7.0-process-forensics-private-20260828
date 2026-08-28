#!/usr/bin/env python3
"""Measure rendered independent punctuation references on the 300dpi grid."""
import csv
import math
from pathlib import Path
import fitz
import numpy as np
from PIL import Image

OUT = Path(__file__).resolve().parent
PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r97_fullbook\main_full.pdf")
PAGES = (623, 626, 789, 793)

def rgb(v): return ((v >> 16) & 255, (v >> 8) & 255, v & 255)
def box_px(b, sx, sy): return (math.floor(b[0]*sx), math.floor(b[1]*sy), math.ceil(b[2]*sx), math.ceil(b[3]*sy))
def mask(image, box):
    x0,y0,x1,y1=box; reg=image[y0:y1,x0:x1,:3]; flat=reg.reshape(-1,3)
    u,c=np.unique(flat,axis=0,return_counts=True); bg=u[c.argmax()]
    m=np.max(np.abs(reg.astype(np.int16)-bg.astype(np.int16)),axis=2)>=20
    yy,xx=np.where(m)
    return m,bg,0 if not len(yy) else int(yy.max()-yy.min()+1),int(len(yy))
doc=fitz.open(PDF); rows=[]
for physical in PAGES:
    png=OUT/f"calibration_reference_page_{physical}_native_300dpi-{physical}.png"
    if not png.exists(): continue
    im=np.asarray(Image.open(png).convert('RGB')); page=doc[physical-1]; sx=im.shape[1]/page.rect.width; sy=im.shape[0]/page.rect.height
    for block in page.get_text('rawdict')['blocks']:
        if block.get('type')!=0: continue
        for line in block['lines']:
            for sp in line['spans']:
                for ch in sp['chars']:
                    if ch['c'] not in '：；。': continue
                    b=box_px(ch['bbox'],sx,sy); m,bg,h,area=mask(im,b)
                    rows.append({'PHYSICAL_PAGE':physical,'CHAR':ch['c'],'FONT':sp.get('font',''),'PDF_SIZE':f"{float(sp.get('size',0)):.6f}",'COLOR_RGB':'/'.join(map(str,rgb(sp.get('color',0)))),'BBOX_PX':','.join(map(str,b)),'BACKGROUND_RGB':'/'.join(map(str,bg)),'H_INK_PX':h,'AREA_PX':area})
with (OUT/'low_profile_rendered_reference_measurements.csv').open('w',encoding='utf8',newline='') as f:
    w=csv.DictWriter(f,fieldnames=['PHYSICAL_PAGE','CHAR','FONT','PDF_SIZE','COLOR_RGB','BBOX_PX','BACKGROUND_RGB','H_INK_PX','AREA_PX']);w.writeheader();w.writerows(rows)
for r in rows:
    if r['FONT']=='NotoSerifSC-ExtraLight' and r['PDF_SIZE']=='9.564140' and r['COLOR_RGB']=='31/35/40' and r['CHAR']=='：': print(r)
