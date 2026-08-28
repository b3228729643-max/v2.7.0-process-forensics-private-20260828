"""Measure independent low-profile calibration specimens against official glyphs."""
from __future__ import annotations
import csv, json
from pathlib import Path
import fitz
import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parent
CALPDF=ROOT/'calibration_build'/'low_profile_calibration.pdf'
SPECS=[
    (1,'U+002C',',','STIXTwoMath-Regular',9.5641,'regular'),
    (2,'U+002C',',','STIXTwoMath-Regular',11.1581,'regular'),
    (3,'U+FF1F','？','NotoSerifSC-ExtraLight',9.5641,'regular'),
    (4,'U+FF1A','：','NotoSerifSC-ExtraLight',9.5641,'regular'),
    (5,'U+002E','.','STIXTwoText-Bold',9.9626,'bold'),
    (7,'U+4E00','一','NotoSerifSC-ExtraLight',9.9626,'regular'),
    (8,'U+FF1A','：','NotoSerifSC-ExtraLight',9.9626,'regular'),
    (10,'U+3002','。','NotoSerifSC-ExtraLight',9.9626,'regular'),
]

def measure(im, bb):
    x0=max(0,int(np.floor(bb[0])));y0=max(0,int(np.floor(bb[1])));x1=min(im.width,int(np.ceil(bb[2])));y1=min(im.height,int(np.ceil(bb[3])))
    a=np.asarray(im.convert('RGB'))[y0:y1,x0:x1]
    lum=.2126*a[:,:,0]+.7152*a[:,:,1]+.0722*a[:,:,2]
    m=lum<185
    ys,xs=np.where(m)
    h=0 if len(ys)==0 else int(ys.max()-ys.min()+1)
    return h,int(m.sum()),(x0,y0,x1,y1),m

def main():
    target=list(csv.DictReader((ROOT/'glyph_map.csv').open(encoding='utf-8-sig')))
    doc=fitz.open(CALPDF); rows=[]
    out=ROOT/'calibration_masks';out.mkdir(exist_ok=True)
    def process(page_no,cp,ch,expect_font,expect_size,expect_weight,selector=None):
        page=doc[page_no-1]
        raw=page.get_text('rawdict')
        chars=[]
        for b in raw['blocks']:
            if b.get('type')==0:
                for line in b['lines']:
                    for span in line['spans']:
                        for char in span['chars']:
                            if not char['c'].isspace(): chars.append((span,char))
        if selector is None:
            if len(chars)!=1:
                raise SystemExit(f'page {page_no}: expected exactly one glyph, got {len(chars)}')
            span,char=chars[0]
        else:
            matching=[x for x in chars if x[1]['c']==selector]
            if not matching:
                raise SystemExit(f'page {page_no}: missing {selector}')
            span,char=matching[0]
        im=Image.open(ROOT/'calibration_pages'/f'cal-{page_no:02d}.png')
        sx=im.width/page.rect.width;sy=im.height/page.rect.height
        bb=char['bbox']; pxbb=(bb[0]*sx,bb[1]*sy,bb[2]*sx,bb[3]*sy)
        h,area,(x0,y0,x1,y1),mask=measure(im,pxbb)
        full=np.zeros((im.height,im.width),dtype=np.uint8);full[y0:y1,x0:x1]=mask.astype(np.uint8)*255
        maskname=f'CAL-{page_no:02d}-{cp}_raw_mask.png';Image.fromarray(full).save(out/maskname)
        candidates=[g for g in target if g['CODEPOINT']==cp and g['FONT']==expect_font and abs(float(g['PDF_SIZE_PT'])-expect_size)<.02 and g['WEIGHT']==expect_weight]
        if not candidates:
            raise SystemExit(f'no target glyph mapping for {spec}')
        for g in candidates:
            ratio=float(g['INK_AREA_PX'])/area if area else 0
            hr=float(g['H_INK_PX'])/h if h else 0
            rows.append({'CALIBRATION_ID':f'CAL-{page_no:02d}','CODEPOINT':cp,'GLYPH':ch,'CAL_FONT':span['font'],'TARGET_FONT':expect_font,'CAL_SIZE_PT':round(span['size'],4),'TARGET_SIZE_PT':expect_size,'CAL_WEIGHT':expect_weight,'TARGET_GLYPH_ID':g['GLYPH_ID'],'CAL_H_INK_PX':h,'TARGET_H_INK_PX':g['H_INK_PX'],'CAL_INK_AREA_PX':area,'TARGET_INK_AREA_PX':g['INK_AREA_PX'],'AREA_RATIO_TARGET_OVER_CAL':round(ratio,4),'H_RATIO_TARGET_OVER_CAL':round(hr,4),'RAW_MASK':str((out/maskname).relative_to(ROOT)).replace('\\','/'),'FONT_MATCH':'PASS' if span['font']==expect_font else 'FAIL','SIZE_MATCH':'PASS' if abs(span['size']-expect_size)<.03 else 'FAIL','AREA_RATIO_GATE':'PASS' if .92<=ratio<=1.08 else 'FAIL','H_RATIO_GATE':'PASS' if .90<=hr<=1.10 else 'FAIL'})
    for spec in SPECS:
        process(*spec)
    # Exact caption context is the calibration reference for CJK shaping and
    # the TeX double-hyphen en dash.
    process(11,'U+2013','–','STIXTwoText-Regular',9.9626,'regular',selector='–')
    process(11,'U+3001','、','NotoSerifSC-ExtraLight',9.9626,'regular',selector='、')
    fields=list(rows[0]);
    with (ROOT/'low_profile_calibration.csv').open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
    summary={'specimen_count':len(SPECS)+2,'target_comparison_rows':len(rows),'font_failures':sum(r['FONT_MATCH']=='FAIL' for r in rows),'size_failures':sum(r['SIZE_MATCH']=='FAIL' for r in rows),'area_failures':sum(r['AREA_RATIO_GATE']=='FAIL' for r in rows),'h_failures':sum(r['H_RATIO_GATE']=='FAIL' for r in rows)}
    (ROOT/'low_profile_calibration_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    print(summary)

if __name__=='__main__': main()
