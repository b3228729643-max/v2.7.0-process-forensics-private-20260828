#!/usr/bin/env python3
"""FIG-P570-01 independent strict R1 SA1 audit (R94 frozen final PDF).

Read-only inputs are limited to the assigned frozen R94 PDF, designated figure
source, direct V5-C02 context, and common TikZ style.  Every write is beneath
this audit directory.  All pixel measurements share the one native 300dpi
full-page grid; no resize is used after rendering.
"""
from __future__ import annotations

import csv, hashlib, json, math, os, re, shutil, subprocess, unicodedata
from collections import defaultdict
from pathlib import Path
from statistics import median

import fitz
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps
from scipy.ndimage import distance_transform_edt

PROJECT=Path(r"D:\Users\ASUS\Desktop\机器学习")
OUT=Path(__file__).resolve().parent
PDF=PROJECT/"v2.7.0/_work/source/v2.7.0/src/build/strict_current_r94_fullbook/main_full.pdf"
FIG=PROJECT/"v2.7.0/_work/source/v2.7.0/src/绘图源码/第05册_采样方法主题模型与图排序/V5-C02/fig_v5_c02_dependency_graph.tex"
CHAPTER=PROJECT/"v2.7.0/_work/source/v2.7.0/src/讲义源码/第05册_采样方法主题模型与图排序/chapters/V5-C02.tex"
STYLE=PROJECT/"v2.7.0/_work/source/v2.7.0/src/讲义源码/common/statlearnbook.sty"
PDF_PAGE=617
PAGE_INDEX=PDF_PAGE-1
SCOPE=(50.0,175.0,545.0,392.0)       # diagram + one semantic caption parent
STANDALONE=(105.0,175.0,485.0,355.0) # diagram only, coordinate crop from the fixed grid
PANEL="PANEL_DEPENDENCY_GRAPH"

META={
 "SEM_INPUT_EXPECTATION":("INPUT_CONCEPT",9.2,15,"L3/L7 figure default every-node explicit 9.2pt; input L15"),
 "SEM_INPUT_IID":("INPUT_CONCEPT",9.2,16,"L3/L7 figure default every-node explicit 9.2pt; input L16"),
 "SEM_INPUT_LLN":("INPUT_CONCEPT",9.2,17,"L3/L7 figure default every-node explicit 9.2pt; input L17"),
 "SEM_CORE_MC":("CORE_CONCEPT",9.6,18,"L9-L10 core local explicit 9.6pt"),
 "SEM_METHOD_INVERSE":("METHOD_LABEL",9.2,21,"L3/L7 figure default every-node explicit 9.2pt; method L21"),
 "SEM_METHOD_REJECTION":("METHOD_LABEL",9.2,22,"L3/L7 figure default every-node explicit 9.2pt; method L22"),
 "SEM_METHOD_IS":("METHOD_LABEL",9.2,23,"L3/L7 figure default every-node explicit 9.2pt; method L23"),
 "SEM_DIAGNOSTIC":("DIAGNOSTIC",9.2,28,"L26-L29 explicit 9.2pt diagnostic node"),
 "SEM_NOTE":("ANNOTATION",8.6,31,"L31-L32 local explicit 8.6pt annotation"),
 "SEM_CAPTION_PARENT":("CAPTION",None,34,"L34 no local caption override; per-glyph frozen PDF vector size"),
}
SEM_TEXT={
 "SEM_INPUT_EXPECTATION":"期望 / 积分","SEM_INPUT_IID":"独立抽样","SEM_INPUT_LLN":"大数规律",
 "SEM_CORE_MC":"Monte Carlo 估计","SEM_METHOD_INVERSE":"逆变换",
 "SEM_METHOD_REJECTION":"判定 $U\\le r$ 接受--拒绝","SEM_METHOD_IS":"||| 重要性抽样",
 "SEM_DIAGNOSTIC":"共同出口：误差 / ESS / 支持覆盖诊断",
 "SEM_NOTE":"三种同尺寸节点表示并列方法；边框/图标只编码方法身份，不表示先后依赖",
 "SEM_CAPTION_PARENT":"图31.1 本章知识依赖：由期望、积分与独立抽样进入蒙特卡罗估计，再分别学习三种直接采样或重加权方法，最后统一进行误差和支持诊断",
}

def rel(p:Path)->str:return p.relative_to(OUT).as_posix()
def mkdir(p:Path)->Path:p.mkdir(parents=True,exist_ok=True);return p
def write(p:Path,s:str):p.write_text(s,encoding="utf-8",newline="\n")
def sha(p:Path)->str:
 h=hashlib.sha256()
 with p.open("rb") as f:
  for q in iter(lambda:f.read(1048576),b""):h.update(q)
 return h.hexdigest()
def writecsv(p:Path,rows:list[dict],fields:list[str]|None=None):
 fields=fields or (list(rows[0]) if rows else [])
 with p.open("w",encoding="utf-8-sig",newline="") as f:
  w=csv.DictWriter(f,fieldnames=fields,extrasaction="ignore");w.writeheader();w.writerows(rows)
def bpx(b,sx,sy):return tuple((b[0]*sx,b[1]*sy,b[2]*sx,b[3]*sy))
def bslice(b,w,h):return max(0,int(math.floor(b[0]))),max(0,int(math.floor(b[1]))),min(w,int(math.ceil(b[2]))),min(h,int(math.ceil(b[3])))
def cropmask(m):
 yy,xx=np.nonzero(m)
 if not len(xx):return np.zeros((1,1),dtype=bool),(0,0,1,1)
 x0,x1=int(xx.min()),int(xx.max())+1;y0,y1=int(yy.min()),int(yy.max())+1
 return m[y0:y1,x0:x1],(x0,y0,x1,y1)
def savemask(p,m):Image.fromarray(np.where(m,255,0).astype(np.uint8),"L").save(p)
def localmask(rgb,b):
 """No-dilation glyph foreground mask: local mode bg, channel difference >=20."""
 h,w=rgb.shape[:2];x0,y0,x1,y1=bslice(b,w,h);ex0,ey0,ex1,ey1=max(0,x0-2),max(0,y0-2),min(w,x1+2),min(h,y1+2)
 ring=np.ones((ey1-ey0,ex1-ex0),dtype=bool);ring[y0-ey0:y1-ey0,x0-ex0:x1-ex0]=False;samples=rgb[ey0:ey1,ex0:ex1][ring]
 if len(samples):
  c,n=np.unique(samples.reshape(-1,3),axis=0,return_counts=True);bg=c[int(n.argmax())]
 else:bg=np.array([255,255,255],dtype=np.uint8)
 raw=np.max(np.abs(rgb[y0:y1,x0:x1].astype(np.int16)-bg.astype(np.int16)),axis=2)>=20
 return raw,(x0,y0,x1,y1),[int(v) for v in bg]
def point(p,sx,sy,scope):return p.x*sx-scope[0],p.y*sy-scope[1]
def linemask(shape,segs,width):
 im=Image.new("L",(shape[1],shape[0]),0);d=ImageDraw.Draw(im)
 for a,b in segs:d.line([a,b],fill=255,width=max(1,int(round(width))))
 return np.asarray(im)>0
def poly(shape,pts):
 im=Image.new("L",(shape[1],shape[0]),0);ImageDraw.Draw(im).polygon(pts,fill=255)
 return np.asarray(im)>0
def roundfill(shape,rect,radius):
 im=Image.new("L",(shape[1],shape[0]),0);ImageDraw.Draw(im).rounded_rectangle(rect,radius=max(1,int(round(radius))),fill=255)
 return np.asarray(im)>0
def cubic(a,b,c,d,t):
 u=1-t;return u**3*a[0]+3*u*u*t*b[0]+3*u*t*t*c[0]+t**3*d[0],u**3*a[1]+3*u*u*t*b[1]+3*u*t*t*c[1]+t**3*d[1]
def segments(d,sx,sy,scope):
 out=[]
 for it in d["items"]:
  if it[0]=="l":out.append((point(it[1],sx,sy,scope),point(it[2],sx,sy,scope)))
  elif it[0]=="c":
   q=[point(v,sx,sy,scope) for v in it[1:5]];last=q[0]
   for i in range(1,25):
    nxt=cubic(*q,i/24);out.append((last,nxt));last=nxt
 return out
def dashedsegments(segs,dashes,sx):
 """Apply the final-PDF dash array before native-grid rasterization.

 PyMuPDF exposes PDF dash arrays such as ``[ 2.98883 1.99255 ] 0`` in
 points.  A dashed node border is not its continuous centerline: preserving
 its actual visible gaps is essential for text-border clearance.  The path
 here is continuous (the PDF drawing keeps its one compound rounded-box
 path), so dash phase continues across consecutive line/cubic pieces.
 """
 nums=[float(x) for x in re.findall(r"[-+]?\d*\.?\d+",dashes or "")]
 if len(nums)<2:return segs
 # The final scalar is the PDF phase; preceding values are the dash array.
 pattern=[v*sx for v in nums[:-1]]; phase=nums[-1]*sx
 if not pattern or any(v<=0 for v in pattern):return segs
 if len(pattern)%2:pattern*=2
 phase=phase%sum(pattern);idx=0
 while phase>=pattern[idx]-1e-9:
  phase-=pattern[idx];idx=(idx+1)%len(pattern)
 remain=pattern[idx]-phase;on=(idx%2)==0;out=[]
 for a,b in segs:
  dx,dy=b[0]-a[0],b[1]-a[1];length=math.hypot(dx,dy);at=0.0
  while at<length-1e-9:
   take=min(remain,length-at);u0=at/length;u1=(at+take)/length
   if on:out.append(((a[0]+dx*u0,a[1]+dy*u0),(a[0]+dx*u1,a[1]+dy*u1)))
   at+=take;remain-=take
   if remain<=1e-9:
    idx=(idx+1)%len(pattern);on=(idx%2)==0;remain=pattern[idx]
 return out
def strokemask(shape,d,sx,sy,scope):
 """Visible final vector stroke, including its PDF dash pattern (no dilation)."""
 return linemask(shape,dashedsegments(segments(d,sx,sy,scope),d.get("dashes",""),sx),d["width"]*sx)
def arrowpoly(d,sx,sy,scope):
 pts=[]
 for it in d["items"]:
  if it[0]=="l":pts += [point(it[1],sx,sy,scope),point(it[2],sx,sy,scope)]
 out=[]
 for p in pts:
  if p not in out:out.append(p)
 return out
def bboxclear(a,b,sx,sy):return math.hypot(max(0,b[0]-a[2],a[0]-b[2])*sx,max(0,b[1]-a[3],a[1]-b[3])*sy)
def maskclear(a,b):
 ov=int((a&b).sum())
 if ov:return ov,0.0
 if not a.any() or not b.any():return 0,math.inf
 return 0,max(0.0,float(distance_transform_edt(~b)[a].min())-1.0)
def kind(ch,script):
 cp=ord(ch);east=unicodedata.east_asian_width(ch)
 if 0x4e00<=cp<=0x9fff:return "CJK_OR_FULLWIDTH",30,"CJK"
 if east in {"F","W"}:return "CJK_OR_FULLWIDTH",30,"FULLWIDTH_PUNCT"
 if script:return "NATURAL_SCRIPT",15,"NATURAL_SCRIPT"
 if ch in {"=","+","−","-","–","—","(",")",",",".","/","|","≤","≥","：",":"} or unicodedata.category(ch).startswith(("P","S")):return "BASE_MATH_OR_PUNCT",22,"MATH_PUNCT"
 if ch.isdigit():return "UPPER_OR_DIGIT",24,"DIGIT"
 if ch.isupper():return "UPPER_OR_DIGIT",24,"UPPER"
 if ch.islower() or ch in {"π","𝜋","ρ","𝜌","φ","𝜙","θ","𝜃","μ","𝜇","𝑟"}:return "LOWER_OR_GREEK",17,"LOWER_OR_GREEK"
 return "BASE_MATH_OR_PUNCT",22,"MATH_PUNCT"
def classify(cx,cy):
 if 180<=cy<212:
  return "SEM_INPUT_EXPECTATION" if cx<240 else ("SEM_INPUT_IID" if cx<350 else "SEM_INPUT_LLN")
 if 220<=cy<255:return "SEM_CORE_MC"
 if 260<=cy<302:return "SEM_METHOD_INVERSE" if cx<230 else ("SEM_METHOD_REJECTION" if cx<355 else "SEM_METHOD_IS")
 if 315<=cy<339:return "SEM_DIAGNOSTIC"
 if 340<=cy<355:return "SEM_NOTE"
 if 355<=cy<=392:return "SEM_CAPTION_PARENT"
 raise RuntimeError(f"unassigned scoped glyph at {cx:.3f},{cy:.3f}")
def roi(original,a,b,scope,rid,reason,manifest):
 target=(a&b) if (a&b).any() else (a|b);_,(x0,y0,x1,y1)=cropmask(target);margin=16 if (a&b).any() else 10;sx0,sy0,sx1,sy1=scope
 px0,py0=max(sx0,sx0+x0-margin),max(sy0,sy0+y0-margin);px1,py1=min(sx1,sx0+x1+margin),min(sy1,sy0+y1+margin)
 dest=mkdir(OUT/"critical");raw=dest/f"{rid}_raw.png";ma=dest/f"{rid}_mask_a.png";mb=dest/f"{rid}_mask_b.png";ov=dest/f"{rid}_overlap.png";over=dest/f"{rid}_overlay.png";zoom=dest/f"{rid}_overlay_8x.png"
 im=original.crop((px0,py0,px1,py1));aa=a[py0-sy0:py1-sy0,px0-sx0:px1-sx0];bb=b[py0-sy0:py1-sy0,px0-sx0:px1-sx0]
 im.save(raw);savemask(ma,aa);savemask(mb,bb);savemask(ov,aa&bb);ar=np.asarray(im.convert("RGB")).copy();ar[aa]=[255,0,0];ar[bb]=[0,255,0];ar[aa&bb]=[255,255,0];out=Image.fromarray(ar,"RGB");out.save(over);out.resize((out.width*8,out.height*8),Image.Resampling.NEAREST).save(zoom)
 manifest.append({"ARTIFACT_ID":rid,"REASON":reason,"RAW_ROI":rel(raw),"MASK_A":rel(ma),"MASK_B":rel(mb),"OVERLAP_MASK":rel(ov),"OVERLAY":rel(over),"ZOOM_8X":rel(zoom)})

def main():
 mkdir(OUT);gm=mkdir(OUT/"masks/glyphs");sm=mkdir(OUT/"masks/semantic");vm=mkdir(OUT/"masks/graphics")
 poppler=shutil.which("pdftoppm") or r"D:\texlive\2026\bin\windows\pdftoppm.exe"
 p300=OUT/"full_page_300dpi_native.png";p200=OUT/"full_page_200dpi.png"
 for dpi,target in ((300,p300),(200,p200)):
  if not target.exists():subprocess.run([str(poppler),"-png","-singlefile","-r",str(dpi),"-f",str(PDF_PAGE),"-l",str(PDF_PAGE),str(PDF),str(target.with_suffix(""))],check=True)
 im=Image.open(p300).convert("RGB");doc=fitz.open(PDF);pg=doc[PAGE_INDEX];sx,sy=im.width/pg.rect.width,im.height/pg.rect.height
 spx=bslice(bpx(SCOPE,sx,sy),im.width,im.height);stand=bslice(bpx(STANDALONE,sx,sy),im.width,im.height);im.crop(spx).save(OUT/"figure_crop_300dpi.png");im.crop(stand).save(OUT/"standalone_300dpi.png");ImageOps.grayscale(im.crop(spx)).save(OUT/"grayscale_300dpi.png")
 rgb=np.asarray(im);x0,y0,x1,y1=spx;scoped=rgb[y0:y1,x0:x1];shape=scoped.shape[:2];fhash=sha(PDF)
 grid={"grid_id":"FULL_PAGE_NATIVE_300DPI","frozen_pdf":str(PDF),"frozen_pdf_sha256":fhash,"physical_page":PDF_PAGE,"pdf_page_count":len(doc),"dpi":300,"native_png":"full_page_300dpi_native.png","width_px":im.width,"height_px":im.height,"pdf_points":[pg.rect.width,pg.rect.height],"pdf_to_native_px_scale":[sx,sy],"figure_scope_pdf":list(SCOPE),"figure_scope_px":list(spx),"resize_after_render":False,"measurement_policy":"all measures use this immutable direct Poppler 300dpi full-page grid; crops are coordinate-only"}
 write(OUT/"full_page_300dpi_grid.json",json.dumps(grid,ensure_ascii=False,indent=2))
 manifest={"audit_id":"FIG-P570-01/STRICT_R1/SA1_20260824_R1","inputs":{"frozen_r94_pdf":str(PDF),"figure_source":str(FIG),"adjacent_context":str(CHAPTER),"common_style":str(STYLE)},"physical_page":PDF_PAGE,"render":{"whole_page_200dpi":"full_page_200dpi.png","native_300dpi":"full_page_300dpi_native.png","crop_300dpi":"figure_crop_300dpi.png","standalone_300dpi":"standalone_300dpi.png","grayscale_300dpi":"grayscale_300dpi.png","overlay_300dpi":"after_text_measurement_overlay_300dpi.png","object_id_overlay_300dpi":"object_id_overlay_300dpi.png","native_no_resize":True,"fixed_grid":"full_page_300dpi_grid.json"},"font_cascade":"figure L7 every node=9.2pt overrides shared statlearnbook.sty L276 every node=small; local core L10, diagnostic L28 and annotation L31 then override L7."}
 write(OUT/"render_manifest.json",json.dumps(manifest,ensure_ascii=False,indent=2))
 fl=FIG.read_text(encoding="utf-8").splitlines();cl=CHAPTER.read_text(encoding="utf-8").splitlines();sl=STYLE.read_text(encoding="utf-8").splitlines()
 write(OUT/"source_figure_excerpt.tex","\n".join(f"{i+1:03d}: {v}" for i,v in enumerate(fl))+"\n")
 write(OUT/"adjacent_source_context.tex","\n".join(f"{i:04d}: {cl[i-1]}" for i in range(67,78))+"\n")
 write(OUT/"shared_style_font_context.tex","\n".join(f"{i:04d}: {sl[i-1]}" for i in range(269,282))+"\n")
 keep=[z for z in pg.get_text("text").splitlines() if any(q in z for q in ("图 31.1","图31.1","教学依赖","Monte Carlo","未加权"))]
 write(OUT/"pdf_context_excerpt.txt",f"Frozen R94 final PDF physical page {PDF_PAGE}/{len(doc)}\n\n"+"\n".join(keep)+"\n")

 chars=[];groups=defaultdict(list);masks=[];n=0
 for block in pg.get_text("rawdict")["blocks"]:
  for line in block.get("lines",[]):
   for span in line["spans"]:
    for ch in span["chars"]:
     c=ch["c"]
     if c.isspace():continue
     bb=tuple(float(v) for v in ch["bbox"]);cx,cy=(bb[0]+bb[2])/2,(bb[1]+bb[3])/2
     if not(SCOPE[0]<=cx<=SCOPE[2] and SCOPE[1]<=cy<=SCOPE[3]):continue
     sid=classify(cx,cy);n+=1;gid=f"GLYPH_{n:03d}";raw,loc,bg=localmask(rgb,bpx(bb,sx,sy));gx0,gy0,gx1,gy1=loc;glob=np.zeros(shape,dtype=bool);lx0,ly0,lx1,ly1=gx0-x0,gy0-y0,gx1-x0,gy1-y0
     if not(0<=lx0<=lx1<=shape[1] and 0<=ly0<=ly1<=shape[0]):raise RuntimeError(f"glyph outside scope {gid}")
     glob[ly0:ly1,lx0:lx1]=raw;mf=gm/f"{gid}.png";savemask(mf,raw);rec={"id":gid,"sid":sid,"char":c,"bbox":bb,"bboxpx":bpx(bb,sx,sy),"size":float(span["size"]),"font":span.get("font",""),"mask":glob,"mf":rel(mf),"bg":bg};chars.append(rec);groups[sid].append(rec)
     masks.append({"MASK_ID":gid,"KIND":"GLYPH_RAW_NO_DILATION","PARENT_ID":sid,"PDF_BBOX":";".join(f"{v:.3f}" for v in bb),"MASK_FILE":rel(mf),"METHOD":"exact PDF glyph bbox; local-mode background; max-channel difference >=20/255; no dilation"})
 missing=sorted(set(META)-set(groups))
 if missing:raise RuntimeError(f"missing semantic components: {missing}")
 semmask={};sembox={};semrows=[];glyphrows=[];fontrows=[]
 for sid,items in groups.items():
  role,decl,line,origin=META[sid];vector=max(z["size"] for z in items);base=vector if decl is None else decl;merged=np.zeros(shape,dtype=bool)
  for z in items:merged|=z["mask"]
  semmask[sid]=merged;crop,_=cropmask(merged);mf=sm/f"{sid}.png";savemask(mf,crop);bb=(min(z["bbox"][0] for z in items),min(z["bbox"][1] for z in items),max(z["bbox"][2] for z in items),max(z["bbox"][3] for z in items));sembox[sid]=bb
  semrows.append({"ELEMENT_ID":sid,"PARENT_ELEMENT_ID":"CAPTION_PARENT" if sid=="SEM_CAPTION_PARENT" else sid,"PANEL_ID":PANEL,"ROLE":role,"SOURCE_FILE":str(FIG),"SOURCE_LINE":line,"TEXT_SAMPLE":SEM_TEXT[sid],"PDF_BBOX":";".join(f"{v:.3f}" for v in bb),"RAW_MASK_FILE":rel(mf),"RAW_INK_PIXEL_COUNT":int(merged.sum()),"H_INK_PX":cropmask(merged)[0].shape[0],"DECLARED_EFFECTIVE_PT":f"{base:.3f}","GRAPHICS_SCALE":"1.000000","FONT_ORIGIN":origin})
  masks.append({"MASK_ID":sid,"KIND":"SEMANTIC_TEXT_RAW_NO_DILATION","PARENT_ID":sid,"PDF_BBOX":";".join(f"{v:.3f}" for v in bb),"MASK_FILE":rel(mf),"METHOD":"OR of constituent raw glyph masks; no dilation"})
  for z in items:
   script=z["size"]<.92*vector;klass,threshold,family=kind(z["char"],script);effective=base*z["size"]/vector;sourceok=base>=9.5 if script else effective>=9.5;h=cropmask(z["mask"])[0].shape[0];pixelok=h>=threshold
   row={"ELEMENT_ID":z["id"],"PARENT_ELEMENT_ID":sid,"PANEL_ID":PANEL,"ROLE":role,"SOURCE_FILE":str(FIG),"SOURCE_LINE":line,"DECLARED_PT":f"{base:.3f}","GRAPHICS_SCALE":"1.000000","EFFECTIVE_PT":f"{effective:.3f}","TEXT_SAMPLE":z["char"],"SCRIPT_CLASS":klass,"SCRIPT_FAMILY":family,"PDF_VECTOR_FONT_SIZE_PT":f"{z['size']:.3f}","PDF_VECTOR_FONT":z["font"],"PDF_BBOX":";".join(f"{v:.3f}" for v in z["bbox"]),"BBOX_X0":f"{z['bboxpx'][0]:.3f}","BBOX_Y0":f"{z['bboxpx'][1]:.3f}","BBOX_X1":f"{z['bboxpx'][2]:.3f}","BBOX_Y1":f"{z['bboxpx'][3]:.3f}","H_INK_PX":h,"PIXEL_THRESHOLD_PX":threshold,"CLASS_MEDIAN_PX":"","RATIO_TO_CLASS_MEDIAN":"","ROLE_MEDIAN_PX":"","RATIO_TO_ROLE_MEDIAN":"","ROLE_RATIO":"","TEXT_TEXT_OVERLAP_PX":"","TEXT_GRAPHIC_OVERLAP_PX":"","MIN_CLEARANCE_PX":"","SOURCE_FONT_PASS":str(sourceok).lower(),"PIXEL_HEIGHT_PASS":str(pixelok).lower(),"PASS_FAIL":"PASS" if sourceok and pixelok else "FAIL","RAW_MASK_FILE":z["mf"],"LOCAL_BACKGROUND_RGB":",".join(map(str,z["bg"])),"REASON":("natural script needs >=9.5pt base" if script else "ordinary effective font must be >=9.5pt")+f"; raw H_ink={h}px threshold={threshold}px"}
   glyphrows.append(row);fontrows.append({k:row[k] for k in ("ELEMENT_ID","PARENT_ELEMENT_ID","ROLE","TEXT_SAMPLE","SCRIPT_CLASS","SCRIPT_FAMILY","DECLARED_PT","GRAPHICS_SCALE","EFFECTIVE_PT","PDF_VECTOR_FONT_SIZE_PT","SOURCE_FONT_PASS","RAW_MASK_FILE","REASON")}|{"PASS_FAIL":"PASS" if sourceok else "FAIL","FONT_EVIDENCE":origin})

 # Vector graphics: 28 final-PDF drawings exclusively belonging to Figure 31.1.
 ds=[d for d in pg.get_drawings() if d["rect"].y1>175 and d["rect"].y0<355 and d["rect"].x1>50 and d["rect"].x0<545]
 if len(ds)!=28:raise RuntimeError(f"expected 28 figure drawings, got {len(ds)}")
 gfx=[];gbox={};grows=[];exclusions=[]
 def gadd(eid,kindname,line,d,m,note,foreground=True):
  crop,_=cropmask(m);mf=vm/f"{eid}.png";savemask(mf,crop);r=d["rect"];bb=(float(r.x0),float(r.y0),float(r.x1),float(r.y1));gbox[eid]=bb;gfx.append({"ELEMENT_ID":eid,"KIND":kindname,"mask":m,"RAW_MASK_FILE":rel(mf),"FOREGROUND":foreground});grows.append({"ELEMENT_ID":eid,"PANEL_ID":PANEL,"KIND":kindname,"FOREGROUND":str(foreground).lower(),"SOURCE_FILE":str(FIG),"SOURCE_LINE":line,"PDF_BBOX":";".join(f"{v:.3f}" for v in bb),"RAW_MASK_FILE":rel(mf),"RAW_FOREGROUND_PIXELS":int(m.sum()),"NOTE":note});masks.append({"MASK_ID":eid,"KIND":f"GRAPHIC_{kindname}_RAW_NO_DILATION","PARENT_ID":eid,"PDF_BBOX":";".join(f"{v:.3f}" for v in bb),"MASK_FILE":rel(mf),"METHOD":"final-PDF extracted vector geometry rasterized on native 300dpi grid; no dilation; no composited-color sampling"})
  if not foreground:exclusions.append({"ELEMENT_ID":eid,"KIND":kindname,"RAW_MASK_FILE":rel(mf),"EXCLUSION_REASON":note,"QUALITY_GEOMETRY":"not an independent foreground collision target"})
 def boxcoords(d):
  r=d["rect"];q=bpx((r.x0,r.y0,r.x1,r.y1),sx,sy);return q[0]-x0,q[1]-y0,q[2]-x0,q[3]-y0
 def addbox(prefix,line,d,note):
  rc=boxcoords(d);gadd(prefix+"_FILL","FILL_BACKGROUND",line,d,roundfill(shape,rc,2*sx),note+" opaque node fill excluded by Goal F",False);gadd(prefix+"_BORDER","NODE_BORDER",line,d,strokemask(shape,d,sx,sy,spx),note+" final-visible vector border (PDF dash pattern retained)")
 addbox("GRAPHIC_INPUT_EXPECTATION",8,ds[0],"input expectation/integral");addbox("GRAPHIC_INPUT_IID",8,ds[1],"input IID");addbox("GRAPHIC_INPUT_LLN",8,ds[2],"input LLN");addbox("GRAPHIC_CORE",9,ds[3],"core Monte Carlo")
 for name,lineidx,arrow,head in (("EXPECTATION_TO_CORE",19,ds[4],ds[5]),("IID_TO_CORE",19,ds[6],ds[7]),("LLN_TO_CORE",19,ds[8],ds[9])):
   gadd("GRAPHIC_"+name+"_LINE","LINE_ARROW",lineidx,arrow,strokemask(shape,arrow,sx,sy,spx),name+" directed edge");gadd("GRAPHIC_"+name+"_HEAD","ARROW",lineidx,head,poly(shape,arrowpoly(head,sx,sy,spx)),name+" arrowhead")
 addbox("GRAPHIC_METHOD_INVERSE",11,ds[10],"inverse-transform method");gadd("GRAPHIC_INVERSE_ICON","MARKER",21,ds[11],strokemask(shape,ds[11],sx,sy,spx),"blue diagonal method-identity icon")
 addbox("GRAPHIC_METHOD_REJECTION",12,ds[12],"accept-reject method")
 # The double border contains an opaque white gap.  Preserve all three native
 # masks and use final-visible (pre minus halo) only for quality geometry.
 rc=boxcoords(ds[13]);gadd("GRAPHIC_METHOD_IS_FILL","FILL_BACKGROUND",12,ds[13],roundfill(shape,rc,2*sx),"importance-sampling node white fill excluded by Goal F",False)
 pre=strokemask(shape,ds[13],sx,sy,spx);halo=strokemask(shape,ds[14],sx,sy,spx);finalborder=pre & ~halo
 gadd("GRAPHIC_METHOD_IS_BORDER_PREOCCLUSION","PRE_OCCLUSION_BORDER",12,ds[13],pre,"double-border teal stroke before real opaque white gap",False);gadd("GRAPHIC_METHOD_IS_WHITE_GAP_HALO","HALO_BACKGROUND",12,ds[14],halo,"real opaque white double-border gap; excluded as background",False);gadd("GRAPHIC_METHOD_IS_BORDER","NODE_BORDER",12,ds[13],finalborder,"final-visible importance-sampling double border")
 for name,arrow,head in (("CORE_TO_INVERSE",ds[15],ds[16]),("CORE_TO_REJECTION",ds[17],ds[18]),("CORE_TO_IS",ds[19],ds[20])):
   gadd("GRAPHIC_"+name+"_LINE","LINE_ARROW",24,arrow,strokemask(shape,arrow,sx,sy,spx),name+" directed edge");gadd("GRAPHIC_"+name+"_HEAD","ARROW",24,head,poly(shape,arrowpoly(head,sx,sy,spx)),name+" arrowhead")
 addbox("GRAPHIC_DIAGNOSTIC",26,ds[21],"common diagnostic outlet")
 for name,arrow,head in (("INVERSE_TO_DIAGNOSTIC",ds[22],ds[23]),("REJECTION_TO_DIAGNOSTIC",ds[24],ds[25]),("IS_TO_DIAGNOSTIC",ds[26],ds[27])):
   gadd("GRAPHIC_"+name+"_LINE","LINE_ARROW",30,arrow,strokemask(shape,arrow,sx,sy,spx),name+" directed edge");gadd("GRAPHIC_"+name+"_HEAD","ARROW",30,head,poly(shape,arrowpoly(head,sx,sy,spx)),name+" arrowhead")
 double_masks={"pre_occlusion":"masks/graphics/GRAPHIC_METHOD_IS_BORDER_PREOCCLUSION.png","opaque_halo":"masks/graphics/GRAPHIC_METHOD_IS_WHITE_GAP_HALO.png","final_visible":"masks/graphics/GRAPHIC_METHOD_IS_BORDER.png","quality_geometry":"final_visible only; pre/halo retained as evidence; no result-oriented split"}
 write(OUT/"importance_sampling_double_border_masks.json",json.dumps(double_masks,ensure_ascii=False,indent=2))

 # Register every text-text, text-foreground graphic and edge relation.  Each
 # independent foreground pair is also retained in a complete pair universe.
 relations=[];critical=[];ids=sorted(semmask);semfile={r["ELEMENT_ID"]:r["RAW_MASK_FILE"] for r in semrows};gfile={r["ELEMENT_ID"]:r["RAW_MASK_FILE"] for r in gfx};counter=0
 def addrel(a,ak,am,b,bk,bm,typ,need):
  nonlocal counter;counter+=1;rid=f"REL_{counter:04d}";ov,clear=maskclear(am,bm);ba=sembox.get(a,gbox.get(a));bb=sembox.get(b,gbox.get(b));bc=bboxclear(ba,bb,sx,sy);passed=ov==0 and clear>=need and (typ!="TEXT_TEXT" or bc>=need)
  row={"RELATION_ID":rid,"PANEL_ID":PANEL,"ELEMENT_A":a,"CATEGORY_A":ak,"PDF_VECTOR_BBOX_A":";".join(f"{v:.3f}" for v in ba),"ELEMENT_B":b,"CATEGORY_B":bk,"PDF_VECTOR_BBOX_B":";".join(f"{v:.3f}" for v in bb),"RELATION_CLASS":typ,"RAW_MASK_A":semfile.get(a,gfile.get(a,"")),"RAW_MASK_B":semfile.get(b,gfile.get(b,"")),"OVERLAP_PIXEL_COUNT":ov,"CLEARANCE_PX":"INF" if math.isinf(clear) else f"{clear:.3f}","PDF_VECTOR_BBOX_CLEARANCE_PX":f"{bc:.3f}","REQUIRED_CLEARANCE_PX":need,"CLIP_PIXEL_COUNT":0,"PASS_FAIL":"PASS" if passed else "FAIL","REASON":"independent raw no-dilation masks; unexpanded PDF/vector bboxes","CRITICAL_ROI":""}
  if not passed or clear<=need+2 or (typ=="TEXT_TEXT" and bc<=need+2):roi(im,am,bm,spx,rid,f"{typ}; overlap={ov}; raw_clearance={clear}; bbox_clearance={bc:.3f}; required={need}",critical);row["CRITICAL_ROI"]=f"critical/{rid}_raw.png"
  relations.append(row)
 for i,a in enumerate(ids):
  for b in ids[i+1:]:addrel(a,"TEXT",semmask[a],b,"TEXT",semmask[b],"TEXT_TEXT",4)
 collision=[g for g in gfx if g["FOREGROUND"] and g["KIND"] in {"LINE_ARROW","ARROW","MARKER","NODE_BORDER"}]
 for a in ids:
  for g in collision:addrel(a,"TEXT",semmask[a],g["ELEMENT_ID"],g["KIND"],g["mask"],"TEXT_NODE_BORDER" if g["KIND"]=="NODE_BORDER" else f"TEXT_{g['KIND']}",5 if g["KIND"]=="NODE_BORDER" else 3)
 edge=[]
 for eid,category,m,rawfile in [(sid,"TEXT",semmask[sid],semfile[sid]) for sid in ids]+[(g["ELEMENT_ID"],g["KIND"],g["mask"],g["RAW_MASK_FILE"]) for g in collision]:
  yy,xx=np.nonzero(m);dist=min(int(xx.min()),int(yy.min()),int(shape[1]-1-xx.max()),int(shape[0]-1-yy.max()));ok=dist>=6;edge.append({"RELATION_ID":f"EDGE_{eid}","PANEL_ID":PANEL,"ELEMENT_A":eid,"CATEGORY_A":category,"PDF_VECTOR_BBOX_A":"N/A","ELEMENT_B":"FIGURE_SCOPE_EDGE","CATEGORY_B":"PANEL_EDGE","PDF_VECTOR_BBOX_B":"coordinate boundary","RELATION_CLASS":"TEXT_EDGE" if category=="TEXT" else "GRAPHIC_EDGE","RAW_MASK_A":rawfile,"RAW_MASK_B":"coordinate edge","OVERLAP_PIXEL_COUNT":0,"CLEARANCE_PX":f"{dist:.3f}","PDF_VECTOR_BBOX_CLEARANCE_PX":"N/A","REQUIRED_CLEARANCE_PX":6,"CLIP_PIXEL_COUNT":0,"PASS_FAIL":"PASS" if ok else "FAIL","REASON":"native raw foreground distance to immutable crop edge","CRITICAL_ROI":""})
 relations += edge
 universe=[];uniobjs=[(sid,"TEXT",semmask[sid]) for sid in ids]+[(g["ELEMENT_ID"],g["KIND"],g["mask"]) for g in collision]
 lookup={(r["ELEMENT_A"],r["ELEMENT_B"]):r for r in relations if r["RELATION_CLASS"] not in {"TEXT_EDGE","GRAPHIC_EDGE"}}
 for i,(a,ak,am) in enumerate(uniobjs):
  for b,bk,bm in uniobjs[i+1:]:
   r=lookup.get((a,b)) or lookup.get((b,a))
   if r:universe.append({"ELEMENT_A":a,"CATEGORY_A":ak,"ELEMENT_B":b,"CATEGORY_B":bk,"PAIR_SCOPE":"MEASURED_TEXT_RELATION","RELATION_ID":r["RELATION_ID"],"OVERLAP_PIXEL_COUNT":r["OVERLAP_PIXEL_COUNT"],"PASS_FAIL":r["PASS_FAIL"],"REASON":"reader-facing text involved"})
   else:
    ov=int((am&bm).sum());universe.append({"ELEMENT_A":a,"CATEGORY_A":ak,"ELEMENT_B":b,"CATEGORY_B":bk,"PAIR_SCOPE":"GRAPHIC_GRAPHIC_STRUCTURAL","RELATION_ID":"N/A","OVERLAP_PIXEL_COUNT":ov,"PASS_FAIL":"PASS","REASON":"not an illegal reader-text collision; endpoint/border attachment is structural and is retained for exhaustive pair accounting"})

 # Goal D: same panel + same semantic role + same script class only.
 same=[];sameok=True;buckets=defaultdict(list)
 for r in glyphrows:buckets[(r["PANEL_ID"],r["ROLE"],r["SCRIPT_FAMILY"])].append(r)
 for (panel,role,fam),rows in sorted(buckets.items()):
  med=median([int(r["H_INK_PX"]) for r in rows]);rat=[int(r["H_INK_PX"])/med for r in rows];ok=all(.92<=q<=1.08 for q in rat);sameok &= ok
  same.append({"PANEL_ID":panel,"ROLE":role,"SCRIPT_FAMILY":fam,"GROUPING":"same panel + same semantic role + same script class actual raw H_ink; never exact-glyph grouping","N_GLYPHS":len(rows),"MEDIAN_RAW_H_INK_PX":f"{med:.3f}","MIN_RATIO":f"{min(rat):.4f}","MAX_RATIO":f"{max(rat):.4f}","REQUIRED_RANGE":"[0.92,1.08]","PASS_FAIL":"PASS" if ok else "FAIL","MEMBERS":";".join(r["ELEMENT_ID"] for r in rows)})
  for r,q in zip(rows,rat):r["CLASS_MEDIAN_PX"]=f"{med:.3f}";r["RATIO_TO_CLASS_MEDIAN"]=f"{q:.4f}"
 # Source-size same-role and cross-panel checks use component bases, separate from pixel roles.
 semrole=defaultdict(list)
 for r in semrows:semrole[r["ROLE"]].append(r)
 source_role=[];source_role_ok=True
 for role,rows in sorted(semrole.items()):
  pts=[float(r["DECLARED_EFFECTIVE_PT"]) for r in rows];rat=max(pts)/min(pts);delta=max(pts)-min(pts);ok=rat<=1.03 and delta<=.25;source_role_ok &= ok
  source_role.append({"PANEL_ID":PANEL,"ROLE":role,"N_COMPONENTS":len(rows),"EFFECTIVE_PT_VALUES":";".join(f"{q:.3f}" for q in pts),"MAX_MIN_RATIO":f"{rat:.4f}","ABS_DIFF_PT":f"{delta:.4f}","LIMIT_RATIO":"<=1.03","LIMIT_ABS_DIFF_PT":"<=0.25","PASS_FAIL":"PASS" if ok else "FAIL","MEMBERS":";".join(r["ELEMENT_ID"] for r in rows),"REASON":"semantic component base effective fonts; natural scripts excluded from source base-font comparison"})
 source_cross=[{"ROLE":role,"PANEL_COUNT":1,"PANEL_IDS":PANEL,"METRIC":"cross-panel same-role effective-font max/min","OBSERVED":"N/A — one panel only","LIMIT":"<=1.05 or explicit single-panel N/A","PASS_FAIL":"PASS","REASON":"single panel"} for role in sorted(semrole)];source_cross_ok=True
 # Goal E actual raw H_ink role hierarchy with only comparable scripts.
 rolevals=defaultdict(list)
 for r in glyphrows:rolevals[(r["ROLE"],r["SCRIPT_FAMILY"])].append(int(r["H_INK_PX"]))
 specs={
  ("CJK","INPUT_CONCEPT"):("INPUT_CONCEPT",1.00,1.00,"BASE: repeated ordinary prerequisite-concept labels"),
  ("CJK","METHOD_LABEL"):("INPUT_CONCEPT",.95,1.10,"ordinary method labels"),
  ("CJK","DIAGNOSTIC"):("INPUT_CONCEPT",.95,1.10,"ordinary diagnostic annotation"),
  ("CJK","ANNOTATION"):("INPUT_CONCEPT",.95,1.10,"ordinary explanatory annotation"),
  ("CJK","CORE_CONCEPT"):("INPUT_CONCEPT",.90,1.25,"predeclared central core emphasis, source L9-L10"),
  ("CJK","CAPTION"):("INPUT_CONCEPT",.90,1.25,"caption typography is a distinct reader-facing role"),
 }
 base_reason={"INPUT_CONCEPT":"no ticks/axis; three repeated prerequisite boxes are ordinary CJK node labels"}
 roles=[];roleok=True;role_ratio={}
 for fam in sorted({k[1] for k in rolevals}):
  for role in sorted({k[0] for k in rolevals if k[1]==fam}):
   med=median(rolevals[(role,fam)]);spec=specs.get((fam,role))
   if spec is None:base=None;bmed=None;ratio=None;lo=hi=None;state="PASS";reason="N/A: no same-script semantic hierarchy comparator for punctuation/operator, digit, uppercase or natural-script glyphs"
   else:
    base,lo,hi,reason=spec;basevals=rolevals.get((base,fam),[])
    if not basevals:bmed=None;ratio=None;state="FAIL";reason+="; declared BASE unavailable"
    else:bmed=median(basevals);ratio=med/bmed;state="PASS" if lo<=ratio<=hi else "FAIL";reason+=f"; Goal E range [{lo:.2f},{hi:.2f}]"
   roleok &= state=="PASS";role_ratio[(role,fam)]="N/A" if ratio is None else f"{ratio:.4f}";roles.append({"SCRIPT_FAMILY":fam,"ROLE":role,"BASE_ROLE":base or "N/A","BASE_SELECTION_REASON":base_reason.get(base,"N/A: no comparable same-script base"),"ROLE_MEDIAN_RAW_H_INK_PX":f"{med:.3f}","BASE_MEDIAN_RAW_H_INK_PX":"N/A" if bmed is None else f"{bmed:.3f}","RATIO_TO_BASE":"N/A" if ratio is None else f"{ratio:.4f}","EXPECTED_RANGE":"N/A" if lo is None else f"[{lo:.2f},{hi:.2f}]","COMPARISON_POLICY":"same script only; Goal 9.2.1 E","PASS_FAIL":state,"REASON":reason})
   for r in glyphrows:
    if r["ROLE"]==role and r["SCRIPT_FAMILY"]==fam:r["ROLE_MEDIAN_PX"]=f"{med:.3f}";r["RATIO_TO_ROLE_MEDIAN"]=f"{int(r['H_INK_PX'])/med:.4f}";r["ROLE_RATIO"]=role_ratio[(role,fam)]
 cross=[]
 for role,fam in sorted(rolevals):cross.append({"ROLE":role,"SCRIPT_FAMILY":fam,"PANEL_COUNT":1,"PANEL_IDS":PANEL,"METRIC":"cross-panel same-role same-script raw-H-ink median","OBSERVED":"N/A — one panel only","LIMIT":"<=1.10 or explicit single-panel N/A","PASS_FAIL":"PASS","REASON":"single panel; comparison not manufactured"})
 # Fill fields that Goal C requires in every literal glyph row.
 for gr in glyphrows:
  parent=gr["PARENT_ELEMENT_ID"];rr=[r for r in relations if r["ELEMENT_A"]==parent or r["ELEMENT_B"]==parent];tt=[r for r in rr if r["RELATION_CLASS"]=="TEXT_TEXT"];tg=[r for r in rr if r["RELATION_CLASS"] not in {"TEXT_TEXT","TEXT_EDGE","GRAPHIC_EDGE"}];finite=[float(r["CLEARANCE_PX"]) for r in rr if r["CLEARANCE_PX"]!="INF"]
  gr["TEXT_TEXT_OVERLAP_PX"]=str(sum(int(r["OVERLAP_PIXEL_COUNT"]) for r in tt));gr["TEXT_GRAPHIC_OVERLAP_PX"]=str(sum(int(r["OVERLAP_PIXEL_COUNT"]) for r in tg));gr["MIN_CLEARANCE_PX"]="INF" if not finite else f"{min(finite):.3f}"

 mathrows=[
  {"CHECK_ID":"TEACHING_DEPENDENCY","OBSERVED":"inputs expectation/integral, IID and LLN all point to Monte Carlo estimate; diagram deliberately denotes teaching dependency rather than a runtime algorithm","PASS_FAIL":"PASS"},
  {"CHECK_ID":"METHOD_DISTINCTION","OBSERVED":"inverse transform and accept-reject are direct-sampling routes; importance sampling retains proposal samples and changes contribution weights; figure body L76 and caption agree","PASS_FAIL":"PASS"},
  {"CHECK_ID":"DIAGNOSTIC_SCOPE","OBSERVED":"error/support diagnostics apply across methods; weighted ESS reduces to ordinary sample-count diagnostic for unweighted direct samples, so common outlet is not a false probability claim","PASS_FAIL":"PASS"},
  {"CHECK_ID":"ARROW_DIRECTION","OBSERVED":"all arrows point prerequisite -> core -> three parallel methods -> common diagnostic outlet; source footnote explicitly rejects temporal/serial interpretation of border/icon coding","PASS_FAIL":"PASS"},
 ]
 mathmd=r"""# FIG-P570-01 数学、概率与图文语义独立复算（SA1）

图 31.1 的箭头表示教学依赖而非单次算法的执行时间。期望/积分、独立抽样和大数规律共同支撑 Monte Carlo 估计；之后的逆变换、接受--拒绝和重要性抽样是并列方法，不能被图误读为彼此等价或串行步骤。相邻正文 L76 明确给出这个限制，并区分接受--拒绝产生未加权目标样本、重要性抽样保留提议样本并改变贡献权重。

“误差 / ESS / 支持覆盖诊断”作为共同出口在概率上没有错误：误差和支持条件适用于各路径；对未加权直接样本，可把 ESS 视作普通样本计数的退化诊断，重要性路径则是权重集中相关诊断。图源 L32 同样限定边框/图标只是方法身份，不表示先后依赖。题注、图内变量及直接正文一致。

结论：`MATH_SEMANTICS_PASS=true`、`PROBABILITY_SEMANTICS_PASS=true`、`TEXT_CONSISTENCY_PASS=true`。
"""
 write(OUT/"math_semantics_recheck.md",mathmd);writecsv(OUT/"math_semantics_recheck.csv",mathrows);write(OUT/"math_semantics_recheck.json",json.dumps({"math_semantics_pass":True,"probability_semantics_pass":True,"text_consistency_pass":True,"checks":mathrows},ensure_ascii=False,indent=2))
 # The fixed-grid overlay is itself an evidence artifact: every literal
 # glyph receives its ID/bbox/role; the companion object overlay additionally
 # registers every semantic and graphic component.
 def drawbox(draw,bb,label,color):
  q=bpx(bb,sx,sy);xx0,yy0,xx1,yy1=int(round(q[0]-x0)),int(round(q[1]-y0)),int(round(q[2]-x0)),int(round(q[3]-y0))
  draw.rectangle((xx0,yy0,xx1,yy1),outline=color,width=1)
  draw.text((xx0,max(0,yy0-9)),label,fill=color,font=ImageFont.load_default(),stroke_width=0)
 overlay=np.asarray(im.crop(spx).convert("RGB")).copy()
 for m in semmask.values():yy,xx=np.nonzero(m);overlay[yy,xx]=[255,0,255]
 odraw=ImageDraw.Draw(Image.fromarray(overlay,"RGB"))
 # Re-materialize because Pillow draw writes into its Image object, not the
 # original numpy view on every Pillow version.
 text_overlay=Image.fromarray(overlay,"RGB");odraw=ImageDraw.Draw(text_overlay)
 for z in chars:drawbox(odraw,z["bbox"],f"{z['id']}|{META[z['sid']][0]}",(255,220,0))
 Image.fromarray(np.asarray(text_overlay),"RGB").save(OUT/"after_text_measurement_overlay_300dpi.png")
 obj_overlay=np.asarray(im.crop(spx).convert("RGB")).copy();objimg=Image.fromarray(obj_overlay,"RGB");objdraw=ImageDraw.Draw(objimg)
 for z in chars:drawbox(objdraw,z["bbox"],f"{z['id']}|{META[z['sid']][0]}",(255,220,0))
 for sid,bb in sembox.items():drawbox(objdraw,bb,f"{sid}|{META[sid][0]}",(255,0,255))
 for g in gfx:drawbox(objdraw,gbox[g["ELEMENT_ID"]],f"{g['ELEMENT_ID']}|{g['KIND']}",(0,220,255))
 Image.fromarray(np.asarray(objimg),"RGB").save(OUT/"object_id_overlay_300dpi.png")
 ff=[r for r in glyphrows if r["SOURCE_FONT_PASS"]=="false"];pf=[r for r in glyphrows if r["PIXEL_HEIGHT_PASS"]=="false"];ffcomp=len({r["PARENT_ELEMENT_ID"] for r in ff});pfcomp=len({r["PARENT_ELEMENT_ID"] for r in pf});glyphby={r["id"]:r for r in chars}
 objectrows=[]
 for z in chars:objectrows.append({"ELEMENT_ID":z["id"],"PARENT_ELEMENT_ID":z["sid"],"CATEGORY":"GLYPH","ROLE":META[z["sid"]][0],"PDF_BBOX":";".join(f"{v:.3f}" for v in z["bbox"]),"RAW_MASK_FILE":z["mf"]})
 for r in semrows:objectrows.append({"ELEMENT_ID":r["ELEMENT_ID"],"PARENT_ELEMENT_ID":r["PARENT_ELEMENT_ID"],"CATEGORY":"SEMANTIC_TEXT","ROLE":r["ROLE"],"PDF_BBOX":r["PDF_BBOX"],"RAW_MASK_FILE":r["RAW_MASK_FILE"]})
 for g in gfx:objectrows.append({"ELEMENT_ID":g["ELEMENT_ID"],"PARENT_ELEMENT_ID":g["ELEMENT_ID"],"CATEGORY":g["KIND"],"ROLE":"GRAPHIC","PDF_BBOX":";".join(f"{v:.3f}" for v in gbox[g["ELEMENT_ID"]]),"RAW_MASK_FILE":g["RAW_MASK_FILE"]})
 # Every literal font/pixel failure gets raw ROI, its own raw mask, independent
 # zero mask, intersection and NN 8x view.  Relation failures/critical pairs
 # were emitted above with two non-empty independent object masks.
 for gr in glyphrows:
  if gr["SOURCE_FONT_PASS"]=="false" or gr["PIXEL_HEIGHT_PASS"]=="false":z=glyphby[gr["ELEMENT_ID"]];roi(im,z["mask"],np.zeros(shape,dtype=bool),spx,"GLYPH_"+gr["ELEMENT_ID"],"literal glyph source-font or pixel-height failure; second independent mask empty for one-object legibility diagnostic",critical)
 writecsv(OUT/"semantic_component_inventory.csv",semrows);writecsv(OUT/"graphic_component_inventory.csv",grows);writecsv(OUT/"glyph_inventory.csv",[{"ELEMENT_ID":z["id"],"PARENT_ELEMENT_ID":z["sid"],"TEXT_SAMPLE":z["char"],"CODEPOINT":f"U+{ord(z['char']):04X}","PDF_BBOX":";".join(f"{v:.3f}" for v in z["bbox"]),"PDF_VECTOR_FONT_SIZE_PT":f"{z['size']:.3f}","PDF_VECTOR_FONT":z["font"],"RAW_MASK_FILE":z["mf"],"LOCAL_BACKGROUND_RGB":",".join(map(str,z["bg"]))} for z in chars]);writecsv(OUT/"object_bbox_role_inventory.csv",objectrows);writecsv(OUT/"mask_manifest.csv",masks);writecsv(OUT/"foreground_exclusions.csv",exclusions);writecsv(OUT/"pair_universe.csv",universe);writecsv(OUT/"after_font_audit.csv",fontrows);writecsv(OUT/"after_pixel_measurements.csv",glyphrows);writecsv(OUT/"after_overlap_report.csv",relations);writecsv(OUT/"same_class_ratio_audit.csv",same);writecsv(OUT/"source_font_role_ratio_audit.csv",source_role);writecsv(OUT/"source_font_cross_panel_audit.csv",source_cross);writecsv(OUT/"role_ratio_audit.csv",roles);writecsv(OUT/"cross_panel_ratio_audit.csv",cross);writecsv(OUT/"critical_artifacts.csv",critical)
 overlap=sum(int(r["OVERLAP_PIXEL_COUNT"]) for r in relations if r["RELATION_CLASS"] not in {"GRAPHIC_EDGE","TEXT_EDGE"});clip=sum(int(r["CLIP_PIXEL_COUNT"]) for r in relations);tf=[r for r in relations if r["RELATION_CLASS"]=="TEXT_TEXT"];tg=[r for r in relations if r["RELATION_CLASS"] not in {"TEXT_TEXT","TEXT_EDGE","GRAPHIC_EDGE"}];te=[r for r in relations if r["RELATION_CLASS"]=="TEXT_EDGE"];ge=[r for r in relations if r["RELATION_CLASS"]=="GRAPHIC_EDGE"]
 # Keep relation, pair-universe and clearance counts explicit and identical.
 # TEXT_NODE_BORDER uses only final-visible border-mask distance.  The fact
 # that a node's text bbox lies inside the node bbox is never itself a
 # clearance failure; only the raw foreground masks decide this relation.
 relationfails=[r for r in relations if r["PASS_FAIL"]=="FAIL"]
 pairfails=[r for r in universe if r["PASS_FAIL"]=="FAIL"]
 clearancefails=[r for r in relationfails if r["RELATION_CLASS"] in {"TEXT_TEXT","TEXT_LINE_ARROW","TEXT_ARROW","TEXT_MARKER","TEXT_NODE_BORDER","TEXT_EDGE","GRAPHIC_EDGE"}]
 relationfail_count=len(relationfails);pairfail_count=len(pairfails);clearancefail_count=len(clearancefails)
 def minraw(rows):
  x=[float(r["CLEARANCE_PX"]) for r in rows if r["CLEARANCE_PX"]!="INF"];return min(x) if x else math.inf
 minbbox=min(float(r["PDF_VECTOR_BBOX_CLEARANCE_PX"]) for r in tf);clearanceok=clearancefail_count==0;sourceok=not ff;pixelok=not pf;crossok=True;harmony=False;mathok=True;probok=True;textok=True;gray=True;pageok=True
 hard={"SOURCE_FONT_PASS":sourceok,"SOURCE_FONT_FAILURE_COUNT":len(ff),"SOURCE_FONT_FAILURE_COMPONENT_COUNT":ffcomp,"SOURCE_SAME_ROLE_FONT_PASS":source_role_ok,"SOURCE_CROSS_PANEL_FONT_PASS":source_cross_ok,"PIXEL_HEIGHT_PASS":pixelok,"PIXEL_HEIGHT_FAILURE_COUNT":len(pf),"PIXEL_HEIGHT_FAILURE_COMPONENT_COUNT":pfcomp,"SAME_CLASS_RATIO_PASS":sameok,"ROLE_RATIO_PASS":roleok,"OVERLAP_PIXEL_COUNT":overlap,"OVERLAP_PASS":overlap==0,"CLIP_PIXEL_COUNT":clip,"CLIP_PASS":clip==0,"RELATION_FAILURE_COUNT":relationfail_count,"PAIR_UNIVERSE_FAILURE_COUNT":pairfail_count,"CLEARANCE_FAILURE_COUNT":clearancefail_count,"CLEARANCE_PASS":clearanceok,"CROSS_PANEL_PASS":crossok,"FONT_VISUAL_HARMONY_PASS":harmony,"MATH_SEMANTICS_PASS":mathok,"PROBABILITY_SEMANTICS_PASS":probok,"TEXT_CONSISTENCY_PASS":textok,"GRAYSCALE_PASS":gray,"PAGE_INTEGRATION_PASS":pageok}
 final=all([sourceok,source_role_ok,source_cross_ok,pixelok,sameok,roleok,overlap==0,clip==0,clearanceok,crossok,harmony,mathok,probok,textok,gray,pageok]);hard["FINAL_RESULT"]="PASS" if final else "FAIL";hard["NEXT_ROLE"]="SA3" if final else "SA2"
 summary={"audit_id":"FIG-P570-01/STRICT_R1/SA1_20260824_R1","role":"SA1 independent blind strict review","input":{"frozen_r94_pdf":str(PDF),"physical_page":PDF_PAGE,"figure_source":str(FIG),"adjacent_context":f"{CHAPTER}:67-77","style":f"{STYLE}:269-281"},"coverage":{"glyphs":len(chars),"semantic_text_components":len(semrows),"graphic_components":len(grows),"foreground_components":len(uniobjs),"all_unordered_foreground_pairs":len(universe),"text_text_pairs":len(tf),"text_graphic_pairs":len(tg),"text_edge_pairs":len(te),"graphic_edge_pairs":len(ge),"relation_failures":relationfail_count,"pair_universe_failures":pairfail_count,"clearance_failures":clearancefail_count,"critical_artifacts":len(critical)},"hard_gates":hard,"result":hard["FINAL_RESULT"],"handoff":hard["NEXT_ROLE"],"strict_method":"R94 native 300dpi fixed grid; per-glyph PDF bbox raw masks threshold 20/no dilation; vector-derived graphic masks; double-border pre/halo/final-visible proof; exhaustive pair universe"}
 write(OUT/"strict_audit_summary.json",json.dumps(summary,ensure_ascii=False,indent=2))
 eight=[]
 def report(cid,cat,evidence,metric,threshold,observed,flag):eight.append({"CHECK_ID":cid,"CATEGORY":cat,"EVIDENCE":evidence,"METRIC":metric,"THRESHOLD":threshold,"OBSERVED":observed,"BOOLEAN":str(bool(flag)).lower(),"STATUS":"PASS" if flag else "FAIL"})
 report("R01","INPUT","render_manifest.json","frozen R94 input and independent physical location","official R94 only",f"page {PDF_PAGE}/{len(doc)}, sha256={fhash}",True);report("R02","RENDER","full_page_200dpi.png","whole page","native 200dpi","Poppler direct",True);report("R03","RENDER","full_page_300dpi_native.png;full_page_300dpi_grid.json","measurement grid","native 300dpi,1:1,no resize",f"{im.width}x{im.height}px; scales={sx:.6f},{sy:.6f}",True);report("R04","COVERAGE","object_bbox_role_inventory.csv;object_id_overlay_300dpi.png;glyph_inventory.csv;semantic_component_inventory.csv;graphic_component_inventory.csv;pair_universe.csv","visible text/vector objects, IDs/bboxes/roles and all unordered foreground pairs","complete",f"objects={len(objectrows)} unique IDs; glyph={len(chars)}, semantic={len(semrows)}, graphic={len(grows)}, pair-universe={len(universe)}",len({r['ELEMENT_ID'] for r in objectrows})==len(objectrows));report("R05","MASKS","mask_manifest.csv;importance_sampling_double_border_masks.json","raw masks / opaque double-border proof","no dilation; final-visible geometry",f"masks={len(masks)}",True)
 report("R06","SOURCE_FONT","after_font_audit.csv;source_font_role_ratio_audit.csv;source_font_cross_panel_audit.csv","ordinary effective font and repeated role sizes",">=9.5pt; same role <=1.03 and <=0.25pt; cross panel <=1.05",f"failure glyphs={len(ff)} across {ffcomp} components; same-role={source_role_ok}; cross-panel={source_cross_ok}",sourceok and source_role_ok and source_cross_ok);report("R07","PIXEL_HEIGHT","after_pixel_measurements.csv","literal raw H_ink","30/24/17/22/15px",f"failed glyphs={len(pf)}",pixelok);report("R08","SAME_CLASS","same_class_ratio_audit.csv","same panel+role+same script actual raw H_ink","[0.92,1.08]","no exact-glyph grouping",sameok);report("R09","ROLE_RATIO","role_ratio_audit.csv","same-script role median relative to local BASE","Goal E ranges; N/A only if no comparable script base","see CSV",roleok);report("R10","OVERLAP","after_overlap_report.csv","illegal text-front-graphic pairs","0",str(overlap),overlap==0);report("R11","CLIP","after_overlap_report.csv","text and graphic edge clip","0",str(clip),clip==0);report("R12","CLEARANCE","after_overlap_report.csv;pair_universe.csv","text/text, text/line-arrow-marker, node border, edge","4/3/5/6px",f"text raw={minraw(tf):.3f}, bbox={minbbox:.3f}; text graphic={minraw(tg):.3f}; text edge={minraw(te):.3f}; graphic edge={minraw(ge):.3f}; relation-fail={relationfail_count}; pair-fail={pairfail_count}; clearance-fail={clearancefail_count}",clearanceok);report("R13","CROSS_PANEL","cross_panel_ratio_audit.csv","same role+same script raw H_ink","<=1.10 or explicit single-panel N/A","one panel",crossok);report("R14","HARMONY","full_page_200dpi.png;figure_crop_300dpi.png;standalone_300dpi.png;grayscale_300dpi.png","FONT_VISUAL_HARMONY_PASS","no undersized or intrusive roles","9.2pt / 8.6pt reader text violates size gate and is visually small",harmony);report("R15","MATH","math_semantics_recheck.md","dependency direction/method distinction/diagnostics","all correct","all correct",mathok);report("R16","TEXT","math_semantics_recheck.md;adjacent_source_context.tex","caption/body/variable consistency","consistent","consistent",textok);report("R17","GRAYSCALE","grayscale_300dpi.png","non-color distinguishability","stable","line style/border/icon differences remain",gray);report("R18","PAGE","full_page_200dpi.png","page integration","intact","placement/caption flow intact; typography independently fails",pageok);report("R19","FINAL","strict_audit_summary.json","all hard gates","all true",hard["FINAL_RESULT"],final)
 writecsv(OUT/"strict_eight_column_report.csv",eight)
 accept=f"""# FIG-P570-01｜STRICT R1｜SA1 正式验收

RESULT: {hard['FINAL_RESULT']}

NEXT_ROLE: {hard['NEXT_ROLE']}

独立 R94 定位：物理页 {PDF_PAGE}/{len(doc)}（页内印刷页 604）。覆盖 {len(chars)} 个可见 glyph、{len(semrows)} 个语义文字组件、{len(grows)} 个线/箭头/marker/node-border/fill/pre-halo 组件、{len(universe)} 个无序独立前景对象对；其中 TEXT--TEXT={len(tf)}、TEXT--graphic={len(tg)}、TEXT--edge={len(te)}、GRAPHIC--edge={len(ge)}。四视图和 300dpi 固定网格均已落盘。

| Gate | Observed | Required | Status |
|---|---:|---:|---|
| SOURCE_FONT_PASS | {str(sourceok).lower()} | true | {'PASS' if sourceok else 'FAIL'} |
| SOURCE_FONT_FAILURE_COUNT | {len(ff)} glyphs / {ffcomp} components | 0 | {'PASS' if not ff else 'FAIL'} |
| SOURCE_ROLE_FONT / SOURCE_CROSS_PANEL_FONT | {str(source_role_ok).lower()} / {str(source_cross_ok).lower()} | true / true | {'PASS' if source_role_ok and source_cross_ok else 'FAIL'} |
| PIXEL_HEIGHT_PASS | {str(pixelok).lower()} ({len(pf)} glyphs / {pfcomp} components) | true | {'PASS' if pixelok else 'FAIL'} |
| SAME_CLASS_RATIO_PASS | {str(sameok).lower()} | true | {'PASS' if sameok else 'FAIL'} |
| ROLE_RATIO_PASS | {str(roleok).lower()} | true | {'PASS' if roleok else 'FAIL'} |
 | OVERLAP / CLIP | {overlap} / {clip} | 0 / 0 | {'PASS' if overlap==0 and clip==0 else 'FAIL'} |
 | RELATION / PAIR / CLEARANCE failures | {relationfail_count} / {pairfail_count} / {clearancefail_count} | 0 / 0 / 0 | {'PASS' if clearanceok else 'FAIL'} |
 | MIN_TEXT_CLEARANCE_PX | text/text raw={minraw(tf):.3f}, bbox={minbbox:.3f}; text/graphic={minraw(tg):.3f}; edge={minraw(te):.3f} | 4 / 3(or 5 node) / 6 | {'PASS' if clearanceok else 'FAIL'} |
| VISUAL_HARMONY_PASS / FONT_VISUAL_HARMONY_PASS | false / false | true / true | FAIL |
| MATH / PROBABILITY / TEXT | true / true / true | all true | PASS |

 硬失败：图源 L3/L7 的 9.2pt 普通 input/method/diagnostic 文字和 L31 的 8.6pt 注释低于 9.5pt；局部明确字体不由公共 `every node=\\small` 覆盖。每个可见 glyph（含 `/`,`≤`,`–`,`|`、全角冒号/分号及所有下标/标点）均有独立 raw H_ink 与 mask。真实 text relation overlap=0、clip=0，但 `REL_0274` 的“接受--拒绝”节点文字与最终可见虚线右边框 raw 净空为 0px（要求 5px），故 relation/pair/clearance 各 1 项失败；节点 bbox 的包含关系不单独作为失败依据。IS 双线边框的 pre-occlusion/opaque-gap/final-visible 三套 mask 均保存，质量关系只使用 final-visible mask。数学、概率语义、箭头方向、题注与紧邻正文一致。

任何硬门失败均不得进入 SA3。本轮只能 **FAIL → SA2**。
"""
 write(OUT/"SA1_RESULT.md",accept);write(OUT/"after_visual_acceptance.md",accept)
 # Machine terminal integrity closure is deliberately separate from quality.
 req=["full_page_200dpi.png","full_page_300dpi_native.png","full_page_300dpi_grid.json","figure_crop_300dpi.png","standalone_300dpi.png","grayscale_300dpi.png","after_text_measurement_overlay_300dpi.png","object_id_overlay_300dpi.png","object_bbox_role_inventory.csv","render_manifest.json","importance_sampling_double_border_masks.json","after_font_audit.csv","after_pixel_measurements.csv","after_overlap_report.csv","same_class_ratio_audit.csv","source_font_role_ratio_audit.csv","source_font_cross_panel_audit.csv","role_ratio_audit.csv","cross_panel_ratio_audit.csv","pair_universe.csv","foreground_exclusions.csv","math_semantics_recheck.md","math_semantics_recheck.csv","math_semantics_recheck.json","strict_audit_summary.json","strict_eight_column_report.csv","critical_artifacts.csv","SA1_RESULT.md"]
 machine=[]
 def M(cid,need,obs,ok,evidence):machine.append({"CHECK_ID":cid,"REQUIREMENT":need,"OBSERVED":obs,"EVIDENCE":evidence,"STATUS":"PASS" if ok else "FAIL"})
 M("MC01_REQUIRED_ARTIFACTS","all prescribed evidence exists",f"{sum((OUT/q).is_file() for q in req)}/{len(req)}",all((OUT/q).is_file() for q in req),";".join(req));tw,th=pg.rect.width*300/72,pg.rect.height*300/72;xr=abs(sx/(300/72)-1);yr=abs(sy/(300/72)-1);native=abs(im.width-tw)<=1 and abs(im.height-th)<=1 and xr<=.0005 and yr<=.0005;M("MC02_FULL_PAGE_NATIVE_GRID","PDF points to integral native 300dpi grid, <=1px / <=0.05% axis tolerance",f"actual={im.width}x{im.height}; target={tw:.3f}x{th:.3f}; relative={xr:.6%},{yr:.6%}",native,"full_page_300dpi_native.png;full_page_300dpi_grid.json")
 object_ids=[r["ELEMENT_ID"] for r in objectrows];expected_objects=len(chars)+len(semrows)+len(gfx);object_ok=len(objectrows)==expected_objects and len(set(object_ids))==expected_objects
 M("MC03_OBJECT_UNIQUENESS","manifest object count and IDs are complete/unique",f"objects={len(objectrows)}/{expected_objects}; unique={len(set(object_ids))}",object_ok,"object_bbox_role_inventory.csv;object_id_overlay_300dpi.png")
 paths=[OUT/z["mf"] for z in chars]+[OUT/r["RAW_MASK_FILE"] for r in semrows]+[OUT/r["RAW_MASK_FILE"] for r in gfx];empty_masks=sum(not np.asarray(Image.open(p).convert("L")).any() for p in paths);M("MC04_MASK_LINKS_NONEMPTY","all glyph/semantic/graphic masks resolve and are nonempty",f"resolved={sum(p.is_file() for p in paths)}/{len(paths)}; empty={empty_masks}",all(p.is_file() for p in paths) and empty_masks==0,"mask_manifest.csv")
 gf=("ELEMENT_ID","PARENT_ELEMENT_ID","PANEL_ID","ROLE","SOURCE_FILE","SOURCE_LINE","DECLARED_PT","GRAPHICS_SCALE","EFFECTIVE_PT","TEXT_SAMPLE","SCRIPT_CLASS","SCRIPT_FAMILY","BBOX_X0","BBOX_Y0","BBOX_X1","BBOX_Y1","H_INK_PX","PIXEL_THRESHOLD_PX","CLASS_MEDIAN_PX","RATIO_TO_CLASS_MEDIAN","ROLE_MEDIAN_PX","RATIO_TO_ROLE_MEDIAN","ROLE_RATIO","TEXT_TEXT_OVERLAP_PX","TEXT_GRAPHIC_OVERLAP_PX","MIN_CLEARANCE_PX","SOURCE_FONT_PASS","PIXEL_HEIGHT_PASS","RAW_MASK_FILE")
 M("MC05_GLYPH_SCHEMA","each glyph has required source/bbox/raw-Hink/script/ratio/relation/mask fields",f"glyphs={len(glyphrows)}",all(all(str(r.get(k,""))!="" for k in gf) for r in glyphrows),"after_pixel_measurements.csv")
 rf=("RELATION_ID","ELEMENT_A","ELEMENT_B","RAW_MASK_A","RAW_MASK_B","OVERLAP_PIXEL_COUNT","CLEARANCE_PX","REQUIRED_CLEARANCE_PX","PASS_FAIL")
 expected_pairs=len(uniobjs)*(len(uniobjs)-1)//2;expected_relations=len(tf)+len(tg)+len(te)+len(ge)
 M("MC06_RELATION_PAIR_SCHEMA","all required relations and exhaustive unordered pairs have complete fields",f"relations={len(relations)}/{expected_relations}; pairs={len(universe)}/{expected_pairs}",all(all(str(r.get(k,""))!="" for k in rf) for r in relations) and all(r["PDF_VECTOR_BBOX_A"] and r["PDF_VECTOR_BBOX_B"] for r in tf) and len(universe)==expected_pairs,"after_overlap_report.csv;pair_universe.csv")
 needed=[r for r in relations if r["PASS_FAIL"]=="FAIL" or (r["CLEARANCE_PX"]!="INF" and float(r["CLEARANCE_PX"])<=int(r["REQUIRED_CLEARANCE_PX"])+2) or (r["RELATION_CLASS"]=="TEXT_TEXT" and float(r["PDF_VECTOR_BBOX_CLEARANCE_PX"])<=int(r["REQUIRED_CLEARANCE_PX"])+2)]
 c_ok=all(r["CRITICAL_ROI"] and (OUT/r["CRITICAL_ROI"]).is_file() for r in needed) and all((OUT/r[k]).is_file() for r in critical for k in ("RAW_ROI","MASK_A","MASK_B","OVERLAP_MASK","OVERLAY","ZOOM_8X"));M("MC07_CRITICAL_EVIDENCE","every failed/critical relation and failed glyph evidence includes raw ROI/two masks/intersection/1x/8x",f"relation-needed={len(needed)}; artifacts={len(critical)}; complete-artifacts={sum(all((OUT/r[k]).is_file() for k in ('RAW_ROI','MASK_A','MASK_B','OVERLAP_MASK','OVERLAY','ZOOM_8X')) for r in critical)}",c_ok,"critical_artifacts.csv")
 # Re-open the written CSVs, rather than trusting only in-memory lists. This
 # makes a stale pair universe or summary impossible to conceal in MC07/MC08.
 with (OUT/"after_overlap_report.csv").open(encoding="utf-8-sig",newline="") as f:diskrelations=list(csv.DictReader(f))
 with (OUT/"pair_universe.csv").open(encoding="utf-8-sig",newline="") as f:diskpairs=list(csv.DictReader(f))
 disk_relation_fail=sum(r["PASS_FAIL"]=="FAIL" for r in diskrelations)
 disk_pair_fail=sum(r["PASS_FAIL"]=="FAIL" for r in diskpairs)
 disk_clearance_fail=sum(r["PASS_FAIL"]=="FAIL" and r["RELATION_CLASS"] in {"TEXT_TEXT","TEXT_LINE_ARROW","TEXT_ARROW","TEXT_MARKER","TEXT_NODE_BORDER","TEXT_EDGE","GRAPHIC_EDGE"} for r in diskrelations)
 countok=overlap==sum(int(r["OVERLAP_PIXEL_COUNT"]) for r in relations if r["RELATION_CLASS"] not in {"GRAPHIC_EDGE","TEXT_EDGE"}) and clip==sum(int(r["CLIP_PIXEL_COUNT"]) for r in relations) and len(ff)==sum(r["SOURCE_FONT_PASS"]=="false" for r in glyphrows) and len(pf)==sum(r["PIXEL_HEIGHT_PASS"]=="false" for r in glyphrows) and disk_relation_fail==relationfail_count and disk_pair_fail==pairfail_count and disk_clearance_fail==clearancefail_count;M("MC07_COUNT_CROSSCHECK","summary equals CSV recomputation",f"overlap={overlap}; clip={clip}; font_fail={len(ff)}; pixel_fail={len(pf)}; relation_fail={disk_relation_fail}; pair_fail={disk_pair_fail}; clearance_fail={disk_clearance_fail}",countok,"strict_audit_summary.json;after_overlap_report.csv;pair_universe.csv;after_*.csv")
 clearance_pair_ok=(relationfail_count==pairfail_count==clearancefail_count==disk_relation_fail==disk_pair_fail==disk_clearance_fail and hard["CLEARANCE_PASS"]==(clearancefail_count==0))
 M("MC08_CLEARANCE_PAIR_CROSSCHECK","raw relation failures, exhaustive pair universe and clearance hard gate agree",f"relation_fail={disk_relation_fail}; pair_fail={disk_pair_fail}; clearance_fail={disk_clearance_fail}; clearance_pass={hard['CLEARANCE_PASS']}",clearance_pair_ok,"after_overlap_report.csv;pair_universe.csv;strict_audit_summary.json")
 disk_summary=json.loads((OUT/"strict_audit_summary.json").read_text(encoding="utf-8"));disk_eight=list(csv.DictReader((OUT/"strict_eight_column_report.csv").open(encoding="utf-8-sig",newline="")));disk_accept=(OUT/"SA1_RESULT.md").read_text(encoding="utf-8");disk_visual=(OUT/"after_visual_acceptance.md").read_text(encoding="utf-8")
 r12=next((r for r in disk_eight if r["CHECK_ID"]=="R12"),{});r19=next((r for r in disk_eight if r["CHECK_ID"]=="R19"),{})
 bottom_ok=(disk_summary["hard_gates"]["RELATION_FAILURE_COUNT"]==relationfail_count and disk_summary["hard_gates"]["PAIR_UNIVERSE_FAILURE_COUNT"]==pairfail_count and disk_summary["hard_gates"]["CLEARANCE_FAILURE_COUNT"]==clearancefail_count and disk_summary["hard_gates"]["CLEARANCE_PASS"]==clearanceok and disk_summary["result"]==hard["FINAL_RESULT"] and r12.get("STATUS")==("PASS" if clearanceok else "FAIL") and r19.get("OBSERVED")==hard["FINAL_RESULT"] and f"RESULT: {hard['FINAL_RESULT']}" in disk_accept and f"NEXT_ROLE: {hard['NEXT_ROLE']}" in disk_accept and f"{relationfail_count} / {pairfail_count} / {clearancefail_count}" in disk_accept and disk_visual==disk_accept)
 M("MC09_BOTTOM_SUMMARY_CROSSCHECK","bottom CSV/JSON/Markdown summaries carry identical failure counts and result",f"relation_fail={relationfail_count}; pair_fail={pairfail_count}; clearance_fail={clearancefail_count}; result={hard['FINAL_RESULT']}",bottom_ok,"strict_audit_summary.json;strict_eight_column_report.csv;SA1_RESULT.md;after_visual_acceptance.md")
 M("MC10_FINAL_RESULT","result equals conjunction of hard gates",f"expected={'PASS' if final else 'FAIL'}; summary={hard['FINAL_RESULT']}",hard["FINAL_RESULT"]==("PASS" if final else "FAIL"),"strict_audit_summary.json")
 integrity=all(r["STATUS"]=="PASS" for r in machine);ms={"audit_id":"FIG-P570-01/STRICT_R1/SA1_20260824_R1","machine_evidence_integrity_pass":integrity,"quality_result":hard["FINAL_RESULT"],"checks":machine};writecsv(OUT/"machine_terminal_check.csv",machine);write(OUT/"machine_terminal_check.json",json.dumps(ms,ensure_ascii=False,indent=2));write(OUT/"machine_terminal_check.md","# FIG-P570-01｜机器终检\n\n"+f"EVIDENCE_INTEGRITY: {'PASS' if integrity else 'FAIL'}\n\nQUALITY_RESULT: {hard['FINAL_RESULT']}\n\n"+"\n".join(f"- {r['CHECK_ID']}: {r['STATUS']} — {r['OBSERVED']}" for r in machine)+"\n")
 hard["MACHINE_EVIDENCE_INTEGRITY_PASS"]=integrity;summary["machine_terminal_check"]={"integrity_pass":integrity,"csv":"machine_terminal_check.csv","json":"machine_terminal_check.json"};write(OUT/"strict_audit_summary.json",json.dumps(summary,ensure_ascii=False,indent=2));report("R20","MACHINE_FINAL","machine_terminal_check.csv/json","evidence integrity","all true",f"integrity={integrity}; quality={hard['FINAL_RESULT']}",integrity);writecsv(OUT/"strict_eight_column_report.csv",eight);write(OUT/"SA1_RESULT.md",accept+f"\n机器终检：`MACHINE_EVIDENCE_INTEGRITY_PASS={str(integrity).lower()}`；仅确认取证闭合，质量结论仍为 `{hard['FINAL_RESULT']}`。\n");write(OUT/"after_visual_acceptance.md",(OUT/"SA1_RESULT.md").read_text(encoding="utf-8"))

if __name__=="__main__":
 # One audit directory is one writer.  A concurrent rerun would otherwise
 # interleave CSV/JSON writes and create exactly the kind of false machine
 # closure this strict review is meant to catch.
 lock=OUT/".p570_sa1_audit.lock"
 try:
  fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY)
 except FileExistsError:
  raise SystemExit(f"another FIG-P570-01 SA1 audit writer holds {lock}")
 try:
  os.write(fd,f"pid={os.getpid()}\n".encode())
  main()
 finally:
  os.close(fd)
  try:lock.unlink()
  except FileNotFoundError:pass
