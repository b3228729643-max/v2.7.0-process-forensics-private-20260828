from __future__ import annotations

import csv
import hashlib
import json
import math
import shutil
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

import cv2
import fitz
import numpy as np
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习")
EV = ROOT / r"v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P547-01\STRICT_R12_SA3_BLIND_R98_20260824"
PDF = ROOT / r"v2.7.0\_work\source\v2.7.0\src\build\strict_current_r98_fullbook\main_full.pdf"
SRC = ROOT / r"v2.7.0\_work\worktrees\dialogue_A_visual\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C01\fig_v5_c01_transition_graph.tex"
CAL_PDF = EV / r"_tmp\punctuation_calibration_official.pdf"
PAGE_INDEX = 590
SCALE_300 = 300.0 / 72.0
SCALE_200 = 200.0 / 72.0
FIG_CROP = (280, 1180, 2160, 1850)  # exact whole-page 300-dpi integer pixels
GRAPH_CROP = (280, 1210, 2160, 1770)


PARENTS = {
    "T01": dict(panel="LEFT", role="TITLE", text="行随机 A：a_ij = P(i→j)", line=32, pt=10.2),
    "T02": dict(panel="LEFT", role="STATE_LABEL", text="1", line=33, pt=10.2),
    "T03": dict(panel="LEFT", role="STATE_LABEL", text="2", line=34, pt=10.2),
    "T04": dict(panel="LEFT", role="EDGE_LABEL", text="0.7", line=35, pt=11.6),
    "T05": dict(panel="LEFT", role="EDGE_LABEL", text="0.8", line=36, pt=11.6),
    "T06": dict(panel="LEFT", role="EDGE_FORMULA", text="a_12 = 0.3", line=37, pt=11.6),
    "T07": dict(panel="LEFT", role="EDGE_FORMULA", text="a_21 = 0.2", line=38, pt=11.6),
    "T08": dict(panel="LEFT", role="FORMULA_BLOCK", text="A = [[0.7,0.3],[0.2,0.8]]", line=41, pt=11.8),
    "T09": dict(panel="LEFT", role="ANNOTATION", text="每行和为1；", line=42, pt=9.8),
    "T10": dict(panel="LEFT", role="UPDATE_FORMULA", text="rho_(t+1) = rho_t A", line=42, pt=11.6),
    "T11": dict(panel="BRIDGE", role="BRIDGE_TITLE", text="P = A^T", line=46, pt=12.0),
    "T12": dict(panel="BRIDGE", role="BRIDGE_BODY", text="物理边 i→j：a_ij = P_ji", line=47, pt=11.6),
    "T13": dict(panel="RIGHT", role="TITLE", text="列随机 P / PageRank：P_ji = P(i→j)", line=52, pt=10.2),
    "T14": dict(panel="RIGHT", role="STATE_LABEL", text="1", line=53, pt=10.2),
    "T15": dict(panel="RIGHT", role="STATE_LABEL", text="2", line=54, pt=10.2),
    "T16": dict(panel="RIGHT", role="EDGE_LABEL", text="0.7", line=55, pt=11.6),
    "T17": dict(panel="RIGHT", role="EDGE_LABEL", text="0.8", line=56, pt=11.6),
    "T18": dict(panel="RIGHT", role="EDGE_FORMULA", text="P_21 = 0.3", line=57, pt=11.6),
    "T19": dict(panel="RIGHT", role="EDGE_FORMULA", text="P_12 = 0.2", line=58, pt=11.6),
    "T20": dict(panel="RIGHT", role="FORMULA_BLOCK", text="P = [[0.7,0.2],[0.3,0.8]]", line=61, pt=11.8),
    "T21": dict(panel="RIGHT", role="ANNOTATION", text="每列和为1；", line=62, pt=9.8),
    "T22": dict(panel="RIGHT", role="UPDATE_FORMULA", text="p^(t+1) = P p^(t)", line=62, pt=11.6),
    "T23": dict(panel="CAPTION", role="CAPTION", text="图30.2 行随机约定下的两状态转移图，并给出到列随机PageRank约定的显式转置桥。", line=65, pt=10.0),
}


RULE_MAP = {
    13: "R01", 14: "R01", 16: "R02", 17: "R02", 20: "N01", 23: "N02",
    26: "E01", 27: "E01", 29: "BG01", 31: "E02", 32: "E02", 34: "BG02",
    36: "E03", 37: "E03", 39: "B01", 42: "R03", 43: "R03", 45: "E04",
    46: "E04", 48: "BG03", 50: "R04", 51: "R04", 54: "R05", 55: "R05",
    58: "H01", 59: "H01", 60: "H01", 61: "H01", 63: "R06", 64: "R06",
    66: "C01", 69: "R07", 70: "R07", 72: "R08", 73: "R08", 76: "R09",
    77: "R09", 79: "C02", 80: "C02", 82: "C03", 83: "C03", 86: "R10",
    87: "R10", 89: "R11", 90: "R11", 93: "N03", 96: "N04", 99: "E05",
    100: "E05", 102: "BG04", 104: "E06", 105: "E06", 107: "BG05", 109: "E07",
    110: "E07", 112: "B02", 115: "R12", 116: "R12", 118: "E08", 119: "E08",
    121: "BG06", 123: "R13", 124: "R13", 127: "R14", 128: "R14", 131: "H02",
    132: "H02", 133: "H02", 134: "H02", 136: "R15", 137: "R15",
}

MIXED_BACKGROUND_IDS = {"N01", "N02", "N03", "N04", "B01", "B02", "C01"}
PURE_BACKGROUND_IDS = {f"BG{i:02d}" for i in range(1, 7)}


def ensure_dirs() -> None:
    for rel in [
        "00_identity", "01_source", "02_renders", "03_objects", "04_glyphs/cards",
        "04_glyphs/masks", "04_glyphs/contact_sheets", "04_glyphs/calibration_cards",
        "05_pairs/critical", "06_primitives/record_masks", "06_primitives/record_cards",
        "06_primitives/contact_sheets", "07_views", "08_reports", "09_manifest",
    ]:
        (EV / rel).mkdir(parents=True, exist_ok=True)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def save_csv(path: Path, rows: list[dict], fields: list[str] | None = None) -> None:
    if fields is None:
        fields = []
        for row in rows:
            for key in row:
                if key not in fields:
                    fields.append(key)
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def pil_from_pix(pix: fitz.Pixmap) -> Image.Image:
    return Image.frombytes("RGB", (pix.width, pix.height), pix.samples)


def rgb_from_int(value: int) -> tuple[int, int, int]:
    return ((value >> 16) & 255, (value >> 8) & 255, value & 255)


def pixel_bbox_from_pt(bbox: list[float] | tuple[float, ...], origin=(0, 0)) -> tuple[int, int, int, int]:
    ox, oy = origin
    x0 = math.floor(float(bbox[0]) * SCALE_300) - ox
    y0 = math.floor(float(bbox[1]) * SCALE_300) - oy
    x1 = math.ceil(float(bbox[2]) * SCALE_300) - ox
    y1 = math.ceil(float(bbox[3]) * SCALE_300) - oy
    return x0, y0, x1, y1


def parent_for(block: int, x0: float) -> str:
    fixed = {
        12: "T01", 14: "T06", 15: "T07", 16: "T08", 18: "T11", 19: "T12",
        20: "T13", 22: "T18", 23: "T19", 24: "T20", 26: "T23",
    }
    if block in fixed:
        return fixed[block]
    if block == 13:
        if x0 < 100: return "T04"
        if x0 < 160: return "T02"
        if x0 < 230: return "T03"
        return "T05"
    if block == 17:
        return "T09" if x0 < 169.394 else "T10"
    if block == 21:
        if x0 < 350: return "T16"
        if x0 < 410: return "T14"
        if x0 < 480: return "T15"
        return "T17"
    if block == 25:
        return "T21" if x0 < 409.625 else "T22"
    raise ValueError(f"unmapped block {block}")


def draw_record_mask(page_rect: fitz.Rect, d: dict, clip: fitz.Rect, mode: str) -> np.ndarray:
    tmp = fitz.open()
    p = tmp.new_page(width=page_rect.width, height=page_rect.height)
    s = p.new_shape()
    for item in d["items"]:
        if item[0] == "l":
            s.draw_line(item[1], item[2])
        elif item[0] == "c":
            s.draw_bezier(item[1], item[2], item[3], item[4])
        elif item[0] == "re":
            s.draw_rect(item[1])
        else:
            raise ValueError(f"unknown path item {item[0]}")
    color = d.get("color") if mode in {"stroke", "both"} else None
    fill = d.get("fill") if mode in {"fill", "both"} else None
    if mode == "fill_geometry":
        fill = (0.0, 0.0, 0.0)
    if color is None and fill is None:
        return np.zeros((FIG_CROP[3] - FIG_CROP[1], FIG_CROP[2] - FIG_CROP[0]), dtype=bool)
    raw_cap = d.get("lineCap")
    line_cap = max(raw_cap) if isinstance(raw_cap, tuple) else int(raw_cap or 0)
    s.finish(
        width=float(d.get("width") or 1.0), color=color, fill=fill,
        lineCap=int(line_cap), lineJoin=int(d.get("lineJoin") or 0),
        dashes=d.get("dashes"), even_odd=bool(d.get("even_odd", False)),
        closePath=bool(d.get("closePath", False)),
        fill_opacity=float(d.get("fill_opacity") or 1.0), stroke_opacity=float(d.get("stroke_opacity") or 1.0),
    )
    s.commit()
    pix = p.get_pixmap(matrix=fitz.Matrix(SCALE_300, SCALE_300), clip=clip, alpha=False, colorspace=fitz.csRGB)
    arr = np.asarray(pil_from_pix(pix), dtype=np.int16)
    tmp.close()
    return np.max(np.abs(arr - 255), axis=2) >= 20


def dominant_background(arr: np.ndarray, bbox: tuple[int, int, int, int], exclusion: np.ndarray) -> np.ndarray:
    x0, y0, x1, y1 = bbox
    h, w = arr.shape[:2]
    rx0, ry0, rx1, ry1 = max(0, x0 - 4), max(0, y0 - 4), min(w, x1 + 4), min(h, y1 + 4)
    roi = arr[ry0:ry1, rx0:rx1]
    ring = np.ones(roi.shape[:2], bool)
    ix0, iy0, ix1, iy1 = x0 - rx0, y0 - ry0, x1 - rx0, y1 - ry0
    ring[max(0, iy0 + 2):max(0, iy1 - 2), max(0, ix0 + 2):max(0, ix1 - 2)] = False
    ring &= ~exclusion[ry0:ry1, rx0:rx1]
    px = roi[ring]
    if len(px) == 0:
        px = roi.reshape(-1, 3)
    q = (px // 8).astype(np.uint8)
    counts = Counter(map(tuple, q.tolist()))
    key = counts.most_common(1)[0][0]
    sel = np.all(q == np.array(key, dtype=np.uint8), axis=1)
    return np.median(px[sel], axis=0).astype(float)


def expected_color_mask(arr: np.ndarray, bbox: tuple[int, int, int, int], fg_rgb: tuple[int, int, int], bg: np.ndarray) -> np.ndarray:
    x0, y0, x1, y1 = bbox
    p = arr[y0:y1, x0:x1].astype(float)
    fg = np.array(fg_rgb, dtype=float)
    v = fg - bg
    denom = float(np.dot(v, v)) or 1.0
    t = np.sum((p - bg) * v, axis=2) / denom
    projection = bg + t[..., None] * v
    residual = np.linalg.norm(p - projection, axis=2)
    contrast = np.max(np.abs(p - bg), axis=2)
    return (t >= 0.045) & (t <= 1.18) & (residual <= 26.0) & (contrast >= 20.0)


def tight_bbox(mask: np.ndarray) -> tuple[int, int, int, int] | None:
    ys, xs = np.where(mask)
    if not len(xs):
        return None
    return int(xs.min()), int(ys.min()), int(xs.max() + 1), int(ys.max() + 1)


def classify_char(ch: str, raw_size: float) -> tuple[str, int]:
    low = {".", ",", "，", "。", ":", "：", ";", "；", "…", "·"}
    if ch in low:
        return "LOW_PROFILE_PUNCTUATION", 1
    if ch in {"+", "−", "-", "=", "≠", "≤", "≥", "∑"}:
        return "MATH_OPERATOR", 22
    cat = unicodedata.category(ch)
    if raw_size < 9.0:
        return "NATURAL_SCRIPT", 15
    code = ord(ch)
    if 0x2E80 <= code <= 0x9FFF or 0xF900 <= code <= 0xFAFF:
        return "CJK_FULL", 30
    if ch.isdigit() or cat == "Lu":
        return "LATIN_UPPER_DIGIT", 24
    if cat == "Ll" or ch.islower():
        return "LATIN_GREEK_XHEIGHT", 17
    return "MATH_BASE", 22


def make_triptych(original: np.ndarray, mask: np.ndarray, bbox: tuple[int, int, int, int], label: str, scale=8) -> Image.Image:
    x0, y0, x1, y1 = bbox
    pad = 3
    h, w = original.shape[:2]
    xa, ya, xb, yb = max(0, x0-pad), max(0, y0-pad), min(w, x1+pad), min(h, y1+pad)
    orig = original[ya:yb, xa:xb].copy()
    m = mask[ya:yb, xa:xb]
    over = orig.copy()
    over[m] = (255, 0, 0)
    only = np.full_like(orig, 255)
    only[m] = (0, 0, 0)
    ims = [Image.fromarray(x).resize((x.shape[1]*scale, x.shape[0]*scale), Image.Resampling.NEAREST) for x in (orig, over, only)]
    head = 34
    out = Image.new("RGB", (sum(x.width for x in ims), max(x.height for x in ims)+head), "white")
    d = ImageDraw.Draw(out)
    d.text((4, 3), label + " | ORIGINAL | TARGET OVERLAY | MASK ONLY | 8x nearest", fill="black")
    xx = 0
    for im in ims:
        out.paste(im, (xx, head)); xx += im.width
    return out


def add_contact_sheets(cards: list[tuple[str, Image.Image]], outdir: Path, prefix: str, per_sheet=12) -> list[dict]:
    register = []
    for si in range(0, len(cards), per_sheet):
        batch = cards[si:si+per_sheet]
        cols = 2
        rows = math.ceil(len(batch)/cols)
        cw = max(im.width for _, im in batch) + 12
        ch = max(im.height for _, im in batch) + 12
        sheet = Image.new("RGB", (cw*cols, ch*rows), (238,238,238))
        for ci, (ident, im) in enumerate(batch):
            col, row = ci % cols, ci // cols
            sheet.paste(im, (col*cw+6, row*ch+6))
            register.append({"id": ident, "sheet": f"{prefix}_{si//per_sheet+1:03d}.png", "cell": ci+1})
        sheet.save(outdir / f"{prefix}_{si//per_sheet+1:03d}.png")
    return register


def main() -> None:
    ensure_dirs()
    doc = fitz.open(PDF)
    page = doc[PAGE_INDEX]
    raw = page.get_text("rawdict", flags=fitz.TEXT_PRESERVE_LIGATURES | fitz.TEXT_PRESERVE_WHITESPACE)
    drawings = [d for d in page.get_drawings(extended=True) if int(d["seqno"]) in RULE_MAP]
    assert len(drawings) == 71, len(drawings)

    pix300 = page.get_pixmap(matrix=fitz.Matrix(SCALE_300, SCALE_300), alpha=False, colorspace=fitz.csRGB)
    full300 = pil_from_pix(pix300)
    assert full300.size == (2481, 3508), full300.size
    full300.save(EV / "02_renders/native_page591_pymupdf_300dpi_color.png")
    pix200 = page.get_pixmap(matrix=fitz.Matrix(SCALE_200, SCALE_200), alpha=False, colorspace=fitz.csRGB)
    full200 = pil_from_pix(pix200)
    full200.save(EV / "full_page_200dpi.png")
    fig = full300.crop(FIG_CROP)
    graph = full300.crop(GRAPH_CROP)
    fig.save(EV / "figure_crop_300dpi.png")
    graph.save(EV / "standalone_300dpi.png")
    fig.convert("L").save(EV / "grayscale_300dpi.png")
    arr = np.asarray(fig).copy()

    # Simple deterministic color-vision simulations, preserving the native pixel grid.
    sims = {
        "protanopia_300dpi.png": np.array([[0.567,0.433,0],[0.558,0.442,0],[0,0.242,0.758]]),
        "deuteranopia_300dpi.png": np.array([[0.625,0.375,0],[0.7,0.3,0],[0,0.3,0.7]]),
        "tritanopia_300dpi.png": np.array([[0.95,0.05,0],[0,0.433,0.567],[0,0.475,0.525]]),
    }
    for name, mat in sims.items():
        sim = np.clip(arr.astype(float) @ mat.T, 0, 255).astype(np.uint8)
        Image.fromarray(sim).save(EV / "07_views" / name)

    # Vector record pre/final/background masks and exhaustive primitive ledger.
    clip = fitz.Rect(FIG_CROP[0]/SCALE_300, FIG_CROP[1]/SCALE_300, FIG_CROP[2]/SCALE_300, FIG_CROP[3]/SCALE_300)
    recdata = []
    opaque = []
    command_rows = []
    for ri, d in enumerate(drawings, 1):
        seq = int(d["seqno"]); sid = RULE_MAP[seq]
        stroke = draw_record_mask(page.rect, d, clip, "stroke") if d.get("color") is not None else np.zeros(arr.shape[:2], bool)
        fill = draw_record_mask(page.rect, d, clip, "fill") if d.get("fill") is not None else np.zeros(arr.shape[:2], bool)
        fill_geometry = draw_record_mask(page.rect, d, clip, "fill_geometry") if d.get("fill") is not None else np.zeros(arr.shape[:2], bool)
        if sid in PURE_BACKGROUND_IDS:
            pre = np.zeros_like(stroke)
            bg = fill_geometry
        elif sid in MIXED_BACKGROUND_IDS:
            pre = stroke
            bg = fill_geometry
        else:
            pre = stroke | fill
            bg = np.zeros_like(stroke)
        if bg.any():
            opaque.append((seq, bg))
        for ci, item in enumerate(d["items"], 1):
            pts = []
            for val in item[1:]:
                if isinstance(val, fitz.Point): pts.append([float(val.x), float(val.y)])
                elif isinstance(val, fitz.Rect): pts.append([float(val.x0),float(val.y0),float(val.x1),float(val.y1)])
                else: pts.append(str(val))
            command_rows.append({
                "COMMAND_ID": f"V{len(command_rows)+1:03d}", "RECORD_ID": f"D{ri:03d}", "SEQNO": seq,
                "SEMANTIC_ID": sid, "COMMAND_INDEX": ci, "COMMAND_TYPE": item[0],
                "POINTS_PT_JSON": json.dumps(pts), "UNIQUE": "true",
            })
        recdata.append(dict(ri=ri, d=d, seq=seq, sid=sid, stroke=stroke, fill=fill, bg=bg, pre=pre))
    assert len(command_rows) == 143, len(command_rows)
    all_pre = np.zeros(arr.shape[:2], bool)
    all_final = np.zeros(arr.shape[:2], bool)
    record_rows = []
    record_cards = []
    for r in recdata:
        later_bg = np.zeros_like(r["pre"])
        for seq2, bg2 in opaque:
            if seq2 > r["seq"]:
                later_bg |= bg2
        final = r["pre"] & ~later_bg
        r["final"] = final
        all_pre |= r["pre"]; all_final |= final
        rid = f"D{r['ri']:03d}"
        Image.fromarray((r["pre"]*255).astype(np.uint8)).save(EV / "06_primitives/record_masks" / f"{rid}_pre.png")
        Image.fromarray((final*255).astype(np.uint8)).save(EV / "06_primitives/record_masks" / f"{rid}_final.png")
        if r["bg"].any():
            Image.fromarray((r["bg"]*255).astype(np.uint8)).save(EV / "06_primitives/record_masks" / f"{rid}_background.png")
        bb = tight_bbox(r["pre"] | r["bg"])
        assert bb is not None, (rid, r["seq"], r["sid"], r["d"]["type"], r["d"].get("rect"))
        card = make_triptych(arr, final if final.any() else r["bg"], bb, f"{rid} seq={r['seq']} {r['sid']}")
        card.save(EV / "06_primitives/record_cards" / f"{rid}_8x_card.png")
        record_cards.append((rid, card))
        d = r["d"]
        record_rows.append({
            "RECORD_ID": rid, "SEQNO": r["seq"], "SEMANTIC_ID": r["sid"], "PDF_TYPE": d["type"],
            "COMMAND_COUNT": len(d["items"]), "WIDTH_PT": d.get("width") if d.get("width") is not None else "",
            "WIDTH_PX_300DPI": round(float(d.get("width") or 0)*SCALE_300, 4),
            "STROKE_RGB": json.dumps(d.get("color")), "FILL_RGB": json.dumps(d.get("fill")),
            "PRE_PIXEL_COUNT": int(r["pre"].sum()), "BACKGROUND_PIXEL_COUNT": int(r["bg"].sum()),
            "FINAL_VISIBLE_PIXEL_COUNT": int(final.sum()), "OCCLUDED_PIXEL_COUNT": int((r["pre"] & later_bg).sum()),
            "PRE_MASK": f"06_primitives/record_masks/{rid}_pre.png",
            "FINAL_MASK": f"06_primitives/record_masks/{rid}_final.png",
            "CARD": f"06_primitives/record_cards/{rid}_8x_card.png",
            "NONEMPTY_PASS": str(bool((r["pre"] | r["bg"]).any())).lower(),
        })
    save_csv(EV / "06_primitives/vector_record_ledger.csv", record_rows)
    save_csv(EV / "06_primitives/vector_command_ledger.csv", command_rows)
    rec_register = add_contact_sheets(record_cards, EV / "06_primitives/contact_sheets", "vector_records", per_sheet=12)
    save_csv(EV / "06_primitives/vector_contact_register_pending.csv", rec_register)
    Image.fromarray((all_pre*255).astype(np.uint8)).save(EV / "06_primitives/all_foreground_pre_mask.png")
    Image.fromarray((all_final*255).astype(np.uint8)).save(EV / "06_primitives/all_foreground_final_mask.png")

    # Extract all 193 glyph records.
    chars = []
    for block in raw["blocks"]:
        if block.get("type") != 0 or int(block.get("number", -1)) not in range(12, 27):
            continue
        bn = int(block["number"])
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                for ch in span.get("chars", []):
                    c = ch.get("c", "")
                    if not c or c.isspace():
                        continue
                    parent = parent_for(bn, float(ch["bbox"][0]))
                    chars.append({
                        "c": c, "parent": parent, "block": bn, "bbox_pt": list(ch["bbox"]),
                        "bbox": pixel_bbox_from_pt(ch["bbox"], FIG_CROP[:2]), "origin_pt": list(ch["origin"]),
                        "raw_size": float(span["size"]), "font": span["font"], "color": int(span["color"]),
                    })
    assert len(chars) == 193, len(chars)
    for i, ch in enumerate(chars, 1):
        ch["id"] = f"G{i:03d}"
        ch["safe"] = f"G{i:03d}_U{ord(ch['c']):04X}_{ch['parent']}"

    # Candidate masks are generated from the final native PDF raster after exact vector-path subtraction,
    # then assigned by exclusive connected-component ownership. No raw bbox threshold alone is accepted.
    union_candidate = np.zeros(arr.shape[:2], bool)
    per_candidate = []
    bbox_coverage = np.zeros(arr.shape[:2], np.uint16)
    for ch in chars:
        x0,y0,x1,y1 = ch["bbox"]
        x0=max(0,x0);y0=max(0,y0);x1=min(arr.shape[1],x1);y1=min(arr.shape[0],y1)
        ch["bbox"]=(x0,y0,x1,y1)
        bbox_coverage[y0:y1,x0:x1] += 1
    for ch in chars:
        bg = dominant_background(arr, ch["bbox"], all_pre)
        ch["bg_rgb"] = [round(float(x), 3) for x in bg]
        local = expected_color_mask(arr, ch["bbox"], rgb_from_int(ch["color"]), bg)
        x0,y0,x1,y1 = ch["bbox"]
        local &= ~all_final[y0:y1,x0:x1]
        cm = np.zeros(arr.shape[:2], bool); cm[y0:y1,x0:x1] = local
        per_candidate.append(cm); union_candidate |= cm

    nlab, labels = cv2.connectedComponents(union_candidate.astype(np.uint8), connectivity=8)
    owner_by_component = {}
    ambiguous = []
    for lab in range(1, nlab):
        comp = labels == lab
        owners = []
        for ci, ch in enumerate(chars):
            x0,y0,x1,y1 = ch["bbox"]
            roi = comp[y0:y1,x0:x1] & per_candidate[ci][y0:y1,x0:x1]
            if not roi.any():
                continue
            exclusive = roi & (bbox_coverage[y0:y1,x0:x1] == 1)
            if exclusive.any():
                owners.append(ci)
        if len(owners) == 1:
            owner_by_component[lab] = owners[0]
        else:
            ambiguous.append({"component": lab, "exclusive_owner_indices": owners, "pixel_count": int(comp.sum())})
    masks = [np.zeros(arr.shape[:2], bool) for _ in chars]
    for lab, ci in owner_by_component.items():
        masks[ci] |= labels == lab
    # If adjacent glyphs are 8-connected at the antialias boundary, split the component by the
    # PDF character's own raw candidate support. Pixels present in two overlapping character bboxes
    # are assigned to the nearest normalized glyph-bbox centre. This is a traced PDF char-geometry
    # partition, not a bbox-wide foreground threshold, and every split is retained in the audit JSON.
    resolved_splits = []
    for item in ambiguous:
        lab = item["component"]
        comp = labels == lab
        ys, xs = np.where(comp)
        assigned = Counter(); shared = 0; unassigned = 0
        for y, x in zip(ys.tolist(), xs.tolist()):
            cand = [ci for ci in range(len(chars)) if per_candidate[ci][y, x]]
            if not cand:
                unassigned += 1
                continue
            if len(cand) > 1:
                shared += 1
                # Adjacent raw bboxes share at most the single raster column produced by
                # floor/ceil mapping of one PDF boundary. PDF text-show order assigns that
                # boundary antialias sample to the later glyph, preventing a left glyph from
                # acquiring the next glyph's overhanging stroke (visually verified for ；/p).
                ci=max(cand)
            else:
                ci=cand[0]
            masks[ci][y,x]=True; assigned[ci]+=1
        pre_reassignment_counts = {chars[k]["id"]:v for k,v in assigned.items()}
        dominant_reassignment = None
        if assigned:
            dom_ci, dom_n = assigned.most_common(1)[0]
            minor_n = sum(assigned.values()) - dom_n
            # A 1--3 px fragment at an adjacent bbox edge can be the dominant glyph's
            # antialias overhang. If the connected component is otherwise >=20:1 owned by
            # one glyph, the indivisible visible component is assigned wholly to that glyph.
            if minor_n <= 3 and dom_n >= 20 * max(1, minor_n):
                for ci0 in assigned:
                    masks[ci0][comp] = False
                masks[dom_ci][comp] = True
                dominant_reassignment = {"glyph": chars[dom_ci]["id"], "component_pixels": int(comp.sum()), "discarded_minor_boundary_pixels": minor_n}
                assigned = Counter({dom_ci: int(comp.sum())})
        resolved_splits.append({
            "component":lab,"method":"PDF-char-candidate-support; later text-show glyph owns shared floor/ceil boundary pixels",
            "pre_reassignment_pixels_by_glyph": pre_reassignment_counts,
            "assigned_pixels_by_glyph":{chars[k]["id"]:v for k,v in assigned.items()},
            "shared_candidate_pixels":shared,"unassigned_pixels":unassigned,
            "dominant_connected_component_reassignment": dominant_reassignment,
        })

    # STIX stretchy bmatrix delimiters are emitted as one rawdict character whose
    # visible top / extender / bottom pieces extend well beyond the raw char bbox.
    # Recover the complete final-visible contour from a narrow, non-overlapping
    # native-raster ownership ROI.  Clear those pixels from every bbox candidate
    # before assigning them to the semantic delimiter glyph.  This is required for
    # G035/G048/G120/G133 completeness and prevents the right-hand matrix's top-left
    # bracket cap from being mis-owned by the preceding P_{12} subscript (G114/G115).
    stretchy_rois_wholepage = {
        "G035": (633, 1560, 669, 1684),
        "G048": (845, 1560, 873, 1684),
        "G120": (1657, 1560, 1696, 1684),
        "G133": (1881, 1560, 1901, 1684),
    }
    extended_visible_contour_corrections = []
    for glyph_id, whole_bb in stretchy_rois_wholepage.items():
        ci = int(glyph_id[1:]) - 1
        ch = chars[ci]
        x0, y0, x1, y1 = (
            whole_bb[0] - FIG_CROP[0], whole_bb[1] - FIG_CROP[1],
            whole_bb[2] - FIG_CROP[0], whole_bb[3] - FIG_CROP[1],
        )
        bg = np.array([255.0, 255.0, 255.0])
        local = expected_color_mask(arr, (x0, y0, x1, y1), rgb_from_int(ch["color"]), bg)
        local &= ~all_final[y0:y1, x0:x1]
        recovered = np.zeros(arr.shape[:2], bool)
        recovered[y0:y1, x0:x1] = local
        assert recovered.any(), glyph_id
        previous = masks[ci].copy()
        # Keep only connected components that meet the already reliable vertical
        # delimiter stem.  This rejects the adjacent matrix digit's one-column
        # antialias overhang in the tightly packed left matrix.
        n_ext, ext_labels = cv2.connectedComponents(recovered.astype(np.uint8), connectivity=8)
        keep_labels = [lab for lab in range(1, n_ext) if (previous & (ext_labels == lab)).any()]
        recovered = np.isin(ext_labels, keep_labels)
        assert recovered.any(), (glyph_id, keep_labels)
        cleared_from = {}
        for other_ci in range(len(masks)):
            if other_ci == ci:
                continue
            n = int((masks[other_ci] & recovered).sum())
            if n:
                cleared_from[chars[other_ci]["id"]] = n
                masks[other_ci] &= ~recovered
        masks[ci] |= recovered
        extended_visible_contour_corrections.append({
            "glyph": glyph_id,
            "char": ch["c"],
            "semantic_parent": ch["parent"],
            "raw_char_bbox_wholepage_px": [v + off for v, off in zip(ch["bbox"], (FIG_CROP[0], FIG_CROP[1], FIG_CROP[0], FIG_CROP[1]))],
            "ownership_roi_wholepage_px": list(whole_bb),
            "previous_owned_px": int(previous.sum()),
            "recovered_complete_contour_px": int(recovered.sum()),
            "final_owned_px": int(masks[ci].sum()),
            "cleared_foreign_candidate_pixels": cleared_from,
            "method": "native final raster, exact dark-glyph color, narrow non-overlapping stretchy-delimiter ROI",
        })
    unresolved = [x for x in resolved_splits if x["unassigned_pixels"] != 0]
    cards = []
    glyph_rows = []
    low_indices = []
    all_owned_text = np.zeros(arr.shape[:2], bool)
    for owned in masks:
        all_owned_text |= owned
    for ci, (ch, mask) in enumerate(zip(chars, masks)):
        bb = tight_bbox(mask)
        x0,y0,x1,y1 = ch["bbox"]
        exclusive_expected = per_candidate[ci] & (bbox_coverage == 1)
        # Candidate pixels proven to belong to another final glyph are not missing strokes
        # of this glyph even when integer bbox rounding placed them in its exclusive column.
        missing = int((exclusive_expected & ~mask & ~all_owned_text).sum())
        foreign_vector = int((mask & all_pre).sum())
        foreign_other = sum(int((mask & masks[j]).sum()) for j in range(len(masks)) if j != ci)
        foreign = foreign_vector + foreign_other
        empty = bb is None
        if empty:
            bb = ch["bbox"]
        ink_h = 0 if empty else bb[3]-bb[1]
        ink_w = 0 if empty else bb[2]-bb[0]
        area = int(mask.sum())
        cls, threshold = classify_char(ch["c"], ch["raw_size"])
        if cls == "LOW_PROFILE_PUNCTUATION": low_indices.append(ci)
        pixel_pass = (not empty and (ink_h >= threshold if cls != "LOW_PROFILE_PUNCTUATION" else True))
        isolation_pass = (not empty and missing == 0 and foreign == 0)
        Image.fromarray((mask*255).astype(np.uint8)).crop(bb).save(EV / "04_glyphs/masks" / f"{ch['safe']}_mask_1x.png")
        Image.fromarray(arr).crop(bb).save(EV / "04_glyphs/cards" / f"{ch['safe']}_original_1x.png")
        card = make_triptych(arr, mask, bb, f"{ch['id']} {ch['parent']} U+{ord(ch['c']):04X} {repr(ch['c'])}")
        card.save(EV / "04_glyphs/cards" / f"{ch['safe']}_8x_card.png")
        cards.append((ch["id"], card))
        glyph_rows.append({
            "GLYPH_ID": ch["id"], "SAFE_FILENAME": ch["safe"], "PARENT_ID": ch["parent"],
            "PANEL_ID": PARENTS[ch["parent"]]["panel"], "ROLE": PARENTS[ch["parent"]]["role"],
            "CHAR": ch["c"], "CODEPOINT": f"U+{ord(ch['c']):04X}", "PDF_FONT": ch["font"],
            "PDF_SIZE_BP": round(ch["raw_size"], 6), "SOURCE_EFFECTIVE_PT": PARENTS[ch["parent"]]["pt"],
            "SCRIPT_CLASS": cls, "THRESHOLD_PX": threshold if cls != "LOW_PROFILE_PUNCTUATION" else "CALIBRATION",
            "BBOX_X0": x0+FIG_CROP[0], "BBOX_Y0": y0+FIG_CROP[1], "BBOX_X1": x1+FIG_CROP[0], "BBOX_Y1": y1+FIG_CROP[1],
            "INK_X0": bb[0]+FIG_CROP[0], "INK_Y0": bb[1]+FIG_CROP[1], "INK_X1": bb[2]+FIG_CROP[0], "INK_Y1": bb[3]+FIG_CROP[1],
            "H_INK_PX": ink_h, "W_INK_PX": ink_w, "INK_AREA_PX": area,
            "LOCAL_BACKGROUND_RGB": json.dumps(ch["bg_rgb"]), "FOREGROUND_RGB": json.dumps(rgb_from_int(ch["color"])),
            "ISOLATION_METHOD": "native-final-raster + exact-vector-subtraction + exclusive-connected-component",
            "MISSING_STROKE_PX": missing, "FOREIGN_PIXEL_PX": foreign,
            "ISOLATION_PASS": str(isolation_pass).lower(), "PIXEL_HEIGHT_PASS": str(pixel_pass).lower(),
            "LOW_PROFILE_COMPARATOR": "PENDING" if cls == "LOW_PROFILE_PUNCTUATION" else "N/A",
            "PASS_FAIL": "PENDING_CALIBRATION" if cls == "LOW_PROFILE_PUNCTUATION" else ("PASS" if isolation_pass and pixel_pass else "FAIL"),
            "MASK_PATH": f"04_glyphs/masks/{ch['safe']}_mask_1x.png",
            "ORIGINAL_PATH": f"04_glyphs/cards/{ch['safe']}_original_1x.png",
            "CARD_PATH": f"04_glyphs/cards/{ch['safe']}_8x_card.png",
        })
    contact_register = add_contact_sheets(cards, EV / "04_glyphs/contact_sheets", "glyphs", per_sheet=12)
    contact_by_id = {x["id"]: x for x in contact_register}
    for row in glyph_rows:
        reg = contact_by_id[row["GLYPH_ID"]]
        row["CONTACT_SHEET"] = f"04_glyphs/contact_sheets/{reg['sheet']}"
        row["CONTACT_CELL"] = reg["cell"]

    # Independent calibration glyphs.
    cal_targets = {0: "，", 1: "。", 2: "：", 3: "."}
    cal_data = {}
    caldoc = fitz.open(CAL_PDF)
    for pi, target in cal_targets.items():
        cp = caldoc[pi]
        cpix = cp.get_pixmap(matrix=fitz.Matrix(SCALE_300,SCALE_300), alpha=False, colorspace=fitz.csRGB)
        cim = np.asarray(pil_from_pix(cpix)).copy()
        craw = cp.get_text("rawdict")
        hit = None
        for b in craw["blocks"]:
            for line in b.get("lines", []):
                for span in line.get("spans", []):
                    for c in span.get("chars", []):
                        if c.get("c") == target:
                            hit=(span,c); break
                    if hit: break
                if hit: break
            if hit: break
        assert hit, (pi,target)
        span,c = hit
        bbx = pixel_bbox_from_pt(c["bbox"])
        exclusion=np.zeros(cim.shape[:2],bool)
        bg=dominant_background(cim,bbx,exclusion)
        local=expected_color_mask(cim,bbx,rgb_from_int(int(span["color"])),bg)
        cm=np.zeros(cim.shape[:2],bool); x0,y0,x1,y1=bbx; cm[y0:y1,x0:x1]=local
        tbb=tight_bbox(cm); assert tbb
        key={0:"CAL_COMMA",1:"CAL_FULLSTOP",2:"CAL_COLON",3:"CAL_PERIOD"}[pi]
        card=make_triptych(cim,cm,tbb,f"{key} {target}")
        card.save(EV / "04_glyphs/calibration_cards" / f"{key}_8x_card.png")
        Image.fromarray((cm*255).astype(np.uint8)).crop(tbb).save(EV / "04_glyphs/calibration_cards" / f"{key}_mask_1x.png")
        Image.fromarray(cim).crop(tbb).save(EV / "04_glyphs/calibration_cards" / f"{key}_original_1x.png")
        cal_data[key]={"h":tbb[3]-tbb[1],"area":int(cm.sum()),"font":span["font"],"size":float(span["size"]),"char":target}

    # Low-profile comparator assignment and hard [0.92,1.08] H/area gates.
    groups=defaultdict(list)
    for i in low_indices:
        ch=chars[i]
        groups[(ch["c"],ch["font"],round(ch["raw_size"],3),ch["color"])].append(i)
    for i in low_indices:
        ch=chars[i]; row=glyph_rows[i]
        peers=[j for j in groups[(ch["c"],ch["font"],round(ch["raw_size"],3),ch["color"])] if j!=i]
        if peers:
            hs=[glyph_rows[j]["H_INK_PX"] for j in peers]; areas=[glyph_rows[j]["INK_AREA_PX"] for j in peers]
            comp_id="candidate:"+"|".join(chars[j]["id"] for j in peers)
            href=float(np.median(hs)); aref=float(np.median(areas))
        else:
            if ch["c"]=="，": key="CAL_COMMA"
            elif ch["c"]=="。": key="CAL_FULLSTOP"
            elif ch["c"]=="：": key="CAL_COLON"
            elif ch["c"]==".": key="CAL_PERIOD"
            else: key=""
            if not key:
                row["LOW_PROFILE_COMPARATOR"]="MISSING"; row["PASS_FAIL"]="FAIL"; continue
            comp_id="official:"+key; href=cal_data[key]["h"]; aref=cal_data[key]["area"]
        hr=row["H_INK_PX"]/href if href else 0; ar=row["INK_AREA_PX"]/aref if aref else 0
        ok=(0.92<=hr<=1.08 and 0.92<=ar<=1.08 and row["ISOLATION_PASS"]=="true")
        row["LOW_PROFILE_COMPARATOR"]=comp_id
        row["CALIBRATION_H_RATIO"]=round(hr,6); row["CALIBRATION_AREA_RATIO"]=round(ar,6)
        row["PIXEL_HEIGHT_PASS"]=str(ok).lower(); row["PASS_FAIL"]="PASS" if ok else "FAIL"

    save_csv(EV / "after_pixel_measurements.csv", glyph_rows)
    save_csv(EV / "04_glyphs/glyph_mapping_ledger.csv", glyph_rows)
    (EV / "04_glyphs/component_ownership_audit.json").write_text(json.dumps({
        "method":"native-final-raster + exact-vector-subtraction + exclusive-connected-component",
        "component_count":nlab-1,"owned_component_count":len(owner_by_component),
        "initial_multi_owner_components":ambiguous,"resolved_component_splits":resolved_splits,
        "extended_visible_contour_corrections":extended_visible_contour_corrections,
        "unresolved_component_splits":unresolved,
        "glyph_count":len(chars),"empty_glyph_count":sum(1 for m in masks if not m.any()),
        "pairwise_glyph_mask_intersection_px":sum(int((masks[i]&masks[j]).sum()) for i in range(len(masks)) for j in range(i+1,len(masks))),
    },ensure_ascii=False,indent=2),encoding="utf-8")
    (EV / "04_glyphs/calibration_measurements.json").write_text(json.dumps(cal_data,ensure_ascii=False,indent=2),encoding="utf-8")

    # Parent masks / bbox overlay / source font audit.
    parent_masks={pid:np.zeros(arr.shape[:2],bool) for pid in PARENTS}
    for ch,m in zip(chars,masks): parent_masks[ch["parent"]] |= m
    overlay=Image.fromarray(arr.copy()); od=ImageDraw.Draw(overlay)
    parent_rows=[]; font_rows=[]
    colors=[(220,20,60),(0,100,210),(0,150,70),(180,80,0),(120,0,180)]
    for idx,(pid,meta) in enumerate(PARENTS.items()):
        bb=tight_bbox(parent_masks[pid]); assert bb
        od.rectangle(bb,outline=colors[idx%len(colors)],width=2); od.text((bb[0]+2,max(0,bb[1]-13)),pid,fill=colors[idx%len(colors)])
        parent_rows.append({"OBJECT_ID":pid,"PANEL_ID":meta["panel"],"ROLE":meta["role"],"TEXT":meta["text"],
                            "BBOX_X0":bb[0]+FIG_CROP[0],"BBOX_Y0":bb[1]+FIG_CROP[1],"BBOX_X1":bb[2]+FIG_CROP[0],"BBOX_Y1":bb[3]+FIG_CROP[1],
                            "H_INK_PX":bb[3]-bb[1],"PIXELS":int(parent_masks[pid].sum())})
        font_rows.append({
            "ELEMENT_ID":pid,"PANEL_ID":meta["panel"],"ROLE":meta["role"],"SOURCE_FILE":str(SRC),"SOURCE_LINE":meta["line"],
            "DECLARED_PT":meta["pt"],"GRAPHICS_SCALE":1.0,"EFFECTIVE_PT":meta["pt"],"TEXT_SAMPLE":meta["text"],
            "MINIMUM_PT":9.5,"SOURCE_FONT_PASS":str(meta["pt"]>=9.5).lower(),"OVERRIDE_CHAIN":"local fontsize or named style; no resizebox/scalebox/transform shape",
        })
        Image.fromarray((parent_masks[pid]*255).astype(np.uint8)).save(EV / "03_objects" / f"{pid}_text_mask.png")
    overlay.save(EV / "after_text_measurement_overlay_300dpi.png")
    save_csv(EV / "03_objects/text_parent_ledger.csv",parent_rows)
    save_csv(EV / "after_font_audit.csv",font_rows)

    # Identity and environment records.
    identity={
        "candidate_pdf":str(PDF),"pdf_size_bytes":PDF.stat().st_size,"pdf_sha256":sha256(PDF),"pdf_pages":doc.page_count,
        "source":str(SRC),"source_size_bytes":SRC.stat().st_size,"source_sha256":sha256(SRC),
        "physical_page":591,"printed_page":578,"page_rect_pt":list(page.rect),"native_300dpi_grid":[2481,3508],
        "figure_crop_wholepage_px":list(FIG_CROP),"standalone_crop_wholepage_px":list(GRAPH_CROP),
        "renderer":"PyMuPDF direct PDF raster, Matrix(300/72), no resize","glyph_count":len(chars),
        "text_parent_count":len(PARENTS),"drawing_record_count":len(drawings),"vector_command_count":len(command_rows),
    }
    (EV / "00_identity/identity.json").write_text(json.dumps(identity,ensure_ascii=False,indent=2),encoding="utf-8")
    fonts=page.get_fonts(full=True)
    save_csv(EV / "00_identity/page591_font_inventory.csv",[
        {"xref":x[0],"ext":x[1],"type":x[2],"basefont":x[3],"name":x[4],"encoding":x[5],"referencer":x[6]} for x in fonts
    ])
    summary={
        "glyph_count":len(chars),"glyph_fail_count":sum(r["PASS_FAIL"]!="PASS" for r in glyph_rows),
        "glyph_fail_ids":[r["GLYPH_ID"] for r in glyph_rows if r["PASS_FAIL"]!="PASS"],
        "initial_multi_owner_component_count":len(ambiguous),"unresolved_component_count":len(unresolved),
        "empty_glyph_count":sum(1 for m in masks if not m.any()),
        "text_parent_count":len(PARENTS),"drawing_record_count":len(drawings),"vector_command_count":len(command_rows),
        "path_record_all_pairs":math.comb(len(drawings),2),
        "within_record_command_pairs":sum(math.comb(len(d["items"]),2) for d in drawings),
    }
    (EV / "08_reports/core_machine_summary.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(summary,ensure_ascii=False,indent=2))


if __name__ == "__main__":
    main()
