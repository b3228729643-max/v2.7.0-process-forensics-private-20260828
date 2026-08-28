from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import re
import shutil
import unicodedata
from collections import Counter, defaultdict
from dataclasses import dataclass
from itertools import combinations
from pathlib import Path

import cv2
import fitz
import numpy as np
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P610-01\sa1_r104_fresh_isolated_v1")
PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r104_fullbook\main_full.pdf")
SOURCE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C03\fig_v5_c03_rejection_sampling_comparison.tex")
PHYSICAL_PAGE = 662
PAGE_INDEX = PHYSICAL_PAGE - 1
PDF_SHA256 = "E5C871642FBDDBEC6508BE1B61BD911FE281CA5ACFBD16B0449B13357770A641"
FIG_UID = "FIG-P610-01"
HANDOFF_ID = "C-FIG-P610-01-R104-SA1-FRESH-ISOLATED-V1"

SCALE_300 = 300.0 / 72.0
SCALE_200 = 200.0 / 72.0
FIG_RECT_PT = fitz.Rect(70.0, 492.0, 535.0, 658.0)
BODY_RECT_PT = fitz.Rect(109.0, 492.0, 497.0, 624.0)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(1024 * 1024)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest().upper()


def ensure_dirs() -> None:
    # Idempotent regeneration is limited to this script's own unsealed machine products.
    for rel in ["renders", "inventories", "machine"]:
        target = ROOT / rel
        if target.exists():
            shutil.rmtree(target)
    for rel in [
        "renders",
        "inventories",
        "machine/glyph_masks",
        "machine/glyph_evidence_1x",
        "machine/glyph_evidence_8x",
        "machine/glyph_contact_sheets",
        "machine/graphic_masks",
        "machine/graphic_special_masks",
        "machine/pair_evidence_1x",
        "machine/pair_evidence_8x",
        "machine/pair_contact_sheets",
    ]:
        (ROOT / rel).mkdir(parents=True, exist_ok=True)


def rgb_from_int(value: int) -> tuple[int, int, int]:
    return ((value >> 16) & 255, (value >> 8) & 255, value & 255)


def rect_px(rect: fitz.Rect, scale: float) -> tuple[int, int, int, int]:
    return (
        math.floor(rect.x0 * scale),
        math.floor(rect.y0 * scale),
        math.ceil(rect.x1 * scale),
        math.ceil(rect.y1 * scale),
    )


def crop_bbox_from_page_bbox(bbox: tuple[float, float, float, float], crop_xyxy: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
    cx0, cy0, _, _ = crop_xyxy
    x0 = math.floor(bbox[0] * SCALE_300) - cx0
    y0 = math.floor(bbox[1] * SCALE_300) - cy0
    x1 = math.ceil(bbox[2] * SCALE_300) - cx0
    y1 = math.ceil(bbox[3] * SCALE_300) - cy0
    return x0, y0, x1, y1


def safe_id(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("_")


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def render_page(page: fitz.Page, dpi: int) -> Image.Image:
    pix = page.get_pixmap(matrix=fitz.Matrix(dpi / 72.0, dpi / 72.0), alpha=False, colorspace=fitz.csRGB)
    return Image.frombytes("RGB", (pix.width, pix.height), pix.samples)


def assign_parent(block_no: int, bbox: tuple[float, float, float, float]) -> str:
    cx = (bbox[0] + bbox[2]) / 2.0
    if block_no == 22:
        return "TXT_TITLE_L" if cx < 300 else "TXT_TITLE_R"
    if block_no == 23:
        centers = [(153.07, "TXT_CAND_L1"), (204.10, "TXT_CAND_L2"), (255.12, "TXT_CAND_L3"), (351.50, "TXT_CAND_R1"), (402.52, "TXT_CAND_R2"), (453.55, "TXT_CAND_R3")]
        return min(centers, key=lambda t: abs(cx - t[0]))[1]
    if block_no == 24:
        return "TXT_OUT_L1" if cx < 200 else "TXT_OUT_L3"
    if block_no == 25:
        return "TXT_REJECT_L"
    if block_no == 26:
        return "TXT_NOTE_L"
    if block_no == 27:
        centers = [(351.50, "TXT_OUT_R1"), (402.52, "TXT_OUT_R2"), (453.55, "TXT_OUT_R3")]
        return min(centers, key=lambda t: abs(cx - t[0]))[1]
    if block_no == 28:
        return "TXT_REJECT_R"
    if block_no == 29:
        return "TXT_NOTE_R"
    if block_no == 30:
        return "TXT_CAPTION"
    raise ValueError(f"Unexpected figure block {block_no}")


PARENT_META = {
    "TXT_TITLE_L": ("TEXT", "PANEL_TITLE", "L"),
    "TXT_TITLE_R": ("TEXT", "PANEL_TITLE", "R"),
    "TXT_CAND_L1": ("FORMULA", "NODE_LABEL_CANDIDATE", "L"),
    "TXT_CAND_L2": ("FORMULA", "NODE_LABEL_CANDIDATE", "L"),
    "TXT_CAND_L3": ("FORMULA", "NODE_LABEL_CANDIDATE", "L"),
    "TXT_CAND_R1": ("FORMULA", "NODE_LABEL_CANDIDATE", "R"),
    "TXT_CAND_R2": ("FORMULA", "NODE_LABEL_CANDIDATE", "R"),
    "TXT_CAND_R3": ("FORMULA", "NODE_LABEL_CANDIDATE", "R"),
    "TXT_OUT_L1": ("FORMULA", "NODE_LABEL_OUTPUT", "L"),
    "TXT_OUT_L3": ("FORMULA", "NODE_LABEL_OUTPUT", "L"),
    "TXT_REJECT_L": ("TEXT", "REJECT_MARKER", "L"),
    "TXT_NOTE_L": ("TEXT_FORMULA", "ANNOTATION", "L"),
    "TXT_OUT_R1": ("FORMULA", "NODE_LABEL_OUTPUT", "R"),
    "TXT_OUT_R2": ("FORMULA", "NODE_LABEL_OUTPUT", "R"),
    "TXT_OUT_R3": ("FORMULA", "NODE_LABEL_OUTPUT", "R"),
    "TXT_REJECT_R": ("TEXT", "REJECT_MARKER", "R"),
    "TXT_NOTE_R": ("TEXT_FORMULA", "ANNOTATION", "R"),
    "TXT_CAPTION": ("TEXT", "CAPTION", "PAGE"),
}


def classify_char(ch: str, parent: str) -> str:
    cp = ord(ch)
    cat = unicodedata.category(ch)
    if 0x4E00 <= cp <= 0x9FFF:
        return "CJK_FULL"
    if ch in ".,;:，。；：、…·":
        return "LOW_PROFILE_PUNCTUATION"
    if ch.isdigit():
        return "NATURAL_SCRIPT_DIGIT" if "CAND" in parent or "OUT" in parent or "NOTE" in parent else "DIGIT"
    if ch in "×−–+-=":
        return "BASE_MATH_OR_OPERATOR" if ch == "×" else "PUNCT_OR_DASH"
    if ch.isalpha() and ch.isascii():
        return "LATIN_UPPER" if ch.isupper() else "LATIN_LOWER"
    if 0x1D400 <= cp <= 0x1D7FF:
        return "BASE_MATH"
    if cat.startswith("P"):
        return "PUNCTUATION"
    return "OTHER_VISIBLE"


def background_for_parent(parent: str) -> np.ndarray:
    if "CAND" in parent:
        return np.array([246.0, 247.0, 248.0], dtype=np.float32)
    return np.array([255.0, 255.0, 255.0], dtype=np.float32)


def glyph_mask_for_bbox(image: np.ndarray, bbox: tuple[int, int, int, int], bg: np.ndarray, target: tuple[int,int,int]) -> np.ndarray:
    # Project antialiased pixels onto the actual PDF text-color/background line.
    # This prevents a differently colored edge/arrow inside a glyph bbox from
    # contaminating the unique target glyph mask.
    return alpha_color_mask(image, bbox, target, [tuple(int(v) for v in bg)])


def alpha_color_mask(image: np.ndarray, bbox: tuple[int, int, int, int], target: tuple[int, int, int], backgrounds: list[tuple[int, int, int]]) -> np.ndarray:
    h, w = image.shape[:2]
    x0, y0, x1, y1 = bbox
    x0, y0 = max(0, x0), max(0, y0)
    x1, y1 = min(w, x1), min(h, y1)
    out = np.zeros((h, w), dtype=np.uint8)
    if x1 <= x0 or y1 <= y0:
        return out
    p = image[y0:y1, x0:x1].astype(np.float32)
    t = np.array(target, dtype=np.float32)
    accepted = np.zeros(p.shape[:2], dtype=bool)
    for bgt in backgrounds:
        bg = np.array(bgt, dtype=np.float32)
        d = bg - t
        denom = float(np.dot(d, d))
        alpha = np.sum((bg - p) * d.reshape(1, 1, 3), axis=2) / max(denom, 1.0)
        recon = bg.reshape(1, 1, 3) - alpha[:, :, None] * d.reshape(1, 1, 3)
        residual = np.max(np.abs(p - recon), axis=2)
        contrast = np.max(np.abs(p - bg.reshape(1, 1, 3)), axis=2)
        obs = bg.reshape(1, 1, 3) - p
        obs_norm = np.linalg.norm(obs, axis=2)
        direction_cos = np.sum(obs * d.reshape(1, 1, 3), axis=2) / np.maximum(obs_norm * math.sqrt(denom), 1e-6)
        accepted |= (alpha > 0.0) & (alpha < 1.25) & (contrast >= 20.0) & (residual <= 12.0) & (direction_cos >= 0.97)
    out[y0:y1, x0:x1] = accepted.astype(np.uint8) * 255
    return out


def page_bbox_to_crop_bbox(page_bbox: tuple[float, float, float, float], crop_xyxy: tuple[int, int, int, int], pad: int = 3) -> tuple[int, int, int, int]:
    b = crop_bbox_from_page_bbox(page_bbox, crop_xyxy)
    return (b[0] - pad, b[1] - pad, b[2] + pad, b[3] + pad)


@dataclass(frozen=True)
class GraphicSpec:
    object_id: str
    role: str
    panel: str
    page_bbox: tuple[float, float, float, float]
    target_rgb: tuple[int, int, int]
    bg_rgbs: tuple[tuple[int, int, int], ...]
    pdf_draw_refs: str
    source_map: str
    shape: str


GRAY = (184, 192, 200)
BLUE = (31, 78, 121)
WHITE = (255, 255, 255)
SOFT_GRAY = (246, 247, 248)
GRAPHICS = [
    GraphicSpec("G_PANEL_L_BORDER", "PANEL_BORDER", "L", (114.80,497.74,293.39,622.47), GRAY, (WHITE,), "draw[4]", "panel rectangle left", "rounded_rect"),
    GraphicSpec("G_PANEL_R_BORDER", "PANEL_BORDER", "R", (313.23,497.74,491.81,622.47), GRAY, (WHITE,), "draw[5]", "panel rectangle right", "rounded_rect"),
    GraphicSpec("G_CAND_L1_BORDER", "NODE_BORDER", "L", (140.31,525.52,165.82,551.03), GRAY, (WHITE,SOFT_GRAY), "draw[6]", "cand lp1", "circle"),
    GraphicSpec("G_CAND_L2_BORDER", "NODE_BORDER", "L", (191.34,525.52,216.85,551.03), GRAY, (WHITE,SOFT_GRAY), "draw[7]", "cand lp2", "circle"),
    GraphicSpec("G_CAND_L3_BORDER", "NODE_BORDER", "L", (242.36,525.52,267.87,551.03), GRAY, (WHITE,SOFT_GRAY), "draw[8]", "cand lp3", "circle"),
    GraphicSpec("G_CAND_R1_BORDER", "NODE_BORDER", "R", (338.74,525.52,364.25,551.03), GRAY, (WHITE,SOFT_GRAY), "draw[9]", "cand mp1", "circle"),
    GraphicSpec("G_CAND_R2_BORDER", "NODE_BORDER", "R", (389.76,525.52,415.28,551.03), GRAY, (WHITE,SOFT_GRAY), "draw[10]", "cand mp2", "circle"),
    GraphicSpec("G_CAND_R3_BORDER", "NODE_BORDER", "R", (440.79,525.52,466.30,551.03), GRAY, (WHITE,SOFT_GRAY), "draw[11]", "cand mp3", "circle"),
    GraphicSpec("G_OUT_L1_BORDER", "NODE_BORDER", "L", (140.03,568.89,166.11,594.97), BLUE, (WHITE,), "draw[12]", "outnode r1", "circle"),
    GraphicSpec("G_OUT_L3_BORDER", "NODE_BORDER", "L", (242.08,568.89,268.16,594.97), BLUE, (WHITE,), "draw[13]", "outnode r3", "circle"),
    GraphicSpec("G_PROP_L1", "LINE_ARROW", "L", (152.65,552.90,153.49,566.90), GRAY, (WHITE,), "draw[14]", "prop lp1-r1", "vertical_line"),
    GraphicSpec("G_PROP_L3", "LINE_ARROW", "L", (254.70,552.90,255.54,566.90), GRAY, (WHITE,), "draw[15]", "prop lp3-r3", "vertical_line"),
    GraphicSpec("G_OUT_R1_BORDER", "NODE_BORDER", "R", (338.46,568.89,364.54,594.97), BLUE, (WHITE,), "draw[16]", "outnode m1", "circle"),
    GraphicSpec("G_OUT_R2_DOUBLE_BORDER", "NODE_BORDER", "R", (389.48,568.89,415.56,594.97), BLUE, (WHITE,), "draw[17]+draw[18]", "outnode m2 double", "double_circle_final_visible"),
    GraphicSpec("G_OUT_R3_BORDER", "NODE_BORDER", "R", (440.51,568.89,466.58,594.97), BLUE, (WHITE,), "draw[19]", "outnode m3", "circle"),
    GraphicSpec("G_PROP_R1", "LINE_ARROW", "R", (351.08,552.90,351.92,566.90), GRAY, (WHITE,), "draw[20]", "prop mp1-m1", "vertical_line"),
    GraphicSpec("G_PROP_R2_UP", "LINE_ARROW", "R", (402.10,552.90,402.94,555.90), GRAY, (WHITE,), "draw[21].item[0]", "prop mp2-rxM", "vertical_line"),
    GraphicSpec("G_PROP_R2_DOWN", "LINE_ARROW", "R", (402.10,564.20,402.94,566.90), GRAY, (WHITE,), "draw[21].item[1]", "prop rxM-m2", "vertical_line"),
    GraphicSpec("G_PROP_R3", "LINE_ARROW", "R", (453.13,552.90,453.97,566.90), GRAY, (WHITE,), "draw[22]", "prop mp3-m3", "vertical_line"),
    GraphicSpec("G_ARROW_R1_R2", "LINE_ARROW", "R", (367.90,580.50,384.40,583.40), BLUE, (WHITE,), "draw[23]+draw[24]", "actual m1-m2", "arrow_shaft_head"),
    GraphicSpec("G_ARROW_R2_R3", "LINE_ARROW", "R", (418.90,580.50,435.40,583.40), BLUE, (WHITE,), "draw[25]+draw[26]", "actual m2-m3", "arrow_shaft_head"),
    GraphicSpec("G_DIVIDER", "PANEL_DIVIDER", "MID", (302.85,501.50,303.77,618.70), GRAY, (WHITE,), "draw[27]", "divider", "vertical_line"),
]


def geometry_gate(mask: np.ndarray, spec: GraphicSpec, crop_xyxy: tuple[int, int, int, int]) -> np.ndarray:
    h, w = mask.shape
    gated = np.zeros_like(mask)
    bbox = page_bbox_to_crop_bbox(spec.page_bbox, crop_xyxy, pad=5)
    x0, y0, x1, y1 = max(0,bbox[0]), max(0,bbox[1]), min(w,bbox[2]), min(h,bbox[3])
    if x1 <= x0 or y1 <= y0:
        return gated
    yy, xx = np.mgrid[y0:y1, x0:x1]
    px0, py0, px1, py1 = crop_bbox_from_page_bbox(spec.page_bbox, crop_xyxy)
    region = np.ones_like(xx, dtype=bool)
    if spec.shape in {"circle", "double_circle_final_visible"}:
        cx, cy = (px0+px1)/2.0, (py0+py1)/2.0
        rx, ry = max((px1-px0)/2.0,1), max((py1-py0)/2.0,1)
        rr = np.sqrt(((xx-cx)/rx)**2 + ((yy-cy)/ry)**2)
        region = (rr >= 0.78) & (rr <= 1.18)
    elif spec.shape == "rounded_rect":
        edge_dist = np.minimum.reduce([np.abs(xx-px0), np.abs(xx-px1), np.abs(yy-py0), np.abs(yy-py1)])
        region = edge_dist <= 8
        # rounded-corner strokes remain inside this broad edge band; internal same-color objects are excluded.
    local = mask[y0:y1, x0:x1] > 0
    gated[y0:y1, x0:x1] = (local & region).astype(np.uint8) * 255
    return gated


def bbox_from_mask(mask: np.ndarray) -> tuple[int, int, int, int] | None:
    ys, xs = np.where(mask > 0)
    if len(xs) == 0:
        return None
    return int(xs.min()), int(ys.min()), int(xs.max()+1), int(ys.max()+1)


def ink_metrics(mask: np.ndarray) -> tuple[int, int, int]:
    b = bbox_from_mask(mask)
    if b is None:
        return 0, 0, 0
    return b[2]-b[0], b[3]-b[1], int(np.count_nonzero(mask))


def mask_clearance(a: np.ndarray, b: np.ndarray) -> float:
    aa = a > 0
    bb = b > 0
    if not aa.any() or not bb.any():
        return math.nan
    if np.any(aa & bb):
        return 0.0
    dt = cv2.distanceTransform((~bb).astype(np.uint8), cv2.DIST_L2, 5)
    return float(dt[aa].min())


def rect_distance(a: tuple[int,int,int,int], b: tuple[int,int,int,int]) -> float:
    dx = max(a[0]-b[2], b[0]-a[2], 0)
    dy = max(a[1]-b[3], b[1]-a[3], 0)
    return math.hypot(dx, dy)


def pair_category(a: dict, b: dict) -> tuple[str, float, str]:
    ta, tb = a["object_type"], b["object_type"]
    ra, rb = a["role"], b["role"]
    if ta == "TEXT" and tb == "TEXT":
        return "TEXT_TEXT", 4.0, "independent semantic-parent bbox clearance"
    if ta == "TEXT" or tb == "TEXT":
        grole = rb if ta == "TEXT" else ra
        textrole = ra if ta == "TEXT" else rb
        if grole == "NODE_BORDER":
            return "TEXT_NODE_BORDER", 5.0, "final-visible ink to border"
        if grole == "PANEL_BORDER":
            return "TEXT_PANEL_BORDER", 6.0, "text ink to panel/figure boundary"
        if grole in {"LINE_ARROW", "PANEL_DIVIDER"}:
            return "TEXT_LINE_ARROW", 3.0, "text/formula ink to line/arrow"
        return "TEXT_GRAPHIC_OTHER", 3.0, "text ink to graphic foreground"
    return "GRAPHIC_GRAPHIC", 0.0, "non-text foreground relation; semantic adjudication required if contact"


def evidence_triptych(image: np.ndarray, mask: np.ndarray, bbox: tuple[int,int,int,int], pad: int = 6) -> tuple[Image.Image, Image.Image]:
    h,w = mask.shape
    x0,y0,x1,y1 = bbox
    x0,y0,x1,y1 = max(0,x0-pad),max(0,y0-pad),min(w,x1+pad),min(h,y1+pad)
    orig = image[y0:y1,x0:x1].copy()
    m = mask[y0:y1,x0:x1] > 0
    overlay = orig.copy()
    overlay[m] = np.array([255,0,0],dtype=np.uint8)
    monly = np.full_like(orig,255)
    monly[m] = 0
    spacer = np.full((orig.shape[0],4,3),235,dtype=np.uint8)
    trip = np.concatenate([orig,spacer,overlay,spacer,monly],axis=1)
    one = Image.fromarray(trip)
    eight = one.resize((one.width*8,one.height*8),Image.Resampling.NEAREST)
    return one,eight


def main() -> None:
    ensure_dirs()
    if sha256(PDF) != PDF_SHA256:
        raise RuntimeError("official R104 PDF SHA mismatch")
    if PDF.stat().st_size != 4_967_222:
        raise RuntimeError("official R104 PDF size mismatch")
    doc = fitz.open(PDF)
    if doc.page_count != 817:
        raise RuntimeError("official R104 page count mismatch")
    if round(doc[0].rect.width,3) != 595.276 or round(doc[0].rect.height,3) != 841.890:
        raise RuntimeError("official R104 page geometry mismatch")

    needle = "接受–拒绝抽样拒绝候选后不输出该候选"
    locator_matches = []
    for i in range(doc.page_count):
        txt = doc[i].get_text("text")
        if needle in txt.replace(" ", "").replace("\n", ""):
            locator_matches.append(i+1)
    if locator_matches != [PHYSICAL_PAGE]:
        raise RuntimeError(f"locator not unique: {locator_matches}")

    page = doc[PAGE_INDEX]
    full200 = render_page(page, 200)
    full300 = render_page(page, 300)
    full200.save(ROOT / "renders/full_page_200dpi.png", dpi=(200,200))
    full300.save(ROOT / "renders/full_page_300dpi.png", dpi=(300,300))
    fig_xyxy = rect_px(FIG_RECT_PT, SCALE_300)
    body_xyxy = rect_px(BODY_RECT_PT, SCALE_300)
    fig = full300.crop(fig_xyxy)
    standalone = full300.crop(body_xyxy)
    fig.save(ROOT / "renders/figure_crop_300dpi.png", dpi=(300,300))
    standalone.save(ROOT / "renders/standalone_300dpi.png", dpi=(300,300))
    fig.convert("L").save(ROOT / "renders/grayscale_300dpi.png", dpi=(300,300))
    fig_arr = np.asarray(fig.convert("RGB")).copy()
    h,w = fig_arr.shape[:2]

    raw = page.get_text("rawdict")
    glyph_rows: list[dict] = []
    glyph_masks: dict[str,np.ndarray] = {}
    parent_chars: dict[str,list[str]] = defaultdict(list)
    parent_masks: dict[str,np.ndarray] = {k: np.zeros((h,w),dtype=np.uint8) for k in PARENT_META}
    parent_bboxes: dict[str,list[int]] = {}
    counters: Counter[str] = Counter()
    safe_rows: list[dict] = []

    for block in raw["blocks"]:
        if block.get("type") != 0 or block.get("number") not in range(22,31):
            continue
        for line_no,line in enumerate(block.get("lines",[])):
            for span_no,span in enumerate(line.get("spans",[])):
                for ch in span.get("chars",[]):
                    char = ch["c"]
                    if not char.strip():
                        continue
                    bbox_pt = tuple(float(v) for v in ch["bbox"])
                    if bbox_pt[1] < 497 or bbox_pt[3] > 655:
                        continue
                    parent = assign_parent(block["number"],bbox_pt)
                    counters[parent] += 1
                    gid = f"GLYPH_{parent}_{counters[parent]:03d}"
                    safe = safe_id(gid)
                    bbox = crop_bbox_from_page_bbox(bbox_pt,fig_xyxy)
                    bg = background_for_parent(parent)
                    mask = glyph_mask_for_bbox(fig_arr,bbox,bg,rgb_from_int(span["color"]))
                    glyph_masks[gid] = mask
                    parent_masks[parent] = cv2.bitwise_or(parent_masks[parent],mask)
                    parent_chars[parent].append(char)
                    mb = bbox_from_mask(mask)
                    iw,ih,area = ink_metrics(mask)
                    codepoint = f"U+{ord(char):04X}"
                    cls = classify_char(char,parent)
                    pt_size = float(span["size"])
                    row = {
                        "glyph_id":gid,"safe_filename":safe,"parent_id":parent,"char":char,
                        "codepoint":codepoint,"unicode_name":unicodedata.name(char,"UNNAMED"),
                        "class":cls,"pdf_block":block["number"],"pdf_line":line_no,"pdf_span":span_no,
                        "font":span["font"],"pdf_font_size_pt":f"{pt_size:.4f}","pdf_color_rgb":str(rgb_from_int(span["color"])),
                        "bbox_pt_x0":f"{bbox_pt[0]:.4f}","bbox_pt_y0":f"{bbox_pt[1]:.4f}","bbox_pt_x1":f"{bbox_pt[2]:.4f}","bbox_pt_y1":f"{bbox_pt[3]:.4f}",
                        "bbox_px_x0":bbox[0],"bbox_px_y0":bbox[1],"bbox_px_x1":bbox[2],"bbox_px_y1":bbox[3],
                        "raw_mask_bbox_px":json.dumps(mb),"h_ink_px":ih,"w_ink_px":iw,"ink_area_px":area,
                        "threshold_local_background_delta":20,"mask_nonempty":str(bool(area)).lower(),
                        "source_pdf":str(PDF),"physical_page":PHYSICAL_PAGE,
                    }
                    glyph_rows.append(row)
                    safe_rows.append({"element_id":gid,"safe_filename":safe+".png","kind":"GLYPH_MASK"})
                    Image.fromarray(mask).save(ROOT / "machine/glyph_masks" / f"{safe}.png")
                    evidence_bbox = mb if mb else bbox
                    one,eight = evidence_triptych(fig_arr,mask,evidence_bbox)
                    one.save(ROOT / "machine/glyph_evidence_1x" / f"{safe}__triptych_1x.png")
                    eight.save(ROOT / "machine/glyph_evidence_8x" / f"{safe}__triptych_8x_nearest.png")

    if len(glyph_rows) != 132:
        raise RuntimeError(f"expected 132 visible glyphs, got {len(glyph_rows)}")

    # Parent bboxes from final visible raw masks.
    text_objects: list[dict] = []
    for pid,(otype,role,panel) in PARENT_META.items():
        mb = bbox_from_mask(parent_masks[pid])
        if mb is None:
            raise RuntimeError(f"empty parent mask: {pid}")
        parent_bboxes[pid] = list(mb)
        text_objects.append({
            "object_id":pid,"object_type":"TEXT","source_kind":otype,"role":role,"panel":panel,
            "visible_text":"".join(parent_chars[pid]),"mask_file":f"machine/parent_masks/{safe_id(pid)}.png",
            "bbox_px":json.dumps(mb),"foreground_pixels":int(np.count_nonzero(parent_masks[pid])),
            "source_mapping":"official PDF rawdict blocks 22-30; source node/caption mapping",
        })
        safe_rows.append({"element_id":pid,"safe_filename":safe_id(pid)+".png","kind":"TEXT_PARENT_MASK"})
    (ROOT / "machine/parent_masks").mkdir(parents=True,exist_ok=True)
    for pid,mask in parent_masks.items():
        Image.fromarray(mask).save(ROOT / "machine/parent_masks" / f"{safe_id(pid)}.png")

    graphic_rows: list[dict] = []
    graphic_masks: dict[str,np.ndarray] = {}
    for spec in GRAPHICS:
        bbox = page_bbox_to_crop_bbox(spec.page_bbox,fig_xyxy,pad=6)
        cm = alpha_color_mask(fig_arr,bbox,spec.target_rgb,list(spec.bg_rgbs))
        mask = geometry_gate(cm,spec,fig_xyxy)
        graphic_masks[spec.object_id] = mask
        mb = bbox_from_mask(mask)
        iw,ih,area = ink_metrics(mask)
        if area == 0:
            raise RuntimeError(f"empty graphic mask: {spec.object_id}")
        safe = safe_id(spec.object_id)
        Image.fromarray(mask).save(ROOT / "machine/graphic_masks" / f"{safe}.png")
        safe_rows.append({"element_id":spec.object_id,"safe_filename":safe+".png","kind":"GRAPHIC_MASK"})
        graphic_rows.append({
            "object_id":spec.object_id,"object_type":"GRAPHIC","role":spec.role,"panel":spec.panel,
            "shape":spec.shape,"source_mapping":spec.source_map,"pdf_draw_refs":spec.pdf_draw_refs,
            "target_rgb":str(spec.target_rgb),"background_rgbs":str(spec.bg_rgbs),
            "declared_page_bbox_pt":json.dumps(spec.page_bbox),"raw_mask_bbox_px":json.dumps(mb),
            "h_ink_px":ih,"w_ink_px":iw,"foreground_pixels":area,
            "mask_file":f"machine/graphic_masks/{safe}.png","mask_nonempty":"true",
        })

    # Double-border required pre-occlusion / opaque-gap / final-visible evidence.
    m2 = next(s for s in GRAPHICS if s.object_id == "G_OUT_R2_DOUBLE_BORDER")
    bx = crop_bbox_from_page_bbox(m2.page_bbox,fig_xyxy)
    cx,cy=(bx[0]+bx[2])//2,(bx[1]+bx[3])//2
    radius=int(round(((bx[2]-bx[0])+(bx[3]-bx[1]))/4.0))
    pre=np.zeros((h,w),dtype=np.uint8)
    gap=np.zeros((h,w),dtype=np.uint8)
    cv2.circle(pre,(cx,cy),radius,255,max(1,int(round(2.98883*SCALE_300))),lineType=cv2.LINE_8)
    cv2.circle(gap,(cx,cy),radius,255,max(1,int(round(1.09590*SCALE_300))),lineType=cv2.LINE_8)
    final_model=cv2.bitwise_and(pre,cv2.bitwise_not(gap))
    Image.fromarray(pre).save(ROOT / "machine/graphic_special_masks/G_OUT_R2__pre_occlusion_outer_blue_model.png")
    Image.fromarray(gap).save(ROOT / "machine/graphic_special_masks/G_OUT_R2__opaque_white_gap_model.png")
    Image.fromarray(final_model).save(ROOT / "machine/graphic_special_masks/G_OUT_R2__final_visible_model.png")
    Image.fromarray(graphic_masks[m2.object_id]).save(ROOT / "machine/graphic_special_masks/G_OUT_R2__final_visible_observed.png")

    excluded_rows = [
        {"component_id":f"BG_CAND_FILL_{x}","pdf_draw_refs":f"draw[{i}] fill","disposition":"EXCLUDED_FROM_FOREGROUND_PAIRS","reason":"soft-gray node interior is background fill, not semantic foreground"}
        for x,i in zip(["L1","L2","L3","R1","R2","R3"],range(6,12))
    ]
    excluded_rows += [
        {"component_id":f"BG_OUT_FILL_{x}","pdf_draw_refs":f"draw[{i}] fill","disposition":"EXCLUDED_FROM_FOREGROUND_PAIRS","reason":"white output-node interior is background fill, not semantic foreground"}
        for x,i in zip(["L1","L3","R1","R2","R3"],[12,13,16,17,19])
    ]
    excluded_rows.append({"component_id":"BG_OUT_R2_OPAQUE_WHITE_GAP","pdf_draw_refs":"draw[18] stroke","disposition":"OPAQUE_BACKGROUND_ACCOUNTED","reason":"real double-border white gap; pre/opaque/final-visible masks preserved; final quality uses observed final-visible blue border"})
    excluded_rows.append({"component_id":"LOOPS_NONE","pdf_draw_refs":"none","disposition":"EXCLUDED_BY_ABSENCE","reason":"source and PDF contain no loop edge in this figure"})
    excluded_rows.append({"component_id":"MATH_RULES_NONE","pdf_draw_refs":"none","disposition":"EXCLUDED_BY_ABSENCE","reason":"Y_i uses glyph-stream subscript digits; no fraction/root/accent/rule path exists"})

    all_objects = text_objects + graphic_rows
    if len(all_objects) != 40:
        raise RuntimeError(f"expected 40 semantic foreground objects, got {len(all_objects)}")
    object_masks = {**parent_masks,**graphic_masks}
    object_by_id = {r["object_id"]:r for r in all_objects}

    pair_rows: list[dict] = []
    critical_rows: list[dict] = []
    for idx,(aid,bid) in enumerate(combinations([r["object_id"] for r in all_objects],2),start=1):
        a,b=object_by_id[aid],object_by_id[bid]
        ma,mb=object_masks[aid],object_masks[bid]
        inter=cv2.bitwise_and(ma,mb)
        overlap=int(np.count_nonzero(inter))
        clearance=mask_clearance(ma,mb)
        ba=bbox_from_mask(ma); bb=bbox_from_mask(mb)
        assert ba is not None and bb is not None
        bbox_gap=rect_distance(ba,bb)
        cat,threshold,basis=pair_category(a,b)
        pid=f"PAIR-{idx:04d}"
        evidence=""
        bbox_is_gate = cat == "TEXT_TEXT" and bbox_gap <= 12.0
        if overlap>0 or (not math.isnan(clearance) and clearance<=12.0) or bbox_is_gate:
            roi=(min(ba[0],bb[0]),min(ba[1],bb[1]),max(ba[2],bb[2]),max(ba[3],bb[3]))
            x0,y0,x1,y1=roi
            x0,y0=max(0,x0-8),max(0,y0-8); x1,y1=min(w,x1+8),min(h,y1+8)
            orig=fig_arr[y0:y1,x0:x1].copy()
            am=ma[y0:y1,x0:x1]>0; bm=mb[y0:y1,x0:x1]>0
            ov=orig.copy()
            ov[am]=np.array([255,0,0],dtype=np.uint8)
            ov[bm]=np.array([0,120,255],dtype=np.uint8)
            ov[am & bm]=np.array([255,0,255],dtype=np.uint8)
            onlya=np.full_like(orig,255); onlya[am]=0
            onlyb=np.full_like(orig,255); onlyb[bm]=0
            onlyi=np.full_like(orig,255); onlyi[am&bm]=0
            spacer=np.full((orig.shape[0],4,3),235,dtype=np.uint8)
            strip=np.concatenate([orig,spacer,ov,spacer,onlya,spacer,onlyb,spacer,onlyi],axis=1)
            one=Image.fromarray(strip)
            one_name=f"{pid}__{safe_id(aid)}__{safe_id(bid)}__1x.png"
            eight_name=f"{pid}__{safe_id(aid)}__{safe_id(bid)}__8x_nearest.png"
            one.save(ROOT / "machine/pair_evidence_1x" / one_name)
            one.resize((one.width*8,one.height*8),Image.Resampling.NEAREST).save(ROOT / "machine/pair_evidence_8x" / eight_name)
            evidence=f"machine/pair_evidence_1x/{one_name}|machine/pair_evidence_8x/{eight_name}"
            critical_rows.append({"pair_id":pid,"a_id":aid,"b_id":bid,"overlap_px":overlap,"clearance_px":f"{clearance:.3f}","bbox_gap_px":f"{bbox_gap:.3f}","category":cat,"evidence":evidence})
        pair_rows.append({
            "pair_id":pid,"a_id":aid,"b_id":bid,"a_type":a["object_type"],"b_type":b["object_type"],
            "category":cat,"hard_protocol_threshold_px":f"{threshold:.1f}","measurement_basis":basis,
            "raw_mask_overlap_px":overlap,"raw_mask_clearance_px":f"{clearance:.3f}","bbox_clearance_px":f"{bbox_gap:.3f}",
            "a_mask_nonempty":"true","b_mask_nonempty":"true","critical_or_near":str(bool(evidence)).lower(),"evidence_paths":evidence,
        })
    if len(pair_rows) != math.comb(40,2):
        raise RuntimeError("pair denominator mismatch")

    # Reviewable contact sheets for every C(40,2) pair.  These contain only
    # machine identity/measurement labels and colored masks; no reviewer or
    # decision fields are generated here.
    pair_sheet_rows=[]
    pair_font=ImageFont.load_default()
    thumb_size=(485,173)
    cell_size=(520,220)
    per_pair_sheet=20
    for sheet_no,start in enumerate(range(0,len(pair_rows),per_pair_sheet),start=1):
        subset=pair_rows[start:start+per_pair_sheet]
        sheet=Image.new("RGB",(cell_size[0]*4,cell_size[1]*5),(244,244,244))
        sd=ImageDraw.Draw(sheet)
        for local,row in enumerate(subset):
            aid,bid=row["a_id"],row["b_id"]
            ma,mb=object_masks[aid]>0,object_masks[bid]>0
            ov=fig_arr.copy()
            ov[ma]=np.array([255,0,0],dtype=np.uint8)
            ov[mb]=np.array([0,110,255],dtype=np.uint8)
            ov[ma & mb]=np.array([255,0,255],dtype=np.uint8)
            thumb=Image.fromarray(ov).resize(thumb_size,Image.Resampling.LANCZOS)
            col,rowno=local%4,local//4
            ox,oy=col*cell_size[0],rowno*cell_size[1]
            sd.text((ox+4,oy+4),f"{row['pair_id']} {aid} / {bid}",fill="black",font=pair_font)
            sd.text((ox+4,oy+18),f"overlap={row['raw_mask_overlap_px']} clearance={row['raw_mask_clearance_px']} px",fill="black",font=pair_font)
            sheet.paste(thumb,(ox+4,oy+40))
        name=f"pair_contact_sheet_{sheet_no:02d}__1x_overview.png"
        sheet.save(ROOT / "machine/pair_contact_sheets" / name)
        pair_sheet_rows.append({"sheet_id":f"PAIR-SHEET-{sheet_no:02d}","path":f"machine/pair_contact_sheets/{name}","first_pair_id":subset[0]["pair_id"],"last_pair_id":subset[-1]["pair_id"],"pair_count":len(subset)})

    # Machine-only edge/clip inventory.  Pixel contact with a crop edge is a
    # necessary alarm, not a reviewer judgment.  The caption is intentionally
    # outside the standalone-body view and is therefore recorded as excluded
    # there rather than reported as clipped.
    sx0,sy0,sx1,sy1=(body_xyxy[0]-fig_xyxy[0],body_xyxy[1]-fig_xyxy[1],
                     body_xyxy[2]-fig_xyxy[0],body_xyxy[3]-fig_xyxy[1])
    clip_rows=[]
    for obj in all_objects:
        oid=obj["object_id"]
        mask=object_masks[oid]
        bb=bbox_from_mask(mask)
        assert bb is not None
        edge_pixels=int(np.count_nonzero(mask[0,:]))+int(np.count_nonzero(mask[-1,:]))+int(np.count_nonzero(mask[:,0]))+int(np.count_nonzero(mask[:,-1]))
        fig_clear=min(bb[0],bb[1],w-bb[2],h-bb[3])
        if oid=="TXT_CAPTION":
            standalone_disposition="EXCLUDED_CAPTION_OUTSIDE_STANDALONE_BODY"
            standalone_edge_pixels=""
            standalone_clearance=""
        else:
            sub=mask[sy0:sy1,sx0:sx1]
            sbb=bbox_from_mask(sub)
            if sbb is None:
                standalone_edge_pixels="NOT_PRESENT"
                standalone_clearance="NOT_PRESENT"
            else:
                sh,sw=sub.shape
                standalone_edge_pixels=str(int(np.count_nonzero(sub[0,:]))+int(np.count_nonzero(sub[-1,:]))+int(np.count_nonzero(sub[:,0]))+int(np.count_nonzero(sub[:,-1])))
                standalone_clearance=str(min(sbb[0],sbb[1],sw-sbb[2],sh-sbb[3]))
            standalone_disposition="IN_SCOPE"
        clip_rows.append({"object_id":oid,"figure_edge_contact_pixels":edge_pixels,
                          "figure_min_edge_clearance_px":fig_clear,
                          "standalone_disposition":standalone_disposition,
                          "standalone_edge_contact_pixels":standalone_edge_pixels,
                          "standalone_min_edge_clearance_px":standalone_clearance})

    # Draw full object measurement overlay.
    overlay=fig.copy()
    draw=ImageDraw.Draw(overlay)
    palette=[(220,20,60),(0,112,192),(0,150,90),(180,90,0),(120,60,170)]
    for i,obj in enumerate(all_objects):
        bb=bbox_from_mask(object_masks[obj["object_id"]])
        assert bb is not None
        color=palette[i%len(palette)]
        draw.rectangle(bb,outline=color,width=2)
        draw.text((bb[0],max(0,bb[1]-10)),str(i+1),fill=color)
        obj["overlay_index"]=i+1
    overlay.save(ROOT / "renders/after_text_measurement_overlay_300dpi.png",dpi=(300,300))

    # Per-object numbered key avoids unreadable long IDs on the overlay.
    write_csv(ROOT / "inventories/overlay_index_key.csv",[
        {"overlay_index":o["overlay_index"],"object_id":o["object_id"],"role":o["role"],"panel":o["panel"],"bbox_px":o["bbox_px"] if o["object_type"]=="TEXT" else o["raw_mask_bbox_px"]}
        for o in all_objects], ["overlay_index","object_id","role","panel","bbox_px"])

    # Contact sheets: 12 glyph triptychs per sheet, actual evidence is preserved at 8x nearest.
    font=ImageFont.load_default()
    per_sheet=12
    sheet_rows=[]
    for sheet_no,start in enumerate(range(0,len(glyph_rows),per_sheet),start=1):
        subset=glyph_rows[start:start+per_sheet]
        cells=[]
        for row in subset:
            gid=row["glyph_id"]
            p8=Image.open(ROOT / "machine/glyph_evidence_8x" / f"{safe_id(gid)}__triptych_8x_nearest.png").convert("RGB")
            label=f"{gid} {row['codepoint']}"
            cw=max(p8.width,520); ch=p8.height+22
            cell=Image.new("RGB",(cw,ch),"white")
            cell.paste(p8,(0,22))
            ImageDraw.Draw(cell).text((4,4),label,fill="black",font=font)
            cells.append(cell)
        sw=max(c.width for c in cells)
        sh=sum(c.height for c in cells)
        sheet=Image.new("RGB",(sw,sh),(245,245,245))
        yy=0
        for c in cells:
            sheet.paste(c,(0,yy)); yy+=c.height
        name=f"glyph_contact_sheet_{sheet_no:02d}__8x_nearest.png"
        sheet.save(ROOT / "machine/glyph_contact_sheets" / name)
        sheet_rows.append({"sheet_id":f"SHEET-{sheet_no:02d}","path":f"machine/glyph_contact_sheets/{name}","first_glyph_id":subset[0]["glyph_id"],"last_glyph_id":subset[-1]["glyph_id"],"glyph_count":len(subset)})

    source_text=SOURCE.read_text(encoding="utf-8")
    source_font_rows=[
        {"scope":"slfig global/every node","declared_pt":"9.2","leading_pt":"11.0","graphics_scale":"1.0","effective_pt":"9.2","source_token":"font=\\fontsize{9.2pt}{11.0pt}"},
        {"scope":"panel titles","declared_pt":"10.2","leading_pt":"12.2","graphics_scale":"1.0","effective_pt":"10.2","source_token":"title/.style fontsize{10.2pt}{12.2pt}"},
        {"scope":"reject markers","declared_pt":"14.0","leading_pt":"14.0","graphics_scale":"1.0","effective_pt":"14.0","source_token":"reject/.style fontsize{14pt}{14pt}"},
        {"scope":"annotation notes","declared_pt":"8.5","leading_pt":"10.4","graphics_scale":"1.0","effective_pt":"8.5","source_token":"note/.style fontsize{8.5pt}{10.4pt}"},
        {"scope":"caption","declared_pt":"document-controlled","leading_pt":"document-controlled","graphics_scale":"1.0","effective_pt":"PDF observed 9.86-9.96","source_token":"caption outside tikzpicture"},
    ]
    flags=[]
    for token in ["resizebox","scalebox","transform shape","\\tiny","\\scriptsize","\\footnotesize","\\small","\\large"]:
        flags.append({"token":token,"occurrences":source_text.count(token),"disposition":"none present" if source_text.count(token)==0 else "present; inspect"})

    # Per-glyph ratio/reference machine measurements (no reviewer decision fields).
    class_groups=defaultdict(list)
    for row in glyph_rows:
        class_groups[(row["parent_id"],row["class"])].append(row["h_ink_px"])
    for row in glyph_rows:
        vals=class_groups[(row["parent_id"],row["class"])]
        med=float(np.median(vals)) if vals else math.nan
        row["parent_class_median_h_px"]=f"{med:.3f}"
        row["h_over_parent_class_median"]=f"{row['h_ink_px']/med:.4f}" if med else ""

    write_csv(ROOT / "inventories/glyph_inventory_machine.csv",glyph_rows,list(glyph_rows[0].keys()))
    write_csv(ROOT / "inventories/text_parent_inventory_machine.csv",text_objects,list(text_objects[0].keys()))
    write_csv(ROOT / "inventories/graphic_inventory_machine.csv",graphic_rows,list(graphic_rows[0].keys()))
    write_csv(ROOT / "inventories/excluded_drawing_components.csv",excluded_rows,["component_id","pdf_draw_refs","disposition","reason"])
    write_csv(ROOT / "inventories/object_inventory_machine.csv",all_objects,sorted({k for r in all_objects for k in r.keys()}))
    write_csv(ROOT / "inventories/id_safe_filename_map.csv",safe_rows,["element_id","safe_filename","kind"])
    write_csv(ROOT / "inventories/pair_inventory_machine.csv",pair_rows,list(pair_rows[0].keys()))
    write_csv(ROOT / "inventories/critical_pair_inventory_machine.csv",critical_rows,list(critical_rows[0].keys()) if critical_rows else ["pair_id","a_id","b_id","overlap_px","clearance_px","bbox_gap_px","category","evidence"])
    write_csv(ROOT / "inventories/pair_contact_sheet_index.csv",pair_sheet_rows,list(pair_sheet_rows[0].keys()))
    write_csv(ROOT / "inventories/clip_inventory_machine.csv",clip_rows,list(clip_rows[0].keys()))
    write_csv(ROOT / "inventories/glyph_contact_sheet_index.csv",sheet_rows,list(sheet_rows[0].keys()))
    write_csv(ROOT / "inventories/source_font_inventory_machine.csv",source_font_rows,list(source_font_rows[0].keys()))
    write_csv(ROOT / "inventories/source_scaling_token_scan.csv",flags,["token","occurrences","disposition"])

    # Machine-only cross-checks and identity. No manual booleans/decisions/notes.
    all_draw_refs=set()
    for spec in GRAPHICS:
        all_draw_refs.update(int(x) for x in re.findall(r"draw\[(\d+)\]",spec.pdf_draw_refs))
    in_scope_draw_refs=set(range(4,28))
    summary={
        "uid":FIG_UID,"handoff_id":HANDOFF_ID,"review_role":"SA1","reviewer_model":"gpt-5.6-sol","reasoning_effort":"xhigh",
        "official_pdf_resolved_path":str(PDF.resolve()),"official_pdf_bytes":PDF.stat().st_size,"official_pdf_sha256":sha256(PDF),
        "official_pdf_pages":doc.page_count,"official_page_size_pt":[page.rect.width,page.rect.height],"physical_page":PHYSICAL_PAGE,"printed_page":"649","caption":"图32.10 接受–拒绝抽样拒绝候选后不输出该候选；MH拒绝候选后把当前状态再次记入链，因此输出通常相关而非独立",
        "locator_needle":needle,"locator_matches":locator_matches,
        "source_resolved_path":str(SOURCE.resolve()),"source_bytes":SOURCE.stat().st_size,"source_sha256":sha256(SOURCE),
        "tex_execution":"DISABLED","source_writer":"NONE","fresh_root_absent_pre_dispatch":True,
        "figure_crop_pt":[FIG_RECT_PT.x0,FIG_RECT_PT.y0,FIG_RECT_PT.x1,FIG_RECT_PT.y1],"figure_crop_full_page_px_300dpi":list(fig_xyxy),"figure_crop_native_dimensions_px":[w,h],
        "standalone_crop_pt":[BODY_RECT_PT.x0,BODY_RECT_PT.y0,BODY_RECT_PT.x1,BODY_RECT_PT.y1],"standalone_crop_full_page_px_300dpi":list(body_xyxy),"standalone_native_dimensions_px":list(standalone.size),
        "full_page_300dpi_dimensions_px":list(full300.size),"full_page_200dpi_dimensions_px":list(full200.size),
        "glyph_count_visible_nonspace":len(glyph_rows),"glyph_mask_count":len(list((ROOT/"machine/glyph_masks").glob("*.png"))),"glyph_1x_count":len(list((ROOT/"machine/glyph_evidence_1x").glob("*.png"))),"glyph_8x_count":len(list((ROOT/"machine/glyph_evidence_8x").glob("*.png"))),
        "text_parent_count":len(text_objects),"graphic_foreground_object_count":len(graphic_rows),"semantic_foreground_object_count":len(all_objects),
        "expected_pair_count":math.comb(len(all_objects),2),"actual_pair_count":len(pair_rows),"critical_pair_count":len(critical_rows),
        "empty_glyph_mask_count":sum(1 for r in glyph_rows if r["mask_nonempty"]!="true"),"empty_graphic_mask_count":sum(1 for r in graphic_rows if r["mask_nonempty"]!="true"),
        "raw_pair_overlap_nonzero_count":sum(1 for r in pair_rows if r["raw_mask_overlap_px"]>0),"raw_pair_overlap_pixel_sum":sum(int(r["raw_mask_overlap_px"]) for r in pair_rows),
        "figure_crop_edge_contact_pixel_sum":sum(int(r["figure_edge_contact_pixels"]) for r in clip_rows),
        "figure_crop_min_object_edge_clearance_px":min(int(r["figure_min_edge_clearance_px"]) for r in clip_rows),
        "standalone_body_edge_contact_pixel_sum":sum(int(r["standalone_edge_contact_pixels"]) for r in clip_rows if r["standalone_edge_contact_pixels"] not in ("","NOT_PRESENT")),
        "standalone_body_missing_in_scope_object_count":sum(1 for r in clip_rows if r["standalone_disposition"]=="IN_SCOPE" and r["standalone_edge_contact_pixels"]=="NOT_PRESENT"),
        "figure_pdf_drawing_refs_expected":sorted(in_scope_draw_refs),"figure_pdf_drawing_refs_mapped":sorted(all_draw_refs),"unmapped_figure_pdf_drawing_refs":sorted(in_scope_draw_refs-all_draw_refs),
        "math_rule_object_count":0,"math_rule_disposition":"No drawing/path math rules; Y_i subscripts are PDF glyph-stream characters and are individually inventoried.",
        "loop_object_count":0,"loop_disposition":"Source and official PDF contain no loop edge in this comparison figure.",
        "ads_check_pending_final_seal":True,"manual_review_fields_generated_by_machine":False,
    }
    (ROOT/"IDENTITY_AND_MACHINE_SUMMARY.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding="utf-8")
    (ROOT/"inventories/render_geometry.json").write_text(json.dumps({k:summary[k] for k in ["physical_page","official_page_size_pt","figure_crop_pt","figure_crop_full_page_px_300dpi","figure_crop_native_dimensions_px","standalone_crop_pt","standalone_crop_full_page_px_300dpi","standalone_native_dimensions_px","full_page_300dpi_dimensions_px","full_page_200dpi_dimensions_px"]},ensure_ascii=False,indent=2),encoding="utf-8")


if __name__ == "__main__":
    main()
