from __future__ import annotations

import csv
import hashlib
import itertools
import json
import math
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

import cv2
import fitz
import numpy as np
from PIL import Image, ImageDraw
from scipy.spatial import cKDTree


sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习")
EV = ROOT / r"v2.7.0\_work\dialogues\C_visual\evidence\FIG-P602-01\sa1_r101_initial"
PDF = ROOT / r"v2.7.0\_work\source\v2.7.0\src\build\strict_current_r101_fullbook\main_full.pdf"
SRC = ROOT / r"v2.7.0\_work\worktrees\dialogue_C_visual\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C03\fig_v5_c03_mh_accept_reject.tex"
PAGE_INDEX = 650
PAGE_NUMBER = 651
BOOK_PAGE = 638
S1 = 300.0 / 72.0
S8 = 2400.0 / 72.0
EVIDENCE_CROP_1X = (220, 1250, 2260, 3300)


TEXT_OBJECTS = {
    "T01": dict(blocks=[(16, None), (17, None)], panel="FLOW", role="STATE_NODE", source_line="17", pt=9.6, text="当前状态 X_t=x"),
    "T02": dict(blocks=[(18, None), (19, None)], panel="FLOW", role="PROPOSAL_NODE", source_line="18", pt=9.6, text="按 q(x,·) 提出候选 Y=y"),
    "T03": dict(blocks=[(20, None)], panel="FLOW", role="RATIO_NODE_LABEL", source_line="19", pt=9.6, text="计算接受率（g(x,y)>0）"),
    "T04": dict(blocks=[(21, None), (22, None)], panel="FLOW", role="FORMULA_BLOCK", source_line="20-22", pt=11.2, text="alpha(x,y)=min{1, pi~(y)q(y,x)/pi~(x)q(x,y)}"),
    "T05": dict(blocks=[(23, None)], panel="FLOW", role="DECISION_NODE", source_line="23", pt=9.6, text="抽取 U~U(0,1) 并判定 U<=alpha(x,y)?"),
    "T06": dict(blocks=[(24, None), (25, None)], panel="FLOW", role="OUTCOME_NODE", source_line="24", pt=9.6, text="接受候选 X_(t+1)=y"),
    "T07": dict(blocks=[(26, None), (27, None)], panel="FLOW", role="OUTCOME_NODE", source_line="25", pt=9.6, text="拒绝并记录旧状态 X_(t+1)=x"),
    "T08": dict(blocks=[(28, None)], panel="FLOW", role="EDGE_LABEL", source_line="27", pt=9.6, text="提议"),
    "T09": dict(blocks=[(29, None)], panel="FLOW", role="EDGE_LABEL", source_line="28", pt=9.6, text="计算"),
    "T10": dict(blocks=[(30, None)], panel="FLOW", role="EDGE_LABEL", source_line="29", pt=9.6, text="判定"),
    "T11": dict(blocks=[(31, 0)], panel="FLOW", role="BRANCH_LABEL", source_line="30", pt=9.6, text="接受"),
    "T12": dict(blocks=[(31, 1)], panel="FLOW", role="BRANCH_LABEL", source_line="31", pt=9.6, text="拒绝"),
    "T13": dict(blocks=[(32, None)], panel="FLOW", role="EDGE_LABEL", source_line="32-33", pt=9.6, text="自环：保留 x"),
    "T14": dict(blocks=[(33, None)], panel="CAPTION", role="CAPTION", source_line="35", pt=10.0, text="图32.5 Metropolis-Hastings 一步更新：提议、接受与拒绝自环。"),
}

VECTOR_OBJECTS = {
    "B01": dict(records=[2], panel="FLOW", role="STATE_BORDER", kind="border", source_line="17"),
    "B02": dict(records=[3], panel="FLOW", role="PROPOSAL_BORDER", kind="border", source_line="18"),
    "B03": dict(records=[4], panel="FLOW", role="RATIO_BORDER", kind="border", source_line="19-22"),
    "B04": dict(records=[6], panel="FLOW", role="DECISION_BORDER", kind="border", source_line="23"),
    "B05": dict(records=[7], panel="FLOW", role="ACCEPT_BORDER", kind="border", source_line="24"),
    "B06": dict(records=[8], panel="FLOW", role="REJECT_BORDER", kind="border", source_line="25"),
    "E01": dict(records=[10, 11], panel="FLOW", role="PROPOSAL_EDGE", kind="edge", source_line="27"),
    "E02": dict(records=[13, 14], panel="FLOW", role="CALC_EDGE", kind="edge", source_line="28"),
    "E03": dict(records=[16, 17], panel="FLOW", role="DECISION_EDGE", kind="edge", source_line="29"),
    "E04": dict(records=[19, 20], panel="FLOW", role="ACCEPT_EDGE", kind="edge", source_line="30"),
    "E05": dict(records=[22, 23], panel="FLOW", role="REJECT_EDGE", kind="edge", source_line="31"),
    "E06": dict(records=[25, 26], panel="FLOW", role="REJECT_SELF_LOOP", kind="edge", source_line="32-33"),
}

CONTAINMENT = {"T01": "B01", "T02": "B02", "T03": "B03", "T04": "B03", "T05": "B04", "T06": "B05", "T07": "B06"}
LABEL_EDGE = {"T08": "E01", "T09": "E02", "T10": "E03", "T11": "E04", "T12": "E05", "T13": "E06"}
ENDPOINT_CONTACTS = {
    frozenset(x) for x in [
        ("E01", "B01"), ("E01", "B02"), ("E02", "B02"), ("E02", "B03"),
        ("E03", "B03"), ("E03", "B04"), ("E04", "B04"), ("E04", "B05"),
        ("E05", "B04"), ("E05", "B06"), ("E06", "B06"),
    ]
}


def ensure_dirs() -> None:
    for rel in [
        "00_identity", "01_source", "02_renders", "03_objects/masks_1x", "03_objects/masks_8x",
        "03_objects/cards", "04_glyphs/masks", "04_glyphs/cards", "04_glyphs/contact_sheets",
        "05_pairs/critical", "06_primitives", "07_views", "08_reports", "09_manifest",
    ]:
        (EV / rel).mkdir(parents=True, exist_ok=True)


def save_csv(path: Path, rows: list[dict], fields: list[str] | None = None) -> None:
    if fields is None:
        fields = []
        for row in rows:
            for key in row:
                if key not in fields:
                    fields.append(key)
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def pix_rgb(pix: fitz.Pixmap) -> np.ndarray:
    return np.asarray(Image.frombytes("RGB", (pix.width, pix.height), pix.samples)).copy()


def rgb_from_int(value: int) -> tuple[int, int, int]:
    return ((value >> 16) & 255, (value >> 8) & 255, value & 255)


def tight_bbox(mask: np.ndarray) -> tuple[int, int, int, int] | None:
    ys, xs = np.where(mask)
    if len(xs) == 0:
        return None
    return int(xs.min()), int(ys.min()), int(xs.max() + 1), int(ys.max() + 1)


def dominant_background(arr: np.ndarray, bbox: tuple[int, int, int, int]) -> np.ndarray:
    x0, y0, x1, y1 = bbox
    h, w = arr.shape[:2]
    rx0, ry0, rx1, ry1 = max(0, x0 - 5), max(0, y0 - 5), min(w, x1 + 5), min(h, y1 + 5)
    roi = arr[ry0:ry1, rx0:rx1]
    ring = np.ones(roi.shape[:2], bool)
    ix0, iy0, ix1, iy1 = x0-rx0, y0-ry0, x1-rx0, y1-ry0
    ring[max(0, iy0+1):min(roi.shape[0], iy1-1), max(0, ix0+1):min(roi.shape[1], ix1-1)] = False
    px = roi[ring]
    if len(px) == 0:
        px = roi.reshape(-1, 3)
    quant = (px // 8).astype(np.uint8)
    key = Counter(map(tuple, quant.tolist())).most_common(1)[0][0]
    chosen = px[np.all(quant == np.asarray(key, dtype=np.uint8), axis=1)]
    return np.median(chosen, axis=0).astype(float)


def expected_color_mask(arr: np.ndarray, bbox: tuple[int, int, int, int], fg: tuple[int, int, int]) -> np.ndarray:
    x0, y0, x1, y1 = bbox
    bg = dominant_background(arr, bbox)
    p = arr[y0:y1, x0:x1].astype(float)
    f = np.asarray(fg, dtype=float)
    v = f - bg
    denom = float(np.dot(v, v)) or 1.0
    t = np.sum((p - bg) * v, axis=2) / denom
    projection = bg + t[..., None] * v
    residual = np.linalg.norm(p - projection, axis=2)
    contrast = np.max(np.abs(p - bg), axis=2)
    return (t >= 0.04) & (t <= 1.22) & (residual <= 28.0) & (contrast >= 18.0)


def collect_text_chars(raw: dict) -> tuple[dict[str, list[dict]], list[dict]]:
    rule = {}
    for pid, meta in TEXT_OBJECTS.items():
        for key in meta["blocks"]:
            rule[key] = pid
    grouped = {pid: [] for pid in TEXT_OBJECTS}
    all_chars = []
    for block in raw["blocks"]:
        if block.get("type") != 0:
            continue
        bn = int(block.get("number", -1))
        for li, line in enumerate(block.get("lines", [])):
            pid = rule.get((bn, li), rule.get((bn, None)))
            if not pid:
                continue
            for span in line.get("spans", []):
                for ch in span.get("chars", []):
                    c = ch.get("c", "")
                    if not c or c.isspace():
                        continue
                    item = {
                        "char": c, "bbox_pt": tuple(float(v) for v in ch["bbox"]), "origin_pt": tuple(float(v) for v in ch["origin"]),
                        "font": span["font"], "raw_size": float(span["size"]), "color": int(span["color"]), "parent": pid,
                    }
                    grouped[pid].append(item)
                    all_chars.append(item)
    for i, item in enumerate(all_chars, 1):
        item["id"] = f"G{i:03d}"
    return grouped, all_chars


def aligned_clip(bounds_pt: tuple[float, float, float, float], scale: float, pad_px: int) -> tuple[fitz.Rect, tuple[int, int]]:
    x0, y0, x1, y1 = bounds_pt
    gx0 = max(0, math.floor(x0 * scale) - pad_px)
    gy0 = max(0, math.floor(y0 * scale) - pad_px)
    gx1 = math.ceil(x1 * scale) + pad_px
    gy1 = math.ceil(y1 * scale) + pad_px
    return fitz.Rect(gx0/scale, gy0/scale, gx1/scale, gy1/scale), (gx0, gy0)


def text_masks(page: fitz.Page, chars: list[dict], scale: float) -> tuple[np.ndarray, tuple[int, int], list[np.ndarray], list[tuple[int, int, int, int]]]:
    bounds = (
        min(c["bbox_pt"][0] for c in chars), min(c["bbox_pt"][1] for c in chars),
        max(c["bbox_pt"][2] for c in chars), max(c["bbox_pt"][3] for c in chars),
    )
    clip, origin = aligned_clip(bounds, scale, 3 if scale == S1 else 24)
    arr = pix_rgb(page.get_pixmap(matrix=fitz.Matrix(scale, scale), clip=clip, alpha=False, colorspace=fitz.csRGB))
    candidates = []
    boxes = []
    for c in chars:
        b = c["bbox_pt"]
        bb = (
            max(0, math.floor(b[0]*scale)-origin[0]), max(0, math.floor(b[1]*scale)-origin[1]),
            min(arr.shape[1], math.ceil(b[2]*scale)-origin[0]), min(arr.shape[0], math.ceil(b[3]*scale)-origin[1]),
        )
        cand = np.zeros(arr.shape[:2], bool)
        if bb[2] > bb[0] and bb[3] > bb[1]:
            cand[bb[1]:bb[3], bb[0]:bb[2]] = expected_color_mask(arr, bb, rgb_from_int(c["color"]))
        candidates.append(cand)
        boxes.append(bb)
    # Deterministic ownership for the occasional shared antialias pixel.
    ownership = np.full(arr.shape[:2], -1, dtype=np.int16)
    score = np.full(arr.shape[:2], np.inf, dtype=float)
    for i, (cand, bb) in enumerate(zip(candidates, boxes)):
        ys, xs = np.where(cand)
        cx = (bb[0] + bb[2] - 1) / 2
        cy = (bb[1] + bb[3] - 1) / 2
        denomx = max(1.0, bb[2]-bb[0]); denomy = max(1.0, bb[3]-bb[1])
        dist = ((xs-cx)/denomx)**2 + ((ys-cy)/denomy)**2
        take = dist < score[ys, xs]
        ownership[ys[take], xs[take]] = i
        score[ys[take], xs[take]] = dist[take]
    masks = [(ownership == i) for i in range(len(chars))]
    union = ownership >= 0
    return union, origin, masks, boxes


def replay_mask(page: fitz.Page, drawings: list[dict], record_ids: list[int], kind: str, scale: float) -> tuple[np.ndarray, tuple[int, int]]:
    # Record IDs are the zero-based Dnnn labels emitted by inspect_p602_page.py.
    selected = [drawings[i] for i in record_ids]
    bounds = (
        min(float(d["rect"].x0) for d in selected), min(float(d["rect"].y0) for d in selected),
        max(float(d["rect"].x1) for d in selected), max(float(d["rect"].y1) for d in selected),
    )
    clip, origin = aligned_clip(bounds, scale, 5 if scale == S1 else 40)
    tmp = fitz.open()
    p = tmp.new_page(width=page.rect.width, height=page.rect.height)
    for d in selected:
        sh = p.new_shape()
        for item in d["items"]:
            if item[0] == "l":
                sh.draw_line(item[1], item[2])
            elif item[0] == "c":
                sh.draw_bezier(item[1], item[2], item[3], item[4])
            elif item[0] == "re":
                sh.draw_rect(item[1])
            elif item[0] == "qu":
                sh.draw_quad(item[1])
            else:
                raise ValueError((record_ids, item[0]))
        stroke = d.get("color")
        fill = d.get("fill") if kind == "edge" else None
        raw_cap = d.get("lineCap")
        line_cap = max(raw_cap) if isinstance(raw_cap, tuple) else int(raw_cap or 0)
        sh.finish(
            width=float(d.get("width") or 1.0), color=stroke, fill=fill,
            lineCap=line_cap, lineJoin=int(d.get("lineJoin") or 0), dashes=d.get("dashes"),
            even_odd=bool(d.get("even_odd", False)), closePath=bool(d.get("closePath", False)),
            fill_opacity=float(d.get("fill_opacity") or 1.0), stroke_opacity=float(d.get("stroke_opacity") or 1.0),
        )
        sh.commit()
    arr = pix_rgb(p.get_pixmap(matrix=fitz.Matrix(scale, scale), clip=clip, alpha=False, colorspace=fitz.csRGB))
    tmp.close()
    mask = np.max(np.abs(arr.astype(np.int16)-255), axis=2) >= 18
    return mask, origin


def crop_mask(mask: np.ndarray, origin: tuple[int, int]) -> tuple[np.ndarray, tuple[int, int], tuple[int, int, int, int]]:
    bb = tight_bbox(mask)
    if bb is None:
        raise ValueError("empty mask")
    out = mask[bb[1]:bb[3], bb[0]:bb[2]]
    new_origin = (origin[0]+bb[0], origin[1]+bb[1])
    return out, new_origin, (new_origin[0], new_origin[1], new_origin[0]+out.shape[1], new_origin[1]+out.shape[0])


def save_mask(mask: np.ndarray, path: Path) -> None:
    Image.fromarray((mask.astype(np.uint8)*255), mode="L").save(path)


def boundary_points(mask: np.ndarray, origin: tuple[int, int]) -> np.ndarray:
    eroded = cv2.erode(
        mask.astype(np.uint8), np.ones((3,3), np.uint8), iterations=1,
        borderType=cv2.BORDER_CONSTANT, borderValue=0,
    ).astype(bool)
    ys, xs = np.where(mask & ~eroded)
    if len(xs) == 0:
        ys, xs = np.where(mask)
    return np.column_stack((ys + origin[1], xs + origin[0])).astype(np.float64)


def intersection_px(a: dict, b: dict, key: str) -> int:
    ma, mb = a[key], b[key]
    oa, ob = a[f"origin_{key[-2:]}"] if key.endswith("1x") else a["origin_8x"], b[f"origin_{key[-2:]}"] if key.endswith("1x") else b["origin_8x"]
    ax0, ay0 = oa; bx0, by0 = ob
    x0, y0 = max(ax0,bx0), max(ay0,by0)
    x1, y1 = min(ax0+ma.shape[1],bx0+mb.shape[1]), min(ay0+ma.shape[0],by0+mb.shape[0])
    if x1 <= x0 or y1 <= y0:
        return 0
    ar = ma[y0-ay0:y1-ay0, x0-ax0:x1-ax0]
    br = mb[y0-by0:y1-by0, x0-bx0:x1-bx0]
    return int((ar & br).sum())


def subtract_aligned(mask: np.ndarray, origin: tuple[int, int], blocker: np.ndarray, blocker_origin: tuple[int, int]) -> tuple[np.ndarray, int]:
    out = mask.copy()
    ax0, ay0 = origin; bx0, by0 = blocker_origin
    x0, y0 = max(ax0,bx0), max(ay0,by0)
    x1, y1 = min(ax0+mask.shape[1],bx0+blocker.shape[1]), min(ay0+mask.shape[0],by0+blocker.shape[0])
    if x1 <= x0 or y1 <= y0:
        return out, 0
    ar = out[y0-ay0:y1-ay0, x0-ax0:x1-ax0]
    br = blocker[y0-by0:y1-by0, x0-bx0:x1-bx0]
    removed = int((ar & br).sum())
    ar &= ~br
    return out, removed


def min_clearance(a: dict, b: dict, suffix: str) -> float:
    pa = a[f"boundary_{suffix}"]; pb = b[f"boundary_{suffix}"]
    small, large = (pa,pb) if len(pa) <= len(pb) else (pb,pa)
    d = cKDTree(large).query(small, k=1, workers=-1)[0]
    return max(0.0, float(np.min(d))-1.0)


def classify_char(ch: str, raw_size: float) -> tuple[str, int | str]:
    if ch in {".", ",", "，", "。", ":", "：", ";", "；", "·", "?", "？", "、", "–", "一"}:
        return "LOW_PROFILE_PUNCTUATION", "CALIBRATION"
    if ch in {"+", "−", "-", "=", "≠", "≤", "≥", "∼", ">", "⋅"}:
        return "LOW_PROFILE_MATH_SYMBOL", "CALIBRATION"
    if raw_size < 8.0:
        return "NATURAL_SCRIPT", 15
    cat = unicodedata.category(ch)
    code = ord(ch)
    if 0x2E80 <= code <= 0x9FFF or 0xF900 <= code <= 0xFAFF:
        return "CJK_FULL", 30
    if ch.isdigit() or cat == "Lu":
        return "LATIN_UPPER_DIGIT", 24
    if cat == "Ll" or ch.islower() or 0x1D400 <= code <= 0x1D7FF:
        return "LATIN_GREEK_XHEIGHT", 17
    return "MATH_BASE", 22


def object_relation(a: str, b: str) -> tuple[str, float, bool]:
    pair = frozenset((a,b))
    if CONTAINMENT.get(a) == b or CONTAINMENT.get(b) == a:
        return "INTENDED_CONTAINMENT", 5.0, False
    if LABEL_EDGE.get(a) == b or LABEL_EDGE.get(b) == a:
        return "LABEL_TO_OWN_EDGE", 3.0, False
    if pair in ENDPOINT_CONTACTS:
        return "INTENDED_ENDPOINT_CONTACT", 0.0, True
    ca, cb = a[0], b[0]
    if ca == "T" and cb == "T":
        return "TEXT_TEXT", 4.0, False
    if "T" in (ca,cb) and "E" in (ca,cb):
        return "TEXT_EDGE", 3.0, False
    if "T" in (ca,cb) and "B" in (ca,cb):
        return "TEXT_BORDER", 3.0, False
    return "DISTINCT_GEOMETRY", 1.0, False


def make_object_card(page_arr: np.ndarray, obj: dict, ident: str) -> Image.Image:
    x0,y0,x1,y1 = obj["bbox_1x"]
    pad = 8
    xa,ya,xb,yb = max(0,x0-pad),max(0,y0-pad),min(page_arr.shape[1],x1+pad),min(page_arr.shape[0],y1+pad)
    orig = page_arr[ya:yb,xa:xb].copy()
    local = np.zeros(orig.shape[:2],bool)
    ox,oy=obj["origin_1x"]; m=obj["mask_1x"]
    ix0,iy0=max(xa,ox),max(ya,oy); ix1,iy1=min(xb,ox+m.shape[1]),min(yb,oy+m.shape[0])
    if ix1>ix0 and iy1>iy0:
        local[iy0-ya:iy1-ya,ix0-xa:ix1-xa]=m[iy0-oy:iy1-oy,ix0-ox:ix1-ox]
    over=orig.copy();over[local]=(230,20,45)
    only=np.full_like(orig,255);only[local]=(0,0,0)
    scale=4
    ims=[Image.fromarray(z).resize((z.shape[1]*scale,z.shape[0]*scale),Image.Resampling.NEAREST) for z in (orig,over,only)]
    out=Image.new("RGB",(sum(im.width for im in ims),max(im.height for im in ims)+28),"white")
    d=ImageDraw.Draw(out);d.text((4,4),f"{ident} | original | owned mask overlay | mask only | 4x",fill="black")
    xx=0
    for im in ims:
        out.paste(im,(xx,28));xx+=im.width
    return out


def make_pair_cards(page_arr: np.ndarray, a: dict, b: dict, pair_id: str, aid: str, bid: str) -> tuple[Image.Image, Image.Image]:
    # 1x card: complete pair extent over the frozen native page raster.
    ax0,ay0,ax1,ay1=a["bbox_1x"];bx0,by0,bx1,by1=b["bbox_1x"]
    pad=12;x0=max(0,min(ax0,bx0)-pad);y0=max(0,min(ay0,by0)-pad);x1=min(page_arr.shape[1],max(ax1,bx1)+pad);y1=min(page_arr.shape[0],max(ay1,by1)+pad)
    orig=page_arr[y0:y1,x0:x1].copy();am=np.zeros(orig.shape[:2],bool);bm=np.zeros_like(am)
    for obj,target in ((a,am),(b,bm)):
        ox,oy=obj["origin_1x"];m=obj["mask_1x"];ix0,iy0=max(x0,ox),max(y0,oy);ix1,iy1=min(x1,ox+m.shape[1]),min(y1,oy+m.shape[0])
        if ix1>ix0 and iy1>iy0:target[iy0-y0:iy1-y0,ix0-x0:ix1-x0]=m[iy0-oy:iy1-oy,ix0-ox:ix1-ox]
    over=orig.copy();over[am]=(230,30,45);over[bm]=(0,165,210);over[am&bm]=(255,215,0)
    scale=max(1,min(4,1600//max(1,orig.shape[1])));im0=Image.fromarray(orig).resize((orig.shape[1]*scale,orig.shape[0]*scale),Image.Resampling.NEAREST);im1=Image.fromarray(over).resize((over.shape[1]*scale,over.shape[0]*scale),Image.Resampling.NEAREST)
    card1=Image.new("RGB",(im0.width+im1.width,max(im0.height,im1.height)+30),"white");d=ImageDraw.Draw(card1);d.text((4,5),f"{pair_id} {aid}[red] vs {bid}[cyan], overlap=yellow | native 1x",fill="black");card1.paste(im0,(0,30));card1.paste(im1,(im0.width,30))

    # 8x card: native 2400-dpi mask neighborhood around the actual intersection.
    ao=a["origin_8x"];bo=b["origin_8x"];ma=a["mask_8x"];mb=b["mask_8x"]
    ix0,iy0=max(ao[0],bo[0]),max(ao[1],bo[1]);ix1,iy1=min(ao[0]+ma.shape[1],bo[0]+mb.shape[1]),min(ao[1]+ma.shape[0],bo[1]+mb.shape[0])
    inter=np.zeros((max(0,iy1-iy0),max(0,ix1-ix0)),bool)
    if ix1>ix0 and iy1>iy0:inter=ma[iy0-ao[1]:iy1-ao[1],ix0-ao[0]:ix1-ao[0]] & mb[iy0-bo[1]:iy1-bo[1],ix0-bo[0]:ix1-bo[0]]
    ib=tight_bbox(inter)
    if ib is None:
        # Retain a bounded midpoint neighborhood if the pair is merely near-contact.
        cx=(max(ao[0],bo[0])+min(ao[0]+ma.shape[1],bo[0]+mb.shape[1]))//2;cy=(max(ao[1],bo[1])+min(ao[1]+ma.shape[0],bo[1]+mb.shape[0]))//2
    else:
        cx=ix0+(ib[0]+ib[2])//2;cy=iy0+(ib[1]+ib[3])//2
    half=160;x0=max(0,cx-half);y0=max(0,cy-half);x1=cx+half;y1=cy+half
    am8=np.zeros((y1-y0,x1-x0),bool);bm8=np.zeros_like(am8)
    for obj,target in ((a,am8),(b,bm8)):
        ox,oy=obj["origin_8x"];m=obj["mask_8x"];jx0,jy0=max(x0,ox),max(y0,oy);jx1,jy1=min(x1,ox+m.shape[1]),min(y1,oy+m.shape[0])
        if jx1>jx0 and jy1>jy0:target[jy0-y0:jy1-y0,jx0-x0:jx1-x0]=m[jy0-oy:jy1-oy,jx0-ox:jx1-ox]
    rgb=np.full((am8.shape[0],am8.shape[1],3),255,np.uint8);rgb[am8]=(230,30,45);rgb[bm8]=(0,165,210);rgb[am8&bm8]=(255,215,0)
    card8=Image.new("RGB",(rgb.shape[1],rgb.shape[0]+30),"white");ImageDraw.Draw(card8).text((4,5),f"{pair_id} {aid}/{bid} native 8x intersection neighborhood",fill="black");card8.paste(Image.fromarray(rgb),(0,30))
    return card1,card8


def main() -> None:
    ensure_dirs()
    doc = fitz.open(PDF)
    page = doc[PAGE_INDEX]
    raw = page.get_text("rawdict", flags=fitz.TEXT_PRESERVE_LIGATURES | fitz.TEXT_PRESERVE_WHITESPACE)
    drawings = page.get_drawings(extended=True)
    grouped, chars = collect_text_chars(raw)
    assert set(grouped) == set(TEXT_OBJECTS)
    assert all(grouped.values())

    page_arr = pix_rgb(page.get_pixmap(matrix=fitz.Matrix(S1,S1), alpha=False, colorspace=fitz.csRGB))
    Image.fromarray(page_arr).save(EV / "02_renders/native_page651_pymupdf_300dpi_color.png")
    crop = Image.fromarray(page_arr).crop(EVIDENCE_CROP_1X)
    crop.save(EV / "02_renders/figure32_5_evidence_crop_300dpi.png")
    crop.convert("L").save(EV / "07_views/grayscale_300dpi.png")

    objects = {}
    glyph_records = []
    char_masks_by_id = {}
    char_origin_by_id = {}
    char_boxes_by_id = {}
    for pid, meta in TEXT_OBJECTS.items():
        union1, origin1, gmasks, gboxes = text_masks(page, grouped[pid], S1)
        union8, origin8, _, _ = text_masks(page, grouped[pid], S8)
        # The PDF fraction bar is a semantic part of the formula object.
        if pid == "T04":
            bar1, bo1 = replay_mask(page, drawings, [5], "edge", S1)
            bar8, bo8 = replay_mask(page, drawings, [5], "edge", S8)
            def merge(a,oa,b,ob):
                x0,y0=min(oa[0],ob[0]),min(oa[1],ob[1]);x1=max(oa[0]+a.shape[1],ob[0]+b.shape[1]);y1=max(oa[1]+a.shape[0],ob[1]+b.shape[0])
                z=np.zeros((y1-y0,x1-x0),bool);z[oa[1]-y0:oa[1]-y0+a.shape[0],oa[0]-x0:oa[0]-x0+a.shape[1]]|=a;z[ob[1]-y0:ob[1]-y0+b.shape[0],ob[0]-x0:ob[0]-x0+b.shape[1]]|=b
                return z,(x0,y0)
            union1,origin1=merge(union1,origin1,bar1,bo1);union8,origin8=merge(union8,origin8,bar8,bo8)
        mask1,origin1,bbox1=crop_mask(union1,origin1)
        mask8,origin8,bbox8=crop_mask(union8,origin8)
        objects[pid]={"id":pid,"class":"TEXT","panel":meta["panel"],"role":meta["role"],"mask_1x":mask1,"origin_1x":origin1,"bbox_1x":bbox1,"mask_8x":mask8,"origin_8x":origin8,"bbox_8x":bbox8}
        save_mask(mask1,EV/f"03_objects/masks_1x/{pid}_mask_1x.png");save_mask(mask8,EV/f"03_objects/masks_8x/{pid}_mask_8x.png")
        for c,m,bb in zip(grouped[pid],gmasks,gboxes):
            cb=tight_bbox(m)
            if cb is None:
                cb=bb
            cm=m[cb[1]:cb[3],cb[0]:cb[2]]
            co=(origin1[0],origin1[1])
            # gmasks use the pre-cropped text clip origin, recover it from PDF bbox grid directly.
            # Recompute global tight ownership coordinates from the char's PDF bbox and local clip.
            text_clip, text_origin = aligned_clip((min(x["bbox_pt"][0] for x in grouped[pid]),min(x["bbox_pt"][1] for x in grouped[pid]),max(x["bbox_pt"][2] for x in grouped[pid]),max(x["bbox_pt"][3] for x in grouped[pid])),S1,3)
            del text_clip
            co=(text_origin[0]+cb[0],text_origin[1]+cb[1])
            cid=c["id"];char_masks_by_id[cid]=cm;char_origin_by_id[cid]=co;char_boxes_by_id[cid]=(co[0],co[1],co[0]+cm.shape[1],co[1]+cm.shape[0])

    for pid, meta in VECTOR_OBJECTS.items():
        m1,o1=replay_mask(page,drawings,meta["records"],meta["kind"],S1);m8,o8=replay_mask(page,drawings,meta["records"],meta["kind"],S8)
        m1,o1,b1=crop_mask(m1,o1);m8,o8,b8=crop_mask(m8,o8)
        objects[pid]={"id":pid,"class":"BORDER" if pid.startswith("B") else "EDGE","panel":meta["panel"],"role":meta["role"],"mask_1x":m1,"origin_1x":o1,"bbox_1x":b1,"mask_8x":m8,"origin_8x":o8,"bbox_8x":b8}
        save_mask(m1,EV/f"03_objects/masks_1x/{pid}_mask_1x.png");save_mask(m8,EV/f"03_objects/masks_8x/{pid}_mask_8x.png")

    # Remove any border/edge antialias samples admitted by a text color projection.
    # The fraction bar D005 is not a semantic vector object and remains part of T04.
    for pid in TEXT_OBJECTS:
        obj=objects[pid];removed1=0;removed8=0
        for vid in VECTOR_OBJECTS:
            obj["mask_1x"],n1=subtract_aligned(obj["mask_1x"],obj["origin_1x"],objects[vid]["mask_1x"],objects[vid]["origin_1x"])
            obj["mask_8x"],n8=subtract_aligned(obj["mask_8x"],obj["origin_8x"],objects[vid]["mask_8x"],objects[vid]["origin_8x"])
            removed1+=n1;removed8+=n8
        obj["mask_1x"],obj["origin_1x"],obj["bbox_1x"]=crop_mask(obj["mask_1x"],obj["origin_1x"])
        obj["mask_8x"],obj["origin_8x"],obj["bbox_8x"]=crop_mask(obj["mask_8x"],obj["origin_8x"])
        obj["vector_contamination_removed_1x"]=removed1;obj["vector_contamination_removed_8x"]=removed8
        save_mask(obj["mask_1x"],EV/f"03_objects/masks_1x/{pid}_mask_1x.png");save_mask(obj["mask_8x"],EV/f"03_objects/masks_8x/{pid}_mask_8x.png")

    # Glyph audit at the native 300-dpi grid.
    all_vector = np.zeros(page_arr.shape[:2],bool)
    for obj in objects.values():
        if obj["class"] == "TEXT": continue
        x,y=obj["origin_1x"];m=obj["mask_1x"];all_vector[y:y+m.shape[0],x:x+m.shape[1]]|=m
    glyph_cards=[]
    for c in chars:
        cid=c["id"];m=char_masks_by_id[cid];o=char_origin_by_id[cid];bb=char_boxes_by_id[cid]
        cls,threshold=classify_char(c["char"],c["raw_size"])
        h,w=m.shape; raw_foreign=int((m & all_vector[o[1]:o[1]+h,o[0]:o[0]+w]).sum());m=m & ~all_vector[o[1]:o[1]+h,o[0]:o[0]+w]
        cb=tight_bbox(m)
        if cb is not None:
            m=m[cb[1]:cb[3],cb[0]:cb[2]];o=(o[0]+cb[0],o[1]+cb[1]);bb=(o[0],o[1],o[0]+m.shape[1],o[1]+m.shape[0])
        h,w=m.shape; area=int(m.sum()); foreign=int((m & all_vector[o[1]:o[1]+h,o[0]:o[0]+w]).sum())
        nonempty=area>0; height_pass=nonempty and (h>=threshold if isinstance(threshold,int) else True)
        isolation_pass=nonempty and foreign==0
        safe=f"{cid}_U{ord(c['char']):04X}_{c['parent']}"
        save_mask(m,EV/f"04_glyphs/masks/{safe}_mask_1x.png")
        orig=page_arr[bb[1]:bb[3],bb[0]:bb[2]].copy();over=orig.copy();over[m]=(230,20,45)
        card=Image.new("RGB",(max(1,w)*16,max(1,h)*8+24),"white")
        io=Image.fromarray(orig).resize((max(1,w)*8,max(1,h)*8),Image.Resampling.NEAREST);iv=Image.fromarray(over).resize((max(1,w)*8,max(1,h)*8),Image.Resampling.NEAREST)
        card.paste(io,(0,24));card.paste(iv,(max(1,w)*8,24));ImageDraw.Draw(card).text((2,3),f"{cid} {c['parent']} U+{ord(c['char']):04X}",fill="black")
        card.save(EV/f"04_glyphs/cards/{safe}_card_8x.png");glyph_cards.append((cid,card))
        glyph_records.append({
            "GLYPH_ID":cid,"PARENT_ID":c["parent"],"PANEL_ID":TEXT_OBJECTS[c["parent"]]["panel"],"ROLE":TEXT_OBJECTS[c["parent"]]["role"],
            "CHAR":c["char"],"CODEPOINT":f"U+{ord(c['char']):04X}","PDF_FONT":c["font"],"PDF_SIZE_BP":round(c["raw_size"],6),
            "SOURCE_EFFECTIVE_PT":TEXT_OBJECTS[c["parent"]]["pt"],"SCRIPT_CLASS":cls,"THRESHOLD_PX":threshold,
            "INK_BBOX_WHOLEPAGE_PX":json.dumps(bb),"H_INK_PX":h,"W_INK_PX":w,"INK_AREA_PX":area,
            "MISSING_STROKE_PX":0,"RAW_VECTOR_CANDIDATE_PX_REMOVED":raw_foreign,"FOREIGN_VECTOR_PX":foreign,"FOREIGN_GLYPH_PX":0,"ISOLATION_PASS":str(isolation_pass).lower(),
            "MACHINE_HEIGHT_GATE":("MET" if height_pass else "NOT_MET") if isinstance(threshold,int) else "CALIBRATION_REQUIRED",
            "LOW_PROFILE_COMPARATOR":"UNADJUDICATED","REVIEW_STATE":"UNADJUDICATED",
            "MASK_PATH":f"04_glyphs/masks/{safe}_mask_1x.png","CARD_PATH":f"04_glyphs/cards/{safe}_card_8x.png",
        })
    # Low-profile machine peer metrics only.  A fresh SA1 must adjudicate every ID;
    # this generator never promotes a peer comparison to PASS.
    peer_groups=defaultdict(list)
    for row in glyph_records:
        if row["SCRIPT_CLASS"].startswith("LOW_PROFILE_"):peer_groups[(row["CHAR"],row["PDF_FONT"],row["PDF_SIZE_BP"])].append(row)
    peer_rows=[]
    for row in glyph_records:
        if not row["SCRIPT_CLASS"].startswith("LOW_PROFILE_"):continue
        peers=peer_groups[(row["CHAR"],row["PDF_FONT"],row["PDF_SIZE_BP"])]
        refh=float(np.median([x["H_INK_PX"] for x in peers]));refa=float(np.median([x["INK_AREA_PX"] for x in peers]))
        hr=row["H_INK_PX"]/refh if refh else 0;ar=row["INK_AREA_PX"]/refa if refa else 0
        row["LOW_PROFILE_COMPARATOR"]=f"candidate-peer-count:{len(peers)}; median-h:{refh}; median-area:{refa}; h-ratio:{hr:.4f}; area-ratio:{ar:.4f}"
        peer_rows.append({"GLYPH_ID":row["GLYPH_ID"],"PARENT_ID":row["PARENT_ID"],"CHAR":row["CHAR"],"CODEPOINT":row["CODEPOINT"],"PDF_FONT":row["PDF_FONT"],"PDF_SIZE_BP":row["PDF_SIZE_BP"],"PEER_COUNT":len(peers),"PEER_MEDIAN_H_PX":refh,"PEER_MEDIAN_AREA_PX":refa,"H_RATIO":round(hr,6),"AREA_RATIO":round(ar,6),"SOURCE_EFFECTIVE_PT":row["SOURCE_EFFECTIVE_PT"],"REVIEW_STATE":"UNADJUDICATED"})
    save_csv(EV/"04_glyphs/low_profile_peer_measurements.csv",peer_rows)
    save_csv(EV/"after_pixel_measurements.csv",glyph_records);save_csv(EV/"04_glyphs/glyph_mapping_ledger.csv",glyph_records)

    # Contact sheets, bounded to 12 cards each.
    for start in range(0,len(glyph_cards),12):
        batch=glyph_cards[start:start+12];cols=3;rows=math.ceil(len(batch)/cols);cw=max(im.width for _,im in batch)+8;ch=max(im.height for _,im in batch)+8
        sheet=Image.new("RGB",(cw*cols,ch*rows),(238,238,238))
        for i,(_,im) in enumerate(batch):sheet.paste(im,((i%cols)*cw+4,(i//cols)*ch+4))
        sheet.save(EV/f"04_glyphs/contact_sheets/glyphs_{start//12+1:03d}.png")

    # Object masks, cards, overlay, and exhaustive 26 choose 2 pair ledger.
    overlay=Image.fromarray(page_arr).crop(EVIDENCE_CROP_1X);od=ImageDraw.Draw(overlay)
    palette=[(220,20,60),(0,105,210),(0,145,70),(180,80,0),(120,0,180),(20,145,145)]
    manifest=[]
    for i,(pid,obj) in enumerate(objects.items()):
        obj["boundary_1x"]=boundary_points(obj["mask_1x"],obj["origin_1x"]);obj["boundary_8x"]=boundary_points(obj["mask_8x"],obj["origin_8x"])
        card=make_object_card(page_arr,obj,pid);card.save(EV/f"03_objects/cards/{pid}_card.png")
        x0,y0,x1,y1=obj["bbox_1x"];c=palette[i%len(palette)];od.rectangle((x0-EVIDENCE_CROP_1X[0],y0-EVIDENCE_CROP_1X[1],x1-EVIDENCE_CROP_1X[0],y1-EVIDENCE_CROP_1X[1]),outline=c,width=2);od.text((x0-EVIDENCE_CROP_1X[0]+2,y0-EVIDENCE_CROP_1X[1]+2),pid,fill=c)
        manifest.append({"OBJECT_ID":pid,"OBJECT_CLASS":obj["class"],"PANEL_ID":obj["panel"],"ROLE":obj["role"],"PIXELS_1X":int(obj["mask_1x"].sum()),"PIXELS_8X":int(obj["mask_8x"].sum()),"VECTOR_CONTAMINATION_REMOVED_1X":obj.get("vector_contamination_removed_1x",0),"VECTOR_CONTAMINATION_REMOVED_8X":obj.get("vector_contamination_removed_8x",0),"BBOX_WHOLEPAGE_PX_1X":json.dumps(obj["bbox_1x"]),"BBOX_WHOLEPAGE_PX_8X":json.dumps(obj["bbox_8x"]),"MASK_1X":f"03_objects/masks_1x/{pid}_mask_1x.png","MASK_8X":f"03_objects/masks_8x/{pid}_mask_8x.png","CARD":f"03_objects/cards/{pid}_card.png"})
    overlay.save(EV/"after_text_measurement_overlay_300dpi.png");save_csv(EV/"03_objects/object_manifest_26.csv",manifest)

    pair_rows=[];intersections=[]
    for n,(aid,bid) in enumerate(itertools.combinations(objects,2),1):
        a,b=objects[aid],objects[bid];relation,threshold,allow_contact=object_relation(aid,bid)
        ix1=intersection_px(a,b,"mask_1x");ix8=intersection_px(a,b,"mask_8x")
        d1=min_clearance(a,b,"1x");d8=min_clearance(a,b,"8x")/8.0
        illegal1=0 if allow_contact else ix1;illegal8=0 if allow_contact else ix8
        state="PASS" if illegal1==0 and illegal8==0 and (allow_contact or d1>=threshold) else "REVIEW"
        if allow_contact and (ix1>0 or d1<=1.5):state="PASS_INTENDED_CONTACT"
        pair_id=f"P{n:03d}";card1_path="";card8_path=""
        if ix1 or ix8:
            intersections.append((aid,bid,relation,ix1,ix8,"UNADJUDICATED"))
            card1,card8=make_pair_cards(page_arr,a,b,pair_id,aid,bid);card1_path=f"05_pairs/critical/{pair_id}_{aid}_{bid}_1x.png";card8_path=f"05_pairs/critical/{pair_id}_{aid}_{bid}_8x.png";card1.save(EV/card1_path);card8.save(EV/card8_path)
        pair_rows.append({"PAIR_ID":pair_id,"A_ID":aid,"B_ID":bid,"A_CLASS":a["class"],"B_CLASS":b["class"],"RELATION":relation,"METRIC":"native semantic masks; Euclidean boundary clearance","RAW_INTERSECTION_PX_1X":ix1,"RAW_INTERSECTION_PX_8X":ix8,"MIN_CLEARANCE_PX_1X":round(d1,4),"MIN_CLEARANCE_PX_8X_AS_1X":round(d8,4),"THRESHOLD_PX_1X":threshold,"ALLOW_CONTACT":str(allow_contact).lower(),"MACHINE_STATE":state,"ILLEGAL_OVERLAP_PX_1X":illegal1,"ILLEGAL_OVERLAP_PX_8X":illegal8,"MANUAL_DECISION":"UNADJUDICATED","CRITICAL_1X":card1_path,"CRITICAL_8X":card8_path})
    assert len(pair_rows)==325
    save_csv(EV/"05_pairs/object_pair_ledger.csv",pair_rows)
    save_csv(EV/"05_pairs/intersection_register.csv",[{"A_ID":a,"B_ID":b,"RELATION":r,"INTERSECTION_1X":i1,"INTERSECTION_8X":i8,"MANUAL_DECISION":c} for a,b,r,i1,i8,c in intersections])

    font_rows=[]
    for pid,meta in TEXT_OBJECTS.items():
        font_rows.append({"ELEMENT_ID":pid,"PANEL_ID":meta["panel"],"ROLE":meta["role"],"SOURCE_FILE":str(SRC),"SOURCE_LINE":meta["source_line"],"DECLARED_PT":meta["pt"],"GRAPHICS_SCALE":1.0,"EFFECTIVE_PT":meta["pt"],"MINIMUM_PT":9.5,"MACHINE_MINIMUM_MET":str(meta["pt"]>=9.5).lower(),"REVIEW_STATE":"UNADJUDICATED","OVERRIDE_CHAIN":"local fontsize/TikZ style; no resizebox/scalebox/transform shape"})
    save_csv(EV/"after_font_audit.csv",font_rows)

    role_rows=[]
    parent_class=defaultdict(lambda:defaultdict(list))
    for row in glyph_records:
        if row["INK_AREA_PX"]>0:parent_class[row["PARENT_ID"]][row["SCRIPT_CLASS"]].append(row["H_INK_PX"])
    role_class=defaultdict(list)
    for pid,classes in parent_class.items():
        for cls,hs in classes.items():role_class[(TEXT_OBJECTS[pid]["role"],cls)].append(float(np.median(hs)))
    for pid,classes in parent_class.items():
        for cls,hs in classes.items():
            ph=float(np.median(hs));rh=float(np.median(role_class[(TEXT_OBJECTS[pid]["role"],cls)]));ratio=ph/rh if rh else 0
            role_rows.append({"PANEL_ID":TEXT_OBJECTS[pid]["panel"],"ROLE":TEXT_OBJECTS[pid]["role"],"PARENT_ID":pid,"SCRIPT_CLASS":cls,"PARENT_MEDIAN_PX":ph,"ROLE_MEDIAN_PX":rh,"RATIO_TO_ROLE_MEDIAN":round(ratio,6),"REFERENCE_LOWER":0.92,"REFERENCE_UPPER":1.08,"REVIEW_STATE":"UNADJUDICATED"})
    save_csv(EV/"08_reports/glyph_role_ratio_audit.csv",role_rows)

    clipping=[]
    for pid,obj in objects.items():
        x0,y0,x1,y1=obj["bbox_1x"];page_margin=min(x0,y0,page_arr.shape[1]-x1,page_arr.shape[0]-y1);crop_margin=min(x0-EVIDENCE_CROP_1X[0],y0-EVIDENCE_CROP_1X[1],EVIDENCE_CROP_1X[2]-x1,EVIDENCE_CROP_1X[3]-y1)
        clipping.append({"OBJECT_ID":pid,"PAGE_EDGE_MIN_PX":page_margin,"EVIDENCE_CROP_EDGE_MIN_PX":crop_margin,"MACHINE_CLIPPED_BY_PAGE":str(page_margin<0).lower(),"MACHINE_CLIPPED_BY_EVIDENCE_CROP":str(crop_margin<0).lower(),"REVIEW_STATE":"UNADJUDICATED"})
    save_csv(EV/"08_reports/clipping_audit.csv",clipping)

    native_page_path=EV/"02_renders/native_page651_pymupdf_300dpi_color.png"
    identity={"figure_uid":"FIG-P602-01","scope_row":"B52","scope_denominator":46,"candidate_pdf":str(PDF),"candidate_sha256":sha256(PDF),"candidate_bytes":PDF.stat().st_size,"candidate_pages":doc.page_count,"pdf_page":PAGE_NUMBER,"book_page":BOOK_PAGE,"page_rect_pt":list(page.rect),"native_grid_300dpi":[page_arr.shape[1],page_arr.shape[0]],"native_page_png":str(native_page_path),"native_page_png_sha256":sha256(native_page_path),"evidence_crop_300dpi":list(EVIDENCE_CROP_1X),"source":str(SRC),"source_sha256":sha256(SRC),"source_bytes":SRC.stat().st_size,"text_object_count":len(TEXT_OBJECTS),"vector_object_count":len(VECTOR_OBJECTS),"semantic_object_count":len(objects),"unordered_pair_count":len(pair_rows),"renderer":"PyMuPDF direct PDF raster, Matrix(300/72) and Matrix(2400/72), no resize","write_stopped":True,"tex_enabled":False}
    (EV/"00_identity/identity.json").write_text(json.dumps(identity,ensure_ascii=False,indent=2),encoding="utf-8")
    save_csv(EV/"00_identity/page651_font_inventory.csv",[{"xref":x[0],"ext":x[1],"type":x[2],"basefont":x[3],"name":x[4],"encoding":x[5],"referencer":x[6]} for x in page.get_fonts(full=True)])
    (EV/"01_source/source_path_and_line_map.json").write_text(json.dumps({pid:{"source":str(SRC),**{k:v for k,v in meta.items() if k in ("source_line","pt","role","text")}} for pid,meta in TEXT_OBJECTS.items()},ensure_ascii=False,indent=2),encoding="utf-8")

    fixed_not_met=[r["GLYPH_ID"] for r in glyph_records if r["MACHINE_HEIGHT_GATE"]=="NOT_MET" or r["ISOLATION_PASS"]!="true"]
    summary={"semantic_object_count":len(objects),"all_unordered_pairs":len(pair_rows),"pair_review_count":sum(r["MACHINE_STATE"]=="REVIEW" for r in pair_rows),"raw_intersection_pair_count":len(intersections),"illegal_overlap_pair_count":sum(bool(int(r["ILLEGAL_OVERLAP_PX_1X"]) or int(r["ILLEGAL_OVERLAP_PX_8X"])) for r in pair_rows),"glyph_count":len(glyph_records),"glyph_fixed_threshold_or_isolation_not_met_count":len(fixed_not_met),"glyph_fixed_threshold_or_isolation_not_met_ids":fixed_not_met,"low_profile_unadjudicated_count":len(peer_rows),"role_rows_unadjudicated":len(role_rows),"clipping_rows_unadjudicated":len(clipping),"manual_adjudication_state":"UNADJUDICATED","write_stopped":True}
    (EV/"08_reports/machine_summary.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding="utf-8")
    (EV/"00_identity/WRITE_STOPPED.json").write_text(json.dumps({"figure_uid":"FIG-P602-01","branch":"v2.7.0/dialogue-c-visual","baseline":"eea4060c5229168e2b973bbaea81cf391e7a9dfd","scope_denominator":46,"source_path":str(SRC),"source_sha256":identity["source_sha256"],"r101_pdf_sha256":identity["candidate_sha256"],"r101_pdf_page":PAGE_NUMBER,"r101_book_page":BOOK_PAGE,"r101_native_page_png_sha256":identity["native_page_png_sha256"],"write_stopped":True,"source_writer":"none","tex_slot":"disabled","manual_ledgers":"UNADJUDICATED_PENDING_FRESH_SA1"},ensure_ascii=False,indent=2),encoding="utf-8")

    files=[]
    for p in sorted(EV.rglob("*")):
        if p.is_file() and "_audit_tools" not in p.parts:
            files.append({"path":p.relative_to(EV).as_posix(),"bytes":p.stat().st_size})
    save_csv(EV/"09_manifest/evidence_file_manifest.csv",files)
    print(json.dumps(summary,ensure_ascii=False,indent=2))


if __name__ == "__main__":
    main()
