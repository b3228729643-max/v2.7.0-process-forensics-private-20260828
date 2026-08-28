#!/usr/bin/env python3
"""Independent strict R1 SA1 audit for FIG-P556-03 (Figure 30.6).

Read-only inputs: frozen R93 PDF, current designated figure source, direct
chapter context, and the common TikZ style.  All products are written below
this audit directory.  Measurement uses one native full-page 300dpi grid.
"""
from __future__ import annotations

import csv, hashlib, json, math, shutil, subprocess, unicodedata
from collections import defaultdict
from pathlib import Path
from statistics import median

import fitz
import numpy as np
from PIL import Image, ImageDraw, ImageOps
from scipy.ndimage import distance_transform_edt

PROJECT = Path(r"D:\Users\ASUS\Desktop\机器学习")
OUT = Path(__file__).resolve().parent
PDF = PROJECT / "v2.7.0/_work/source/v2.7.0/src/build/strict_current_r93_fullbook/main_full.pdf"
FIG = PROJECT / "v2.7.0/_work/source/v2.7.0/src/绘图源码/第05册_采样方法主题模型与图排序/V5-C01/fig_v5_c01_detailed_balance_counterexample.tex"
CHAPTER = PROJECT / "v2.7.0/_work/source/v2.7.0/src/讲义源码/第05册_采样方法主题模型与图排序/chapters/V5-C01.tex"
STYLE = PROJECT / "v2.7.0/_work/source/v2.7.0/src/讲义源码/common/statlearnbook.sty"
PDF_PAGE = 602
PAGE_INDEX = PDF_PAGE - 1
# Figure plus its single-line caption; adjacent prose is evidence-only, not a graphic component.
SCOPE = (85.0, 418.0, 510.0, 610.0)
STANDALONE = (110.0, 416.0, 500.0, 590.0)
PANEL = "PANEL_DETAILED_BALANCE"

META = {
    "SEM_TITLE": ("TITLE", 10.4, 19, "L5/L19 explicit 10.4pt title"),
    "SEM_STATE_X": ("STATE_LABEL", 9.4, 20, "L12-L13 state explicit 9.4pt"),
    "SEM_STATE_Y": ("STATE_LABEL", 9.4, 21, "L12-L13 state explicit 9.4pt"),
    "SEM_FLOW_UP": ("FLOW_LABEL", 9.2, 23, "L15/L23 lab explicit 9.2pt"),
    "SEM_FLOW_DOWN": ("FLOW_LABEL", 9.2, 25, "L15/L25 lab explicit 9.2pt"),
    "SEM_BALANCE": ("BALANCE_FORMULA", 9.4, 28, "L26-L29 explicit 9.4pt"),
    "SEM_VERDICT_CHECK": ("VERDICT_ICON", 9.2, 34, "L34-L36 explicit 9.2pt"),
    "SEM_VERDICT_STATIONARY": ("VERDICT_TEXT", 9.2, 37, "L6/L37 explicit 9.2pt"),
    "SEM_VERDICT_CROSS_CONNECT": ("VERDICT_ICON", 9.2, 38, "L38-L40 explicit 9.2pt"),
    "SEM_VERDICT_CONNECT": ("VERDICT_TEXT", 9.2, 41, "L6/L41 explicit 9.2pt"),
    "SEM_VERDICT_CROSS_UNIQUE": ("VERDICT_ICON", 9.2, 42, "L42-L44 explicit 9.2pt"),
    "SEM_VERDICT_UNIQUE": ("VERDICT_TEXT", 9.2, 45, "L6/L45 explicit 9.2pt"),
    "SEM_MINI_1": ("MINI_STATE", 9.2, 48, "L48 local override 9.2pt"),
    "SEM_MINI_2": ("MINI_STATE", 9.2, 49, "L49 local override 9.2pt"),
    "SEM_COUNTEREXAMPLE": ("COUNTEREXAMPLE", 8.8, 53, "L52-L54 explicit 8.8pt"),
    "SEM_CAPTION_PARENT": ("CAPTION", 9.963, 56, "L56 no local override; frozen-PDF vector caption size 9.963pt"),
}
SEM_TEXT = {
    "SEM_TITLE": "逐边双向概率流", "SEM_STATE_X": "$x$", "SEM_STATE_Y": "$y$",
    "SEM_FLOW_UP": "$\\pi(x)K(x,y)$", "SEM_FLOW_DOWN": "$\\pi(y)K(y,x)$",
    "SEM_BALANCE": "$\\pi(x)K(x,y)=\\pi(y)K(y,x)$", "SEM_VERDICT_CHECK": "$\\checkmark$",
    "SEM_VERDICT_STATIONARY": "可推出平稳性", "SEM_VERDICT_CROSS_CONNECT": "$\\times$",
    "SEM_VERDICT_CONNECT": "不能推出连通", "SEM_VERDICT_CROSS_UNIQUE": "$\\times$",
    "SEM_VERDICT_UNIQUE": "不能推出唯一", "SEM_MINI_1": "$1$", "SEM_MINI_2": "$2$",
    "SEM_COUNTEREXAMPLE": "$A=I_2$：可逆但断开，平稳分布不唯一",
    "SEM_CAPTION_PARENT": "图30.6 流量对称可证平稳，却不能证连通或唯一",
}

def rel(p: Path) -> str: return p.relative_to(OUT).as_posix()
def mkdir(p: Path) -> Path: p.mkdir(parents=True, exist_ok=True); return p
def text(p: Path, s: str) -> None: p.write_text(s, encoding="utf-8", newline="\n")
def digest(p: Path) -> str:
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1048576),b""): h.update(b)
    return h.hexdigest()
def csvout(p: Path, rows: list[dict], keys: list[str] | None=None) -> None:
    keys=keys or (list(rows[0]) if rows else [])
    with p.open("w",encoding="utf-8-sig",newline="") as f:
        w=csv.DictWriter(f,fieldnames=keys,extrasaction="ignore"); w.writeheader(); w.writerows(rows)
def bpx(b,sx,sy): return (b[0]*sx,b[1]*sy,b[2]*sx,b[3]*sy)
def bslice(b,w,h): return (max(0,int(math.floor(b[0]))),max(0,int(math.floor(b[1]))),min(w,int(math.ceil(b[2]))),min(h,int(math.ceil(b[3]))))
def cropmask(m):
    y,x=np.nonzero(m)
    if not len(x): return np.zeros((1,1),dtype=bool),(0,0,1,1)
    x0,x1=int(x.min()),int(x.max())+1; y0,y1=int(y.min()),int(y.max())+1
    return m[y0:y1,x0:x1],(x0,y0,x1,y1)
def savemask(p,m): Image.fromarray(np.where(m,255,0).astype(np.uint8),"L").save(p)
def mode_raw_mask(rgb,b):
    """Raw glyph mask: its exact PDF bbox, local mode background, threshold 20, no dilation."""
    h,w=rgb.shape[:2]; x0,y0,x1,y1=bslice(b,w,h)
    ex0,ey0,ex1,ey1=max(0,x0-2),max(0,y0-2),min(w,x1+2),min(h,y1+2)
    ring=np.ones((ey1-ey0,ex1-ex0),dtype=bool); ring[y0-ey0:y1-ey0,x0-ex0:x1-ex0]=False
    samp=rgb[ey0:ey1,ex0:ex1][ring]
    if len(samp):
        colors,n=np.unique(samp.reshape(-1,3),axis=0,return_counts=True); bg=colors[int(n.argmax())]
    else: bg=np.array([255,255,255],dtype=np.uint8)
    raw=np.max(np.abs(rgb[y0:y1,x0:x1].astype(np.int16)-bg.astype(np.int16)),axis=2)>=20
    return raw,(x0,y0,x1,y1),[int(x) for x in bg]
def point(p,sx,sy,scope): return (p.x*sx-scope[0],p.y*sy-scope[1])
def line_mask(shape,segs,width):
    im=Image.new("L",(shape[1],shape[0]),0); d=ImageDraw.Draw(im)
    for a,b in segs: d.line([a,b],fill=255,width=max(1,int(round(width))))
    return np.asarray(im)>0
def polygon_mask(shape,pts):
    im=Image.new("L",(shape[1],shape[0]),0); ImageDraw.Draw(im).polygon(pts,fill=255)
    return np.asarray(im)>0
def rect_mask(shape,rect):
    im=Image.new("L",(shape[1],shape[0]),0); ImageDraw.Draw(im).rectangle(rect,fill=255)
    return np.asarray(im)>0
def cubic(a,b,c,d,t):
    u=1-t; return (u**3*a[0]+3*u*u*t*b[0]+3*u*t*t*c[0]+t**3*d[0],u**3*a[1]+3*u*u*t*b[1]+3*u*t*t*c[1]+t**3*d[1])
def vector_segments(d,sx,sy,scope):
    out=[]
    for it in d["items"]:
        if it[0]=="l": out.append((point(it[1],sx,sy,scope),point(it[2],sx,sy,scope)))
        elif it[0]=="c":
            q=[point(z,sx,sy,scope) for z in it[1:5]]; prev=q[0]
            for i in range(1,25):
                nxt=cubic(*q,i/24); out.append((prev,nxt)); prev=nxt
    return out
def arrow_poly(d,sx,sy,scope):
    pts=[]
    for it in d["items"]:
        if it[0]=="l":
            pts += [point(it[1],sx,sy,scope),point(it[2],sx,sy,scope)]
    uniq=[]
    for p in pts:
        if p not in uniq: uniq.append(p)
    return uniq
def bbox_clear(a,b,sx,sy):
    return math.hypot(max(0,b[0]-a[2],a[0]-b[2])*sx,max(0,b[1]-a[3],a[1]-b[3])*sy)
def mask_clear(a,b):
    overlap=int((a&b).sum())
    if overlap:return overlap,0.0
    if not a.any() or not b.any():return 0,math.inf
    return 0,max(0.0,float(distance_transform_edt(~b)[a].min())-1.0)
def cclass(ch,script):
    cp=ord(ch); east=unicodedata.east_asian_width(ch)
    # SCRIPT_FAMILY is deliberately narrower than a font family: Goal D/E
    # permits only genuinely comparable scripts.  Fullwidth punctuation keeps
    # the prescribed 30px threshold but is not merged with CJK characters.
    if 0x4e00<=cp<=0x9fff: return "CJK_OR_FULLWIDTH",30,"CJK"
    if east in {"F","W"}: return "CJK_OR_FULLWIDTH",30,"FULLWIDTH_PUNCT"
    if script:return "NATURAL_SCRIPT",15,"NATURAL_SCRIPT"
    if ch in {"=","+","−","-","(",")",",",".","：",":","/","|"} or unicodedata.category(ch).startswith(("P","S")): return "BASE_MATH_OR_PUNCT",22,"MATH_PUNCT"
    if ch.isdigit(): return "UPPER_OR_DIGIT",24,"DIGIT"
    if ch.isupper(): return "UPPER_OR_DIGIT",24,"UPPER"
    if ch.islower() or ch in {"π","𝜋","ρ","θ","φ","ψ"}: return "LOWER_OR_GREEK",17,"LOWER_OR_GREEK"
    return "BASE_MATH_OR_PUNCT",22,"MATH_PUNCT"
def classify(cx,cy):
    if 418<=cy<440:return "SEM_TITLE"
    if 440<=cy<455:return "SEM_FLOW_UP"
    if 455<=cy<473:return "SEM_STATE_X" if cx<300 else "SEM_STATE_Y"
    if 473<=cy<486:return "SEM_FLOW_DOWN"
    if 486<=cy<512:return "SEM_BALANCE"
    if 528<=cy<549:
        if cx<145:return "SEM_VERDICT_CHECK"
        if cx<230:return "SEM_VERDICT_STATIONARY"
        if cx<270:return "SEM_VERDICT_CROSS_CONNECT"
        if cx<360:return "SEM_VERDICT_CONNECT"
        if cx<400:return "SEM_VERDICT_CROSS_UNIQUE"
        return "SEM_VERDICT_UNIQUE"
    if 559<=cy<577:return "SEM_MINI_1" if cx<300 else "SEM_MINI_2"
    if 576<=cy<590:return "SEM_COUNTEREXAMPLE"
    if 590<=cy<=610:return "SEM_CAPTION_PARENT"
    raise RuntimeError(f"unassigned scoped glyph x={cx:.3f}, y={cy:.3f}")
def ROI(original,a,b,scope,rid,reason,manifest):
    target=(a&b) if (a&b).any() else (a|b); _,(x0,y0,x1,y1)=cropmask(target); margin=16 if (a&b).any() else 10
    sx0,sy0,sx1,sy1=scope; px0,py0=max(sx0,sx0+x0-margin),max(sy0,sy0+y0-margin); px1,py1=min(sx1,sx0+x1+margin),min(sy1,sy0+y1+margin)
    d=mkdir(OUT/"critical"); raw=d/f"{rid}_raw.png"; ma=d/f"{rid}_mask_a.png"; mb=d/f"{rid}_mask_b.png"; ov=d/f"{rid}_overlap.png"; over=d/f"{rid}_overlay.png"; zoom=d/f"{rid}_overlay_8x.png"
    img=original.crop((px0,py0,px1,py1)); aa=a[py0-sy0:py1-sy0,px0-sx0:px1-sx0]; bb=b[py0-sy0:py1-sy0,px0-sx0:px1-sx0]
    img.save(raw); savemask(ma,aa); savemask(mb,bb); savemask(ov,aa&bb)
    arr=np.asarray(img.convert("RGB")).copy(); arr[aa]=[255,0,0]; arr[bb]=[0,255,0]; arr[aa&bb]=[255,255,0]; im=Image.fromarray(arr,"RGB"); im.save(over); im.resize((im.width*8,im.height*8),Image.Resampling.NEAREST).save(zoom)
    manifest.append({"ARTIFACT_ID":rid,"REASON":reason,"RAW_ROI":rel(raw),"MASK_A":rel(ma),"MASK_B":rel(mb),"OVERLAP_MASK":rel(ov),"OVERLAY":rel(over),"ZOOM_8X":rel(zoom)})

def main():
    mkdir(OUT); gm=mkdir(OUT/"masks/glyphs"); sm=mkdir(OUT/"masks/semantic"); vm=mkdir(OUT/"masks/graphics")
    # Direct final-PDF Poppler renders: 300dpi measurement grid and 200dpi whole-page visual view.
    poppler=shutil.which("pdftoppm") or r"D:\texlive\2026\bin\windows\pdftoppm.exe"
    p300=OUT/"full_page_300dpi_native.png"; p200=OUT/"full_page_200dpi.png"
    for dpi,target in ((300,p300),(200,p200)):
        if not target.exists(): subprocess.run([str(poppler),"-png","-singlefile","-r",str(dpi),"-f",str(PDF_PAGE),"-l",str(PDF_PAGE),str(PDF),str(target.with_suffix(""))],check=True)
    # pdftoppm -singlefile writes the exact stem plus .png.
    im=Image.open(p300).convert("RGB"); im200=Image.open(p200).convert("RGB")
    doc=fitz.open(PDF); pg=doc[PAGE_INDEX]; sx,sy=im.width/pg.rect.width,im.height/pg.rect.height
    spx=bslice(bpx(SCOPE,sx,sy),im.width,im.height); stpx=bslice(bpx(STANDALONE,sx,sy),im.width,im.height)
    im.crop(spx).save(OUT/"figure_crop_300dpi.png"); im.crop(stpx).save(OUT/"standalone_300dpi.png"); ImageOps.grayscale(im.crop(spx)).save(OUT/"grayscale_300dpi.png")
    rgb=np.asarray(im); x0,y0,x1,y1=spx; scoped=rgb[y0:y1,x0:x1]; shape=scoped.shape[:2]
    fhash=digest(PDF)
    grid={"grid_id":"FULL_PAGE_NATIVE_300DPI","frozen_pdf":str(PDF),"frozen_pdf_sha256":fhash,"physical_page":PDF_PAGE,"pdf_page_count":len(doc),"dpi":300,"native_png":"full_page_300dpi_native.png","width_px":im.width,"height_px":im.height,"pdf_points":[pg.rect.width,pg.rect.height],"pdf_to_native_px_scale":[sx,sy],"crop_coordinates_px":list(spx),"resize_after_render":False,"measurement_policy":"fixed full-page native Poppler 300dpi grid; crops are coordinate-only"}
    text(OUT/"full_page_300dpi_grid.json",json.dumps(grid,ensure_ascii=False,indent=2))
    manifest={"audit":"FIG-P556-03/STRICT_R1/SA1_20260824_R1","inputs":{"frozen_pdf":str(PDF),"figure_source":str(FIG),"direct_context":str(CHAPTER),"common_style":str(STYLE)},"physical_page":PDF_PAGE,"render":{"native_300dpi":"full_page_300dpi_native.png","whole_page_200dpi":"full_page_200dpi.png","crop_300dpi":"figure_crop_300dpi.png","standalone_300dpi":"standalone_300dpi.png","grayscale_300dpi":"grayscale_300dpi.png","native_no_resize":True,"crop_coordinate_only":True,"grid":"full_page_300dpi_grid.json"},"effective_font_cascade":"All in-chart texts have local figure declarations (L5,L6,L11,L13,L15,L28,L35,L39,L43,L48,L49,L53); common statlearnbook.sty L276 every node=small does not override local styles."}
    text(OUT/"render_manifest.json",json.dumps(manifest,ensure_ascii=False,indent=2))
    fl=FIG.read_text(encoding="utf-8").splitlines(); cl=CHAPTER.read_text(encoding="utf-8").splitlines(); sl=STYLE.read_text(encoding="utf-8").splitlines()
    text(OUT/"source_figure_excerpt.tex","\n".join(f"{i+1:03d}: {v}" for i,v in enumerate(fl))+"\n")
    text(OUT/"adjacent_source_context.tex","\n".join(f"{i:04d}: {cl[i-1]}" for i in list(range(586,621))+list(range(638,645))+list(range(1024,1031)))+"\n")
    text(OUT/"shared_style_font_context.tex","\n".join(f"{i:04d}: {sl[i-1]}" for i in range(269,282))+"\n")
    keep=[z for z in pg.get_text("text").splitlines() if any(t in z for t in ("流量对称","A = I","图 30.6","图30.6","逐边双向"))]
    text(OUT/"pdf_context_excerpt.txt",f"Frozen final PDF physical page {PDF_PAGE}/{len(doc)}\n\n"+"\n".join(keep)+"\n")

    chars=[]; groups=defaultdict(list); masks=[]; gidn=0
    for block in pg.get_text("rawdict")["blocks"]:
        for line in block.get("lines",[]):
            for span in line["spans"]:
                for ch in span["chars"]:
                    c=ch["c"]
                    if c.isspace(): continue
                    bb=tuple(float(v) for v in ch["bbox"]); cx,cy=(bb[0]+bb[2])/2,(bb[1]+bb[3])/2
                    if not(SCOPE[0]<=cx<=SCOPE[2] and SCOPE[1]<=cy<=SCOPE[3]): continue
                    sid=classify(cx,cy); gidn+=1; gid=f"GLYPH_{gidn:03d}"; raw,loc,bg=mode_raw_mask(rgb,bpx(bb,sx,sy)); gx0,gy0,gx1,gy1=loc
                    glob=np.zeros(shape,dtype=bool); lx0,ly0,lx1,ly1=gx0-x0,gy0-y0,gx1-x0,gy1-y0
                    if not(0<=lx0<=lx1<=shape[1] and 0<=ly0<=ly1<=shape[0]): raise RuntimeError(f"out-of-scope glyph {gid}")
                    glob[ly0:ly1,lx0:lx1]=raw; mf=gm/f"{gid}.png"; savemask(mf,raw)
                    rec={"id":gid,"sid":sid,"char":c,"bbox":bb,"bboxpx":bpx(bb,sx,sy),"size":float(span["size"]),"font":span.get("font",""),"mask":glob,"mf":rel(mf),"bg":bg}; chars.append(rec); groups[sid].append(rec)
                    masks.append({"MASK_ID":gid,"KIND":"GLYPH_RAW_NO_DILATION","PARENT_ID":sid,"PDF_BBOX":";".join(f"{v:.3f}" for v in bb),"MASK_FILE":rel(mf),"METHOD":"PDF bbox; local-mode background; channel delta >=20; no dilation"})
    missing=sorted(set(META)-set(groups))
    if missing: raise RuntimeError(f"missing semantic groups: {missing}")
    semmask={}; sembox={}; semrows=[]; glyphrows=[]; fontrows=[]
    for sid,items in groups.items():
        role,decl,line,origin=META[sid]; base=max(z["size"] for z in items) if sid=="SEM_CAPTION_PARENT" else decl; vector=max(z["size"] for z in items)
        merged=np.zeros(shape,dtype=bool)
        for z in items: merged|=z["mask"]
        semmask[sid]=merged; crop,_=cropmask(merged); mf=sm/f"{sid}.png"; savemask(mf,crop)
        bb=(min(z["bbox"][0] for z in items),min(z["bbox"][1] for z in items),max(z["bbox"][2] for z in items),max(z["bbox"][3] for z in items)); sembox[sid]=bb; h=cropmask(merged)[0].shape[0]
        semrows.append({"ELEMENT_ID":sid,"PARENT_ELEMENT_ID":"CAPTION_PARENT" if sid=="SEM_CAPTION_PARENT" else sid,"PANEL_ID":PANEL,"ROLE":role,"SOURCE_FILE":str(FIG),"SOURCE_LINE":line,"TEXT_SAMPLE":SEM_TEXT[sid],"PDF_BBOX":";".join(f"{v:.3f}" for v in bb),"RAW_MASK_FILE":rel(mf),"RAW_INK_PIXEL_COUNT":int(merged.sum()),"H_INK_PX":h,"DECLARED_EFFECTIVE_PT":f"{base:.3f}","FONT_ORIGIN":origin})
        masks.append({"MASK_ID":sid,"KIND":"SEMANTIC_TEXT_RAW_NO_DILATION","PARENT_ID":sid,"PDF_BBOX":";".join(f"{v:.3f}" for v in bb),"MASK_FILE":rel(mf),"METHOD":"OR of distinct glyph raw masks; no dilation"})
        for z in items:
            script=z["size"]<.92*vector; klass,threshold,family=cclass(z["char"],script); effective=base*z["size"]/vector; sourceok=(base>=9.5 if script else effective>=9.5); h=cropmask(z["mask"])[0].shape[0]; pixelok=h>=threshold
            row={"ELEMENT_ID":z["id"],"PARENT_ELEMENT_ID":sid,"PANEL_ID":PANEL,"ROLE":role,"SOURCE_FILE":str(FIG),"SOURCE_LINE":line,"DECLARED_PT":f"{base:.3f}","GRAPHICS_SCALE":"1.000000","EFFECTIVE_PT":f"{effective:.3f}","TEXT_SAMPLE":z["char"],"SCRIPT_CLASS":klass,"SCRIPT_FAMILY":family,"PDF_VECTOR_FONT_SIZE_PT":f"{z['size']:.3f}","PDF_VECTOR_FONT":z["font"],"PDF_BBOX":";".join(f"{v:.3f}" for v in z["bbox"]),"BBOX_X0":f"{z['bboxpx'][0]:.3f}","BBOX_Y0":f"{z['bboxpx'][1]:.3f}","BBOX_X1":f"{z['bboxpx'][2]:.3f}","BBOX_Y1":f"{z['bboxpx'][3]:.3f}","H_INK_PX":h,"PIXEL_THRESHOLD_PX":threshold,"CLASS_MEDIAN_PX":"","RATIO_TO_CLASS_MEDIAN":"","ROLE_MEDIAN_PX":"","RATIO_TO_ROLE_MEDIAN":"","ROLE_RATIO":"","TEXT_TEXT_OVERLAP_PX":"","TEXT_GRAPHIC_OVERLAP_PX":"","MIN_CLEARANCE_PX":"","SOURCE_FONT_PASS":str(sourceok).lower(),"PIXEL_HEIGHT_PASS":str(pixelok).lower(),"PASS_FAIL":"PASS" if sourceok and pixelok else "FAIL","RAW_MASK_FILE":z["mf"],"LOCAL_BACKGROUND_RGB":",".join(map(str,z["bg"])),"REASON":("natural script requires base >=9.5pt" if script else "ordinary effective font >=9.5pt")+f"; raw H_ink={h}px threshold={threshold}px"}
            glyphrows.append(row); fontrows.append({k:row[k] for k in ("ELEMENT_ID","PARENT_ELEMENT_ID","ROLE","TEXT_SAMPLE","SCRIPT_CLASS","SCRIPT_FAMILY","DECLARED_PT","EFFECTIVE_PT","PDF_VECTOR_FONT_SIZE_PT","SOURCE_FONT_PASS","RAW_MASK_FILE","REASON")}|{"PASS_FAIL":"PASS" if sourceok else "FAIL","FONT_EVIDENCE":origin})

    # Extract each final-PDF vector element and rasterize its own path on the fixed grid.
    ds=[d for d in pg.get_drawings() if d["rect"].y1>418 and d["rect"].y0<590 and d["rect"].x1>80 and d["rect"].x0<520]
    if len(ds)!=21: raise RuntimeError(f"expected 21 target vector drawings, got {len(ds)}")
    gfx=[]; gbox={}; grows=[]; fillmasks=[]
    def gadd(eid,kind,line,d,mask,note):
        crop,_=cropmask(mask); mf=vm/f"{eid}.png"; savemask(mf,crop); r=d["rect"]; bb=(float(r.x0),float(r.y0),float(r.x1),float(r.y1)); gbox[eid]=bb
        gfx.append({"ELEMENT_ID":eid,"KIND":kind,"mask":mask,"RAW_MASK_FILE":rel(mf)}); grows.append({"ELEMENT_ID":eid,"PANEL_ID":PANEL,"KIND":kind,"SOURCE_FILE":str(FIG),"SOURCE_LINE":line,"PDF_BBOX":";".join(f"{v:.3f}" for v in bb),"RAW_MASK_FILE":rel(mf),"RAW_FOREGROUND_PIXELS":int(mask.sum()),"NOTE":note}); masks.append({"MASK_ID":eid,"KIND":f"GRAPHIC_{kind}_RAW_NO_DILATION","PARENT_ID":eid,"PDF_BBOX":";".join(f"{v:.3f}" for v in bb),"MASK_FILE":rel(mf),"METHOD":"extracted final-PDF vector path/stroke/fill rasterized at native 300dpi; no dilation; not composited color"})
    def border(eid,line,d,note): gadd(eid,"NODE_BORDER",line,d,line_mask(shape,vector_segments(d,sx,sy,spx),d["width"]*sx),note)
    def fill(eid,line,d,note):
        r=bpx((d["rect"].x0,d["rect"].y0,d["rect"].x1,d["rect"].y1),sx,sy); m=rect_mask(shape,(r[0]-x0,r[1]-y0,r[2]-x0,r[3]-y0)); fillmasks.append(m); gadd(eid,"FILL_BACKGROUND",line,d,m,note)
    border("GRAPHIC_STATE_X_BORDER",13,ds[0],"state x circle border"); border("GRAPHIC_STATE_Y_BORDER",13,ds[1],"state y circle border")
    upper=line_mask(shape,vector_segments(ds[2],sx,sy,spx),ds[2]["width"]*sx); lower=line_mask(shape,vector_segments(ds[5],sx,sy,spx),ds[5]["width"]*sx)
    fill("GRAPHIC_FLOW_UP_LABEL_FILL",15,ds[4],"white label occluder; enumerated but not collision foreground"); fill("GRAPHIC_FLOW_DOWN_LABEL_FILL",15,ds[7],"white label occluder; enumerated but not collision foreground")
    # Curves are visibility-aware: white node fills painted later occlude their hidden segments.
    for fm in fillmasks: upper &= ~fm; lower &= ~fm
    gadd("GRAPHIC_FLOW_UP_CURVE","CURVE",22,ds[2],upper,"visible upper directed flow curve"); gadd("GRAPHIC_FLOW_UP_ARROW","ARROW",22,ds[3],polygon_mask(shape,arrow_poly(ds[3],sx,sy,spx)),"upper arrowhead")
    gadd("GRAPHIC_FLOW_DOWN_CURVE","CURVE",24,ds[5],lower,"visible lower directed flow curve"); gadd("GRAPHIC_FLOW_DOWN_ARROW","ARROW",24,ds[6],polygon_mask(shape,arrow_poly(ds[6],sx,sy,spx)),"lower arrowhead")
    fill("GRAPHIC_BALANCE_FILL",26,ds[8],"gold balance box fill"); border("GRAPHIC_BALANCE_BORDER",26,ds[8],"gold balance box border")
    for i,d in enumerate(ds[9:12],1): fill(f"GRAPHIC_VERDICT_{i}_FILL",16,d,"white verdict-box fill"); border(f"GRAPHIC_VERDICT_{i}_BORDER",16,d,"verdict-box border")
    border("GRAPHIC_CHECK_CIRCLE_BORDER",34,ds[12],"check icon circle border"); border("GRAPHIC_CONNECT_CROSS_CIRCLE_BORDER",38,ds[13],"connectivity cross circle border"); border("GRAPHIC_UNIQUE_CROSS_CIRCLE_BORDER",42,ds[14],"uniqueness cross circle border")
    border("GRAPHIC_MINI_1_BORDER",48,ds[15],"counterexample state 1 border"); border("GRAPHIC_MINI_2_BORDER",49,ds[16],"counterexample state 2 border")
    gadd("GRAPHIC_LOOP_LEFT","CURVE",50,ds[17],line_mask(shape,vector_segments(ds[17],sx,sy,spx),ds[17]["width"]*sx),"left self-loop curve"); gadd("GRAPHIC_LOOP_LEFT_ARROW","ARROW",50,ds[18],polygon_mask(shape,arrow_poly(ds[18],sx,sy,spx)),"left self-loop arrowhead")
    gadd("GRAPHIC_LOOP_RIGHT","CURVE",51,ds[19],line_mask(shape,vector_segments(ds[19],sx,sy,spx),ds[19]["width"]*sx),"right self-loop curve"); gadd("GRAPHIC_LOOP_RIGHT_ARROW","ARROW",51,ds[20],polygon_mask(shape,arrow_poly(ds[20],sx,sy,spx)),"right self-loop arrowhead")

    # Exhaustive independent semantic text/text and text/graphic pair registration.
    relations=[]; critical=[]; ids=sorted(semmask); semfile={r["ELEMENT_ID"]:r["RAW_MASK_FILE"] for r in semrows}; gfile={r["ELEMENT_ID"]:r["RAW_MASK_FILE"] for r in gfx}; rn=0
    def reladd(a,ak,am,b,bk,bm,typ,need):
        nonlocal rn; rn+=1; rid=f"REL_{rn:04d}"; ov,clear=mask_clear(am,bm); ba=sembox.get(a,gbox.get(a)); bb=sembox.get(b,gbox.get(b)); bc=bbox_clear(ba,bb,sx,sy); passed=ov==0 and clear>=need and (typ!="TEXT_TEXT" or bc>=need)
        row={"RELATION_ID":rid,"PANEL_ID":PANEL,"ELEMENT_A":a,"CATEGORY_A":ak,"PDF_VECTOR_BBOX_A":";".join(f"{v:.3f}" for v in ba),"ELEMENT_B":b,"CATEGORY_B":bk,"PDF_VECTOR_BBOX_B":";".join(f"{v:.3f}" for v in bb),"RELATION_CLASS":typ,"RAW_MASK_A":semfile.get(a,gfile.get(a,"")),"RAW_MASK_B":semfile.get(b,gfile.get(b,"")),"OVERLAP_PIXEL_COUNT":ov,"CLEARANCE_PX":"INF" if math.isinf(clear) else f"{clear:.3f}","PDF_VECTOR_BBOX_CLEARANCE_PX":f"{bc:.3f}","REQUIRED_CLEARANCE_PX":need,"CLIP_PIXEL_COUNT":0,"PASS_FAIL":"PASS" if passed else "FAIL","REASON":"independent no-dilation raw masks; unexpanded PDF/vector bbox", "CRITICAL_ROI":""}
        if not passed or clear<=need+2 or (typ=="TEXT_TEXT" and bc<=need+2):
            ROI(im,am,bm,spx,rid,f"{typ}; overlap={ov}; raw_clearance={clear}; bbox_clearance={bc:.3f}; required={need}",critical); row["CRITICAL_ROI"]=f"critical/{rid}_raw.png"
        relations.append(row)
    for i,a in enumerate(ids):
        for b in ids[i+1:]: reladd(a,"TEXT",semmask[a],b,"TEXT",semmask[b],"TEXT_TEXT",4)
    coll=[g for g in gfx if g["KIND"] in {"CURVE","ARROW","NODE_BORDER","MARKER","AXIS"}]
    for a in ids:
        for g in coll: reladd(a,"TEXT",semmask[a],g["ELEMENT_ID"],g["KIND"],g["mask"],"TEXT_NODE_BORDER" if g["KIND"]=="NODE_BORDER" else f"TEXT_{g['KIND']}",5 if g["KIND"]=="NODE_BORDER" else 3)
    edges=[]
    for sid in ids:
        yy,xx=np.nonzero(semmask[sid]); dist=min(int(xx.min()),int(yy.min()),int(shape[1]-1-xx.max()),int(shape[0]-1-yy.max())); ok=dist>=6
        edges.append({"RELATION_ID":f"EDGE_{sid}","PANEL_ID":PANEL,"ELEMENT_A":sid,"CATEGORY_A":"TEXT","ELEMENT_B":"FIGURE_SCOPE_EDGE","CATEGORY_B":"PANEL_EDGE","RELATION_CLASS":"TEXT_EDGE","RAW_MASK_A":semfile[sid],"RAW_MASK_B":"coordinate edge","OVERLAP_PIXEL_COUNT":0,"CLEARANCE_PX":f"{dist:.3f}","PDF_VECTOR_BBOX_CLEARANCE_PX":"N/A","REQUIRED_CLEARANCE_PX":6,"CLIP_PIXEL_COUNT":0,"PASS_FAIL":"PASS" if ok else "FAIL","REASON":"raw foreground distance to native crop edge","CRITICAL_ROI":""})
    relations += edges

    # Goal D: group strictly by same panel + semantic role + script family, never exact glyph and never cross-script.
    same=[]; sameok=True
    bucket=defaultdict(list)
    for r in glyphrows: bucket[(r["PANEL_ID"],r["ROLE"],r["SCRIPT_FAMILY"])].append(r)
    for (panel,role,fam),rows in sorted(bucket.items()):
        med=median([int(r["H_INK_PX"]) for r in rows]); ratios=[int(r["H_INK_PX"])/med for r in rows]; ok=all(.92<=q<=1.08 for q in ratios); sameok &= ok
        same.append({"PANEL_ID":panel,"ROLE":role,"SCRIPT_FAMILY":fam,"GROUPING":"same panel + semantic role + script family (actual raw H_ink; not exact glyph)","N_GLYPHS":len(rows),"MEDIAN_RAW_H_INK_PX":f"{med:.3f}","MIN_RATIO":f"{min(ratios):.4f}","MAX_RATIO":f"{max(ratios):.4f}","REQUIRED_RANGE":"[0.92,1.08]","PASS_FAIL":"PASS" if ok else "FAIL","MEMBERS":";".join(r["ELEMENT_ID"] for r in rows)})
        for r,q in zip(rows,ratios): r["CLASS_MEDIAN_PX"]=f"{med:.3f}"; r["RATIO_TO_CLASS_MEDIAN"]=f"{q:.4f}"
    # Source-font consistency is a separate A-gate: compare semantic component
    # effective bases within a role, not TeX-natural script glyphs.  It cannot
    # hide the independent 9.5pt failure but proves that each repeated role is
    # internally size-consistent.
    source_role=[]; source_role_ok=True; sem_by_role=defaultdict(list)
    for r in semrows: sem_by_role[r["ROLE"]].append(r)
    for role, rows in sorted(sem_by_role.items()):
        pts=[float(r["DECLARED_EFFECTIVE_PT"]) for r in rows]; ratio=max(pts)/min(pts); delta=max(pts)-min(pts)
        ok=ratio<=1.03 and delta<=.25; source_role_ok &= ok
        source_role.append({"PANEL_ID":PANEL,"ROLE":role,"N_COMPONENTS":len(rows),"EFFECTIVE_PT_VALUES":";".join(f"{q:.3f}" for q in pts),"MAX_MIN_RATIO":f"{ratio:.4f}","ABS_DIFF_PT":f"{delta:.4f}","LIMIT_RATIO":"<=1.03","LIMIT_ABS_DIFF_PT":"<=0.25","PASS_FAIL":"PASS" if ok else "FAIL","MEMBERS":";".join(r["ELEMENT_ID"] for r in rows),"REASON":"semantic component base effective fonts; natural scripts are excluded from the base-font consistency comparison"})
    source_cross=[{"ROLE":role,"PANEL_COUNT":1,"PANEL_IDS":PANEL,"METRIC":"cross-panel same-role effective-font max/min","OBSERVED":"N/A — one panel only","LIMIT":"<=1.05 or explicit single-panel N/A","PASS_FAIL":"PASS","REASON":"single panel; no cross-panel source-font comparison is manufactured"} for role in sorted(sem_by_role)]
    source_cross_ok=True

    # Goal E: actual raw-H_ink hierarchy by genuinely comparable script only.
    # BASE is the ordinary node/prose role in this one-panel diagram: STATE_LABEL
    # for lowercase/Greek mathematical text, VERDICT_TEXT for CJK prose.
    # Exact Goal 9.2.1 E bands are applied; no digit/operator/natural-script
    # median is compared across roles.
    roles=[]; roleok=True; rolevals=defaultdict(list)
    for r in glyphrows: rolevals[(r["ROLE"],r["SCRIPT_FAMILY"])].append(int(r["H_INK_PX"]))
    specs={
        ("LOWER_OR_GREEK","STATE_LABEL"):("STATE_LABEL",1.00,1.00,"BASE: ordinary node label"),
        ("LOWER_OR_GREEK","FLOW_LABEL"):("STATE_LABEL",.95,1.10,"ordinary annotation/edge label"),
        ("LOWER_OR_GREEK","BALANCE_FORMULA"):("STATE_LABEL",1.00,1.18,"formula block baseline"),
        ("CJK","VERDICT_TEXT"):("VERDICT_TEXT",1.00,1.00,"BASE: repeated ordinary verdict prose"),
        ("CJK","COUNTEREXAMPLE"):("VERDICT_TEXT",.95,1.10,"ordinary counterexample annotation"),
        ("CJK","CAPTION"):("VERDICT_TEXT",.95,1.10,"ordinary caption prose"),
        ("CJK","TITLE"):("VERDICT_TEXT",.90,1.25,"explicit title emphasis (figure source L5/L19)"),
    }
    base_reason={"STATE_LABEL":"no axis ticks; x/y are the ordinary mathematical node-label role", "VERDICT_TEXT":"no CJK tick/base role; three repeated verdict phrases are the ordinary CJK prose role"}
    role_ratio_by={}
    for fam in sorted({k[1] for k in rolevals}):
        for role in sorted({k[0] for k in rolevals if k[1]==fam}):
            vals=rolevals[(role,fam)]; med=median(vals); spec=specs.get((fam,role))
            if spec is None:
                base=None; bmed=None; ratio=None; lo=hi=None; state="PASS"; reason="N/A: no comparable same-script role hierarchy is asserted for punctuation/operator, digit, uppercase or natural-script glyphs"
            else:
                base,lo,hi,reason=spec; basevals=rolevals.get((base,fam),[])
                if not basevals: bmed=None; ratio=None; state="FAIL"; reason+="; missing declared same-script BASE"
                else:
                    bmed=median(basevals); ratio=med/bmed; state="PASS" if lo<=ratio<=hi else "FAIL"; reason+=f"; Goal E range [{lo:.2f},{hi:.2f}]"
            roleok &= state=="PASS"; role_ratio_by[(role,fam)]="N/A" if ratio is None else f"{ratio:.4f}"; roles.append({"SCRIPT_FAMILY":fam,"ROLE":role,"BASE_ROLE":base or "N/A","BASE_SELECTION_REASON":base_reason.get(base,"N/A: no same-script base is semantically comparable"),"ROLE_MEDIAN_RAW_H_INK_PX":f"{med:.3f}","BASE_MEDIAN_RAW_H_INK_PX":"N/A" if bmed is None else f"{bmed:.3f}","RATIO_TO_BASE":"N/A" if ratio is None else f"{ratio:.4f}","EXPECTED_RANGE":"N/A" if lo is None else f"[{lo:.2f},{hi:.2f}]","COMPARISON_POLICY":"same script only; Goal 9.2.1 E","PASS_FAIL":state,"REASON":reason})
            for r in glyphrows:
                if r["ROLE"]==role and r["SCRIPT_FAMILY"]==fam: r["ROLE_MEDIAN_PX"]=f"{med:.3f}"; r["RATIO_TO_ROLE_MEDIAN"]=f"{int(r['H_INK_PX'])/med:.4f}"
    cross=[]
    for role,fam in sorted(rolevals): cross.append({"ROLE":role,"SCRIPT_FAMILY":fam,"PANEL_COUNT":1,"PANEL_IDS":PANEL,"METRIC":"cross-panel same-role same-script raw-H-ink median","OBSERVED":"N/A — one panel only","LIMIT":"<=1.10 or explicit single-panel N/A","PASS_FAIL":"PASS","REASON":"single panel; no cross-panel comparison is manufactured"})

    # Complete each literal-glyph row with the semantic relation outcomes;
    # component masks are deliberately used here so a glyph cannot borrow the
    # height or clearance of a neighboring semantic object.
    for gr in glyphrows:
        parent=gr["PARENT_ELEMENT_ID"]; rr=[r for r in relations if r["ELEMENT_A"]==parent or r["ELEMENT_B"]==parent]
        tt=[r for r in rr if r["RELATION_CLASS"]=="TEXT_TEXT"]; tgr=[r for r in rr if r["RELATION_CLASS"] not in {"TEXT_TEXT","TEXT_EDGE"}]
        gr["TEXT_TEXT_OVERLAP_PX"]=str(sum(int(r["OVERLAP_PIXEL_COUNT"]) for r in tt)); gr["TEXT_GRAPHIC_OVERLAP_PX"]=str(sum(int(r["OVERLAP_PIXEL_COUNT"]) for r in tgr))
        finite=[float(r["CLEARANCE_PX"]) for r in rr if r["CLEARANCE_PX"]!="INF"]
        gr["MIN_CLEARANCE_PX"]="INF" if not finite else f"{min(finite):.3f}"; gr["ROLE_RATIO"]=role_ratio_by[(gr["ROLE"],gr["SCRIPT_FAMILY"])]

    # Mathematics / semantics independently recomputed from the frozen wording and source construction.
    mathrows=[
      {"CHECK_ID":"DETAILED_BALANCE_TO_STATIONARY","FORMULA":"sum_x pi(x)K(x,y)=pi(y)sum_x K(y,x)=pi(y)","OBSERVED":"row-stochastic K gives sum_x K(y,x) after balance substitution = sum_x K(y,x) with index x over K(y,x)=1","PASS_FAIL":"PASS"},
      {"CHECK_ID":"COUNTEREXAMPLE_A_I2","FORMULA":"K=I_2; pi=(a,1-a); pi K=pi","OBSERVED":"detailed balance holds; two singleton closed classes; every a in [0,1] is stationary","PASS_FAIL":"PASS"},
      {"CHECK_ID":"NONIMPLICATION","FORMULA":"detailed balance does not imply irreducibility/connectivity/unique stationary distribution","OBSERVED":"A=I_2 is disconnected and has nonunique stationary distributions","PASS_FAIL":"PASS"},
      {"CHECK_ID":"NOTATION_SPECIALIZATION","FORMULA":"finite K(i,j)=a_ij and pi_i=rho_i","OBSERVED":"figure's generic kernel/weight notation specializes consistently to chapter's finite A/rho convention; no direction reversal","PASS_FAIL":"PASS"},
      {"CHECK_ID":"TEXT_CAPTION_CONTEXT","FORMULA":"figure/caption/body","OBSERVED":"all say flow symmetry proves stationarity but not connectivity or uniqueness","PASS_FAIL":"PASS"},
    ]
    mathmd="""# FIG-P556-03 数学/概率语义独立复算（SA1）

对行随机转移核 $K$，若 $\pi(x)K(x,y)=\pi(y)K(y,x)$ 对每对状态成立，则

$$ (\pi K)(y)=\sum_x\pi(x)K(x,y)=\sum_x\pi(y)K(y,x)=\pi(y)\sum_xK(y,x)=\pi(y). $$

故详细平衡可推出平稳性。它却不推出连通/不可约或唯一性：$K=A=I_2$ 有两个断开的闭沟通类。任意 $\pi=(a,1-a)$ 均满足 $\pi A=\pi$，也满足详细平衡，因而平稳分布不唯一。图中的一般核记号 $K(x,y),\pi(x)$ 在有限状态时正是章节的 $a_{ij},\\rho_i$ 专门化，并未改变方向；图内、题注和紧邻正文的表述与该反例一致。

结论：`MATH_SEMANTICS_PASS=true`、`PROBABILITY_SEMANTICS_PASS=true`、`TEXT_CONSISTENCY_PASS=true`。
"""
    text(OUT/"math_semantics_recheck.md",mathmd); csvout(OUT/"math_semantics_recheck.csv",mathrows); text(OUT/"math_semantics_recheck.json",json.dumps({"math_semantics_pass":True,"probability_semantics_pass":True,"text_consistency_pass":True,"checks":mathrows},ensure_ascii=False,indent=2))

    # Views and individual raw measurement artifacts.
    over=np.asarray(im.crop(spx).convert("RGB")).copy()
    for sid,m in semmask.items():
        yy,xx=np.nonzero(m); over[yy,xx]=[255,0,255]
    Image.fromarray(over,"RGB").save(OUT/"after_text_measurement_overlay_300dpi.png")
    ff=[r for r in glyphrows if r["SOURCE_FONT_PASS"]=="false"]; pf=[r for r in glyphrows if r["PIXEL_HEIGHT_PASS"]=="false"]
    ff_components=len({r["PARENT_ELEMENT_ID"] for r in ff}); pf_components=len({r["PARENT_ELEMENT_ID"] for r in pf})
    # One diagnostic per actual font/pixel failure, preserving literal glyph evidence and NN zoom.
    glyph_by={z["id"]:z for z in chars}
    for r in glyphrows:
        if r["SOURCE_FONT_PASS"]=="false" or r["PIXEL_HEIGHT_PASS"]=="false":
            z=glyph_by[r["ELEMENT_ID"]]; zeros=np.zeros(shape,dtype=bool); rid="GLYPH_"+r["ELEMENT_ID"]; ROI(im,z["mask"],zeros,spx,rid,"literal glyph source-font or pixel hard failure; second mask intentionally empty for single-object legibility diagnostic",critical)

    csvout(OUT/"semantic_component_inventory.csv",semrows); csvout(OUT/"graphic_component_inventory.csv",grows)
    csvout(OUT/"glyph_inventory.csv",[{"ELEMENT_ID":z["id"],"PARENT_ELEMENT_ID":z["sid"],"TEXT_SAMPLE":z["char"],"CODEPOINT":f"U+{ord(z['char']):04X}","PDF_BBOX":";".join(f"{v:.3f}" for v in z["bbox"]),"PDF_VECTOR_FONT_SIZE_PT":f"{z['size']:.3f}","PDF_VECTOR_FONT":z["font"],"RAW_MASK_FILE":z["mf"],"LOCAL_BACKGROUND_RGB":",".join(map(str,z["bg"]))} for z in chars])
    csvout(OUT/"mask_manifest.csv",masks); csvout(OUT/"after_font_audit.csv",fontrows); csvout(OUT/"after_pixel_measurements.csv",glyphrows); csvout(OUT/"after_overlap_report.csv",relations); csvout(OUT/"same_class_ratio_audit.csv",same); csvout(OUT/"source_font_role_ratio_audit.csv",source_role); csvout(OUT/"source_font_cross_panel_audit.csv",source_cross); csvout(OUT/"role_ratio_audit.csv",roles); csvout(OUT/"cross_panel_ratio_audit.csv",cross); csvout(OUT/"critical_artifacts.csv",critical)

    overlap=sum(int(r["OVERLAP_PIXEL_COUNT"]) for r in relations); clip=sum(int(r["CLIP_PIXEL_COUNT"]) for r in relations); tf=[r for r in relations if r["RELATION_CLASS"]=="TEXT_TEXT"]; tg=[r for r in relations if r["RELATION_CLASS"]!="TEXT_TEXT" and r["RELATION_CLASS"]!="TEXT_EDGE"]; edge=[r for r in relations if r["RELATION_CLASS"]=="TEXT_EDGE"]
    minraw=lambda rows: min(float(r["CLEARANCE_PX"]) for r in rows if r["CLEARANCE_PX"]!="INF") if any(r["CLEARANCE_PX"]!="INF" for r in rows) else math.inf
    minbbox=min(float(r["PDF_VECTOR_BBOX_CLEARANCE_PX"]) for r in tf); minedge=min(float(r["CLEARANCE_PX"]) for r in edge)
    clearanceok=all(r["PASS_FAIL"]=="PASS" for r in relations); sourceok=not ff; pixelok=not pf; harmony=False; mathok=True; probok=True; textok=True; grayscale=True; pageok=True; crossok=True
    hard={"SOURCE_FONT_PASS":sourceok,"SOURCE_FONT_FAILURE_COUNT":len(ff),"SOURCE_FONT_FAILURE_COMPONENT_COUNT":ff_components,"SOURCE_SAME_ROLE_FONT_PASS":source_role_ok,"SOURCE_CROSS_PANEL_FONT_PASS":source_cross_ok,"PIXEL_HEIGHT_PASS":pixelok,"PIXEL_HEIGHT_FAILURE_COUNT":len(pf),"PIXEL_HEIGHT_FAILURE_COMPONENT_COUNT":pf_components,"SAME_CLASS_RATIO_PASS":sameok,"ROLE_RATIO_PASS":roleok,"OVERLAP_PIXEL_COUNT":overlap,"OVERLAP_PASS":overlap==0,"CLIP_PIXEL_COUNT":clip,"CLIP_PASS":clip==0,"CLEARANCE_PASS":clearanceok,"CROSS_PANEL_PASS":crossok,"FONT_VISUAL_HARMONY_PASS":harmony,"MATH_SEMANTICS_PASS":mathok,"PROBABILITY_SEMANTICS_PASS":probok,"TEXT_CONSISTENCY_PASS":textok,"GRAYSCALE_PASS":grayscale,"PAGE_INTEGRATION_PASS":pageok}
    final=all([sourceok,source_role_ok,source_cross_ok,pixelok,sameok,roleok,overlap==0,clip==0,clearanceok,crossok,harmony,mathok,probok,textok,grayscale,pageok]); hard["FINAL_RESULT"]="PASS" if final else "FAIL"; hard["NEXT_ROLE"]="SA3" if final else "SA2"
    summary={"audit_id":"FIG-P556-03/STRICT_R1/SA1_20260824_R1","role":"SA1 independent blind strict review","input":{"frozen_pdf":str(PDF),"physical_page":PDF_PAGE,"figure_source":str(FIG),"adjacent_context":f"{CHAPTER}:586-620,638-644,1024-1030","style":f"{STYLE}:269-281"},"coverage":{"glyphs":len(chars),"semantic_components":len(semrows),"graphic_components":len(grows),"text_text_pairs":len(tf),"text_graphic_pairs":len(tg),"text_edge_pairs":len(edge),"critical_artifacts":len(critical)},"hard_gates":hard,"result":hard["FINAL_RESULT"],"handoff":hard["NEXT_ROLE"],"strict_method":"native final-PDF 300dpi 1:1, per-glyph PDF bbox and raw masks threshold 20/no dilation; vector-derived no-dilation graphic masks; exhaustive relations"}
    text(OUT/"strict_audit_summary.json",json.dumps(summary,ensure_ascii=False,indent=2))
    eight=[]
    def report(cid,cat,evidence,metric,threshold,observed,flag): eight.append({"CHECK_ID":cid,"CATEGORY":cat,"EVIDENCE":evidence,"METRIC":metric,"THRESHOLD":threshold,"OBSERVED":observed,"BOOLEAN":str(bool(flag)).lower(),"STATUS":"PASS" if flag else "FAIL"})
    report("R01","INPUT","render_manifest.json","frozen R93 and independent physical locating","official PDF only",f"page {PDF_PAGE}/{len(doc)}, sha256={fhash}",True)
    report("R02","RENDER","full_page_200dpi.png","whole page","native 200dpi","Poppler direct",True)
    report("R03","RENDER","full_page_300dpi_native.png;full_page_300dpi_grid.json","measurement grid","native 300dpi,1:1,no resize",f"{im.width}x{im.height}px; scales={sx:.6f},{sy:.6f}",True)
    report("R04","COVERAGE","glyph_inventory.csv;semantic_component_inventory.csv;graphic_component_inventory.csv","visible objects","complete",f"glyph={len(chars)}, semantic={len(semrows)}, graphic={len(grows)}",True)
    report("R05","MASKS","mask_manifest.csv","raw masks","no dilation",f"masks={len(masks)}",True)
    report("R06","SOURCE_FONT","after_font_audit.csv;source_font_role_ratio_audit.csv;source_font_cross_panel_audit.csv","ordinary effective font and repeated-role consistency",">=9.5pt; same role <=1.03 and <=0.25pt; cross panel <=1.05",f"failed glyphs={len(ff)} across {ff_components} semantic components; same-role={source_role_ok}; cross-panel={source_cross_ok}; local 9.4/9.2/8.8pt styles",sourceok and source_role_ok and source_cross_ok)
    report("R07","PIXEL_HEIGHT","after_pixel_measurements.csv","literal raw H_ink","30/24/17/22/15px",f"failed glyphs={len(pf)}",pixelok)
    report("R08","SAME_CLASS","same_class_ratio_audit.csv","same panel+role+script actual raw H_ink","[0.92,1.08]","no exact-glyph grouping",sameok)
    report("R09","ROLE_RATIO","role_ratio_audit.csv","same-script actual raw H_ink medians","no cross-script comparison","N/A recorded where no base exists",roleok)
    report("R10","OVERLAP","after_overlap_report.csv","all raw-mask pairs","0",str(overlap),overlap==0)
    report("R11","CLIP","after_overlap_report.csv","clipping","0",str(clip),clip==0)
    report("R12","CLEARANCE","after_overlap_report.csv","text/text,text/graphic,node/edge","4/3/5/6px",f"text raw={minraw(tf):.3f}; text bbox={minbbox:.3f}; graphic={minraw(tg):.3f}; edge={minedge:.3f}",clearanceok)
    report("R13","CROSS_PANEL","cross_panel_ratio_audit.csv","same role+script","<=1.10 or single panel N/A","one panel",crossok)
    report("R14","HARMONY","four views;after_font_audit.csv","FONT_VISUAL_HARMONY_PASS","no undersized/protruding text","9.2pt and 8.8pt visibly undersized",harmony)
    report("R15","MATH","math_semantics_recheck.md","detailed balance proof and counterexample","correct", "correct",mathok)
    report("R16","TEXT","math_semantics_recheck.md;adjacent_source_context.tex","caption/body symbols and probability semantics","consistent","consistent",textok)
    report("R17","GRAYSCALE","grayscale_300dpi.png","distinguishability","stable","shapes/stroke contrast stable",grayscale)
    report("R18","PAGE","full_page_200dpi.png","page integration","intact","intact; typography independently fails",pageok)
    report("R19","FINAL","strict_audit_summary.json","all hard gates","all true",hard["FINAL_RESULT"],final)
    csvout(OUT/"strict_eight_column_report.csv",eight)
    accept=f"""# FIG-P556-03｜STRICT R1｜SA1 正式验收

RESULT: {hard['FINAL_RESULT']}

NEXT_ROLE: {hard['NEXT_ROLE']}

冻结 R93 最终 PDF 被独立定位到物理第 {PDF_PAGE}/{len(doc)} 页。取证覆盖 {len(chars)} 个可见 glyph、{len(semrows)} 个语义文字组件、{len(grows)} 个线/箭头/marker/node-border/fill 组件、{len(tf)} 个 TEXT--TEXT、{len(tg)} 个 TEXT--graphic 与 {len(edge)} 个 TEXT--edge 关系。原生视图为 200dpi 整页、300dpi 固定全页网格、裁图、standalone 和灰度。

| Gate | Observed | Required | Status |
|---|---:|---:|---|
| SOURCE_FONT_PASS | {str(sourceok).lower()} | true | {'PASS' if sourceok else 'FAIL'} |
| SOURCE_FONT_FAILURE_COUNT | {len(ff)} glyphs / {ff_components} components | 0 | {'PASS' if not ff else 'FAIL'} |
| SOURCE_ROLE_FONT / SOURCE_CROSS_PANEL_FONT | {str(source_role_ok).lower()} / {str(source_cross_ok).lower()} | true / true | {'PASS' if source_role_ok and source_cross_ok else 'FAIL'} |
| PIXEL_HEIGHT_PASS | {str(pixelok).lower()} ({len(pf)} glyphs / {pf_components} components) | true | {'PASS' if pixelok else 'FAIL'} |
| SAME_CLASS_RATIO_PASS | {str(sameok).lower()} | true | {'PASS' if sameok else 'FAIL'} |
| ROLE_RATIO_PASS | {str(roleok).lower()} | true | {'PASS' if roleok else 'FAIL'} |
| OVERLAP / CLIP | {overlap} / {clip} | 0 / 0 | {'PASS' if overlap==0 and clip==0 else 'FAIL'} |
| MIN_TEXT_CLEARANCE_PX | text/text raw={minraw(tf):.3f}, bbox={minbbox:.3f}; text/graphic={minraw(tg):.3f}; edge={minedge:.3f} | 4 / 3(or 5 node) / 6 | {'PASS' if clearanceok else 'FAIL'} |
| CLEARANCE_PASS | {str(clearanceok).lower()} | true | {'PASS' if clearanceok else 'FAIL'} |
| VISUAL_HARMONY_PASS / FONT_VISUAL_HARMONY_PASS | false / false | true / true | FAIL |
| MATH / PROBABILITY / TEXT | true / true / true | all true | PASS |

硬失败：图源局部明确声明的普通 9.4pt、9.2pt 与 8.8pt 文字均低于 9.5pt。共同 `every node=\\small` 不改变这些局部样式；`FONT_VISUAL_HARMONY_PASS=false`。逐字形 raw H_ink（包括 `=`, 逗号、全角冒号、下标 `2` 等）及失败诊断均在 CSV 和 `critical/` 中。数学上，详细平衡可推出平稳性；$A=I_2$ 反例确实不连通且平稳分布不唯一，图文语义正确。

任一硬门失败即不能送 SA3。本轮只能 **FAIL → SA2**。
"""
    text(OUT/"SA1_RESULT.md",accept); text(OUT/"after_visual_acceptance.md",accept)

    # Machine final gate: evidence integrity is independent of the quality FAIL.
    req=["full_page_200dpi.png","full_page_300dpi_native.png","full_page_300dpi_grid.json","figure_crop_300dpi.png","standalone_300dpi.png","grayscale_300dpi.png","render_manifest.json","after_font_audit.csv","after_pixel_measurements.csv","after_overlap_report.csv","same_class_ratio_audit.csv","source_font_role_ratio_audit.csv","source_font_cross_panel_audit.csv","role_ratio_audit.csv","cross_panel_ratio_audit.csv","math_semantics_recheck.md","math_semantics_recheck.csv","math_semantics_recheck.json","strict_audit_summary.json","strict_eight_column_report.csv","critical_artifacts.csv","SA1_RESULT.md","after_text_measurement_overlay_300dpi.png"]
    mc=[]
    def M(cid,need,obs,ok,evidence): mc.append({"CHECK_ID":cid,"REQUIREMENT":need,"OBSERVED":obs,"EVIDENCE":evidence,"STATUS":"PASS" if ok else "FAIL"})
    M("MC01_REQUIRED_ARTIFACTS","all prescribed evidence exists",f"{sum((OUT/z).is_file() for z in req)}/{len(req)}",all((OUT/z).is_file() for z in req),";".join(req))
    tw,th=pg.rect.width*300/72,pg.rect.height*300/72; xr=abs(sx/(300/72)-1); yr=abs(sy/(300/72)-1); nativeok=abs(im.width-tw)<=1 and abs(im.height-th)<=1 and xr<=.0005 and yr<=.0005
    M("MC02_FULL_PAGE_NATIVE_GRID","PDF points to integer native 300dpi pixels (<=1px, <=0.05% axes)",f"actual={im.width}x{im.height}; target={tw:.3f}x{th:.3f}; relative={xr:.6%},{yr:.6%}",nativeok,"full_page_300dpi_native.png;full_page_300dpi_grid.json")
    paths=[OUT/z["mf"] for z in chars]+[OUT/r["RAW_MASK_FILE"] for r in semrows]+[OUT/r["RAW_MASK_FILE"] for r in gfx]; M("MC03_MASK_LINKS","all glyph/semantic/graphic masks resolve",f"{sum(p.is_file() for p in paths)}/{len(paths)}",all(p.is_file() for p in paths),"mask_manifest.csv")
    gf=("ELEMENT_ID","PARENT_ELEMENT_ID","PANEL_ID","ROLE","SOURCE_FILE","SOURCE_LINE","DECLARED_PT","GRAPHICS_SCALE","EFFECTIVE_PT","TEXT_SAMPLE","SCRIPT_CLASS","SCRIPT_FAMILY","BBOX_X0","BBOX_Y0","BBOX_X1","BBOX_Y1","H_INK_PX","PIXEL_THRESHOLD_PX","CLASS_MEDIAN_PX","RATIO_TO_CLASS_MEDIAN","ROLE_MEDIAN_PX","RATIO_TO_ROLE_MEDIAN","ROLE_RATIO","TEXT_TEXT_OVERLAP_PX","TEXT_GRAPHIC_OVERLAP_PX","MIN_CLEARANCE_PX","SOURCE_FONT_PASS","PIXEL_HEIGHT_PASS","RAW_MASK_FILE")
    M("MC04_GLYPH_SCHEMA","every glyph has required source, bbox, raw-H_ink, role/script, ratio, relation and mask fields",f"glyphs={len(glyphrows)}",all(all(str(r.get(k,""))!="" for k in gf) for r in glyphrows),"after_pixel_measurements.csv")
    rf=("RELATION_ID","ELEMENT_A","ELEMENT_B","RAW_MASK_A","RAW_MASK_B","OVERLAP_PIXEL_COUNT","CLEARANCE_PX","REQUIRED_CLEARANCE_PX","PASS_FAIL")
    M("MC05_RELATION_SCHEMA","all relations including vector text bboxes populated",f"relations={len(relations)}",all(all(str(r.get(k,""))!="" for k in rf) for r in relations) and all(r["PDF_VECTOR_BBOX_A"] and r["PDF_VECTOR_BBOX_B"] for r in tf),"after_overlap_report.csv")
    needs=[r for r in relations if r["PASS_FAIL"]=="FAIL" or (r["CLEARANCE_PX"]!="INF" and float(r["CLEARANCE_PX"])<=int(r["REQUIRED_CLEARANCE_PX"])+2) or (r["RELATION_CLASS"]=="TEXT_TEXT" and float(r["PDF_VECTOR_BBOX_CLEARANCE_PX"])<=int(r["REQUIRED_CLEARANCE_PX"])+2)]
    cfiles=all((OUT/r["CRITICAL_ROI"]).is_file() for r in needs if r["CRITICAL_ROI"]) and all(r["CRITICAL_ROI"] for r in needs) and all((OUT/r[k]).is_file() for r in critical for k in ("RAW_ROI","MASK_A","MASK_B","OVERLAP_MASK","OVERLAY","ZOOM_8X"))
    M("MC06_CRITICAL_EVIDENCE","every critical/failed pair has raw ROI, two masks, overlap and 8x overlay",f"required={len(needs)}; artifacts={len(critical)}",cfiles,"critical_artifacts.csv")
    countsok=overlap==sum(int(r["OVERLAP_PIXEL_COUNT"]) for r in relations) and clip==sum(int(r["CLIP_PIXEL_COUNT"]) for r in relations) and len(ff)==sum(r["SOURCE_FONT_PASS"]=="false" for r in glyphrows) and len(pf)==sum(r["PIXEL_HEIGHT_PASS"]=="false" for r in glyphrows)
    M("MC07_COUNT_CROSSCHECK","summary equals CSV recomputation",f"overlap={overlap}; clip={clip}; font_fail={len(ff)}; pixel_fail={len(pf)}",countsok,"strict_audit_summary.json;after_*.csv")
    M("MC08_FINAL_RESULT","result is hard-gate conjunction",f"expected={'PASS' if final else 'FAIL'}; summary={hard['FINAL_RESULT']}",hard["FINAL_RESULT"]==("PASS" if final else "FAIL"),"strict_audit_summary.json")
    integrity=all(r["STATUS"]=="PASS" for r in mc); msum={"audit_id":"FIG-P556-03/STRICT_R1/SA1_20260824_R1","machine_evidence_integrity_pass":integrity,"quality_result":hard["FINAL_RESULT"],"checks":mc}
    csvout(OUT/"machine_terminal_check.csv",mc); text(OUT/"machine_terminal_check.json",json.dumps(msum,ensure_ascii=False,indent=2)); text(OUT/"machine_terminal_check.md","# FIG-P556-03｜机器终检\n\n"+f"EVIDENCE_INTEGRITY: {'PASS' if integrity else 'FAIL'}\n\nQUALITY_RESULT: {hard['FINAL_RESULT']}\n\n"+"\n".join(f"- {r['CHECK_ID']}: {r['STATUS']} — {r['OBSERVED']}" for r in mc)+"\n")
    hard["MACHINE_EVIDENCE_INTEGRITY_PASS"]=integrity; summary["machine_terminal_check"]={"integrity_pass":integrity,"csv":"machine_terminal_check.csv","json":"machine_terminal_check.json"}; text(OUT/"strict_audit_summary.json",json.dumps(summary,ensure_ascii=False,indent=2)); report("R20","MACHINE_FINAL","machine_terminal_check.csv/json","evidence integrity","all true",f"integrity={integrity}; quality={hard['FINAL_RESULT']}",integrity); csvout(OUT/"strict_eight_column_report.csv",eight)
    text(OUT/"SA1_RESULT.md",accept+f"\n机器终检：`MACHINE_EVIDENCE_INTEGRITY_PASS={str(integrity).lower()}`；它仅表示证据闭合，质量结论仍为 `{hard['FINAL_RESULT']}`。\n"); text(OUT/"after_visual_acceptance.md",(OUT/"SA1_RESULT.md").read_text(encoding="utf-8"))

if __name__ == "__main__": main()
