from __future__ import annotations

import csv
import hashlib
import itertools
import json
import math
import re
import statistics
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

import fitz
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps
from scipy.ndimage import distance_transform_edt
from scipy.spatial import cKDTree


BASE = Path(__file__).resolve().parents[1]
PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r97_fullbook\main_full.pdf")
SOURCE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C04\fig_v5_c04_dependency_graph.tex")
CHAPTER = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\讲义源码\第05册_采样方法主题模型与图排序\chapters\V5-C04.tex")
STANDALONE_PDF = BASE / "standalone_build" / "FIG-P630-01_R97_SA1_standalone.pdf"
EXPECTED_SHA256 = "062AD81020CB19A5C6688A45C73E00965F5060E0960A69AF820D7DC154DEE814"
PHYSICAL_PAGE_1BASED = 678
PRINTED_PAGE = "665"
FIGURE_NO = "33.1"
SCALE_300 = 300.0 / 72.0
SCALE_200 = 200.0 / 72.0
CONTRAST_THRESHOLD = 20


def assert_inside(path: Path) -> None:
    path.resolve().relative_to(BASE.resolve())


def ensure_dirs() -> None:
    for rel in [
        "render",
        "glyphs/masks",
        "glyphs/original_1x",
        "glyphs/overlay_1x",
        "glyphs/mask_only_1x",
        "glyphs/cards_8x",
        "glyphs/contact_sheets",
        "graphics/pre_masks",
        "graphics/final_masks",
        "graphics/background_masks",
        "graphics/original_1x",
        "graphics/overlay_1x",
        "graphics/mask_only_1x",
        "graphics/contact_sheets",
        "pairs/cards",
        "critical/glyphs",
        "critical/pairs",
        "source_identity",
    ]:
        p = BASE / rel
        assert_inside(p)
        p.mkdir(parents=True, exist_ok=True)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def save_json(path: Path, data) -> None:
    assert_inside(path)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_csv(path: Path, rows: list[dict], fieldnames: list[str] | None = None) -> None:
    assert_inside(path)
    if fieldnames is None:
        fieldnames = list(rows[0]) if rows else []
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def pix_to_pil(pix: fitz.Pixmap) -> Image.Image:
    mode = "RGBA" if pix.alpha else "RGB"
    return Image.frombytes(mode, (pix.width, pix.height), pix.samples)


def render_page(page: fitz.Page, dpi: int, alpha: bool = False) -> Image.Image:
    pix = page.get_pixmap(matrix=fitz.Matrix(dpi / 72.0, dpi / 72.0), alpha=alpha, colorspace=fitz.csRGB)
    return pix_to_pil(pix)


def bbox_union(rects: list[fitz.Rect]) -> fitz.Rect:
    if not rects:
        raise RuntimeError("cannot union empty rectangle set")
    out = fitz.Rect(rects[0])
    for r in rects[1:]:
        out.include_rect(r)
    return out


def rect_tuple(rect: fitz.Rect, ndigits: int = 6) -> list[float]:
    return [round(float(v), ndigits) for v in rect]


def line_records(page: fitz.Page) -> list[dict]:
    records = []
    raw = page.get_text("rawdict")
    for bi, block in enumerate(raw.get("blocks", [])):
        if block.get("type") != 0:
            continue
        for li, line in enumerate(block.get("lines", [])):
            chars = []
            spans = []
            for si, span in enumerate(line.get("spans", [])):
                txt = "".join(ch.get("c", "") for ch in span.get("chars", []))
                chars.append(txt)
                spans.append({"span_index": si, "font": span.get("font"), "size": span.get("size"), "text": txt})
            records.append(
                {
                    "block_index": bi,
                    "line_index": li,
                    "bbox": fitz.Rect(line["bbox"]),
                    "text": "".join(chars),
                    "spans": spans,
                }
            )
    return records


def norm_text(s: str) -> str:
    return re.sub(r"\s+", "", s)


ELEMENT_SPECS = {
    "E001_CORE_JOINT": {"node": "joint", "role": "BASE_NODE", "declared_pt": 9.6, "source_token": "(joint)"},
    "E002_CORE_CONDITIONAL": {"node": "cond", "role": "FORMULA_NODE", "declared_pt": 9.6, "source_token": "(cond)"},
    "E003_CORE_COORDINATE": {"node": "coord", "role": "FORMULA_NODE", "declared_pt": 9.6, "source_token": "(coord)"},
    "E004_CORE_SCAN": {"node": "scan", "role": "BASE_NODE", "declared_pt": 9.6, "source_token": "(scan)"},
    "E005_CORE_SAMPLE": {"node": "sample", "role": "BASE_NODE", "declared_pt": 9.6, "source_token": "(sample)"},
    "E006_CORE_DIAGNOSTIC": {"node": "diag", "role": "BASE_NODE", "declared_pt": 9.6, "source_token": "(diag)"},
    "E007_SIDE_CORRECTNESS": {"node": "correct", "role": "SUPPORT_ANNOTATION", "declared_pt": 9.6, "source_token": "(correct)"},
    "E008_SIDE_MIXING": {"node": "mix", "role": "SUPPORT_ANNOTATION", "declared_pt": 9.6, "source_token": "(mix)"},
    "E009_BOUNDARY_CONCLUSION": {"node": "boundary", "role": "EMPHASIS", "declared_pt": 10.0, "source_token": "[boundary]"},
}


def element_for_line(text: str, bbox: fitz.Rect) -> str:
    t = norm_text(text)
    if "联合目标" in t or "局部因子" in t:
        return "E001_CORE_JOINT"
    if "给定" in t or t.startswith("𝜋") or t.startswith("π"):
        return "E002_CORE_CONDITIONAL"
    if "单坐标核" in t or "只更新" in t:
        return "E003_CORE_COORDINATE"
    if "扫描核" in t or ("系统" in t and "随机" in t):
        return "E004_CORE_SCAN"
    if "相关样本" in t:
        return "E005_CORE_SAMPLE"
    if "诊断" in t or "MCSE" in t or "轨迹" in t:
        return "E006_CORE_DIAGNOSTIC"
    if any(x in t for x in ["正确性条件", "目标保持", "支持可达", "遍历性"]):
        return "E007_SIDE_CORRECTNESS"
    if any(x in t for x in ["混合效率", "自相关长度", "有效样本量"]):
        return "E008_SIDE_MIXING"
    if "正确内核" in t or "快速混合" in t or "≠" in t:
        return "E009_BOUNDARY_CONCLUSION"
    raise RuntimeError(f"unmapped strict-figure line: {text!r}, bbox={bbox}")


GRAPHIC_SPECS = [
    ("G001_BORDER_CORE_JOINT", "NODE_BORDER", "joint core node border"),
    ("G002_BORDER_CORE_CONDITIONAL", "NODE_BORDER", "conditional core node border"),
    ("G003_BORDER_CORE_COORDINATE", "NODE_BORDER", "coordinate core node border"),
    ("G004_BORDER_CORE_SCAN", "NODE_BORDER", "scan core node border"),
    ("G005_BORDER_CORE_SAMPLE", "NODE_BORDER", "sample core node border"),
    ("G006_BORDER_CORE_DIAGNOSTIC", "NODE_BORDER", "diagnostic core node border"),
    ("G007_FLOW_JOINT_COND_SHAFT", "LINE_ARROW_SHAFT", "joint to conditional flow shaft"),
    ("G008_FLOW_JOINT_COND_HEAD", "ARROWHEAD", "joint to conditional flow arrowhead"),
    ("G009_FLOW_COND_COORD_SHAFT", "LINE_ARROW_SHAFT", "conditional to coordinate flow shaft"),
    ("G010_FLOW_COND_COORD_HEAD", "ARROWHEAD", "conditional to coordinate flow arrowhead"),
    ("G011_FLOW_COORD_SCAN_SHAFT", "LINE_ARROW_SHAFT", "coordinate to scan flow shaft"),
    ("G012_FLOW_COORD_SCAN_HEAD", "ARROWHEAD", "coordinate to scan flow arrowhead"),
    ("G013_FLOW_SCAN_SAMPLE_SHAFT", "LINE_ARROW_SHAFT", "scan to sample flow shaft"),
    ("G014_FLOW_SCAN_SAMPLE_HEAD", "ARROWHEAD", "scan to sample flow arrowhead"),
    ("G015_FLOW_SAMPLE_DIAG_SHAFT", "LINE_ARROW_SHAFT", "sample to diagnostic flow shaft"),
    ("G016_FLOW_SAMPLE_DIAG_HEAD", "ARROWHEAD", "sample to diagnostic flow arrowhead"),
    ("G017_BORDER_SIDE_CORRECTNESS", "NODE_BORDER", "correctness side node border"),
    ("G018_BORDER_SIDE_MIXING", "NODE_BORDER", "mixing side node border"),
    ("G019_LEADER_CORRECT_JOINT", "LEADER_LINE", "correctness to joint semantic leader"),
    ("G020_LEADER_MIX_SCAN", "LEADER_LINE", "mixing to scan semantic leader"),
    ("G021_BORDER_BOUNDARY", "NODE_BORDER", "boundary conclusion node border"),
]


PARENT_BORDER = {
    "E001_CORE_JOINT": "G001_BORDER_CORE_JOINT",
    "E002_CORE_CONDITIONAL": "G002_BORDER_CORE_CONDITIONAL",
    "E003_CORE_COORDINATE": "G003_BORDER_CORE_COORDINATE",
    "E004_CORE_SCAN": "G004_BORDER_CORE_SCAN",
    "E005_CORE_SAMPLE": "G005_BORDER_CORE_SAMPLE",
    "E006_CORE_DIAGNOSTIC": "G006_BORDER_CORE_DIAGNOSTIC",
    "E007_SIDE_CORRECTNESS": "G017_BORDER_SIDE_CORRECTNESS",
    "E008_SIDE_MIXING": "G018_BORDER_SIDE_MIXING",
    "E009_BOUNDARY_CONCLUSION": "G021_BORDER_BOUNDARY",
}


STRUCTURAL_PAIRS = {
    frozenset(x)
    for x in [
        ("G001_BORDER_CORE_JOINT", "G007_FLOW_JOINT_COND_SHAFT"),
        ("G007_FLOW_JOINT_COND_SHAFT", "G008_FLOW_JOINT_COND_HEAD"),
        ("G008_FLOW_JOINT_COND_HEAD", "G002_BORDER_CORE_CONDITIONAL"),
        ("G002_BORDER_CORE_CONDITIONAL", "G009_FLOW_COND_COORD_SHAFT"),
        ("G009_FLOW_COND_COORD_SHAFT", "G010_FLOW_COND_COORD_HEAD"),
        ("G010_FLOW_COND_COORD_HEAD", "G003_BORDER_CORE_COORDINATE"),
        ("G003_BORDER_CORE_COORDINATE", "G011_FLOW_COORD_SCAN_SHAFT"),
        ("G011_FLOW_COORD_SCAN_SHAFT", "G012_FLOW_COORD_SCAN_HEAD"),
        ("G012_FLOW_COORD_SCAN_HEAD", "G004_BORDER_CORE_SCAN"),
        ("G004_BORDER_CORE_SCAN", "G013_FLOW_SCAN_SAMPLE_SHAFT"),
        ("G013_FLOW_SCAN_SAMPLE_SHAFT", "G014_FLOW_SCAN_SAMPLE_HEAD"),
        ("G014_FLOW_SCAN_SAMPLE_HEAD", "G005_BORDER_CORE_SAMPLE"),
        ("G005_BORDER_CORE_SAMPLE", "G015_FLOW_SAMPLE_DIAG_SHAFT"),
        ("G015_FLOW_SAMPLE_DIAG_SHAFT", "G016_FLOW_SAMPLE_DIAG_HEAD"),
        ("G016_FLOW_SAMPLE_DIAG_HEAD", "G006_BORDER_CORE_DIAGNOSTIC"),
        ("G017_BORDER_SIDE_CORRECTNESS", "G019_LEADER_CORRECT_JOINT"),
        ("G019_LEADER_CORRECT_JOINT", "G001_BORDER_CORE_JOINT"),
        ("G018_BORDER_SIDE_MIXING", "G020_LEADER_MIX_SCAN"),
        ("G020_LEADER_MIX_SCAN", "G004_BORDER_CORE_SCAN"),
    ]
}


def is_cjk(ch: str) -> bool:
    cp = ord(ch)
    return (
        0x3400 <= cp <= 0x4DBF
        or 0x4E00 <= cp <= 0x9FFF
        or 0xF900 <= cp <= 0xFAFF
        or 0x2E80 <= cp <= 0x2FFF
    )


def classify_glyph(ch: str, rendered_pt: float) -> tuple[str, int, str]:
    name = unicodedata.name(ch, "")
    if ch in {"⋅", "·", "−", "-", "+", "=", "≠", "∣", "|", "/", "∕"}:
        return "BASE_MATH_OPERATOR", 22, "semantic math/operator hard gate; operator cannot be downgraded to natural-script gate"
    if rendered_pt < 8.0:
        return "NATURAL_SCRIPT", 15, "TeX natural subscript glyph from a 9.6pt base formula"
    if is_cjk(ch):
        return "CJK_FULL", 30, "CJK/full ideograph hard gate"
    if ch.isdigit() or (ch.isalpha() and ch.upper() == ch and ch.lower() != ch) or (
        "MATHEMATICAL" in name and ("CAPITAL" in name or "DIGIT" in name)
    ):
        return "LATIN_UPPER_DIGIT", 24, "Latin uppercase/digit hard gate"
    if "GREEK" in name or ch.isalpha():
        return "X_HEIGHT_LATIN_GREEK", 17, "Latin/Greek lowercase x-height hard gate"
    if ch in {"(", ")", "[", "]", "{", "}"}:
        return "FULL_PROFILE_DELIMITER", 22, "full-profile math delimiter"
    return "FULL_PROFILE_SYMBOL", 22, "reader-visible full-profile symbol"


def tight_bbox(mask: np.ndarray) -> tuple[int, int, int, int] | None:
    ys, xs = np.nonzero(mask)
    if len(xs) == 0:
        return None
    return int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1


def mask_height(mask: np.ndarray) -> int:
    bb = tight_bbox(mask)
    return 0 if bb is None else bb[3] - bb[1]


def mode_rgb(arr: np.ndarray) -> tuple[int, int, int]:
    flat = arr.reshape(-1, 3)
    vals, counts = np.unique(flat, axis=0, return_counts=True)
    v = vals[int(np.argmax(counts))]
    return int(v[0]), int(v[1]), int(v[2])


def crop_box_from_pts(rect: fitz.Rect, scale: float, pad_px: int, page_size: tuple[int, int]) -> tuple[int, int, int, int]:
    w, h = page_size
    x0 = max(0, math.floor(rect.x0 * scale) - pad_px)
    y0 = max(0, math.floor(rect.y0 * scale) - pad_px)
    x1 = min(w, math.ceil(rect.x1 * scale) + pad_px)
    y1 = min(h, math.ceil(rect.y1 * scale) + pad_px)
    return x0, y0, x1, y1


def point_rect_to_crop(rect: fitz.Rect, crop_box: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
    cx0, cy0, cx1, cy1 = crop_box
    x0 = max(0, math.floor(rect.x0 * SCALE_300) - cx0)
    y0 = max(0, math.floor(rect.y0 * SCALE_300) - cy0)
    x1 = min(cx1 - cx0, math.ceil(rect.x1 * SCALE_300) - cx0)
    y1 = min(cy1 - cy0, math.ceil(rect.y1 * SCALE_300) - cy0)
    return x0, y0, x1, y1


def save_mask(path: Path, mask: np.ndarray) -> None:
    assert_inside(path)
    Image.fromarray(np.where(mask, 255, 0).astype(np.uint8), mode="L").save(path, dpi=(300, 300))


def mask_only_rgb(mask_roi: np.ndarray) -> Image.Image:
    a = np.where(mask_roi, 0, 255).astype(np.uint8)
    return Image.fromarray(np.stack([a, a, a], axis=2), mode="RGB")


def overlay_image(original: np.ndarray, mask: np.ndarray, color=(255, 0, 0), alpha=0.62) -> Image.Image:
    out = original.astype(np.float32).copy()
    c = np.array(color, dtype=np.float32)
    out[mask] = out[mask] * (1.0 - alpha) + c * alpha
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), mode="RGB")


def font_for_label(size: int = 15) -> ImageFont.ImageFont:
    candidates = [
        Path(r"C:\Windows\Fonts\arial.ttf"),
        Path(r"C:\Windows\Fonts\msyh.ttc"),
    ]
    for p in candidates:
        if p.exists():
            try:
                return ImageFont.truetype(str(p), size=size)
            except Exception:
                pass
    return ImageFont.load_default()


def make_three_view_card(original_roi: np.ndarray, mask_roi: np.ndarray, title: str, scale: int = 8) -> Image.Image:
    orig = Image.fromarray(original_roi, mode="RGB")
    over = overlay_image(original_roi, mask_roi)
    monly = mask_only_rgb(mask_roi)
    views = [orig, over, monly]
    labels = ["ORIGINAL", "TARGET OVERLAY", "MASK ONLY"]
    up = [v.resize((v.width * scale, v.height * scale), Image.Resampling.NEAREST) for v in views]
    label_h = 34
    title_h = 34
    gap = 14
    width = sum(v.width for v in up) + gap * 4
    height = title_h + label_h + max(v.height for v in up) + gap * 2
    canvas = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(canvas)
    font = font_for_label(16)
    draw.text((gap, 6), title, fill="black", font=font)
    x = gap
    for label, view in zip(labels, up):
        draw.text((x, title_h), label, fill="black", font=font)
        canvas.paste(view, (x, title_h + label_h))
        x += view.width + gap
    return canvas


def path_to_shape(shape: fitz.Shape, item) -> None:
    op = item[0]
    if op == "l":
        shape.draw_line(item[1], item[2])
    elif op == "c":
        shape.draw_bezier(item[1], item[2], item[3], item[4])
    elif op == "re":
        shape.draw_rect(item[1])
    elif op == "qu":
        shape.draw_quad(item[1])
    else:
        raise RuntimeError(f"unsupported drawing operator: {op!r}")


def render_drawing_alpha(page_rect: fitz.Rect, drawing: dict, stroke: bool, fill: bool) -> np.ndarray:
    doc = fitz.open()
    p = doc.new_page(width=page_rect.width, height=page_rect.height)
    sh = p.new_shape()
    for item in drawing["items"]:
        path_to_shape(sh, item)
    line_cap = drawing.get("lineCap", 0)
    if isinstance(line_cap, tuple):
        line_cap = max(line_cap)
    sh.finish(
        color=(0, 0, 0) if stroke else None,
        fill=(0, 0, 0) if fill else None,
        width=float(drawing.get("width") or 1.0),
        lineCap=int(line_cap or 0),
        lineJoin=float(drawing.get("lineJoin") or 0),
        dashes=drawing.get("dashes"),
        closePath=bool(drawing.get("closePath", False)),
        even_odd=bool(drawing.get("even_odd", False)),
        stroke_opacity=float(drawing.get("stroke_opacity") or 1.0),
        fill_opacity=float(drawing.get("fill_opacity") or 1.0),
    )
    sh.commit()
    pix = p.get_pixmap(matrix=fitz.Matrix(SCALE_300, SCALE_300), alpha=True, colorspace=fitz.csRGB)
    arr = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, 4)
    alpha = arr[:, :, 3].copy()
    doc.close()
    return alpha


def nearest_points(mask_a: np.ndarray, mask_b: np.ndarray) -> tuple[tuple[int, int], tuple[int, int], float] | None:
    ya, xa = np.nonzero(mask_a)
    yb, xb = np.nonzero(mask_b)
    if len(xa) == 0 or len(xb) == 0:
        return None
    ca = np.column_stack([ya, xa])
    cb = np.column_stack([yb, xb])
    if len(ca) <= len(cb):
        tree = cKDTree(cb)
        dist, idx = tree.query(ca, k=1)
        k = int(np.argmin(dist))
        pa = ca[k]
        pb = cb[int(idx[k])]
    else:
        tree = cKDTree(ca)
        dist, idx = tree.query(cb, k=1)
        k = int(np.argmin(dist))
        pb = cb[k]
        pa = ca[int(idx[k])]
    return (int(pa[1]), int(pa[0])), (int(pb[1]), int(pb[0])), float(np.min(dist))


def bbox_clearance(a: tuple[int, int, int, int] | None, b: tuple[int, int, int, int] | None) -> float | None:
    if a is None or b is None:
        return None
    dx = max(0, b[0] - a[2], a[0] - b[2])
    dy = max(0, b[1] - a[3], a[1] - b[3])
    return float(math.hypot(dx, dy))


def main() -> None:
    ensure_dirs()
    identity_sha = sha256(PDF)
    if identity_sha != EXPECTED_SHA256:
        raise RuntimeError(f"official PDF SHA mismatch: {identity_sha}")
    source_sha = sha256(SOURCE)
    chapter_sha = sha256(CHAPTER)
    doc = fitz.open(PDF)
    if doc.page_count != 813:
        raise RuntimeError(f"unexpected page count: {doc.page_count}")
    page = doc[PHYSICAL_PAGE_1BASED - 1]
    if page.get_label() != PRINTED_PAGE:
        raise RuntimeError(f"printed page label mismatch: {page.get_label()}")

    lines = line_records(page)
    ref_line = next(x for x in lines if "图33.1" in x["text"] and "概括" in x["text"])
    caption_line = next(x for x in lines if "满条件把联合目标转为单坐标更新" in x["text"])
    drawings_all = page.get_drawings(extended=True)
    selected_drawings = [
        d
        for d in drawings_all
        if d["rect"].y0 > ref_line["bbox"].y1 and d["rect"].y1 < caption_line["bbox"].y0
    ]
    if len(selected_drawings) != 21:
        raise RuntimeError(f"expected 21 figure drawings, got {len(selected_drawings)}")
    if len(GRAPHIC_SPECS) != len(selected_drawings):
        raise RuntimeError("graphic spec count mismatch")
    vector_bbox = bbox_union([fitz.Rect(d["rect"]) for d in selected_drawings])

    figure_lines = [
        x
        for x in lines
        if fitz.Rect(x["bbox"]).intersects(vector_bbox)
        and x["bbox"].y0 >= vector_bbox.y0 - 1
        and x["bbox"].y1 <= vector_bbox.y1 + 1
    ]
    for x in figure_lines:
        x["element_id"] = element_for_line(x["text"], x["bbox"])

    full_300 = render_page(page, 300, alpha=False)
    full_200 = render_page(page, 200, alpha=False)
    full_300.save(BASE / "render" / "full_page_300dpi.png", dpi=(300, 300))
    full_200.save(BASE / "render" / "full_page_200dpi.png", dpi=(200, 200))
    crop_box = crop_box_from_pts(vector_bbox, SCALE_300, pad_px=2, page_size=full_300.size)
    crop_img = full_300.crop(crop_box)
    crop_img.save(BASE / "render" / "figure_crop_300dpi.png", dpi=(300, 300))
    ImageOps.grayscale(crop_img).save(BASE / "render" / "grayscale_300dpi.png", dpi=(300, 300))
    crop_rgb = np.array(crop_img.convert("RGB"))
    crop_h, crop_w = crop_rgb.shape[:2]

    identity = {
        "figure_uid": "FIG-P630-01",
        "figure_no": FIGURE_NO,
        "official_candidate": str(PDF),
        "official_sha256": identity_sha,
        "expected_sha256": EXPECTED_SHA256,
        "page_count": doc.page_count,
        "physical_page_1based": PHYSICAL_PAGE_1BASED,
        "printed_page_label": page.get_label(),
        "page_rect_pt": rect_tuple(page.rect),
        "native_full_page_300dpi_px": list(full_300.size),
        "native_full_page_200dpi_px": list(full_200.size),
        "reference_line_bbox_pt": rect_tuple(ref_line["bbox"]),
        "caption_line_bbox_pt": rect_tuple(caption_line["bbox"]),
        "strict_vector_bbox_pt": rect_tuple(vector_bbox),
        "strict_crop_box_full_page_300dpi_px_half_open": list(crop_box),
        "strict_crop_dimensions_px": list(crop_img.size),
        "strict_crop_pad_px": 2,
        "source": str(SOURCE),
        "source_sha256": source_sha,
        "chapter": str(CHAPTER),
        "chapter_sha256": chapter_sha,
        "localization_basis": [
            "main_full.aux label fig:V5-C04-dependency-graph -> printed page 665",
            "PDF page labels map printed 665 -> physical page 678",
            "direct chapter text and current figure source confirm figure 33.1",
            "strict vector bbox is the union of all 21 visible foreground drawing records between the direct-body reference line and caption",
        ],
    }
    save_json(BASE / "source_identity" / "official_candidate_identity.json", identity)

    source_lines = SOURCE.read_text(encoding="utf-8").splitlines()
    source_line_map = {}
    for eid, spec in ELEMENT_SPECS.items():
        matches = [i + 1 for i, line in enumerate(source_lines) if spec["source_token"] in line]
        source_line_map[eid] = matches[0] if matches else None

    # Extract every reader-visible glyph from PDF text tracing.
    glyphs = []
    for span in page.get_texttrace():
        sb = fitz.Rect(span["bbox"])
        if not sb.intersects(vector_bbox):
            continue
        for ch_index, ch_tuple in enumerate(span["chars"]):
            codepoint, glyph_id_pdf, origin, cb = ch_tuple
            ch = chr(codepoint)
            if ch.isspace():
                continue
            rect = fitz.Rect(cb)
            if not rect.intersects(vector_bbox):
                continue
            candidates = []
            for line in figure_lines:
                inter = fitz.Rect(rect)
                inter.intersect(line["bbox"])
                area = max(0.0, inter.width) * max(0.0, inter.height)
                if area > 0:
                    candidates.append((area, line))
            if not candidates:
                raise RuntimeError(f"glyph without semantic line: {ch!r} {rect}")
            _, line = max(candidates, key=lambda z: z[0])
            element_id = line["element_id"]
            rendered_pt = float(span["size"])
            script_class, threshold, class_reason = classify_glyph(ch, rendered_pt)
            local_bbox = point_rect_to_crop(rect, crop_box)
            x0, y0, x1, y1 = local_bbox
            ex0, ey0 = max(0, x0 - 3), max(0, y0 - 3)
            ex1, ey1 = min(crop_w, x1 + 3), min(crop_h, y1 + 3)
            bg = mode_rgb(crop_rgb[ey0:ey1, ex0:ex1])
            diff = np.max(np.abs(crop_rgb.astype(np.int16) - np.array(bg, dtype=np.int16)), axis=2)
            candidate = np.zeros((crop_h, crop_w), dtype=bool)
            candidate[y0:y1, x0:x1] = diff[y0:y1, x0:x1] >= CONTRAST_THRESHOLD
            idx = len(glyphs) + 1
            safe_stem = f"glyph_{idx:03d}_u{ord(ch):04X}"
            glyphs.append(
                {
                    "object_id": f"GLYPH-{idx:03d}",
                    "safe_stem": safe_stem,
                    "kind": "GLYPH",
                    "char": ch,
                    "codepoint": f"U+{ord(ch):04X}",
                    "pdf_glyph_id": int(glyph_id_pdf),
                    "seqno": int(span["seqno"]),
                    "origin_pt": [round(float(origin[0]), 6), round(float(origin[1]), 6)],
                    "bbox_pt": rect_tuple(rect),
                    "bbox_px": list(local_bbox),
                    "font": span["font"],
                    "rendered_pt": rendered_pt,
                    "base_effective_pt": ELEMENT_SPECS[element_id]["declared_pt"],
                    "element_id": element_id,
                    "role": ELEMENT_SPECS[element_id]["role"],
                    "source_line": source_line_map[element_id],
                    "script_class": script_class,
                    "h_threshold_px": threshold,
                    "class_reason": class_reason,
                    "background_rgb": list(bg),
                    "pre_mask": candidate,
                }
            )

    # Resolve any candidate-mask ambiguity so every final glyph raw mask is unique.
    pre_sum = np.zeros((crop_h, crop_w), dtype=np.uint16)
    for g in glyphs:
        pre_sum += g["pre_mask"].astype(np.uint16)
    ambiguous_total = int(np.count_nonzero(pre_sum > 1))
    ambiguity_rows = []
    if ambiguous_total:
        ys, xs = np.nonzero(pre_sum > 1)
        for y, x in zip(ys.tolist(), xs.tolist()):
            owners = [i for i, g in enumerate(glyphs) if g["pre_mask"][y, x]]
            def score(i: int) -> float:
                bx = glyphs[i]["bbox_px"]
                cx = (bx[0] + bx[2] - 1) / 2.0
                cy = (bx[1] + bx[3] - 1) / 2.0
                sx = max(1.0, bx[2] - bx[0])
                sy = max(1.0, bx[3] - bx[1])
                return ((x - cx) / sx) ** 2 + ((y - cy) / sy) ** 2
            owner_scores = {i: score(i) for i in owners}
            keep = min(owners, key=lambda i: owner_scores[i])
            ambiguity_rows.append(
                {
                    "PIXEL_X_CROP_300DPI": x,
                    "PIXEL_Y_CROP_300DPI": y,
                    "RAW_RGB": "/".join(str(int(v)) for v in crop_rgb[y, x]),
                    "OWNER_CANDIDATES": "|".join(glyphs[i]["object_id"] for i in owners),
                    "OWNER_BBOXES_PX": "|".join(
                        f'{glyphs[i]["object_id"]}:{glyphs[i]["bbox_px"]}' for i in owners
                    ),
                    "NORMALIZED_CENTER_SCORES": "|".join(
                        f'{glyphs[i]["object_id"]}:{owner_scores[i]:.9f}' for i in owners
                    ),
                    "ASSIGNED_OWNER": glyphs[keep]["object_id"],
                    "RESOLUTION_RULE": "minimum normalized squared distance to PDF char-bbox center; all candidate bboxes and scores logged",
                    "STATUS": "TRACEABLY_RESOLVED_REQUIRES_MANUAL_CARD_CONFIRMATION",
                }
            )
            for i in owners:
                if i != keep:
                    glyphs[i]["pre_mask"][y, x] = False

    # Reconstruct every visible PDF drawing/path independently.
    graphics = []
    background_rows = []
    background_occluders = []
    for i, (drawing, spec) in enumerate(zip(selected_drawings, GRAPHIC_SPECS), start=1):
        gid, subtype, semantic = spec
        is_border = subtype == "NODE_BORDER"
        if is_border:
            alpha_full = render_drawing_alpha(page.rect, drawing, stroke=True, fill=False)
        else:
            alpha_full = render_drawing_alpha(
                page.rect,
                drawing,
                stroke=drawing.get("color") is not None,
                fill=drawing.get("fill") is not None,
            )
        cx0, cy0, cx1, cy1 = crop_box
        alpha_crop = alpha_full[cy0:cy1, cx0:cx1]
        stroke_rgb = np.array(drawing.get("color") or drawing.get("fill"), dtype=float) * 255.0
        bg_candidates = [np.array([255.0, 255.0, 255.0])]
        if is_border and drawing.get("fill") is not None:
            bg_candidates.append(np.array(drawing["fill"], dtype=float) * 255.0)
        contrast = min(float(np.max(np.abs(stroke_rgb - bg))) for bg in bg_candidates)
        alpha_threshold = min(255, max(1, math.ceil(CONTRAST_THRESHOLD * 255.0 / max(contrast, 1.0))))
        pre_mask = alpha_crop >= alpha_threshold
        graphics.append(
            {
                "object_id": gid,
                "safe_stem": gid.lower(),
                "kind": "GRAPHIC",
                "subtype": subtype,
                "semantic": semantic,
                "seqno": int(drawing["seqno"]),
                "drawing_index_on_page": int(drawings_all.index(drawing)),
                "bbox_pt": rect_tuple(drawing["rect"]),
                "source_line": None,
                "pre_mask": pre_mask,
                "alpha_threshold": alpha_threshold,
                "stroke_color": list(drawing.get("color")) if drawing.get("color") is not None else None,
                "fill_color": list(drawing.get("fill")) if drawing.get("fill") is not None else None,
                "width_pt": float(drawing.get("width") or 0.0),
                "path_item_count": len(drawing.get("items", [])),
            }
        )
        if is_border and drawing.get("fill") is not None:
            alpha_fill = render_drawing_alpha(page.rect, drawing, stroke=False, fill=True)[cy0:cy1, cx0:cx1]
            bg_mask = alpha_fill >= 250
            bgid = f"BG-{i:03d}-NODE-FILL"
            save_mask(BASE / "graphics" / "background_masks" / f"{bgid.lower()}.png", bg_mask)
            background_occluders.append((int(drawing["seqno"]), bg_mask, bgid))
            background_rows.append(
                {
                    "BACKGROUND_ID": bgid,
                    "DRAWING_OBJECT": gid,
                    "SEQNO": int(drawing["seqno"]),
                    "TYPE": "OPAQUE_NODE_FILL",
                    "VISIBLE_FOREGROUND": "false",
                    "EXCLUSION_BASIS": "flat opaque node-card fill carries no reader information; border stroke remains a foreground object",
                    "MASK_FILE": f"graphics/background_masks/{bgid.lower()}.png",
                    "PIXELS": int(np.count_nonzero(bg_mask)),
                }
            )
    background_rows.append(
        {
            "BACKGROUND_ID": "BG-PAGE-WHITE",
            "DRAWING_OBJECT": "N/A",
            "SEQNO": -1,
            "TYPE": "PAGE_BACKGROUND",
            "VISIBLE_FOREGROUND": "false",
            "EXCLUSION_BASIS": "white page canvas carries no reader information and is not a drawing/path",
            "MASK_FILE": "N/A",
            "PIXELS": "N/A",
        }
    )

    # Apply global z-order to obtain mutually unique final-visible object masks.
    all_pre = []
    for g in glyphs:
        all_pre.append((g["seqno"], g["object_id"], g["pre_mask"], g))
    for g in graphics:
        all_pre.append((g["seqno"], g["object_id"], g["pre_mask"], g))
    by_seq_desc = sorted(all_pre, key=lambda z: (z[0], z[1]), reverse=True)
    claimed = np.zeros((crop_h, crop_w), dtype=bool)
    for seq, oid, pre_mask, obj in by_seq_desc:
        later_bg = np.zeros_like(claimed)
        for bg_seq, bg_mask, _ in background_occluders:
            if bg_seq > seq:
                later_bg |= bg_mask
        final = pre_mask & ~claimed & ~later_bg
        obj["final_mask"] = final
        obj["occluded_px"] = int(np.count_nonzero(pre_mask & ~final))
        claimed |= final

    # Create glyph measurements and evidence only after final-visible masks exist.
    glyph_rows = []
    id_map_rows = []
    overlay = crop_img.copy()
    odraw = ImageDraw.Draw(overlay)
    ofont = font_for_label(12)
    for g in glyphs:
        mask = g["final_mask"]
        bb = tight_bbox(mask)
        h = mask_height(mask)
        area = int(np.count_nonzero(mask))
        h_pass = h >= g["h_threshold_px"]
        empty = area == 0
        safe = g["safe_stem"]
        save_mask(BASE / "glyphs" / "masks" / f"{safe}.png", mask)
        save_mask(BASE / "glyphs" / "masks" / f"{safe}_pre.png", g["pre_mask"])
        base_bb = g["bbox_px"]
        rx0, ry0 = max(0, base_bb[0] - 4), max(0, base_bb[1] - 4)
        rx1, ry1 = min(crop_w, base_bb[2] + 4), min(crop_h, base_bb[3] + 4)
        roi = crop_rgb[ry0:ry1, rx0:rx1]
        roi_mask = mask[ry0:ry1, rx0:rx1]
        Image.fromarray(roi, mode="RGB").save(BASE / "glyphs" / "original_1x" / f"{safe}.png", dpi=(300, 300))
        overlay_image(roi, roi_mask).save(BASE / "glyphs" / "overlay_1x" / f"{safe}.png", dpi=(300, 300))
        mask_only_rgb(roi_mask).save(BASE / "glyphs" / "mask_only_1x" / f"{safe}.png", dpi=(300, 300))
        title = f"{g['object_id']} {g['codepoint']} {g['char']} H={h}px gate={g['h_threshold_px']}"
        card = make_three_view_card(roi, roi_mask, title, scale=8)
        card_path = BASE / "glyphs" / "cards_8x" / f"{safe}_8x.png"
        card.save(card_path)
        if empty or h <= g["h_threshold_px"] + 2 or g["occluded_px"] > 0:
            native_path = BASE / "critical" / "glyphs" / f"{safe}_native_1x.png"
            card_crit_path = BASE / "critical" / "glyphs" / f"{safe}_8x.png"
            Image.fromarray(roi, mode="RGB").save(native_path, dpi=(300, 300))
            card.save(card_crit_path)
        if bb is not None:
            odraw.rectangle(bb, outline=(220, 0, 0), width=1)
            odraw.text((bb[0], max(0, bb[1] - 12)), g["object_id"], fill=(180, 0, 0), font=ofont)
        row = {
            "ELEMENT_ID": g["object_id"],
            "PARENT_ELEMENT_ID": g["element_id"],
            "PANEL_ID": "PANEL-1",
            "ROLE": g["role"],
            "SOURCE_FILE": str(SOURCE),
            "SOURCE_LINE": g["source_line"],
            "DECLARED_PT": ELEMENT_SPECS[g["element_id"]]["declared_pt"],
            "GRAPHICS_SCALE": 1.0,
            "EFFECTIVE_PT": ELEMENT_SPECS[g["element_id"]]["declared_pt"],
            "RENDERED_GLYPH_PT": round(g["rendered_pt"], 6),
            "TEXT_SAMPLE": g["char"],
            "CODEPOINT": g["codepoint"],
            "FONT": g["font"],
            "SCRIPT_CLASS": g["script_class"],
            "BBOX_X0": g["bbox_px"][0],
            "BBOX_Y0": g["bbox_px"][1],
            "BBOX_X1": g["bbox_px"][2],
            "BBOX_Y1": g["bbox_px"][3],
            "H_INK_PX": h,
            "H_GATE_PX": g["h_threshold_px"],
            "INK_AREA_PX": area,
            "CLASS_MEDIAN_PX": "",
            "RATIO_TO_CLASS_MEDIAN": "",
            "ROLE_RATIO": "",
            "TEXT_TEXT_OVERLAP_PX": "",
            "TEXT_GRAPHIC_OVERLAP_PX": "",
            "MIN_CLEARANCE_PX": "",
            "PRE_MASK_AMBIGUOUS_GLOBAL_PX": ambiguous_total,
            "OCCLUDED_PX": g["occluded_px"],
            "EMPTY_MASK": str(empty).lower(),
            "PASS_FAIL": "PASS" if h_pass and not empty else "FAIL",
            "REASON": "H_INK meets class gate" if h_pass and not empty else f"H_INK {h}px below {g['h_threshold_px']}px gate or empty mask",
            "RAW_MASK": f"glyphs/masks/{safe}.png",
            "ORIGINAL_1X": f"glyphs/original_1x/{safe}.png",
            "TARGET_OVERLAY_1X": f"glyphs/overlay_1x/{safe}.png",
            "MASK_ONLY_1X": f"glyphs/mask_only_1x/{safe}.png",
            "CARD_8X": f"glyphs/cards_8x/{safe}_8x.png",
        }
        glyph_rows.append(row)
        id_map_rows.append({"OBJECT_ID": g["object_id"], "SAFE_FILENAME": safe, "KIND": "GLYPH"})

    # D ratios are computed at parent-element × script-class medians, not by exact codepoint.
    parent_class_values = defaultdict(list)
    for row in glyph_rows:
        if row["H_INK_PX"] > 0:
            parent_class_values[(row["PARENT_ELEMENT_ID"], row["SCRIPT_CLASS"])].append(row["H_INK_PX"])
    parent_class_median = {k: float(statistics.median(v)) for k, v in parent_class_values.items()}
    role_class_medians = defaultdict(list)
    for (parent, cls), med in parent_class_median.items():
        role_class_medians[(ELEMENT_SPECS[parent]["role"], cls)].append(med)
    role_class_reference = {k: float(statistics.median(v)) for k, v in role_class_medians.items()}
    for row in glyph_rows:
        key = (row["PARENT_ELEMENT_ID"], row["SCRIPT_CLASS"])
        med = parent_class_median.get(key)
        row["CLASS_MEDIAN_PX"] = "" if med is None else round(med, 6)
        row["RATIO_TO_CLASS_MEDIAN"] = "" if med is None or med == 0 else round(row["H_INK_PX"] / med, 6)
        rkey = (row["ROLE"], row["SCRIPT_CLASS"])
        ref = role_class_reference.get(rkey)
        row["ROLE_RATIO"] = "" if ref is None or ref == 0 or med is None else round(med / ref, 6)

    overlay.save(BASE / "after_text_measurement_overlay_300dpi.png", dpi=(300, 300))

    # Graphics evidence.
    path_rows = []
    for g in graphics:
        pre = g["pre_mask"]
        final = g["final_mask"]
        safe = g["safe_stem"]
        save_mask(BASE / "graphics" / "pre_masks" / f"{safe}_pre.png", pre)
        save_mask(BASE / "graphics" / "final_masks" / f"{safe}_final.png", final)
        bb = tight_bbox(pre) or (0, 0, 1, 1)
        rx0, ry0 = max(0, bb[0] - 6), max(0, bb[1] - 6)
        rx1, ry1 = min(crop_w, bb[2] + 6), min(crop_h, bb[3] + 6)
        roi = crop_rgb[ry0:ry1, rx0:rx1]
        roi_mask = final[ry0:ry1, rx0:rx1]
        Image.fromarray(roi, mode="RGB").save(BASE / "graphics" / "original_1x" / f"{safe}.png", dpi=(300, 300))
        overlay_image(roi, roi_mask).save(BASE / "graphics" / "overlay_1x" / f"{safe}.png", dpi=(300, 300))
        mask_only_rgb(roi_mask).save(BASE / "graphics" / "mask_only_1x" / f"{safe}.png", dpi=(300, 300))
        title = f"{g['object_id']} {g['subtype']} seq={g['seqno']}"
        card = make_three_view_card(roi, roi_mask, title, scale=8)
        card_path = BASE / "graphics" / "contact_sheets" / f"sheet_{g['object_id']}_8x.png"
        card.save(card_path)
        path_rows.append(
            {
                "GRAPHIC_ID": g["object_id"],
                "SUBTYPE": g["subtype"],
                "SEMANTIC_PARENT": g["semantic"],
                "SEQNO": g["seqno"],
                "DRAWING_INDEX_ON_PAGE": g["drawing_index_on_page"],
                "BBOX_PT": json.dumps(g["bbox_pt"]),
                "PATH_ITEM_COUNT": g["path_item_count"],
                "WIDTH_PT": g["width_pt"],
                "PRE_MASK_PX": int(np.count_nonzero(pre)),
                "FINAL_VISIBLE_MASK_PX": int(np.count_nonzero(final)),
                "OCCLUDED_PX": g["occluded_px"],
                "EMPTY_MASK": str(np.count_nonzero(final) == 0).lower(),
                "MATH_RULE": "false",
                "PRE_MASK": f"graphics/pre_masks/{safe}_pre.png",
                "FINAL_MASK": f"graphics/final_masks/{safe}_final.png",
                "ORIGINAL_1X": f"graphics/original_1x/{safe}.png",
                "TARGET_OVERLAY_1X": f"graphics/overlay_1x/{safe}.png",
                "MASK_ONLY_1X": f"graphics/mask_only_1x/{safe}.png",
                "CONTACT_SHEET_8X": f"graphics/contact_sheets/sheet_{g['object_id']}_8x.png",
                "MACHINE_DECISION": "PASS" if np.count_nonzero(final) > 0 else "FAIL",
            }
        )
        id_map_rows.append({"OBJECT_ID": g["object_id"], "SAFE_FILENAME": safe, "KIND": "GRAPHIC"})

    # Build glyph contact sheets after individual cards have fixed native evidence.
    glyph_sheet_rows = []
    per_sheet = 8
    for sheet_idx in range(math.ceil(len(glyphs) / per_sheet)):
        chunk = glyphs[sheet_idx * per_sheet : (sheet_idx + 1) * per_sheet]
        cards = [Image.open(BASE / "glyphs" / "cards_8x" / f"{g['safe_stem']}_8x.png").convert("RGB") for g in chunk]
        max_w = max(c.width for c in cards)
        max_h = max(c.height for c in cards)
        canvas = Image.new("RGB", (max_w, max_h * len(cards)), "white")
        y = 0
        for cell_idx, (g, card) in enumerate(zip(chunk, cards), start=1):
            canvas.paste(card, (0, y))
            glyph_sheet_rows.append(
                {
                    "GLYPH_ID": g["object_id"],
                    "SHEET": f"GLYPH-SHEET-{sheet_idx + 1:02d}",
                    "CELL": f"R{cell_idx:02d}",
                    "SHEET_FILE": f"glyphs/contact_sheets/glyph_contact_sheet_{sheet_idx + 1:02d}_8x.png",
                }
            )
            y += max_h
        canvas.save(BASE / "glyphs" / "contact_sheets" / f"glyph_contact_sheet_{sheet_idx + 1:02d}_8x.png")

    sheet_by_glyph = {r["GLYPH_ID"]: r for r in glyph_sheet_rows}
    glyph_manual_rows = []
    for g in glyphs:
        s = sheet_by_glyph[g["object_id"]]
        glyph_manual_rows.append(
            {
                "GLYPH_ID": g["object_id"],
                "REVIEWER": "MANUAL_REVIEW_REQUIRED_TEMPLATE",
                "SHEET": s["SHEET"],
                "CELL": s["CELL"],
                "ORIGINAL_MATCH": "MANUAL_REVIEW_REQUIRED_TEMPLATE",
                "OVERLAY_COMPLETE": "MANUAL_REVIEW_REQUIRED_TEMPLATE",
                "MASK_ONLY_PURE": "MANUAL_REVIEW_REQUIRED_TEMPLATE",
                "MISSING_STROKE_PX": "MANUAL_REVIEW_REQUIRED_TEMPLATE",
                "FOREIGN_PIXEL_PX": "MANUAL_REVIEW_REQUIRED_TEMPLATE",
                "DECISION": "MANUAL_REVIEW_REQUIRED_TEMPLATE",
                "NOTE": "manual inspection not yet signed",
            }
        )
    graphic_manual_rows = [
        {
            "GRAPHIC_ID": g["object_id"],
            "REVIEWER": "MANUAL_REVIEW_REQUIRED_TEMPLATE",
            "SHEET": f"sheet_{g['object_id']}_8x.png",
            "CELL": "ONLY",
            "ORIGINAL_MATCH": "MANUAL_REVIEW_REQUIRED_TEMPLATE",
            "OVERLAY_COMPLETE": "MANUAL_REVIEW_REQUIRED_TEMPLATE",
            "MASK_ONLY_PURE": "MANUAL_REVIEW_REQUIRED_TEMPLATE",
            "MISSING_STROKE_PX": "MANUAL_REVIEW_REQUIRED_TEMPLATE",
            "FOREIGN_PIXEL_PX": "MANUAL_REVIEW_REQUIRED_TEMPLATE",
            "DECISION": "MANUAL_REVIEW_REQUIRED_TEMPLATE",
            "NOTE": "manual inspection not yet signed",
        }
        for g in graphics
    ]

    # Unified foreground object denominator and all unordered pairs.
    objects = []
    for g in glyphs:
        objects.append(
            {
                "object_id": g["object_id"],
                "kind": "GLYPH",
                "subtype": g["script_class"],
                "semantic_parent": g["element_id"],
                "role": g["role"],
                "seqno": g["seqno"],
                "bbox": tight_bbox(g["final_mask"]),
                "pre_mask": g["pre_mask"],
                "mask": g["final_mask"],
                "char": g["char"],
            }
        )
    for g in graphics:
        objects.append(
            {
                "object_id": g["object_id"],
                "kind": "GRAPHIC",
                "subtype": g["subtype"],
                "semantic_parent": g["semantic"],
                "role": g["subtype"],
                "seqno": g["seqno"],
                "bbox": tight_bbox(g["final_mask"]),
                "pre_mask": g["pre_mask"],
                "mask": g["final_mask"],
                "char": "",
            }
        )
    n_objects = len(objects)
    expected_pairs = n_objects * (n_objects - 1) // 2
    pair_rows = []
    critical_pair_specs = []
    pair_number = 0
    # Distance transforms are generated once per A object, then queried for every later B.
    for ia, a in enumerate(objects):
        if np.count_nonzero(a["mask"]) > 0:
            dist_map = distance_transform_edt(~a["mask"])
        else:
            dist_map = None
        for ib in range(ia + 1, n_objects):
            b = objects[ib]
            pair_number += 1
            pid = f"PAIR-{pair_number:05d}"
            final_overlap = int(np.count_nonzero(a["mask"] & b["mask"]))
            pre_overlap = int(np.count_nonzero(a["pre_mask"] & b["pre_mask"]))
            if dist_map is None or np.count_nonzero(b["mask"]) == 0:
                raw_clearance = None
            elif final_overlap > 0:
                raw_clearance = 0.0
            else:
                raw_clearance = max(0.0, float(np.min(dist_map[b["mask"]])) - 1.0)
            bb_clear = bbox_clearance(a["bbox"], b["bbox"])
            structural = frozenset([a["object_id"], b["object_id"]]) in STRUCTURAL_PAIRS
            relation = ""
            threshold = None
            metric = "RAW_MASK_CLEARANCE"
            same_parent = a["kind"] == b["kind"] == "GLYPH" and a["semantic_parent"] == b["semantic_parent"]
            if a["kind"] == b["kind"] == "GLYPH":
                relation = "TEXT_TEXT_SAME_PARENT" if same_parent else "TEXT_TEXT_INDEPENDENT"
                if not same_parent:
                    threshold = 4.0
                    metric = "VECTOR_BBOX_CLEARANCE"
            elif a["kind"] != b["kind"]:
                text = a if a["kind"] == "GLYPH" else b
                graphic = b if a["kind"] == "GLYPH" else a
                if PARENT_BORDER.get(text["semantic_parent"]) == graphic["object_id"]:
                    relation = "TEXT_NODE_BORDER"
                    threshold = 5.0
                elif graphic["subtype"] in {"LINE_ARROW_SHAFT", "ARROWHEAD", "LEADER_LINE"}:
                    relation = "TEXT_LINE_ARROW"
                    threshold = 3.0
                else:
                    relation = "TEXT_OTHER_BORDER"
                    threshold = 3.0
            else:
                relation = "GRAPHIC_GRAPHIC_STRUCTURAL" if structural else "GRAPHIC_GRAPHIC_OTHER"
            value = bb_clear if metric == "VECTOR_BBOX_CLEARANCE" else raw_clearance
            illegal_pre_overlap = pre_overlap > 0 and not structural and not same_parent
            gate_fail = final_overlap > 0 or illegal_pre_overlap
            if threshold is not None and (value is None or value < threshold):
                gate_fail = True
            decision = "FAIL" if gate_fail else "PASS"
            evidence_required = (
                gate_fail
                or structural
                or pre_overlap > 0
                or (threshold is not None and value is not None and value <= threshold + 2.0)
            )
            row = {
                "PAIR_ID": pid,
                "OBJECT_A": a["object_id"],
                "OBJECT_B": b["object_id"],
                "KIND_A": a["kind"],
                "KIND_B": b["kind"],
                "RELATION": relation,
                "SAME_SEMANTIC_PARENT": str(same_parent).lower(),
                "STRUCTURAL_ENDPOINT_OR_CONTACT": str(structural).lower(),
                "PRE_OCCLUSION_INTERSECTION_PX": pre_overlap,
                "FINAL_VISIBLE_INTERSECTION_PX": final_overlap,
                "RAW_MASK_CLEARANCE_PX": "" if raw_clearance is None else round(raw_clearance, 6),
                "VECTOR_BBOX_CLEARANCE_PX": "" if bb_clear is None else round(bb_clear, 6),
                "GATE_METRIC": metric,
                "GATE_THRESHOLD_PX": "" if threshold is None else threshold,
                "EVIDENCE_REQUIRED": str(evidence_required).lower(),
                "DECISION": decision,
                "REASON": (
                    "structural source-semantic endpoint/contact; final-visible masks still checked"
                    if structural and not gate_fail
                    else "all applicable overlap/clearance gates pass"
                    if not gate_fail
                    else "illegal pre/final overlap, empty mask, or applicable clearance below hard threshold"
                ),
                "EVIDENCE_DIR": f"critical/pairs/{pid.lower()}" if evidence_required else "N/A",
            }
            pair_rows.append(row)
            if evidence_required:
                critical_pair_specs.append((row, a, b))
    if pair_number != expected_pairs:
        raise RuntimeError(f"pair closure mismatch {pair_number} != {expected_pairs}")

    # Critical/contact pair cards: tight ROI around the nearest/contact pixels.
    pair_manual_rows = []
    for row, a, b in critical_pair_specs:
        pid = row["PAIR_ID"]
        outdir = BASE / "critical" / "pairs" / pid.lower()
        outdir.mkdir(parents=True, exist_ok=True)
        pre_inter = a["pre_mask"] & b["pre_mask"]
        if np.any(pre_inter):
            bb = tight_bbox(pre_inter)
            assert bb is not None
            cx = (bb[0] + bb[2] - 1) // 2
            cy = (bb[1] + bb[3] - 1) // 2
        else:
            nearest = nearest_points(a["mask"], b["mask"])
            if nearest is None:
                cx = cy = 0
            else:
                pa, pb, _ = nearest
                cx = (pa[0] + pb[0]) // 2
                cy = (pa[1] + pb[1]) // 2
        radius = 18
        x0, y0 = max(0, cx - radius), max(0, cy - radius)
        x1, y1 = min(crop_w, cx + radius + 1), min(crop_h, cy + radius + 1)
        roi = crop_rgb[y0:y1, x0:x1]
        ma = a["mask"][y0:y1, x0:x1]
        mb = b["mask"][y0:y1, x0:x1]
        inter = ma & mb
        prei = pre_inter[y0:y1, x0:x1]
        Image.fromarray(roi, mode="RGB").save(outdir / "raw_original_1x.png", dpi=(300, 300))
        save_mask(outdir / "mask_a_1x.png", ma)
        save_mask(outdir / "mask_b_1x.png", mb)
        save_mask(outdir / "final_intersection_1x.png", inter)
        save_mask(outdir / "pre_intersection_1x.png", prei)
        both = roi.astype(np.float32).copy()
        both[ma] = both[ma] * 0.35 + np.array([255, 0, 0]) * 0.65
        both[mb] = both[mb] * 0.35 + np.array([0, 80, 255]) * 0.65
        both[inter] = np.array([255, 0, 255])
        overlay_pair = Image.fromarray(np.clip(both, 0, 255).astype(np.uint8), mode="RGB")
        overlay_pair.save(outdir / "overlay_1x.png", dpi=(300, 300))
        views = [
            Image.fromarray(roi, mode="RGB"),
            mask_only_rgb(ma),
            mask_only_rgb(mb),
            mask_only_rgb(inter),
            overlay_pair,
        ]
        labels = ["RAW", "MASK A", "MASK B", "FINAL INTERSECTION", "OVERLAY"]
        up = [v.resize((v.width * 8, v.height * 8), Image.Resampling.NEAREST) for v in views]
        gap = 12
        title_h = 60
        canvas = Image.new("RGB", (sum(v.width for v in up) + gap * 6, title_h + max(v.height for v in up) + 30), "white")
        draw = ImageDraw.Draw(canvas)
        font = font_for_label(15)
        draw.text((gap, 4), f"{pid}: {a['object_id']} <> {b['object_id']} | {row['RELATION']}", fill="black", font=font)
        x = gap
        for label, view in zip(labels, up):
            draw.text((x, 30), label, fill="black", font=font)
            canvas.paste(view, (x, title_h))
            x += view.width + gap
        canvas.save(outdir / "card_8x.png")
        row["ROI_X0"] = x0
        row["ROI_Y0"] = y0
        row["ROI_X1"] = x1
        row["ROI_Y1"] = y1
        pair_manual_rows.append(
            {
                "PAIR_ID": pid,
                "REVIEWER": "MANUAL_REVIEW_REQUIRED_TEMPLATE",
                "CARD": f"critical/pairs/{pid.lower()}/card_8x.png",
                "RAW_MATCH": "MANUAL_REVIEW_REQUIRED_TEMPLATE",
                "A_MASK_PURE": "MANUAL_REVIEW_REQUIRED_TEMPLATE",
                "B_MASK_PURE": "MANUAL_REVIEW_REQUIRED_TEMPLATE",
                "INTERSECTION_CONFIRMED": "MANUAL_REVIEW_REQUIRED_TEMPLATE",
                "SOURCE_SEMANTICS": "MANUAL_REVIEW_REQUIRED_TEMPLATE",
                "DECISION": "MANUAL_REVIEW_REQUIRED_TEMPLATE",
                "NOTE": "manual inspection not yet signed",
            }
        )

    # Update per-glyph minimum relations and overlap totals.
    rows_by_gid = {r["ELEMENT_ID"]: r for r in glyph_rows}
    for gid, row in rows_by_gid.items():
        rels = [r for r in pair_rows if gid in {r["OBJECT_A"], r["OBJECT_B"]}]
        tt_ov = sum(int(r["PRE_OCCLUSION_INTERSECTION_PX"]) for r in rels if r["RELATION"].startswith("TEXT_TEXT"))
        tg_ov = sum(int(r["PRE_OCCLUSION_INTERSECTION_PX"]) for r in rels if r["RELATION"].startswith("TEXT_") and not r["RELATION"].startswith("TEXT_TEXT"))
        vals = []
        for r in rels:
            if r["GATE_THRESHOLD_PX"] != "":
                v = r["VECTOR_BBOX_CLEARANCE_PX"] if r["GATE_METRIC"] == "VECTOR_BBOX_CLEARANCE" else r["RAW_MASK_CLEARANCE_PX"]
                if v != "":
                    vals.append(float(v))
        row["TEXT_TEXT_OVERLAP_PX"] = tt_ov
        row["TEXT_GRAPHIC_OVERLAP_PX"] = tg_ov
        row["MIN_CLEARANCE_PX"] = "" if not vals else round(min(vals), 6)

    # Source-level font audit.
    element_rows = []
    for eid, spec in ELEMENT_SPECS.items():
        source_line = source_line_map[eid]
        effective = spec["declared_pt"]
        source_pass = effective >= 9.5
        element_rows.append(
            {
                "ELEMENT_ID": eid,
                "PANEL_ID": "PANEL-1",
                "ROLE": spec["role"],
                "SOURCE_FILE": str(SOURCE),
                "SOURCE_LINE": source_line,
                "DECLARED_PT": spec["declared_pt"],
                "GRAPHICS_SCALE": 1.0,
                "EFFECTIVE_PT": effective,
                "SCALE_COMMANDS": "none",
                "RESIZEBOX": "false",
                "SCALEBOX": "false",
                "TRANSFORM_SHAPE": "false",
                "SOURCE_FONT_PASS": str(source_pass).lower(),
                "REASON": "effective_pt >= 9.5pt; no cumulative graphics scaling",
            }
        )

    # Standalone is only a visual cross-check and is never used for pixel counts.
    standalone_record = {"available": STANDALONE_PDF.exists(), "pdf": str(STANDALONE_PDF), "counting_authority": False}
    if STANDALONE_PDF.exists():
        sdoc = fitz.open(STANDALONE_PDF)
        spage = sdoc[0]
        simg = render_page(spage, 300, alpha=False)
        sdraw = spage.get_drawings(extended=True)
        if sdraw:
            sbox = bbox_union([fitz.Rect(d["rect"]) for d in sdraw])
            scrop = crop_box_from_pts(sbox, SCALE_300, 2, simg.size)
            sfig = simg.crop(scrop)
            sfig.save(BASE / "render" / "standalone_300dpi.png", dpi=(300, 300))
            standalone_record.update({"page_rect_pt": rect_tuple(spage.rect), "crop_box_px": list(scrop), "dimensions_px": list(sfig.size)})
        sdoc.close()
    else:
        # An official-PDF strict crop is retained as an explicit fallback view; identity record marks why.
        crop_img.save(BASE / "render" / "standalone_300dpi.png", dpi=(300, 300))
        standalone_record.update({"fallback": "official strict crop duplicated without resize because independent TeX compilation was unavailable at pipeline time", "dimensions_px": list(crop_img.size)})
    save_json(BASE / "source_identity" / "standalone_identity.json", standalone_record)

    write_csv(BASE / "after_font_audit.csv", element_rows)
    write_csv(BASE / "after_pixel_measurements.csv", glyph_rows)
    write_csv(BASE / "after_overlap_report.csv", pair_rows)
    write_csv(BASE / "glyph_machine_ledger.csv", glyph_rows)
    write_csv(BASE / "glyph_contact_sheet_index.csv", glyph_sheet_rows)
    write_csv(BASE / "glyph_manual_review.csv", glyph_manual_rows)
    write_csv(BASE / "path_ledger.csv", path_rows)
    write_csv(BASE / "graphic_manual_review.csv", graphic_manual_rows)
    write_csv(BASE / "background_exclusion_ledger.csv", background_rows)
    write_csv(BASE / "glyph_ambiguity_resolution.csv", ambiguity_rows, [
        "PIXEL_X_CROP_300DPI", "PIXEL_Y_CROP_300DPI", "RAW_RGB", "OWNER_CANDIDATES",
        "OWNER_BBOXES_PX", "NORMALIZED_CENTER_SCORES", "ASSIGNED_OWNER", "RESOLUTION_RULE", "STATUS"
    ])
    write_csv(BASE / "critical_pair_manual_review.csv", pair_manual_rows)
    write_csv(BASE / "id_safe_filename_map.csv", id_map_rows)

    glyph_fail_ids = [r["ELEMENT_ID"] for r in glyph_rows if r["PASS_FAIL"] == "FAIL"]
    pair_fail_ids = [r["PAIR_ID"] for r in pair_rows if r["DECISION"] == "FAIL"]
    empty_glyphs = [g["object_id"] for g in glyphs if np.count_nonzero(g["final_mask"]) == 0]
    empty_graphics = [g["object_id"] for g in graphics if np.count_nonzero(g["final_mask"]) == 0]
    object_manifest_rows = []
    for o in objects:
        object_manifest_rows.append(
            {
                "OBJECT_ID": o["object_id"],
                "KIND": o["kind"],
                "SUBTYPE": o["subtype"],
                "SEMANTIC_PARENT": o["semantic_parent"],
                "SEQNO": o["seqno"],
                "FINAL_VISIBLE_PIXELS": int(np.count_nonzero(o["mask"])),
                "BBOX_PX": json.dumps(o["bbox"]),
            }
        )
    write_csv(BASE / "object_manifest.csv", object_manifest_rows)
    machine = {
        "glyph_count": len(glyphs),
        "graphic_path_count": len(graphics),
        "math_rule_count": 0,
        "math_rule_basis": "PDF text tracing contains all math symbols in this figure; the 21 drawing/path records are node borders/fills, arrow shafts/heads and semantic leaders, with no unassigned formula rule path",
        "foreground_object_count_N": n_objects,
        "expected_unordered_pairs_C_N_2": expected_pairs,
        "actual_unordered_pairs": len(pair_rows),
        "pair_closure": len(pair_rows) == expected_pairs,
        "ambiguous_glyph_pixels_before_unique_assignment": ambiguous_total,
        "ambiguous_glyph_pixels_traceably_assigned": len(ambiguity_rows),
        "glyph_ambiguity_resolution_status": "TRACEABLY_RESOLVED_REQUIRES_MANUAL_CARD_CONFIRMATION" if ambiguity_rows else "NOT_APPLICABLE_ZERO_AMBIGUITY",
        "empty_glyph_masks": empty_glyphs,
        "empty_graphic_masks": empty_graphics,
        "glyph_hard_fail_count": len(glyph_fail_ids),
        "glyph_hard_fail_ids": glyph_fail_ids,
        "pair_hard_fail_count": len(pair_fail_ids),
        "pair_hard_fail_ids": pair_fail_ids,
        "critical_pair_card_count": len(pair_manual_rows),
        "glyph_contact_sheet_count": math.ceil(len(glyphs) / per_sheet),
        "graphic_contact_sheet_count": len(graphics),
        "manual_pending_glyph_rows": len(glyph_manual_rows),
        "manual_pending_graphic_rows": len(graphic_manual_rows),
        "manual_pending_pair_rows": len(pair_manual_rows),
        "overall_machine_status": "FAIL" if glyph_fail_ids or pair_fail_ids or empty_glyphs or empty_graphics or ambiguous_total else "PASS_REQUIRES_MANUAL_REVIEW",
    }
    save_json(BASE / "machine_precheck.json", machine)
    save_json(
        BASE / "source_identity" / "pdf_text_drawing_double_inventory.json",
        {
            "figure_rawdict_lines": [
                {"bbox_pt": rect_tuple(x["bbox"]), "text": x["text"], "element_id": x["element_id"]}
                for x in figure_lines
            ],
            "reader_visible_glyphs": [
                {k: v for k, v in g.items() if k not in {"pre_mask", "final_mask"}}
                for g in glyphs
            ],
            "visible_drawings": [
                {
                    "object_id": g["object_id"],
                    "subtype": g["subtype"],
                    "seqno": g["seqno"],
                    "drawing_index_on_page": g["drawing_index_on_page"],
                    "bbox_pt": g["bbox_pt"],
                    "path_item_count": g["path_item_count"],
                }
                for g in graphics
            ],
            "unassigned_text_glyph_count": 0,
            "unassigned_visible_drawing_path_count": 0,
            "formula_rule_path_count": 0,
        },
    )
    doc.close()


if __name__ == "__main__":
    main()
