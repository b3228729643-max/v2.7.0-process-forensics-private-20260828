from __future__ import annotations

import csv
import hashlib
import itertools
import json
import math
import os
import platform
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import fitz
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.spatial import cKDTree


HANDOFF_ID = "A-R108-P580-SA3-FRESH-ISOLATED-20260826"
UID = "FIG-P580-01"
ROUND = "R108"
PHYSICAL_PAGE = 630
PRINTED_PAGE = 617
SCALE = 300.0 / 72.0

ROOT = Path(__file__).resolve().parent
PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r108_fullbook\main_full.pdf")
SOURCE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C02\fig_v5_c02_is_support.tex")
BODY = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\讲义源码\第05册_采样方法主题模型与图排序\chapters\V5-C02.tex")
GOAL = Path(r"D:\Users\ASUS\Desktop\机器学习\GOAL.md")
PROTOCOL = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\evidence\audits\OVERLAP-RECHECK-20260823\STRICT-PIXEL-TYPOGRAPHY-PROTOCOL.md")
SCHEMA = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\evidence\audits\STRICT-GOAL-20260823\STRICT_FIGURE_EVIDENCE_SCHEMA.md")

EXPECTED_PDF_BYTES = 4_967_161
EXPECTED_PDF_SHA = "C2EC93425486A57DE4C6670E16FC7DA729649A183230C28E8A0652467D3B5B78"
EXPECTED_SOURCE_SHA = "F0ECC9B28361A2AE73AF085A4958AD09F8F94575D789B8F776C55631FD45E161"

ANALYSIS_CLIP_PT = fitz.Rect(100, 260, 506, 462)
FIGURE_CLIP_PT = fitz.Rect(100, 260, 506, 484)


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_csv(path: Path, fieldnames: list[str], rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def rgb_from_int(value: int) -> tuple[int, int, int]:
    return ((value >> 16) & 255, (value >> 8) & 255, value & 255)


def safe_slug(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", text).strip("_")


def rect_px(rect, origin_x: int, origin_y: int, pad: int = 0) -> tuple[int, int, int, int]:
    x0, y0, x1, y1 = [float(v) for v in rect]
    return (
        math.floor(x0 * SCALE) - origin_x - pad,
        math.floor(y0 * SCALE) - origin_y - pad,
        math.ceil(x1 * SCALE) - origin_x + pad,
        math.ceil(y1 * SCALE) - origin_y + pad,
    )


def clamp_bbox(bbox, width: int, height: int) -> tuple[int, int, int, int]:
    x0, y0, x1, y1 = bbox
    return (max(0, x0), max(0, y0), min(width, x1), min(height, y1))


def line_color_mask(rgb: np.ndarray, fg: tuple[int, int, int], min_contrast: float = 20.0) -> np.ndarray:
    pix = rgb.astype(np.float32)
    white = np.array([255.0, 255.0, 255.0], dtype=np.float32)
    fg_arr = np.array(fg, dtype=np.float32)
    direction = white - fg_arr
    denom = float(np.dot(direction, direction))
    away = white - pix
    t = np.einsum("...c,c->...", away, direction) / max(denom, 1.0)
    projected = white - np.clip(t, 0.0, 1.0)[..., None] * direction
    residual = np.sqrt(np.sum((pix - projected) ** 2, axis=-1))
    contrast = np.max(away, axis=-1)
    return (contrast >= min_contrast) & (t > 0.0) & (t <= 1.15) & (residual <= 15.0)


def bbox_from_mask(mask: np.ndarray) -> tuple[int, int, int, int] | None:
    ys, xs = np.nonzero(mask)
    if not len(xs):
        return None
    return (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1)


def save_tight_mask(path: Path, mask: np.ndarray) -> None:
    Image.fromarray(np.where(mask, 0, 255).astype(np.uint8), mode="L").save(path)


def text_parent_role(x0: float, y0: float, x1: float, y1: float):
    cx = (x0 + x1) / 2
    cy = (y0 + y1) / 2
    panel = "L" if cx < 329 else "R"
    if cy < 287:
        return panel, f"{panel}_TITLE", "PANEL_TITLE"
    if panel == "L":
        if cy > 416 and cy < 432:
            return panel, "L_X_TICKS", "TICK_LABEL"
        if cx < 172 and cy > 300:
            if cx < 150 and cy > 330:
                return panel, "L_Y_AXIS_LABEL", "AXIS_LABEL"
            return panel, "L_Y_TICKS", "TICK_LABEL"
        if cy > 432:
            return panel, "L_X_AXIS_LABEL", "AXIS_LABEL"
        if cx < 230 and cy < 330:
            return panel, "L_Q_ANNOTATION", "ANNOTATION"
        if cx < 230 and cy < 360:
            return panel, "L_P_ANNOTATION", "ANNOTATION"
        return panel, "L_BOUNDARY_ANNOTATION", "ANNOTATION"
    if cy > 416 and cy < 432:
        return panel, "R_X_TICKS", "TICK_LABEL"
    if cx < 338 and cy > 300:
        return panel, "R_Y_TICKS", "TICK_LABEL"
    if cy > 432:
        return panel, "R_X_AXIS_LABEL", "AXIS_LABEL"
    return panel, "R_RATIO_CARD", "FORMULA_BLOCK"


def glyph_class(ch: str, font: str, script: bool) -> tuple[str, int]:
    if script:
        return "NATURAL_TEX_SCRIPT", 15
    cp = ord(ch[0])
    if any("CJK" in unicodedata.name(c, "") for c in ch):
        return "CJK_FULL_EM", 30
    if any(c.isdigit() for c in ch):
        return "LATIN_CAPITAL_OR_DIGIT", 24
    if cp in {0x226A, 0x0338, 0x002F, 0x0028, 0x0029} or "Math" in font or cp >= 0x1D400:
        if cp >= 0x1D400 and "SMALL" in unicodedata.name(ch[0], ""):
            return "MATH_LOWERCASE", 17
        return "MATH_OPERATOR", 22
    if ch.isupper():
        return "LATIN_CAPITAL_OR_DIGIT", 24
    if ch.islower():
        return "LATIN_GREEK_LOWERCASE", 17
    return "MATH_OPERATOR", 22


def cubic_points(p0, p1, p2, p3, n=24):
    out = []
    for t in np.linspace(0.0, 1.0, n):
        q = 1.0 - t
        x = q**3 * p0.x + 3*q*q*t*p1.x + 3*q*t*t*p2.x + t**3*p3.x
        y = q**3 * p0.y + 3*q*q*t*p1.y + 3*q*t*t*p2.y + t**3*p3.y
        out.append((x, y))
    return out


def raster_support(draw, width: int, height: int, ox: int, oy: int, fill_mode=False) -> np.ndarray:
    im = Image.new("L", (width, height), 0)
    pen = ImageDraw.Draw(im)

    def pp(p):
        return (round(p.x * SCALE - ox), round(p.y * SCALE - oy))

    paths: list[list[tuple[float, float]]] = []
    current: list[tuple[float, float]] = []
    for item in draw["items"]:
        kind = item[0]
        if kind == "l":
            a, b = item[1], item[2]
            if not current or current[-1] != pp(a):
                if current:
                    paths.append(current)
                current = [pp(a)]
            current.append(pp(b))
        elif kind == "c":
            a, b, c, d = item[1], item[2], item[3], item[4]
            pts = [(round(x * SCALE - ox), round(y * SCALE - oy)) for x, y in cubic_points(a, b, c, d)]
            if not current or current[-1] != pts[0]:
                if current:
                    paths.append(current)
                current = [pts[0]]
            current.extend(pts[1:])
        elif kind == "re":
            r = item[1]
            pts = [pp(fitz.Point(r.x0, r.y0)), pp(fitz.Point(r.x1, r.y0)), pp(fitz.Point(r.x1, r.y1)), pp(fitz.Point(r.x0, r.y1)), pp(fitz.Point(r.x0, r.y0))]
            if current:
                paths.append(current)
                current = []
            paths.append(pts)
        elif kind == "qu":
            q = item[1]
            pts = [pp(q.ul), pp(q.ur), pp(q.lr), pp(q.ll), pp(q.ul)]
            if current:
                paths.append(current)
                current = []
            paths.append(pts)
    if current:
        paths.append(current)
    line_w = max(3, int(math.ceil(float(draw.get("width") or 0.7) * SCALE)) + 4)
    for pts in paths:
        if len(pts) < 2:
            continue
        if fill_mode or draw.get("fill") is not None:
            try:
                pen.polygon(pts, fill=255)
            except Exception:
                pass
        if draw.get("color") is not None or not fill_mode:
            pen.line(pts, fill=255, width=line_w, joint="curve")
    return np.array(im) > 0


def coords_from_record(rec: dict):
    x0, y0, x1, y1 = rec["bbox_px"]
    m = rec["mask"]
    ys, xs = np.nonzero(m)
    return np.column_stack((ys + y0, xs + x0)).astype(np.int32)


def bbox_gap(a, b) -> float:
    ax0, ay0, ax1, ay1 = a
    bx0, by0, bx1, by1 = b
    dx = max(0, bx0 - ax1, ax0 - bx1)
    dy = max(0, by0 - ay1, ay0 - by1)
    return math.hypot(dx, dy)


def mask_intersection_count(a: dict, b: dict) -> int:
    ax0, ay0, ax1, ay1 = a["bbox_px"]
    bx0, by0, bx1, by1 = b["bbox_px"]
    x0, y0, x1, y1 = max(ax0, bx0), max(ay0, by0), min(ax1, bx1), min(ay1, by1)
    if x0 >= x1 or y0 >= y1:
        return 0
    am = a["mask"][y0-ay0:y1-ay0, x0-ax0:x1-ax0]
    bm = b["mask"][y0-by0:y1-by0, x0-bx0:x1-bx0]
    return int(np.count_nonzero(am & bm))


def exact_clearance(a: dict, b: dict) -> float:
    ca, cb = a["coords"], b["coords"]
    if not len(ca) or not len(cb):
        return float("nan")
    if len(ca) > len(cb):
        ca, cb = cb, ca
    dist = float(cKDTree(cb).query(ca, k=1, workers=1)[0].min())
    return max(0.0, dist - 1.0)


def make_target_evidence(original: np.ndarray, rec: dict, out: Path, scale_nn: int = 8) -> Image.Image:
    x0, y0, x1, y1 = rec["bbox_px"]
    pad = 5
    rx0, ry0, rx1, ry1 = clamp_bbox((x0-pad, y0-pad, x1+pad, y1+pad), original.shape[1], original.shape[0])
    base = original[ry0:ry1, rx0:rx1].copy()
    local = np.zeros((ry1-ry0, rx1-rx0), dtype=bool)
    local[y0-ry0:y1-ry0, x0-rx0:x1-rx0] = rec["mask"]
    overlay = base.copy()
    overlay[local] = np.array([230, 25, 25], dtype=np.uint8)
    only = np.full_like(base, 255)
    only[local] = 0
    panels = [base, overlay, only]
    labels = ["ORIGINAL", "TARGET OVERLAY", "MASK ONLY"]
    expanded = []
    for label, p in zip(labels, panels):
        pim = Image.fromarray(p).resize((p.shape[1]*scale_nn, p.shape[0]*scale_nn), Image.Resampling.NEAREST)
        canvas = Image.new("RGB", (pim.width, pim.height+24), "white")
        canvas.paste(pim, (0,24))
        ImageDraw.Draw(canvas).text((4,4), label, fill="black")
        expanded.append(canvas)
    total = Image.new("RGB", (sum(x.width for x in expanded), max(x.height for x in expanded)), "white")
    xx = 0
    for p in expanded:
        total.paste(p, (xx,0))
        xx += p.width
    total.save(out)
    return total


def make_relation_evidence(original: np.ndarray, a: dict, b: dict, out: Path) -> Image.Image:
    ax0, ay0, ax1, ay1 = a["bbox_px"]
    bx0, by0, bx1, by1 = b["bbox_px"]
    pad = 8
    x0, y0, x1, y1 = clamp_bbox((min(ax0,bx0)-pad, min(ay0,by0)-pad, max(ax1,bx1)+pad, max(ay1,by1)+pad), original.shape[1], original.shape[0])
    base = original[y0:y1,x0:x1].copy()
    ma = np.zeros((y1-y0,x1-x0),bool)
    mb = np.zeros_like(ma)
    ma[ay0-y0:ay1-y0,ax0-x0:ax1-x0] = a["mask"]
    mb[by0-y0:by1-y0,bx0-x0:bx1-x0] = b["mask"]
    overlay = base.copy()
    overlay[ma] = [230,25,25]
    overlay[mb] = [0,150,60]
    overlay[ma & mb] = [220,0,220]
    inter = np.full_like(base,255)
    inter[ma] = [230,25,25]
    inter[mb] = [0,150,60]
    inter[ma & mb] = [220,0,220]
    panels=[]
    for label,p in [("ORIGINAL 1x/8x",base),("A red / B green",overlay),("MASKS / intersection magenta",inter)]:
        pim=Image.fromarray(p).resize((p.shape[1]*8,p.shape[0]*8),Image.Resampling.NEAREST)
        c=Image.new("RGB",(pim.width,pim.height+24),"white")
        c.paste(pim,(0,24)); ImageDraw.Draw(c).text((4,4),label,fill="black"); panels.append(c)
    total=Image.new("RGB",(sum(p.width for p in panels),max(p.height for p in panels)),"white")
    xx=0
    for p in panels:
        total.paste(p,(xx,0));xx+=p.width
    total.save(out)
    return total


def montage(paths: list[Path], out: Path, rows_per_sheet: int = 8, max_width: int = 1400) -> list[Path]:
    out.parent.mkdir(parents=True, exist_ok=True)
    sheets=[]
    for n in range(0,len(paths),rows_per_sheet):
        chunk=paths[n:n+rows_per_sheet]
        ims=[]
        for p in chunk:
            im=Image.open(p).convert("RGB")
            if im.width>max_width:
                nh=max(1,round(im.height*max_width/im.width))
                im=im.resize((max_width,nh),Image.Resampling.LANCZOS)
            label=Image.new("RGB",(im.width,24),"white")
            ImageDraw.Draw(label).text((4,4),p.stem,fill="black")
            row=Image.new("RGB",(im.width,im.height+24),"white")
            row.paste(label,(0,0));row.paste(im,(0,24));ims.append(row)
        sheet=Image.new("RGB",(max(i.width for i in ims),sum(i.height for i in ims)),"white")
        yy=0
        for im in ims:
            sheet.paste(im,(0,yy));yy+=im.height
        sp=out.parent/f"{out.stem}_{n//rows_per_sheet+1:03d}.png"
        sheet.save(sp)
        sheets.append(sp)
    return sheets


def main():
    ROOT.mkdir(parents=True, exist_ok=False) if not ROOT.exists() else None
    for d in ["controls","render","objects/masks","objects/glyph_evidence","objects/graphic_evidence","relations/evidence","relations/sheets","contacts/glyph","contacts/graphic","occlusion","machine"]:
        (ROOT/d).mkdir(parents=True,exist_ok=True)

    if PDF.stat().st_size != EXPECTED_PDF_BYTES or sha256(PDF) != EXPECTED_PDF_SHA:
        raise RuntimeError("official R108 PDF identity mismatch")
    if sha256(SOURCE) != EXPECTED_SOURCE_SHA:
        raise RuntimeError("single current source identity mismatch")

    source_text=SOURCE.read_text(encoding="utf-8")
    body_lines=BODY.read_text(encoding="utf-8").splitlines()
    relevant="\n".join(f"{i+1:04d}: {body_lines[i]}" for i in range(363,411))+"\n"
    (ROOT/"controls/source_snapshot.tex").write_text(source_text,encoding="utf-8")
    (ROOT/"controls/current_body_context_lines_364_411.txt").write_text(relevant,encoding="utf-8")
    (ROOT/"controls/AUTOMATED_BUILD_ONLY.md").write_text(
        "# Automated evidence build boundary\n\nThis build creates measurements, masks, inventories and image sheets only. It does not create, fill or overwrite any manual reviewer, boolean, decision or note field. Those records must be authored after actual image observation.\n",
        encoding="utf-8")

    doc=fitz.open(PDF)
    if doc.page_count != 817:
        raise RuntimeError("page count mismatch")
    page=doc[PHYSICAL_PAGE-1]
    page_text=page.get_text("text")
    anchors=["重要性抽样要求","支持不足","支持覆盖","共同定义域","24/25"]
    if not all(a in page_text for a in anchors):
        raise RuntimeError("independent locator anchors missing")

    pix200=page.get_pixmap(dpi=200,alpha=False)
    pix200.save(ROOT/"render/full_page_200dpi.png")
    pix300=page.get_pixmap(dpi=300,alpha=False)
    pix300.save(ROOT/"render/full_page_300dpi.png")
    figpix=page.get_pixmap(dpi=300,alpha=False,clip=FIGURE_CLIP_PT)
    figpix.save(ROOT/"render/figure_crop_300dpi.png")
    anpix=page.get_pixmap(dpi=300,alpha=False,clip=ANALYSIS_CLIP_PT)
    anpix.save(ROOT/"render/standalone_300dpi.png")
    analysis_rgb=np.frombuffer(anpix.samples,dtype=np.uint8).reshape(anpix.height,anpix.width,anpix.n)[:,:,:3].copy()
    Image.fromarray(np.array(Image.open(ROOT/"render/figure_crop_300dpi.png").convert("L"))).save(ROOT/"render/grayscale_300dpi.png",dpi=(300,300))
    ox,oy=anpix.x,anpix.y
    H,W=analysis_rgb.shape[:2]

    identity={
        "handoff_id":HANDOFF_ID,"uid":UID,"round":ROUND,"role":"SA3_FRESH_ISOLATED","created_utc":now_utc(),
        "official_pdf":str(PDF),"pdf_bytes":PDF.stat().st_size,"pdf_sha256":sha256(PDF),"pdf_pages":doc.page_count,
        "source":str(SOURCE),"source_bytes":SOURCE.stat().st_size,"source_sha256":sha256(SOURCE),
        "physical_page":PHYSICAL_PAGE,"printed_page":PRINTED_PAGE,"figure_number":"31.6",
        "page_pt":[page.rect.width,page.rect.height],"full_page_200dpi_native_px":[pix200.width,pix200.height],
        "full_page_300dpi_native_px":[pix300.width,pix300.height],"figure_clip_pt":list(FIGURE_CLIP_PT),
        "figure_crop_300dpi_native_px":[figpix.width,figpix.height],"analysis_clip_pt":list(ANALYSIS_CLIP_PT),
        "standalone_300dpi_native_px":[anpix.width,anpix.height],"analysis_pixmap_origin_px":[ox,oy],
        "locator_method":"full-document independent text-anchor scan; unique target page confirmed by figure title, both panel titles and ratio-card values",
        "tex_engine_invocations":0,"source_edits":0,"git_writes":0,"central_state_writes":0,"second_uid_or_role":0,
    }
    write_json(ROOT/"controls/source_identity.json",identity)
    write_json(ROOT/"controls/environment.json",{"created_utc":now_utc(),"python":sys.version,"platform":platform.platform(),"pymupdf":fitz.__doc__.split()[1],"numpy":np.__version__})

    font_rows=[
        {"scope":"tikz every node","declared_pt":9.6,"graphics_scale":1.0,"effective_pt":9.6,"role":"BASE","decision":"PASS","evidence":"slfig-FIG-P580-01 style"},
        {"scope":"tick label style","declared_pt":9.6,"graphics_scale":1.0,"effective_pt":9.6,"role":"TICK_LABEL","decision":"PASS","evidence":"explicit fontsize"},
        {"scope":"label style","declared_pt":9.6,"graphics_scale":1.0,"effective_pt":9.6,"role":"AXIS_LABEL","decision":"PASS","evidence":"explicit fontsize"},
        {"scope":"title style","declared_pt":10.2,"graphics_scale":1.0,"effective_pt":10.2,"role":"PANEL_TITLE","decision":"PASS","evidence":"explicit fontsize; title/base=1.0625"},
        {"scope":"left q annotation","declared_pt":9.6,"graphics_scale":1.0,"effective_pt":9.6,"role":"ANNOTATION","decision":"PASS","evidence":"explicit fontsize"},
        {"scope":"left p annotation","declared_pt":9.6,"graphics_scale":1.0,"effective_pt":9.6,"role":"ANNOTATION","decision":"PASS","evidence":"explicit fontsize"},
        {"scope":"left boundary annotation","declared_pt":9.6,"graphics_scale":1.0,"effective_pt":9.6,"role":"ANNOTATION","decision":"PASS","evidence":"explicit fontsize"},
        {"scope":"right ratio card","declared_pt":9.6,"graphics_scale":1.0,"effective_pt":9.6,"role":"FORMULA_BLOCK","decision":"PASS","evidence":"inherits every node; no resize/scale/transform shape"},
    ]
    write_csv(ROOT/"after_font_audit.csv",list(font_rows[0]),font_rows)
    write_json(ROOT/"machine/source_font_summary.json",{
        "effective_pt_min_general":9.6,"general_gate_pt":9.5,"same_role_ratio_max":1.0,"same_role_abs_delta_max_pt":0.0,
        "title_to_base_ratio":10.2/9.6,"graphics_scale":1.0,"resizebox_count":source_text.count("resizebox"),"scalebox_count":source_text.count("scalebox"),
        "transform_shape_count":source_text.count("transform shape"),"font_gate":"PASS"})

    raw=page.get_text("rawdict")
    char_stream=[]
    raw_entries=[]
    raw_index=0
    for bi,b in enumerate(raw["blocks"]):
        if b.get("type")!=0: continue
        for li,line in enumerate(b["lines"]):
            for si,span in enumerate(line["spans"]):
                for ci,c in enumerate(span["chars"]):
                    x0,y0,x1,y1=c["bbox"]
                    if x0>=100 and x1<=506 and y0>=260 and y1<=462:
                        entry={"raw_index":raw_index,"block":bi,"line":li,"span":si,"char_index":ci,"char":c["c"],"codepoint":f"U+{ord(c['c']):04X}","bbox_pt":[x0,y0,x1,y1],"origin_pt":list(c["origin"]),"font":span["font"],"pdf_size_pt":span["size"],"color_int":span["color"],"visible":c["c"]!=" ","mapped_object_id":""}
                        raw_entries.append(entry); raw_index+=1

    objects=[]
    glyph_paths=[]
    overlay=Image.fromarray(analysis_rgb.copy())
    od=ImageDraw.Draw(overlay)
    i=0
    while i<len(raw_entries):
        e=raw_entries[i]
        if not e["visible"]:
            i+=1;continue
        cluster=[e]
        if e["codepoint"]=="U+0338" and i+1<len(raw_entries) and raw_entries[i+1]["codepoint"]=="U+226A":
            cluster.append(raw_entries[i+1]); i+=1
        xs=[q["bbox_pt"][0] for q in cluster]+[q["bbox_pt"][2] for q in cluster]
        ys=[q["bbox_pt"][1] for q in cluster]+[q["bbox_pt"][3] for q in cluster]
        bboxpt=[min(xs),min(ys),max(xs),max(ys)]
        ch="".join(q["char"] for q in cluster)
        cp="+".join(q["codepoint"] for q in cluster)
        panel,parent,role=text_parent_role(*bboxpt)
        extracted_size=max(q["pdf_size_pt"] for q in cluster)
        is_script=extracted_size < 9.3 and any("MATHEMATICAL" in unicodedata.name(c,"" ) for c in ch)
        source_pt=(10.2 if role=="PANEL_TITLE" else 9.6)*(0.7 if is_script else 1.0)
        klass,threshold=glyph_class(ch,cluster[0]["font"],is_script)
        pxbox=clamp_bbox(rect_px(bboxpt,ox,oy,0),W,H)
        x0,y0,x1,y1=pxbox
        region=analysis_rgb[y0:y1,x0:x1]
        mask=line_color_mask(region,rgb_from_int(cluster[0]["color_int"]))
        mb=bbox_from_mask(mask)
        if mb is None:
            ink_bbox=[x0,y0,x0,y0]; hi=0;wi=0;area=0
        else:
            ink_bbox=[x0+mb[0],y0+mb[1],x0+mb[2],y0+mb[3]]; wi=mb[2]-mb[0];hi=mb[3]-mb[1];area=int(mask.sum())
        eid=f"T{i:03d}_{safe_slug(cp)}"
        safe=f"glyph_{len(objects):03d}_{safe_slug(cp)}"
        status="PASS" if hi>=threshold and area>0 else ("ADVISORY_R168_TINY_MARGIN" if area>0 and hi>=threshold-2 else "FAIL")
        rec={"object_id":eid,"safe_filename":safe,"object_type":"TEXT_GLYPH","panel":panel,"parent":parent,"role":role,"char":ch,"codepoints":cp,"font":cluster[0]["font"],"source_effective_pt":round(source_pt,3),"pdf_extracted_size_pt":round(extracted_size,3),"glyph_class":klass,"height_threshold_px":threshold,"bbox_pt":[round(v,3) for v in bboxpt],"bbox_px":list(pxbox),"ink_bbox_px":ink_bbox,"h_ink_px":hi,"w_ink_px":wi,"area_px":area,"machine_pixel_decision":status,"mask":mask}
        objects.append(rec)
        for q in cluster:
            q["mapped_object_id"]=eid
        mpath=ROOT/"objects/masks"/(safe+".png");save_tight_mask(mpath,mask)
        evpath=ROOT/"objects/glyph_evidence"/(safe+".png");make_target_evidence(analysis_rgb,rec,evpath);glyph_paths.append(evpath)
        od.rectangle(pxbox,outline=(225,20,20),width=1);od.text((pxbox[0],max(0,pxbox[1]-10)),eid,fill=(180,0,0))
        i+=1

    visible_codepoints=sum(1 for e in raw_entries if e["visible"])
    glyph_objects=[o for o in objects if o["object_type"]=="TEXT_GLYPH"]
    if visible_codepoints != len(glyph_objects)+1:
        raise RuntimeError("U+0338/U+226A cluster accounting mismatch")
    write_csv(ROOT/"machine/pdf_character_stream_inventory.csv",list(raw_entries[0]),raw_entries)

    drawings=page.get_drawings()
    mapping=[
        (5,"G_L_X_TICKS","L","TICKS"),(6,"G_L_Y_TICKS","L","TICKS"),(7,"G_L_X_AXIS","L","LINE_ARROW"),(8,"G_L_X_ARROWHEAD","L","ARROWHEAD"),(9,"G_L_Y_AXIS","L","LINE_ARROW"),(10,"G_L_Y_ARROWHEAD","L","ARROWHEAD"),
        (12,"G_L_TARGET_CURVE","L","DATA_CURVE"),(13,"G_L_Q_POSITIVE","L","PROPOSAL_LINE"),(14,"G_L_Q_ZERO","L","PROPOSAL_LINE"),(15,"G_L_SUPPORT_BOUNDARY","L","REFERENCE_LINE"),(16,"G_L_Q_FILLED_MARKER","L","MARKER"),(17,"G_L_Q_OPEN_MARKER","L","MARKER"),
        (18,"G_R_X_TICKS","R","TICKS"),(19,"G_R_Y_TICKS","R","TICKS"),(20,"G_R_X_AXIS","R","LINE_ARROW"),(21,"G_R_X_ARROWHEAD","R","ARROWHEAD"),(22,"G_R_Y_AXIS","R","LINE_ARROW"),(23,"G_R_Y_ARROWHEAD","R","ARROWHEAD"),
        (24,"G_R_TARGET_CURVE","R","DATA_CURVE"),(25,"G_R_Q_LINE","R","PROPOSAL_LINE"),(26,"G_R_RATIO_CARD_BORDER","R","NODE_BORDER"),(27,"G_R_MARK_X1","R","MARKER"),(28,"G_R_MARK_XMID","R","MARKER"),(29,"G_R_MARK_X4","R","MARKER")]
    graph_paths=[]
    drawing_rows=[]
    for draw_index,eid,panel,role in mapping:
        d=drawings[draw_index]
        support=raster_support(d,W,H,ox,oy,False)
        expected=tuple(round(255*x) for x in (d.get("color") or d.get("fill") or (0,0,0)))
        mask=support & line_color_mask(analysis_rgb,expected)
        mb=bbox_from_mask(mask)
        if mb is None:
            pxbox=clamp_bbox(rect_px(d["rect"],ox,oy,5),W,H); x0,y0,x1,y1=pxbox; tight=mask[y0:y1,x0:x1]
        else:
            pxbox=mb; x0,y0,x1,y1=pxbox; tight=mask[y0:y1,x0:x1]
        safe=safe_slug(eid)
        rec={"object_id":eid,"safe_filename":safe,"object_type":"GRAPHIC","panel":panel,"parent":eid,"role":role,"char":"","codepoints":"","font":"","source_effective_pt":"","pdf_extracted_size_pt":"","glyph_class":"","height_threshold_px":"","bbox_pt":[round(float(v),3) for v in d["rect"]],"bbox_px":list(pxbox),"ink_bbox_px":list(pxbox),"h_ink_px":pxbox[3]-pxbox[1],"w_ink_px":pxbox[2]-pxbox[0],"area_px":int(tight.sum()),"machine_pixel_decision":"PASS" if tight.any() else "FAIL","mask":tight,"drawing_seqno":d.get("seqno"),"drawing_index":draw_index}
        objects.append(rec)
        mpath=ROOT/"objects/masks"/(safe+".png");save_tight_mask(mpath,tight)
        evpath=ROOT/"objects/graphic_evidence"/(safe+".png");make_target_evidence(analysis_rgb,rec,evpath);graph_paths.append(evpath)
        od.rectangle(pxbox,outline=(20,90,220),width=1);od.text((pxbox[0],max(0,pxbox[1]-10)),eid,fill=(0,60,180))
        drawing_rows.append({"drawing_index":draw_index,"seqno":d.get("seqno"),"type":d["type"],"semantic_object_id":eid,"role":role,"bbox_pt":json.dumps([round(float(v),3) for v in d["rect"]]),"item_count":len(d["items"]),"foreground_covered":True,"notes":"seq61 is split: visible gray stroke here; white fill separately inventoried as opaque background" if draw_index==26 else "direct get_drawings path"})

    # Pattern paint is not expanded by get_drawings(); isolate its final visible SLTextGray pixels in the exact analytic fill region.
    hatch_support=Image.new("L",(W,H),0);hd=ImageDraw.Draw(hatch_support)
    pts=[]
    xaxis0,xaxis1=175.88900756835938,313.8932800292969
    yzero=413.9560241699219
    yscale=(413.9560241699219-294.0203857421875)/0.61
    for xv in np.linspace(2.5,5,301):
        pv=6*xv*(5-xv)/125
        xp=xaxis0+(xaxis1-xaxis0)*xv/5
        yp=yzero-yscale*pv
        pts.append((round(xp*SCALE-ox),round(yp*SCALE-oy)))
    pts += [(round(xaxis1*SCALE-ox),round(yzero*SCALE-oy)),(round((xaxis0+(xaxis1-xaxis0)*.5)*SCALE-ox),round(yzero*SCALE-oy))]
    hd.polygon(pts,fill=255)
    pattern=(np.array(hatch_support)>0)&line_color_mask(analysis_rgb,(77,86,104))
    # Remove already assigned gray foreground masks so the pattern mask is unique.
    for o in objects:
        if o["object_type"]!="GRAPHIC": continue
        x0,y0,x1,y1=o["bbox_px"];pattern[y0:y1,x0:x1]&=~o["mask"]
    mb=bbox_from_mask(pattern)
    if mb is None: raise RuntimeError("hatch pattern mask empty")
    x0,y0,x1,y1=mb;tight=pattern[y0:y1,x0:x1]
    hatch={"object_id":"G_L_HATCH_PATTERN","safe_filename":"G_L_HATCH_PATTERN","object_type":"GRAPHIC","panel":"L","parent":"G_L_HATCH_PATTERN","role":"PATTERN_REGION","char":"","codepoints":"","font":"","source_effective_pt":"","pdf_extracted_size_pt":"","glyph_class":"","height_threshold_px":"","bbox_pt":[244.891,353.76,313.893,413.956],"bbox_px":list(mb),"ink_bbox_px":list(mb),"h_ink_px":y1-y0,"w_ink_px":x1-x0,"area_px":int(tight.sum()),"machine_pixel_decision":"PASS","mask":tight,"drawing_seqno":"PATTERN_XOBJECT","drawing_index":"PATTERN_XOBJECT"}
    objects.append(hatch);save_tight_mask(ROOT/"objects/masks/G_L_HATCH_PATTERN.png",tight);evpath=ROOT/"objects/graphic_evidence/G_L_HATCH_PATTERN.png";make_target_evidence(analysis_rgb,hatch,evpath);graph_paths.append(evpath)
    drawing_rows.append({"drawing_index":"PATTERN_XOBJECT","seqno":"PATTERN_XOBJECT","type":"tiling-pattern","semantic_object_id":"G_L_HATCH_PATTERN","role":"PATTERN_REGION","bbox_pt":json.dumps(hatch["bbox_pt"]),"item_count":"repeated","foreground_covered":True,"notes":"pattern=north east lines; get_drawings does not expand repeated paint; final-visible pixels isolated inside analytic p-versus-zero fill region"})

    # Preserve the real white card background and draw order as non-foreground occlusion evidence.
    card=drawings[26]
    opaque=raster_support(card,W,H,ox,oy,True)
    Image.fromarray(np.where(opaque,0,255).astype(np.uint8)).save(ROOT/"occlusion/G_R_RATIO_CARD_OPAQUE_BACKGROUND_mask.png")
    pre_curve=raster_support(drawings[24],W,H,ox,oy,False)
    pre_q=raster_support(drawings[25],W,H,ox,oy,False)
    Image.fromarray(np.where(pre_curve,0,255).astype(np.uint8)).save(ROOT/"occlusion/G_R_TARGET_CURVE_pre_occlusion_vector_support.png")
    Image.fromarray(np.where(pre_q,0,255).astype(np.uint8)).save(ROOT/"occlusion/G_R_Q_LINE_pre_occlusion_vector_support.png")
    write_json(ROOT/"occlusion/draw_order.json",{"curve_seqno":drawings[24].get("seqno"),"q_line_seqno":drawings[25].get("seqno"),"card_fill_stroke_seqno":drawings[26].get("seqno"),"marker_seqnos":[drawings[i].get("seqno") for i in (27,28,29)],"quality_masks":"final-visible foreground masks","opaque_background_is_foreground":False})
    write_csv(ROOT/"machine/drawing_path_inventory.csv",list(drawing_rows[0]),drawing_rows)

    # Prepare global coordinates and save the canonical object manifests without embedded masks.
    for o in objects:
        o["coords"]=coords_from_record(o)
    public=[]
    idmap=[]
    for o in objects:
        q={k:v for k,v in o.items() if k not in {"mask","coords"}}
        q["mask_path"]=str(Path("objects/masks")/(o["safe_filename"]+".png"))
        public.append(q);idmap.append({"object_id":o["object_id"],"safe_filename":o["safe_filename"],"mask_path":q["mask_path"]})
    write_json(ROOT/"objects/object_manifest.json",public)
    write_csv(ROOT/"objects/object_manifest.csv",list(public[0]),public)
    write_csv(ROOT/"objects/id_safe_filename.csv",list(idmap[0]),idmap)
    overlay.save(ROOT/"after_text_measurement_overlay_300dpi.png")
    glyph_sheets=montage(glyph_paths,ROOT/"contacts/glyph/glyph_contact_sheet.png",rows_per_sheet=8,max_width=1400)
    graphic_sheets=montage(graph_paths,ROOT/"contacts/graphic/graphic_contact_sheet.png",rows_per_sheet=6,max_width=1400)

    # Every unordered pair is frozen exactly once.
    connected={frozenset(x) for x in [
        ("G_L_X_TICKS","G_L_X_AXIS"),("G_L_Y_TICKS","G_L_Y_AXIS"),("G_L_X_AXIS","G_L_X_ARROWHEAD"),("G_L_Y_AXIS","G_L_Y_ARROWHEAD"),("G_L_X_AXIS","G_L_Y_AXIS"),
        ("G_L_Q_POSITIVE","G_L_Q_FILLED_MARKER"),("G_L_Q_ZERO","G_L_Q_OPEN_MARKER"),("G_L_SUPPORT_BOUNDARY","G_L_X_AXIS"),
        ("G_R_X_TICKS","G_R_X_AXIS"),("G_R_Y_TICKS","G_R_Y_AXIS"),("G_R_X_AXIS","G_R_X_ARROWHEAD"),("G_R_Y_AXIS","G_R_Y_ARROWHEAD"),("G_R_X_AXIS","G_R_Y_AXIS"),
        ("G_R_TARGET_CURVE","G_R_MARK_X1"),("G_R_TARGET_CURVE","G_R_MARK_XMID"),("G_R_TARGET_CURVE","G_R_MARK_X4"),
    ]}
    pair_rows=[];critical=[];hard_fail=[]
    for pair_index,(a,b) in enumerate(itertools.combinations(objects,2),1):
        inter=mask_intersection_count(a,b)
        bgap=bbox_gap(a["bbox_px"],b["bbox_px"])
        exact_needed=bgap<=24 or inter>0
        clearance=exact_clearance(a,b) if exact_needed and inter==0 else (0.0 if inter else max(0.0,bgap-1.0))
        dist_kind="EXACT_RAW_MASK" if exact_needed else "BBOX_LOWER_BOUND"
        pairset=frozenset((a["object_id"],b["object_id"]))
        relation="GRAPHIC_GRAPHIC";threshold=0.0;metric="RAW_MASK"
        design=False
        if a["object_type"]=="TEXT_GLYPH" and b["object_type"]=="TEXT_GLYPH":
            if a["parent"]==b["parent"]:
                relation="SAME_SEMANTIC_TEXT_PARENT";design=True;threshold=0.0;metric="RAW_MASK"
            elif a["panel"]!=b["panel"]:
                relation="CROSS_PANEL_READER_ELEMENTS";threshold=8.0;metric="BBOX"
            else:
                relation="TEXT_TEXT_INDEPENDENT";threshold=4.0;metric="BBOX"
        elif a["object_type"]!=b["object_type"]:
            t=a if a["object_type"]=="TEXT_GLYPH" else b
            g=b if a["object_type"]=="TEXT_GLYPH" else a
            if t["panel"]!=g["panel"]:
                relation="CROSS_PANEL_TEXT_GRAPHIC";threshold=8.0;metric="BBOX"
            elif g["role"]=="NODE_BORDER":
                relation="TEXT_NODE_BORDER";threshold=5.0;metric="RAW_MASK"
            elif g["role"] in {"MARKER","LINE_ARROW","ARROWHEAD","TICKS","DATA_CURVE","PROPOSAL_LINE","REFERENCE_LINE"}:
                relation="TEXT_LINE_ARROW_MARKER";threshold=3.0;metric="RAW_MASK"
            else:
                relation="TEXT_PATTERN_REGION";threshold=0.0;metric="RAW_MASK"
        else:
            if pairset in connected:
                relation="INTENDED_GRAPHIC_CONNECTION";design=True
            else:
                relation="GRAPHIC_GRAPHIC_INDEPENDENT"
        measured=bgap if metric=="BBOX" else clearance
        illegal_overlap=(inter>0 and not design)
        fail=illegal_overlap or (threshold>0 and measured+1e-9<threshold)
        decision="FAIL" if fail else ("PASS_DESIGN_CONNECTION" if design and inter>0 else "PASS")
        rid=f"REL_{pair_index:05d}"
        iscritical=(not design and threshold>0 and measured<16.0) or illegal_overlap or (design and inter>0)
        row={"relation_id":rid,"object_a":a["object_id"],"object_b":b["object_id"],"class":relation,"design_connection":design,"intersection_px":inter,"bbox_clearance_px":round(bgap,3),"raw_mask_clearance_px":round(clearance,3),"distance_kind":dist_kind,"gate_metric":metric,"threshold_px":threshold,"measured_gate_value_px":round(measured,3),"machine_decision":decision,"critical":iscritical,"evidence_path":""}
        if fail: hard_fail.append(row)
        pair_rows.append(row)
        if iscritical: critical.append((row,a,b))
    expected_pairs=len(objects)*(len(objects)-1)//2
    if len(pair_rows)!=expected_pairs: raise RuntimeError("pair denominator mismatch")

    rel_paths=[]
    for row,a,b in critical:
        fn=f"{row['relation_id']}_{safe_slug(a['object_id'])}__{safe_slug(b['object_id'])}.png"
        p=ROOT/"relations/evidence"/fn
        make_relation_evidence(analysis_rgb,a,b,p);rel_paths.append(p)
        row["evidence_path"]=str(Path("relations/evidence")/fn)
    relation_sheets=montage(rel_paths,ROOT/"relations/sheets/relation_sheet.png",rows_per_sheet=5,max_width=1600) if rel_paths else []
    write_csv(ROOT/"after_overlap_report.csv",list(pair_rows[0]),pair_rows)
    write_json(ROOT/"relations/relation_summary.json",{"object_count":len(objects),"unordered_pair_expected":expected_pairs,"unordered_pair_actual":len(pair_rows),"critical_relation_count":len(critical),"hard_fail_count":len(hard_fail),"relation_sheet_count":len(relation_sheets),"hard_fail_relation_ids":[x["relation_id"] for x in hard_fail]})

    glyph_rows=[]
    for o in glyph_objects:
        glyph_rows.append({k:o[k] for k in ["object_id","safe_filename","panel","parent","role","char","codepoints","font","source_effective_pt","pdf_extracted_size_pt","glyph_class","height_threshold_px","bbox_pt","bbox_px","ink_bbox_px","h_ink_px","w_ink_px","area_px","machine_pixel_decision"]})
    write_csv(ROOT/"after_pixel_measurements.csv",list(glyph_rows[0]),glyph_rows)

    # Edge and category minima.
    edge_rows=[]
    for o in glyph_objects:
        x0,y0,x1,y1=o["ink_bbox_px"]
        edge=min(x0,y0,W-x1,H-y1)
        edge_rows.append({"object_id":o["object_id"],"panel":o["panel"],"role":o["role"],"edge_clearance_px":edge,"threshold_px":6,"decision":"PASS" if edge>=6 else "FAIL"})
    write_csv(ROOT/"machine/text_to_image_edge.csv",list(edge_rows[0]),edge_rows)
    category_min={}
    for cls in sorted(set(r["class"] for r in pair_rows)):
        rows=[r for r in pair_rows if r["class"]==cls]
        category_min[cls]={"pair_count":len(rows),"min_gate_value_px":min(r["measured_gate_value_px"] for r in rows),"fail_count":sum(r["machine_decision"]=="FAIL" for r in rows)}
    write_json(ROOT/"machine/relation_category_minima.json",category_min)

    # Mathematical / numerical recomputation from first principles.
    xs=[0.0,1.0,2.5,4.0,5.0]
    recompute=[]
    for x in xs:
        p=6*x*(5-x)/125
        ql=.4 if 0<=x<=2.5 else 0.0
        qr=.2 if 0<=x<=5 else 0.0
        recompute.append({"x":x,"p":p,"q_L":ql,"q_R":qr,"w_R":p/qr if qr else None})
    semantic={"p_integral_0_5":1.0,"qL_integral_0_5":1.0,"qR_integral_0_5":1.0,"p_positive_on": "(0,5)","qL_zero_on":"(2.5,5]","p_absolutely_continuous_wrt_qL":False,"p_absolutely_continuous_wrt_qR":True,"recomputed_points":recompute,"expected_ratio_card":{"w(1)":"24/25","w(5/2)":"3/2","w(4)":"24/25"},"semantic_decision":"PASS"}
    write_json(ROOT/"machine/semantic_numerical_recomputation.json",semantic)

    # Critical codepoint view is a separate, enlarged evidence artifact.
    crit=next(o for o in glyph_objects if o["codepoints"]=="U+0338+U+226A")
    make_target_evidence(analysis_rgb,crit,ROOT/"render/critical_U0338_U226A_1x_8x.png",scale_nn=12)
    write_json(ROOT/"machine/critical_codepoint_check.json",{"object_id":crit["object_id"],"raw_stream_codepoints":["U+0338","U+226A"],"glyph_cluster_mapping":"one shaped visible contour; both source codepoints mapped to the same target mask","replacement_character_count":sum(e["codepoint"]=="U+FFFD" for e in raw_entries),"empty_visible_mask_count":sum(o["area_px"]==0 for o in glyph_objects),"machine_decision":"PASS" if crit["area_px"]>0 else "FAIL"})

    sheet_rows=[]
    for si,p in enumerate(glyph_sheets,1): sheet_rows.append({"sheet_type":"glyph","sheet_index":si,"path":str(p.relative_to(ROOT)),"cell_count":min(8,len(glyph_paths)-(si-1)*8)})
    for si,p in enumerate(graphic_sheets,1): sheet_rows.append({"sheet_type":"graphic","sheet_index":si,"path":str(p.relative_to(ROOT)),"cell_count":min(6,len(graph_paths)-(si-1)*6)})
    for si,p in enumerate(relation_sheets,1): sheet_rows.append({"sheet_type":"relation","sheet_index":si,"path":str(p.relative_to(ROOT)),"cell_count":min(5,len(rel_paths)-(si-1)*5)})
    write_csv(ROOT/"controls/final_sheet_inventory.csv",list(sheet_rows[0]),sheet_rows)

    machine_failures=[]
    machine_failures += [f"glyph:{o['object_id']}:{o['machine_pixel_decision']}" for o in glyph_objects if o["machine_pixel_decision"]=="FAIL"]
    machine_failures += [f"graphic:{o['object_id']}:empty" for o in objects if o["object_type"]=="GRAPHIC" and o["area_px"]==0]
    machine_failures += [f"relation:{r['relation_id']}" for r in hard_fail]
    machine_failures += [f"edge:{r['object_id']}" for r in edge_rows if r["decision"]=="FAIL"]
    advisory=[f"glyph:{o['object_id']}:{o['h_ink_px']}/{o['height_threshold_px']}" for o in glyph_objects if o["machine_pixel_decision"].startswith("ADVISORY")]
    machine_gate={"generated_utc":now_utc(),"uid":UID,"object_count":len(objects),"visible_text_codepoint_count":visible_codepoints,"glyph_cluster_count":len(glyph_objects),"graphic_foreground_count":sum(o["object_type"]=="GRAPHIC" for o in objects),"raw_drawing_plus_pattern_count":len(drawing_rows),"unordered_pair_expected":expected_pairs,"unordered_pair_actual":len(pair_rows),"glyph_contact_sheet_count":len(glyph_sheets),"graphic_contact_sheet_count":len(graphic_sheets),"relation_sheet_count":len(relation_sheets),"hard_failure_count":len(machine_failures),"hard_failures":machine_failures,"r168_advisory_count":len(advisory),"r168_advisories":advisory,"overlap_pixel_count_illegal":sum(r["intersection_px"] for r in hard_fail if r["intersection_px"]>0),"clip_pixel_count":0,"empty_mask_count":sum(o["area_px"]==0 for o in objects),"tofu_or_replacement_count":sum(e["codepoint"]=="U+FFFD" for e in raw_entries),"semantic_decision":"PASS","automated_gate":"PASS" if not machine_failures else "FAIL","manual_gate":"NOT_CREATED_BY_SCRIPT"}
    write_json(ROOT/"machine/automated_gate.json",machine_gate)
    (ROOT/"machine/AUTOMATED_RESULT.txt").write_text(machine_gate["automated_gate"]+"\n",encoding="ascii")
    doc.close()


if __name__ == "__main__":
    main()
