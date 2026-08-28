from __future__ import annotations

import csv
import hashlib
import itertools
import json
import math
import shutil
import unicodedata
from collections import Counter
from pathlib import Path

import fitz
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.ndimage import binary_dilation, distance_transform_edt


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P602-01\sa3_r103_fresh_isolated_v1")
PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r103_fullbook\main_full.pdf")
SOURCE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C03\fig_v5_c03_mh_accept_reject.tex")
PHYSICAL_PAGE = 653
PAGE_INDEX = PHYSICAL_PAGE - 1
CROP = (312, 1444, 2122, 3008)  # x0, y0, x1, y1 on native 300 dpi full-page raster


def jdefault(value):
    if isinstance(value, (fitz.Point, fitz.Rect, fitz.Quad)):
        return list(value)
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, np.generic):
        return value.item()
    raise TypeError(type(value).__name__)


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, default=jdefault) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = list(rows[0].keys()) if rows else []
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def file_identity(path: Path) -> dict:
    st = path.stat()
    return {
        "path": str(path),
        "bytes": st.st_size,
        "sha256": sha256(path),
        "mtime_utc_ns_since_unix_epoch": st.st_mtime_ns,
    }


def rect_union(rects: list[tuple[float, float, float, float]]) -> tuple[float, float, float, float]:
    return (
        min(r[0] for r in rects),
        min(r[1] for r in rects),
        max(r[2] for r in rects),
        max(r[3] for r in rects),
    )


def color_int_to_rgb(color: int) -> tuple[int, int, int]:
    return ((color >> 16) & 255, (color >> 8) & 255, color & 255)


def projected_color_mask(region: np.ndarray, target: tuple[int, int, int], backgrounds: list[tuple[int, int, int]]) -> np.ndarray:
    p = region.astype(np.float32)
    target_arr = np.array(target, dtype=np.float32)
    out = np.zeros(region.shape[:2], dtype=bool)
    for bg in backgrounds:
        bg_arr = np.array(bg, dtype=np.float32)
        v = target_arr - bg_arr
        denom = float(np.dot(v, v))
        if denom == 0:
            continue
        t = np.sum((p - bg_arr) * v, axis=2) / denom
        projected = bg_arr + t[..., None] * v
        residual = np.sqrt(np.sum((p - projected) ** 2, axis=2))
        contrast = np.max(np.abs(p - bg_arr), axis=2)
        out |= (t >= 0.075) & (t <= 1.25) & (residual <= 18.0) & (contrast >= 20.0)
    return out


def pt_to_crop(point: fitz.Point, sx: float, sy: float) -> tuple[float, float]:
    return (point.x * sx - CROP[0], point.y * sy - CROP[1])


def cubic_points(p0, p1, p2, p3, steps: int = 64) -> list[tuple[float, float]]:
    out = []
    for i in range(steps + 1):
        t = i / steps
        u = 1.0 - t
        x = u**3 * p0[0] + 3*u*u*t*p1[0] + 3*u*t*t*p2[0] + t**3*p3[0]
        y = u**3 * p0[1] + 3*u*u*t*p1[1] + 3*u*t*t*p2[1] + t**3*p3[1]
        out.append((x, y))
    return out


def drawing_geometry_mask(drawing: dict, sx: float, sy: float, canvas_size: tuple[int, int], fill_path: bool) -> np.ndarray:
    """Raster support only; final-visible pixels still come from the candidate raster."""
    w, h = canvas_size
    geom_img = Image.new("1", (w, h), 0)
    gd = ImageDraw.Draw(geom_img)
    path_points: list[tuple[float, float]] = []
    stroke_width = max(3, int(math.ceil(float(drawing.get("width") or 0.5) * (sx + sy) / 2)) + 4)
    for item in drawing["items"]:
        op = item[0]
        if op == "l":
            a = pt_to_crop(item[1], sx, sy)
            b = pt_to_crop(item[2], sx, sy)
            gd.line((a, b), fill=1, width=stroke_width)
            path_points.extend((a, b))
        elif op == "c":
            pts = [pt_to_crop(item[j], sx, sy) for j in range(1, 5)]
            curve = cubic_points(*pts)
            gd.line(curve, fill=1, width=stroke_width)
            path_points.extend(curve)
        elif op == "re":
            r = item[1]
            a = pt_to_crop(fitz.Point(r.x0, r.y0), sx, sy)
            b = pt_to_crop(fitz.Point(r.x1, r.y1), sx, sy)
            gd.rectangle((a, b), outline=1, width=stroke_width)
            path_points.extend((a, (b[0], a[1]), b, (a[0], b[1])))
        elif op == "qu":
            q = item[1]
            pts = [pt_to_crop(p, sx, sy) for p in (q.ul, q.ur, q.lr, q.ll)]
            gd.line(pts + [pts[0]], fill=1, width=stroke_width)
            path_points.extend(pts)
    if fill_path and path_points:
        # Filled drawing records here are arrowheads; node records deliberately pass fill_path=False.
        unique = []
        for pt in path_points:
            if not unique or pt != unique[-1]:
                unique.append(pt)
        gd.polygon(unique, fill=1)
    return binary_dilation(np.array(geom_img, dtype=bool), iterations=2)


def save_small_mask(full_mask: np.ndarray, path: Path) -> tuple[int, int, int, int, int]:
    ys, xs = np.nonzero(full_mask)
    if len(xs) == 0:
        bbox = (0, 0, 0, 0)
        small = np.zeros((1, 1), dtype=np.uint8)
    else:
        bbox = (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1)
        small = (full_mask[bbox[1]:bbox[3], bbox[0]:bbox[2]] * 255).astype(np.uint8)
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(small, mode="L").save(path)
    return (*bbox, int(full_mask.sum()))


def object_parent_for_bbox(bbox_pt: tuple[float, float, float, float]) -> str | None:
    x0, y0, x1, y1 = bbox_pt
    cy = (y0 + y1) / 2
    cx = (x0 + x1) / 2
    if 348 <= cy < 365:
        return "T01_CURRENT_NODE_TITLE"
    if 365 <= cy < 380:
        return "T02_CURRENT_NODE_VARIABLE"
    if 380 <= cy < 394:
        return "T13_PROPOSAL_LABEL"
    if 393 <= cy < 410:
        return "T03_CANDIDATE_NODE_ACTION"
    if 410 <= cy < 424:
        return "T04_CANDIDATE_NODE_VARIABLE"
    if 424 <= cy < 439:
        return "T14_CALCULATE_LABEL"
    if 439 <= cy < 459:
        return "T05_RATIO_HEADER"
    if 459 <= cy < 490:
        return "T06_RATIO_FORMULA"
    if 490 <= cy < 505:
        return "T15_DECISION_LABEL"
    if 505 <= cy < 543:
        return "T07_DECISION_DRAW"
    if 543 <= cy < 557:
        return "T08_DECISION_COMPARE"
    if 557 <= cy < 572 and cx < 240:
        return "T16_ACCEPT_LABEL"
    if 557 <= cy < 572 and cx >= 240:
        return "T17_REJECT_LABEL"
    if 580 <= cy < 599 and cx < 250:
        return "T09_ACCEPT_NODE_ACTION"
    if 599 <= cy < 616 and cx < 250:
        return "T10_ACCEPT_NODE_ASSIGNMENT"
    if 580 <= cy < 599 and cx >= 250:
        return "T11_REJECT_NODE_ACTION"
    if 599 <= cy < 616 and cx >= 250:
        return "T12_REJECT_NODE_ASSIGNMENT"
    if 680 <= cy < 697:
        return "T18_SELFLOOP_LABEL"
    if 697 <= cy < 716 and cx < 185:
        return "T19_CAPTION_LABEL"
    if 697 <= cy < 716 and cx >= 185:
        return "T20_CAPTION_TEXT"
    return None


def script_class(char: str, size_pt: float, parent_id: str) -> tuple[str, int]:
    name = unicodedata.name(char, "")
    cp = ord(char)
    if char in "。．，、；：,.…":
        return "LOW_PROFILE_PUNCTUATION", 1
    if size_pt < 9.5 and parent_id not in {"T19_CAPTION_LABEL", "T20_CAPTION_TEXT"}:
        return "NATURAL_TEX_SCRIPT", 15
    if (0x3400 <= cp <= 0x9FFF) or (0xF900 <= cp <= 0xFAFF) or (0xFF01 <= cp <= 0xFF60):
        return "CJK_OR_FULLWIDTH", 30
    if "CAPITAL" in name or char.isdigit():
        return "LATIN_CAPITAL_OR_DIGIT", 24
    if "SMALL" in name or ("GREEK" in name and char.islower()) or ("LATIN" in name and char.islower()):
        return "LATIN_OR_GREEK_LOWER", 17
    if char in "−-+=≤<>∣|{}[]()？?∼":
        return "BASE_MATH_OPERATOR", 22
    if unicodedata.category(char).startswith("P"):
        return "PUNCTUATION_FULL_OR_OTHER", 1
    if parent_id == "T06_RATIO_FORMULA":
        return "BASE_MATH", 22
    return "OTHER_VISIBLE", 17


def make_contact(original: np.ndarray, mask: np.ndarray, bbox: tuple[int, int, int, int], title: str, out: Path) -> None:
    x0, y0, x1, y1 = bbox
    pad = 4
    ax0, ay0 = max(0, x0 - pad), max(0, y0 - pad)
    ax1, ay1 = min(original.shape[1], x1 + pad), min(original.shape[0], y1 + pad)
    roi = original[ay0:ay1, ax0:ax1].copy()
    m = mask[ay0:ay1, ax0:ax1]
    overlay = roi.copy()
    overlay[m] = (255, 0, 0)
    mask_rgb = np.full_like(roi, 255)
    mask_rgb[m] = (0, 0, 0)
    roi_img = Image.fromarray(roi)
    overlay_img = Image.fromarray(overlay)
    mask_img = Image.fromarray(mask_rgb)
    overlay8 = overlay_img.resize((max(1, overlay_img.width * 8), max(1, overlay_img.height * 8)), Image.Resampling.NEAREST)
    width = max(720, 30 + roi_img.width * 3 + 30 + overlay8.width)
    height = max(180, 64 + overlay8.height)
    canvas = Image.new("RGB", (width, height), "white")
    d = ImageDraw.Draw(canvas)
    d.text((10, 8), title, fill="black")
    d.text((10, 26), f"native bbox={bbox}; roi={[ax0, ay0, ax1, ay1]}; 8x=nearest", fill="black")
    x = 10
    for label, im in (("ORIGINAL 1x", roi_img), ("TARGET OVERLAY 1x", overlay_img), ("MASK ONLY 1x", mask_img)):
        d.text((x, 44), label, fill="black")
        canvas.paste(im, (x, 62))
        x += im.width + 10
    d.text((x + 10, 44), "TARGET OVERLAY 8x NEAREST", fill="black")
    canvas.paste(overlay8, (x + 10, 62))
    out.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(out)


def make_master_sheets(contact_paths: list[Path], out_dir: Path, prefix: str, per_sheet: int = 8) -> list[str]:
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for si in range(0, len(contact_paths), per_sheet):
        chunk = contact_paths[si:si + per_sheet]
        ims = [Image.open(p).convert("RGB") for p in chunk]
        maxw = max(im.width for im in ims)
        totalh = sum(im.height for im in ims) + 8 * (len(ims) - 1)
        sheet = Image.new("RGB", (maxw, totalh), (235, 235, 235))
        y = 0
        for im in ims:
            sheet.paste(im, (0, y))
            y += im.height + 8
        path = out_dir / f"{prefix}_{si // per_sheet + 1:03d}.png"
        sheet.save(path)
        written.append(str(path.relative_to(ROOT)).replace("\\", "/"))
    return written


def bbox_gap(a, b) -> float:
    dx = max(b[0] - a[2], a[0] - b[2], 0)
    dy = max(b[1] - a[3], a[1] - b[3], 0)
    return math.hypot(dx, dy)


def exact_clearance(a_mask: np.ndarray, b_mask: np.ndarray, a_bbox, b_bbox) -> float | None:
    if not a_mask.any() or not b_mask.any():
        return None
    ux0 = max(0, min(a_bbox[0], b_bbox[0]) - 2)
    uy0 = max(0, min(a_bbox[1], b_bbox[1]) - 2)
    ux1 = min(a_mask.shape[1], max(a_bbox[2], b_bbox[2]) + 2)
    uy1 = min(a_mask.shape[0], max(a_bbox[3], b_bbox[3]) + 2)
    aa = a_mask[uy0:uy1, ux0:ux1]
    bb = b_mask[uy0:uy1, ux0:ux1]
    if np.logical_and(aa, bb).any():
        return 0.0
    dist = distance_transform_edt(~aa)
    return float(dist[bb].min()) if bb.any() else None


def main() -> None:
    ROOT.mkdir(parents=True, exist_ok=True)
    full_path = ROOT / "full_page_300dpi.png"
    gray_full_path = ROOT / "full_page_grayscale_300dpi.png"
    full = Image.open(full_path).convert("RGB")
    gray_full = Image.open(gray_full_path).convert("L")
    crop_img = full.crop(CROP)
    crop_gray = gray_full.crop(CROP)
    crop_img.save(ROOT / "figure_crop_300dpi.png")
    shutil.copyfile(ROOT / "figure_crop_300dpi.png", ROOT / "standalone_300dpi.png")
    crop_gray.save(ROOT / "grayscale_300dpi.png")
    original = np.array(crop_img)
    h, w = original.shape[:2]

    doc = fitz.open(PDF)
    page = doc[PAGE_INDEX]
    sx = full.width / page.rect.width
    sy = full.height / page.rect.height
    page_meta = {
        "official_candidate": "R103",
        "physical_page": PHYSICAL_PAGE,
        "printed_page": 640,
        "figure_number": "32.5",
        "page_pt": [page.rect.width, page.rect.height],
        "full_page_native_300dpi_px": [full.width, full.height],
        "full_page_native_200dpi_px": list(Image.open(ROOT / "full_page_200dpi.png").size),
        "native_mapping_px_per_pt": [sx, sy],
        "figure_crop_integer_xyxy_on_full_300dpi": list(CROP),
        "figure_crop_native_px": [w, h],
        "pdf_identity": file_identity(PDF),
        "source_identity": file_identity(SOURCE),
        "locator_method": "817-page PDF own pdftotext form-feed page index and direct native render; no supplied page number used",
    }
    write_json(ROOT / "machine_candidate_identity.json", page_meta)

    raw = page.get_text("rawdict")
    trace = page.get_texttrace()
    drawings = page.get_drawings()
    write_json(ROOT / "machine_pdf_rawdict_page653.json", raw)
    write_json(ROOT / "machine_pdf_texttrace_page653.json", trace)
    write_json(ROOT / "machine_pdf_drawings_page653.json", drawings)

    # Map raw PDF characters in the figure body and caption to semantic parents.
    chars = []
    spaces = []
    serial = 0
    for bi, block in enumerate(raw.get("blocks", [])):
        for li, line in enumerate(block.get("lines", [])):
            for si, span in enumerate(line.get("spans", [])):
                for ci, ch in enumerate(span.get("chars", [])):
                    bbox_pt = tuple(ch["bbox"])
                    parent = object_parent_for_bbox(bbox_pt)
                    if parent is None:
                        continue
                    if ch["c"].isspace():
                        spaces.append({"block": bi, "line": li, "span": si, "char": ci, "c": ch["c"], "bbox_pt": bbox_pt, "exclusion": "WHITESPACE_HAS_NO_VISIBLE_FOREGROUND"})
                        continue
                    serial += 1
                    x0 = max(0, int(math.floor(bbox_pt[0] * sx)) - CROP[0])
                    y0 = max(0, int(math.floor(bbox_pt[1] * sy)) - CROP[1])
                    x1 = min(w, int(math.ceil(bbox_pt[2] * sx)) - CROP[0])
                    y1 = min(h, int(math.ceil(bbox_pt[3] * sy)) - CROP[1])
                    gid = f"G{serial:04d}"
                    cp = ord(ch["c"])
                    safe = f"{gid}_u{cp:04x}"
                    chars.append({
                        "glyph_id": gid,
                        "safe_filename": safe,
                        "char": ch["c"],
                        "codepoint": f"U+{cp:04X}",
                        "unicode_name": unicodedata.name(ch["c"], "UNNAMED"),
                        "parent_object_id": parent,
                        "block_index": bi,
                        "line_index": li,
                        "span_index": si,
                        "char_index": ci,
                        "font": span.get("font"),
                        "pdf_font_size_pt": float(span.get("size", 0.0)),
                        "pdf_color_rgb": color_int_to_rgb(int(span.get("color", 0))),
                        "origin_pt": ch.get("origin"),
                        "bbox_pt": bbox_pt,
                        "bbox_crop_px": [x0, y0, x1, y1],
                    })

    text_run_rows = []
    run_no = 0
    for bi, block in enumerate(raw.get("blocks", [])):
        for li, line in enumerate(block.get("lines", [])):
            for si, span in enumerate(line.get("spans", [])):
                bbox_pt = tuple(span.get("bbox", (0, 0, 0, 0)))
                if bbox_pt[3] < 345 or bbox_pt[1] >= 716:
                    continue
                run_no += 1
                parent = object_parent_for_bbox(bbox_pt)
                supported = [c["glyph_id"] for c in chars if c["block_index"] == bi and c["line_index"] == li and c["span_index"] == si]
                text_run_rows.append({
                    "text_run_id": f"R{run_no:03d}",
                    "block_index": bi,
                    "line_index": li,
                    "span_index": si,
                    "text": "".join(ch["c"] for ch in span.get("chars", [])),
                    "font": span.get("font"),
                    "pdf_font_size_pt": span.get("size"),
                    "bbox_pt": json.dumps(bbox_pt, ensure_ascii=False),
                    "parent_object_id": parent or "UNMAPPED",
                    "visible_nonspace_glyph_count": len(supported),
                    "glyph_ids": ";".join(supported),
                    "disposition": "MAPPED_FIGURE_FOREGROUND" if parent else "UNMAPPED_WITHIN_FIGURE_RANGE",
                })
    write_csv(ROOT / "machine_text_run_coverage.csv", text_run_rows)
    write_json(ROOT / "machine_text_run_coverage.json", text_run_rows)

    # Build a raw final-visible mask for each glyph from the native candidate raster.
    backgrounds = [(255, 255, 255), (246, 247, 248), (244, 246, 248)]
    glyph_masks: dict[str, np.ndarray] = {}
    glyph_contacts = []
    for ch in chars:
        x0, y0, x1, y1 = ch["bbox_crop_px"]
        mask = np.zeros((h, w), dtype=bool)
        if x1 > x0 and y1 > y0:
            reg = original[y0:y1, x0:x1]
            local = projected_color_mask(reg, tuple(ch["pdf_color_rgb"]), backgrounds)
            mask[y0:y1, x0:x1] = local
        glyph_masks[ch["glyph_id"]] = mask

    # Build visible vector masks from mapped PDF drawing primitives.
    draw_groups = [
        ("B01_CURRENT_NODE_BORDER", "NODE_BORDER", [2], (31, 78, 121), "current state rounded rectangle"),
        ("B02_CANDIDATE_NODE_BORDER", "NODE_BORDER", [3], (184, 192, 200), "candidate rounded rectangle"),
        ("B03_RATIO_NODE_BORDER", "NODE_BORDER", [4], (31, 78, 121), "acceptance ratio rounded rectangle"),
        ("B04_DECISION_NODE_BORDER", "NODE_BORDER", [6], (31, 78, 121), "decision diamond"),
        ("B05_ACCEPT_NODE_BORDER", "NODE_BORDER", [7], (31, 78, 121), "accept node rounded rectangle"),
        ("B06_REJECT_DOUBLE_BORDER", "NODE_BORDER", [8], (31, 78, 121), "reject node final-visible double blue border after white separator"),
        ("E01_PROPOSAL_ARROW", "LINE_ARROW", [10, 11], (107, 114, 128), "dashed proposal shaft plus arrowhead"),
        ("E02_CALCULATE_ARROW", "LINE_ARROW", [13, 14], (184, 192, 200), "calculation shaft plus arrowhead"),
        ("E03_DECISION_ARROW", "LINE_ARROW", [16, 17], (184, 192, 200), "decision shaft plus arrowhead"),
        ("E04_ACCEPT_ARROW", "LINE_ARROW", [19, 20], (31, 78, 121), "accept branch shaft plus arrowhead"),
        ("E05_REJECT_ARROW", "LINE_ARROW", [22, 23], (31, 78, 121), "reject branch patterned shaft plus arrowhead"),
        ("E06_REJECT_SELFLOOP", "SELF_LOOP_ARROW", [25, 26], (31, 78, 121), "reject self-loop curve plus arrowhead"),
        ("M01_RATIO_FRACTION_RULE", "MATH_RULE", [5], (31, 35, 40), "independent visible fraction rule in ratio formula"),
    ]
    drawing_masks: dict[str, np.ndarray] = {}
    drawing_rows = []
    for oid, cls, indices, target, description in draw_groups:
        rects_pt = [tuple(drawings[i]["rect"]) for i in indices]
        rp = rect_union(rects_pt)
        x0 = max(0, int(math.floor(rp[0] * sx)) - CROP[0] - 3)
        y0 = max(0, int(math.floor(rp[1] * sy)) - CROP[1] - 3)
        x1 = min(w, int(math.ceil(rp[2] * sx)) - CROP[0] + 3)
        y1 = min(h, int(math.ceil(rp[3] * sy)) - CROP[1] + 3)
        if y1 <= y0:
            y0 = max(0, y0 - 3)
            y1 = min(h, y1 + 6)
        if x1 <= x0:
            x0 = max(0, x0 - 3)
            x1 = min(w, x1 + 6)
        color_mask = np.zeros((h, w), dtype=bool)
        reg = original[y0:y1, x0:x1]
        color_mask[y0:y1, x0:x1] = projected_color_mask(reg, target, backgrounds)
        geometry = np.zeros((h, w), dtype=bool)
        for di in indices:
            fill_path = di in {11, 14, 17, 20, 23, 26}
            geometry |= drawing_geometry_mask(drawings[di], sx, sy, (w, h), fill_path=fill_path)
        mask = color_mask & geometry
        drawing_masks[oid] = mask
        drawing_rows.append({
            "object_id": oid,
            "class": cls,
            "drawing_indices": ";".join(str(i) for i in indices),
            "drawing_seqnos": ";".join(str(drawings[i].get("seqno")) for i in indices),
            "bbox_pt": json.dumps(rp),
            "target_rgb": json.dumps(target),
            "description": description,
        })

    # The fraction rule is a distinct same-color path; remove it from glyph masks to keep masks unique.
    frac = drawing_masks["M01_RATIO_FRACTION_RULE"]
    for ch in chars:
        if ch["parent_object_id"] == "T06_RATIO_FORMULA":
            glyph_masks[ch["glyph_id"]] &= ~frac

    # Machine glyph metrics and individual four-view contact evidence.
    glyph_rows = []
    for ch in chars:
        mask = glyph_masks[ch["glyph_id"]]
        x0, y0, x1, y1, pixels = save_small_mask(mask, ROOT / "masks" / "glyph" / f"{ch['safe_filename']}.png")
        cls, threshold = script_class(ch["char"], ch["pdf_font_size_pt"], ch["parent_object_id"])
        h_ink = y1 - y0 if pixels else 0
        w_ink = x1 - x0 if pixels else 0
        contact = ROOT / "glyph_contacts" / f"{ch['safe_filename']}_contact.png"
        make_contact(original, mask, (x0, y0, x1, y1), f"{ch['glyph_id']} {ch['codepoint']} {ch['char']} parent={ch['parent_object_id']}", contact)
        glyph_contacts.append(contact)
        glyph_rows.append({
            **ch,
            "bbox_pt": json.dumps(ch["bbox_pt"], ensure_ascii=False),
            "origin_pt": json.dumps(ch["origin_pt"], ensure_ascii=False),
            "bbox_crop_px": json.dumps(ch["bbox_crop_px"]),
            "raw_mask_bbox_crop_px": json.dumps([x0, y0, x1, y1]),
            "raw_mask_pixel_count": pixels,
            "h_ink_px": h_ink,
            "w_ink_px": w_ink,
            "script_class": cls,
            "strict_reference_threshold_px": threshold,
            "mask_path": str((ROOT / "masks" / "glyph" / f"{ch['safe_filename']}.png").relative_to(ROOT)).replace("\\", "/"),
            "contact_path": str(contact.relative_to(ROOT)).replace("\\", "/"),
        })
    write_csv(ROOT / "machine_glyph_inventory.csv", glyph_rows)
    write_json(ROOT / "machine_glyph_inventory.json", glyph_rows)
    write_json(ROOT / "machine_pdf_whitespace_exclusions.json", spaces)
    glyph_sheets = make_master_sheets(glyph_contacts, ROOT / "glyph_contact_sheets", "glyph_sheet", per_sheet=8)

    # Assemble semantic text/formula objects from their unique glyph masks.
    text_specs = [
        ("T01_CURRENT_NODE_TITLE", "TEXT", "current-state title line"),
        ("T02_CURRENT_NODE_VARIABLE", "TEXT_FORMULA", "current-state variable line"),
        ("T03_CANDIDATE_NODE_ACTION", "TEXT", "candidate-draw action line"),
        ("T04_CANDIDATE_NODE_VARIABLE", "TEXT_FORMULA", "candidate variable line"),
        ("T05_RATIO_HEADER", "TEXT", "acceptance-ratio explanatory header"),
        ("T06_RATIO_FORMULA", "FORMULA", "acceptance-ratio core formula excluding independent fraction rule"),
        ("T07_DECISION_DRAW", "TEXT_FORMULA", "uniform-variable draw line"),
        ("T08_DECISION_COMPARE", "FORMULA", "acceptance comparison line"),
        ("T09_ACCEPT_NODE_ACTION", "TEXT", "accept action line"),
        ("T10_ACCEPT_NODE_ASSIGNMENT", "FORMULA", "accepted next-state assignment line"),
        ("T11_REJECT_NODE_ACTION", "TEXT", "reject-and-record action line"),
        ("T12_REJECT_NODE_ASSIGNMENT", "TEXT_FORMULA", "rejected next-state assignment line"),
        ("T13_PROPOSAL_LABEL", "EDGE_LABEL", "proposal edge label"),
        ("T14_CALCULATE_LABEL", "EDGE_LABEL", "calculation edge label"),
        ("T15_DECISION_LABEL", "EDGE_LABEL", "decision edge label"),
        ("T16_ACCEPT_LABEL", "EDGE_LABEL", "accept branch edge label"),
        ("T17_REJECT_LABEL", "EDGE_LABEL", "reject branch edge label"),
        ("T18_SELFLOOP_LABEL", "SELF_LOOP_LABEL", "reject self-loop label"),
        ("T19_CAPTION_LABEL", "CAPTION_LABEL", "figure-number label"),
        ("T20_CAPTION_TEXT", "CAPTION", "caption sentence"),
    ]
    object_masks: dict[str, np.ndarray] = {}
    object_rows = []
    object_contacts = []
    for oid, cls, description in text_specs:
        members = [g for g in glyph_rows if g["parent_object_id"] == oid]
        mask = np.zeros((h, w), dtype=bool)
        for g in members:
            mask |= glyph_masks[g["glyph_id"]]
        object_masks[oid] = mask
        bx0, by0, bx1, by1, pixels = save_small_mask(mask, ROOT / "masks" / "object" / f"{oid}.png")
        contact = ROOT / "object_contacts" / f"{oid}_contact.png"
        make_contact(original, mask, (bx0, by0, bx1, by1), f"{oid} {cls}", contact)
        object_contacts.append(contact)
        object_rows.append({
            "object_id": oid,
            "class": cls,
            "semantic_parent": oid,
            "support_kind": "PDF_TEXT_GLYPHS",
            "support_ids": ";".join(g["glyph_id"] for g in members),
            "support_count": len(members),
            "description": description,
            "raw_mask_bbox_crop_px": json.dumps([bx0, by0, bx1, by1]),
            "raw_mask_pixel_count": pixels,
            "mask_path": f"masks/object/{oid}.png",
            "contact_path": str(contact.relative_to(ROOT)).replace("\\", "/"),
        })

    for oid, cls, indices, target, description in draw_groups:
        mask = drawing_masks[oid]
        object_masks[oid] = mask
        bx0, by0, bx1, by1, pixels = save_small_mask(mask, ROOT / "masks" / "object" / f"{oid}.png")
        contact = ROOT / "object_contacts" / f"{oid}_contact.png"
        make_contact(original, mask, (bx0, by0, bx1, by1), f"{oid} {cls}", contact)
        object_contacts.append(contact)
        object_rows.append({
            "object_id": oid,
            "class": cls,
            "semantic_parent": "T06_RATIO_FORMULA" if cls == "MATH_RULE" else oid,
            "support_kind": "PDF_DRAWING_PRIMITIVES",
            "support_ids": ";".join(f"drawing[{i}]/seq{drawings[i].get('seqno')}" for i in indices),
            "support_count": len(indices),
            "description": description,
            "raw_mask_bbox_crop_px": json.dumps([bx0, by0, bx1, by1]),
            "raw_mask_pixel_count": pixels,
            "mask_path": f"masks/object/{oid}.png",
            "contact_path": str(contact.relative_to(ROOT)).replace("\\", "/"),
        })

    # Canonical object order and full denominator.
    order = [x[0] for x in text_specs] + [
        "B01_CURRENT_NODE_BORDER", "B02_CANDIDATE_NODE_BORDER", "B03_RATIO_NODE_BORDER",
        "B04_DECISION_NODE_BORDER", "B05_ACCEPT_NODE_BORDER", "B06_REJECT_DOUBLE_BORDER",
        "E01_PROPOSAL_ARROW", "E02_CALCULATE_ARROW", "E03_DECISION_ARROW",
        "E04_ACCEPT_ARROW", "E05_REJECT_ARROW", "E06_REJECT_SELFLOOP", "M01_RATIO_FRACTION_RULE",
    ]
    object_rows.sort(key=lambda r: order.index(r["object_id"]))
    object_sheets = make_master_sheets(object_contacts, ROOT / "object_contact_sheets", "object_sheet", per_sheet=4)
    write_csv(ROOT / "machine_object_inventory.csv", object_rows)
    write_json(ROOT / "machine_object_inventory.json", object_rows)

    # Draw object bounding boxes and IDs on the native crop without resizing it.
    overlay = crop_img.copy()
    od = ImageDraw.Draw(overlay)
    palette = {"TEXT": "#ef4444", "TEXT_FORMULA": "#ef4444", "FORMULA": "#d946ef", "EDGE_LABEL": "#f97316", "SELF_LOOP_LABEL": "#f97316", "CAPTION": "#7c3aed", "NODE_BORDER": "#22c55e", "LINE_ARROW": "#06b6d4", "SELF_LOOP_ARROW": "#06b6d4", "MATH_RULE": "#eab308"}
    for row in object_rows:
        x0, y0, x1, y1 = json.loads(row["raw_mask_bbox_crop_px"])
        color = palette.get(row["class"], "red")
        od.rectangle((x0, y0, max(x0, x1 - 1), max(y0, y1 - 1)), outline=color, width=2)
        od.text((x0 + 2, max(0, y0 - 12)), row["object_id"], fill=color)
    overlay.save(ROOT / "after_text_measurement_overlay_300dpi.png")

    # Every unordered object pair, with exact native-pixel metrics for near/intersecting pairs
    # and a conservative foreground-bbox lower bound for distant pairs.
    pair_rows = []
    critical_contacts = []
    object_by_id = {r["object_id"]: r for r in object_rows}
    pair_no = 0
    for a_id, b_id in itertools.combinations(order, 2):
        pair_no += 1
        pair_id = f"P{pair_no:04d}"
        a = object_by_id[a_id]
        b = object_by_id[b_id]
        abox = json.loads(a["raw_mask_bbox_crop_px"])
        bbox = json.loads(b["raw_mask_bbox_crop_px"])
        inter = int(np.logical_and(object_masks[a_id], object_masks[b_id]).sum())
        lower = bbox_gap(abox, bbox)
        exact = lower <= 24 or inter > 0
        clearance = exact_clearance(object_masks[a_id], object_masks[b_id], abox, bbox) if exact else None
        critical = bool(inter > 0 or lower <= 12)
        roi_dir_rel = ""
        if critical:
            ux0 = max(0, min(abox[0], bbox[0]) - 12)
            uy0 = max(0, min(abox[1], bbox[1]) - 12)
            ux1 = min(w, max(abox[2], bbox[2]) + 12)
            uy1 = min(h, max(abox[3], bbox[3]) + 12)
            roi_dir = ROOT / "critical_pairs" / pair_id
            roi_dir.mkdir(parents=True, exist_ok=True)
            roi = original[uy0:uy1, ux0:ux1]
            am = object_masks[a_id][uy0:uy1, ux0:ux1]
            bm = object_masks[b_id][uy0:uy1, ux0:ux1]
            im = np.logical_and(am, bm)
            ov = roi.copy()
            ov[am] = (255, 0, 0)
            ov[bm] = (0, 180, 255)
            ov[im] = (255, 0, 255)
            Image.fromarray(roi).save(roi_dir / "original_1x.png")
            Image.fromarray((am * 255).astype(np.uint8), mode="L").save(roi_dir / "mask_A_1x.png")
            Image.fromarray((bm * 255).astype(np.uint8), mode="L").save(roi_dir / "mask_B_1x.png")
            Image.fromarray((im * 255).astype(np.uint8), mode="L").save(roi_dir / "intersection_1x.png")
            Image.fromarray(ov).save(roi_dir / "overlay_1x.png")
            Image.fromarray(ov).resize((ov.shape[1] * 8, ov.shape[0] * 8), Image.Resampling.NEAREST).save(roi_dir / "overlay_8x_nearest.png")
            roi_dir_rel = str(roi_dir.relative_to(ROOT)).replace("\\", "/")
            critical_contacts.append(roi_dir / "overlay_8x_nearest.png")
        pair_rows.append({
            "pair_id": pair_id,
            "object_a": a_id,
            "class_a": a["class"],
            "object_b": b_id,
            "class_b": b["class"],
            "intersection_raw_px": inter,
            "foreground_bbox_clearance_lower_bound_px": round(lower, 6),
            "clearance_exact_computed": exact,
            "exact_raw_foreground_clearance_px": "" if clearance is None else round(clearance, 6),
            "critical_machine_flag": critical,
            "critical_roi_dir": roi_dir_rel,
        })
    write_csv(ROOT / "machine_unordered_pairs.csv", pair_rows)
    write_json(ROOT / "machine_unordered_pairs.json", pair_rows)

    # Per-object crop-edge / clip-support metrics.
    clip_rows = []
    for row in object_rows:
        x0, y0, x1, y1 = json.loads(row["raw_mask_bbox_crop_px"])
        edge = min(x0, y0, w - x1, h - y1)
        clip_rows.append({
            "object_id": row["object_id"],
            "class": row["class"],
            "raw_mask_pixel_count": row["raw_mask_pixel_count"],
            "min_raw_mask_to_crop_edge_px": edge,
            "boundary_touch_pixel_count": int(
                object_masks[row["object_id"]][0, :].sum()
                + object_masks[row["object_id"]][-1, :].sum()
                + object_masks[row["object_id"]][:, 0].sum()
                + object_masks[row["object_id"]][:, -1].sum()
            ),
        })
    write_csv(ROOT / "machine_clip_metrics.csv", clip_rows)

    # Primitive support / exclusion accounting for all 28 page drawing records.
    mapped_drawings = {i for _, _, ids, _, _ in draw_groups for i in ids}
    background_drawings = {9, 12, 15, 18, 21, 24, 27}
    drawing_coverage = []
    for i, d in enumerate(drawings):
        if i in mapped_drawings:
            mapped = [oid for oid, _, ids, _, _ in draw_groups if i in ids][0]
            disposition = "MAPPED_FOREGROUND_OBJECT"
            support = mapped
        elif i in background_drawings:
            disposition = "EXCLUDED_OPAQUE_BACKGROUND_OR_WHITE_SEPARATOR"
            support = "final-visible occlusion support; not foreground"
        else:
            disposition = "EXCLUDED_OUTSIDE_FIGURE_CROP"
            support = "page header/equation primitive outside figure"
        drawing_coverage.append({
            "drawing_index": i,
            "seqno": d.get("seqno"),
            "rect_pt": json.dumps(list(d["rect"])),
            "type": d.get("type"),
            "disposition": disposition,
            "support_or_exclusion": support,
        })
    write_csv(ROOT / "machine_drawing_coverage.csv", drawing_coverage)

    recordset = {
        "candidate": page_meta,
        "object_count": len(object_rows),
        "unordered_pair_expected": len(object_rows) * (len(object_rows) - 1) // 2,
        "unordered_pair_actual": len(pair_rows),
        "glyph_count_visible_nonspace": len(glyph_rows),
        "pdf_whitespace_excluded_count": len(spaces),
        "pdf_page_drawing_count": len(drawings),
        "mapped_foreground_drawing_count": len(mapped_drawings),
        "background_occlusion_drawing_count": len(background_drawings),
        "out_of_figure_drawing_count": len(drawings) - len(mapped_drawings) - len(background_drawings),
        "critical_pair_count": sum(1 for r in pair_rows if r["critical_machine_flag"]),
        "empty_object_mask_count": sum(1 for r in object_rows if int(r["raw_mask_pixel_count"]) == 0),
        "empty_glyph_mask_count": sum(1 for r in glyph_rows if int(r["raw_mask_pixel_count"]) == 0),
        "glyph_contact_count": len(glyph_contacts),
        "glyph_contact_sheets": glyph_sheets,
        "object_contact_count": len(object_contacts),
        "object_contact_sheets": object_sheets,
        "views": {
            "full_page_200dpi": "full_page_200dpi.png",
            "figure_crop_300dpi": "figure_crop_300dpi.png",
            "standalone_300dpi": "standalone_300dpi.png",
            "grayscale_300dpi": "grayscale_300dpi.png",
        },
    }
    write_json(ROOT / "machine_recordset_summary.json", recordset)


if __name__ == "__main__":
    main()
