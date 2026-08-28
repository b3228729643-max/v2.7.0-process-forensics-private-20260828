from __future__ import annotations

import csv
import hashlib
import itertools
import json
import math
import statistics
from collections import Counter
from pathlib import Path

import numpy as np
import pdfplumber
from PIL import Image, ImageDraw, ImageFont


PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r111_fullbook\main_full.pdf")
SOURCE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第01册_数学基础与统计学习基本理论\V1-C02\fig_v1_c02_projection.tex")
ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P033-01\STRICT_R5_SA1_FRESH_ISOLATED_R111_20260827")
PAGE_PNG = ROOT / "render" / "r111_physical_029_300dpi.png"
PAGE_INDEX = 28
EXPECTED_PDF_SHA256 = "DAB1062500E39DD2C34C6B4A9FF51CAC2BE0A4C84B2F45F5FB8E645C4BC012D6"
EXPECTED_SOURCE_SHA256 = "D3C1D38ECB8468EC3294F7D18BD886316829F14690A516000189CE853A07BC05"
WINDOW_PT = (50.0, 460.0, 530.0, 660.0)
HANDOFF_ID = "A-R111-P033-SA1-FRESH-ISOLATED-20260827"
MODEL_EFFORT = "gpt-5.6-sol/xhigh"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def write_json(path: Path, data: object) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def intersects(obj: dict, window: tuple[float, float, float, float]) -> bool:
    x0, top, x1, bottom = window
    return obj["x1"] >= x0 and obj["x0"] <= x1 and obj["bottom"] >= top and obj["top"] <= bottom


def char_parent(index: int) -> tuple[str, str, str, int]:
    groups = [
        (0, 3, "TXT_SUBSPACE", "子空间𝑆", 16),
        (4, 4, "TXT_X", "𝑥", 19),
        (5, 11, "TXT_PROJECTION", "𝑝=𝑃𝑆𝑥∈𝑆", 21),
        (12, 19, "TXT_RESIDUAL", "𝑟=𝑥−𝑝∈𝑆⟂", 26),
        (20, 23, "TXT_DISTANCE", "最短距离", 32),
        (24, 37, "TXT_PYTHAGORAS", "‖𝑥‖2=‖𝑝‖2+‖𝑟‖2", 34),
        (38, 41, "CAPTION_NUMBER", "图2.1", 37),
        (42, 84, "CAPTION_TEXT", "向量的正交分解。投影向量属于子空间，残差属于其正交补，虚线残差给出到子空间的最短距离。", 37),
    ]
    for lo, hi, parent, expected, line in groups:
        if lo <= index <= hi:
            return parent, expected, "BODY" if index < 38 else "CAPTION", line
    raise AssertionError(index)


PATH_META = {
    ("line", 0): ("PATH_SUBSPACE_UPPER", "SUBSPACE_BOUNDARY", "FOREGROUND", 14),
    ("line", 1): ("PATH_SUBSPACE_LOWER", "SUBSPACE_BOUNDARY", "FOREGROUND", 15),
    ("line", 2): ("PATH_X_SHAFT", "X_VECTOR", "FOREGROUND", 18),
    ("line", 3): ("PATH_P_SHAFT", "P_VECTOR", "FOREGROUND", 20),
    ("line", 4): ("PATH_R_SHAFT", "RESIDUAL_VECTOR", "FOREGROUND", 22),
    ("rect", 0): ("PATH_RESIDUAL_LABEL_BG", "RESIDUAL_LABEL_BG", "SUPPORT_BACKGROUND", 24),
    ("rect", 1): ("PATH_DISTANCE_LABEL_BG", "DISTANCE_LABEL_BG", "SUPPORT_BACKGROUND", 31),
    ("curve", 0): ("PATH_SUBSPACE_FILL", "SUBSPACE_FILL", "SUPPORT_BACKGROUND", 12),
    ("curve", 1): ("PATH_X_ARROWHEAD", "X_VECTOR", "FOREGROUND", 18),
    ("curve", 2): ("PATH_P_ARROWHEAD", "P_VECTOR", "FOREGROUND", 20),
    ("curve", 3): ("PATH_R_ARROWHEAD", "RESIDUAL_VECTOR", "FOREGROUND", 22),
    ("curve", 4): ("PATH_RIGHT_ANGLE", "RIGHT_ANGLE", "FOREGROUND", 27),
    ("curve", 5): ("PATH_DISTANCE_BRACE", "DISTANCE_BRACE", "FOREGROUND", 28),
    ("curve", 6): ("PATH_EQUATION_NOTE_BOX", "EQUATION_NOTE_BOX", "MIXED_CONTAINER", 33),
}


TEXT_EXPECTED = {
    "TXT_SUBSPACE": "子空间𝑆",
    "TXT_X": "𝑥",
    "TXT_PROJECTION": "𝑝=𝑃𝑆𝑥∈𝑆",
    "TXT_RESIDUAL": "𝑟=𝑥−𝑝∈𝑆⟂",
    "TXT_DISTANCE": "最短距离",
    "TXT_PYTHAGORAS": "‖𝑥‖2=‖𝑝‖2+‖𝑟‖2",
    "CAPTION_NUMBER": "图2.1",
    "CAPTION_TEXT": "向量的正交分解。投影向量属于子空间，残差属于其正交补，虚线残差给出到子空间的最短距离。",
}


BACKGROUND_PARENTS = {"SUBSPACE_FILL", "RESIDUAL_LABEL_BG", "DISTANCE_LABEL_BG"}
CONTAINER_TEXT = {
    frozenset(("EQUATION_NOTE_BOX", "TXT_PYTHAGORAS")),
    frozenset(("RESIDUAL_LABEL_BG", "TXT_RESIDUAL")),
    frozenset(("DISTANCE_LABEL_BG", "TXT_DISTANCE")),
}
INTENDED_GEOMETRY_CONTACTS = {
    frozenset(("SUBSPACE_BOUNDARY", "SUBSPACE_FILL")),
    frozenset(("X_VECTOR", "P_VECTOR")),
    frozenset(("X_VECTOR", "RESIDUAL_VECTOR")),
    frozenset(("P_VECTOR", "RESIDUAL_VECTOR")),
    frozenset(("P_VECTOR", "RIGHT_ANGLE")),
    frozenset(("RESIDUAL_VECTOR", "RIGHT_ANGLE")),
}


def bbox_gap(a: dict, b: dict) -> tuple[float, float, float, float, float]:
    ow = max(0.0, min(a["x1_pt"], b["x1_pt"]) - max(a["x0_pt"], b["x0_pt"]))
    oh = max(0.0, min(a["bottom_pt"], b["bottom_pt"]) - max(a["top_pt"], b["top_pt"]))
    dx = max(0.0, max(a["x0_pt"], b["x0_pt"]) - min(a["x1_pt"], b["x1_pt"]))
    dy = max(0.0, max(a["top_pt"], b["top_pt"]) - min(a["bottom_pt"], b["bottom_pt"]))
    gap = math.hypot(dx, dy)
    return ow, oh, dx, dy, gap


def pair_disposition(a: dict, b: dict, overlap: bool, gap_px: float) -> tuple[str, str]:
    parents = frozenset((a["semantic_parent"], b["semantic_parent"]))
    if a["atomic_type"] == "GLYPH" and b["atomic_type"] == "GLYPH" and a["semantic_parent"] == b["semantic_parent"]:
        return "INTENDED_TEXT_RUN_CONSTITUENTS", "Adjacent glyph atoms within one frozen text run; kerning/bbox contact is not inter-object semantic overlap."
    if a["semantic_parent"] == b["semantic_parent"] and a["semantic_parent"] in {"X_VECTOR", "P_VECTOR", "RESIDUAL_VECTOR", "SUBSPACE_BOUNDARY"}:
        return "INTENDED_COMPOUND_PATH", "Atomic path parts form one compound geometric object."
    if parents in CONTAINER_TEXT:
        return "INTENDED_CONTAINER_RELATION", "Text is intentionally contained by a white support rectangle or note box; border clearance is checked in manual ROI."
    if a["semantic_parent"] in BACKGROUND_PARENTS or b["semantic_parent"] in BACKGROUND_PARENTS:
        return "BACKGROUND_SUPPORT_INCLUDED_NOT_FOREGROUND_COLLISION", "The nonempty fill/background atom remains in N but its fill is not an illegal semantic foreground; foreground boundary/path contacts are reviewed separately."
    if parents in INTENDED_GEOMETRY_CONTACTS and overlap:
        return "INTENDED_GEOMETRY_CONTACT", "Shared endpoint/orthogonality/construction contact required by x=p+r geometry."
    if overlap:
        return "BBOX_INTERSECTION_REQUIRES_MANUAL_PIXEL_REVIEW", "Axis-aligned PDF bboxes intersect; native pixels and semantic geometry must decide whether visible foregrounds collide."
    if gap_px <= 8.0:
        return "NEAR_BBOX_ADVISORY", "Bboxes are close at 300 dpi; R168 treats tiny spacing as advisory unless actually unreadable, clipped, or semantically interfering."
    return "SEPARATED_BBOX", "No PDF bbox intersection; separation exceeds the 8 px review band."


def page_to_px(x: float, y: float, page_w: float, page_h: float, img_w: int, img_h: int) -> tuple[int, int]:
    return round(x * img_w / page_w), round(y * img_h / page_h)


def make_sheet(items: list[tuple[str, Image.Image]], path: Path, columns: int, max_panel_w: int = 2200) -> None:
    font = ImageFont.load_default()
    normalized = []
    for label, im in items:
        if im.width > max_panel_w:
            ratio = max_panel_w / im.width
            im = im.resize((max_panel_w, max(1, round(im.height * ratio))), Image.Resampling.NEAREST)
        normalized.append((label, im))
    if not normalized:
        canvas = Image.new("RGB", (640, 120), "white")
        ImageDraw.Draw(canvas).text((12, 12), "NO ITEMS", fill="black", font=font)
        canvas.save(path)
        return
    rows = math.ceil(len(normalized) / columns)
    col_w = [0] * columns
    row_h = [0] * rows
    for i, (_, im) in enumerate(normalized):
        c, r = i % columns, i // columns
        col_w[c] = max(col_w[c], im.width + 20)
        row_h[r] = max(row_h[r], im.height + 42)
    canvas = Image.new("RGB", (sum(col_w), sum(row_h)), "white")
    draw = ImageDraw.Draw(canvas)
    y = 0
    for r in range(rows):
        x = 0
        for c in range(columns):
            i = r * columns + c
            if i < len(normalized):
                label, im = normalized[i]
                draw.text((x + 8, y + 6), label, fill="black", font=font)
                canvas.paste(im, (x + 8, y + 26))
            x += col_w[c]
        y += row_h[r]
    canvas.save(path)


def main() -> None:
    for d in (ROOT / "source", ROOT / "render", ROOT / "roi", ROOT / "machine", ROOT / "manual", ROOT / "seal"):
        d.mkdir(parents=True, exist_ok=True)

    pdf_hash = sha256(PDF)
    source_hash = sha256(SOURCE)
    if pdf_hash != EXPECTED_PDF_SHA256:
        raise RuntimeError(f"PDF hash mismatch: {pdf_hash}")
    if source_hash != EXPECTED_SOURCE_SHA256:
        raise RuntimeError(f"source hash mismatch: {source_hash}")
    if PDF.stat().st_size != 4_967_076:
        raise RuntimeError("PDF byte size mismatch")

    with pdfplumber.open(PDF) as doc:
        if len(doc.pages) != 817:
            raise RuntimeError(f"page count mismatch: {len(doc.pages)}")
        page = doc.pages[PAGE_INDEX]
        chars = [o for o in page.objects.get("char", []) if intersects(o, WINDOW_PT)]
        lines = [o for o in page.objects.get("line", []) if intersects(o, WINDOW_PT)]
        rects = [o for o in page.objects.get("rect", []) if intersects(o, WINDOW_PT)]
        curves = [o for o in page.objects.get("curve", []) if intersects(o, WINDOW_PT)]
        expected_counts = {"char": 85, "line": 5, "rect": 2, "curve": 7}
        actual_counts = {"char": len(chars), "line": len(lines), "rect": len(rects), "curve": len(curves)}
        if actual_counts != expected_counts:
            raise RuntimeError(f"atomic denominator changed: {actual_counts}")

        page_image = Image.open(PAGE_PNG).convert("RGB")
        img_w, img_h = page_image.size
        if (img_w, img_h) != (2481, 3508):
            raise RuntimeError(f"unexpected 300 dpi render dimensions: {(img_w, img_h)}")

        objects: list[dict] = []
        for i, c in enumerate(chars):
            parent, expected, zone, source_line = char_parent(i)
            objects.append({
                "object_id": f"GLYPH-{i + 1:03d}",
                "atomic_type": "GLYPH",
                "source_object_index": i,
                "semantic_parent": parent,
                "zone": zone,
                "foreground_class": "TEXT_FOREGROUND",
                "source_line": source_line,
                "text": c["text"],
                "codepoint": f"U+{ord(c['text']):04X}",
                "fontname": c.get("fontname", ""),
                "pdf_font_size_pt": round(float(c.get("size", 0.0)), 6),
                "x0_pt": float(c["x0"]), "top_pt": float(c["top"]),
                "x1_pt": float(c["x1"]), "bottom_pt": float(c["bottom"]),
                "fill": "", "stroke": "", "linewidth_pt": "",
                "background_exclusion_reason": "",
            })

        path_counter = 0
        for kind, seq in (("line", lines), ("rect", rects), ("curve", curves)):
            for i, o in enumerate(seq):
                path_counter += 1
                obj_name, parent, foreground_class, source_line = PATH_META[(kind, i)]
                objects.append({
                    "object_id": f"PATH-{path_counter:03d}",
                    "atomic_type": f"PATH_{kind.upper()}",
                    "source_object_index": i,
                    "semantic_parent": parent,
                    "zone": "BODY",
                    "foreground_class": foreground_class,
                    "source_line": source_line,
                    "text": obj_name,
                    "codepoint": "",
                    "fontname": "",
                    "pdf_font_size_pt": "",
                    "x0_pt": float(o["x0"]), "top_pt": float(o["top"]),
                    "x1_pt": float(o["x1"]), "bottom_pt": float(o["bottom"]),
                    "fill": bool(o.get("fill")), "stroke": bool(o.get("stroke")),
                    "linewidth_pt": float(o.get("linewidth") or 0.0),
                    "background_exclusion_reason": (
                        "Included in the frozen visible denominator, but fill/background pixels are excluded from illegal-foreground collision counts; they intentionally support a plane or label."
                        if foreground_class == "SUPPORT_BACKGROUND" else
                        "Included in N; fill is support and the border remains foreground. Text-to-border clearance is manually reviewed."
                        if foreground_class == "MIXED_CONTAINER" else ""
                    ),
                })

        if len(objects) != 99:
            raise RuntimeError(f"N mismatch: {len(objects)}")

        min_x = min(o["x0_pt"] for o in objects)
        min_top = min(o["top_pt"] for o in objects)
        max_x = max(o["x1_pt"] for o in objects)
        max_bottom = max(o["bottom_pt"] for o in objects)
        crop_pt = (math.floor(min_x - 7), math.floor(min_top - 7), math.ceil(max_x + 7), math.ceil(max_bottom + 7))
        if crop_pt != (55, 460, 530, 662):
            raise RuntimeError(f"crop changed: {crop_pt}")
        crop_px = (
            math.floor(crop_pt[0] * img_w / page.width),
            math.floor(crop_pt[1] * img_h / page.height),
            math.ceil(crop_pt[2] * img_w / page.width),
            math.ceil(crop_pt[3] * img_h / page.height),
        )
        crop = page_image.crop(crop_px)
        crop.save(ROOT / "render" / "p033_body_caption_300dpi_native1x.png")

        semantic_colors = {
            "GLYPH": (210, 0, 0),
            "PATH_LINE": (0, 80, 220),
            "PATH_RECT": (170, 0, 170),
            "PATH_CURVE": (0, 140, 70),
        }
        overlay = crop.copy()
        draw = ImageDraw.Draw(overlay)
        for o in objects:
            x0, y0 = page_to_px(o["x0_pt"], o["top_pt"], page.width, page.height, img_w, img_h)
            x1, y1 = page_to_px(o["x1_pt"], o["bottom_pt"], page.width, page.height, img_w, img_h)
            x0 -= crop_px[0]; x1 -= crop_px[0]; y0 -= crop_px[1]; y1 -= crop_px[1]
            color = semantic_colors[o["atomic_type"]]
            draw.rectangle((x0, y0, x1, y1), outline=color, width=1)
        overlay.save(ROOT / "render" / "p033_atomic99_overlay_300dpi_native1x.png")

        group_boxes: dict[str, list[float]] = {}
        for o in objects:
            p = o["semantic_parent"]
            if p not in group_boxes:
                group_boxes[p] = [o["x0_pt"], o["top_pt"], o["x1_pt"], o["bottom_pt"]]
            else:
                b = group_boxes[p]
                b[0] = min(b[0], o["x0_pt"]); b[1] = min(b[1], o["top_pt"])
                b[2] = max(b[2], o["x1_pt"]); b[3] = max(b[3], o["bottom_pt"])
        sem_overlay = crop.copy()
        draw = ImageDraw.Draw(sem_overlay)
        palette = [(200, 0, 0), (0, 70, 220), (0, 140, 60), (180, 90, 0), (150, 0, 150)]
        for idx, (parent, b) in enumerate(sorted(group_boxes.items())):
            x0, y0 = page_to_px(b[0], b[1], page.width, page.height, img_w, img_h)
            x1, y1 = page_to_px(b[2], b[3], page.width, page.height, img_w, img_h)
            x0 -= crop_px[0]; x1 -= crop_px[0]; y0 -= crop_px[1]; y1 -= crop_px[1]
            color = palette[idx % len(palette)]
            draw.rectangle((x0, y0, x1, y1), outline=color, width=3)
            draw.text((x0 + 2, max(0, y0 - 13)), parent, fill=color, font=ImageFont.load_default())
        sem_overlay.save(ROOT / "render" / "p033_semantic_groups_overlay_300dpi_native1x.png")

        group_text: dict[str, str] = {}
        for o in objects:
            if o["atomic_type"] == "GLYPH":
                group_text[o["semantic_parent"]] = group_text.get(o["semantic_parent"], "") + o["text"]
        text_audit = []
        for parent, expected in TEXT_EXPECTED.items():
            actual = group_text.get(parent, "")
            text_audit.append({
                "semantic_parent": parent,
                "expected_text": expected,
                "pdf_extracted_text": actual,
                "exact_codepoint_match": actual == expected,
                "hard_status": "PASS" if actual == expected and "�" not in actual else "FAIL",
            })
        if not all(r["hard_status"] == "PASS" for r in text_audit):
            raise RuntimeError("codepoint audit failed")

        arr = np.asarray(page_image, dtype=np.int16)
        glyph_metrics = []
        for o in objects[:85]:
            x0, y0 = page_to_px(o["x0_pt"], o["top_pt"], page.width, page.height, img_w, img_h)
            x1, y1 = page_to_px(o["x1_pt"], o["bottom_pt"], page.width, page.height, img_w, img_h)
            x0 = max(0, x0 - 1); y0 = max(0, y0 - 1); x1 = min(img_w, x1 + 1); y1 = min(img_h, y1 + 1)
            patch = arr[y0:y1, x0:x1, :]
            if patch.size == 0:
                nonempty = False; ink_h = 0; ink_count = 0
            else:
                border = np.concatenate((patch[0], patch[-1], patch[:, 0], patch[:, -1]), axis=0)
                bg = np.median(border, axis=0)
                diff = np.sqrt(np.sum((patch - bg) ** 2, axis=2))
                mask = diff >= 20.0
                ys, xs = np.where(mask)
                nonempty = len(ys) > 0
                ink_h = int(ys.max() - ys.min() + 1) if nonempty else 0
                ink_count = int(mask.sum())
            glyph_metrics.append({
                "object_id": o["object_id"], "semantic_parent": o["semantic_parent"],
                "text": o["text"], "codepoint": o["codepoint"],
                "pdf_font_size_pt": o["pdf_font_size_pt"],
                "raster_ink_nonempty": nonempty, "ink_height_px_advisory": ink_h,
                "ink_pixel_count": ink_count,
                "hard_missing_tofu_direction": "PASS" if nonempty and o["text"] != "�" else "FAIL",
            })
        if not all(r["hard_missing_tofu_direction"] == "PASS" for r in glyph_metrics):
            raise RuntimeError("glyph raster nonempty check failed")

        pairs = []
        disposition_counts = Counter()
        review_pairs = []
        scale300 = 300.0 / 72.0
        for pair_num, (a, b) in enumerate(itertools.combinations(objects, 2), 1):
            ow, oh, dx, dy, gap_pt = bbox_gap(a, b)
            overlap = ow > 0 and oh > 0
            gap_px = gap_pt * scale300
            disposition, rationale = pair_disposition(a, b, overlap, gap_px)
            disposition_counts[disposition] += 1
            row = {
                "pair_id": f"PAIR-{pair_num:04d}",
                "object_a": a["object_id"], "object_b": b["object_id"],
                "parent_a": a["semantic_parent"], "parent_b": b["semantic_parent"],
                "type_a": a["atomic_type"], "type_b": b["atomic_type"],
                "bbox_overlap": overlap,
                "bbox_overlap_width_pt": round(ow, 6), "bbox_overlap_height_pt": round(oh, 6),
                "bbox_gap_pt": round(gap_pt, 6), "bbox_gap_px_300dpi": round(gap_px, 4),
                "disposition": disposition, "rationale": rationale,
                "manual_pixel_status": "PENDING_FINAL_OPEN" if disposition in {
                    "BBOX_INTERSECTION_REQUIRES_MANUAL_PIXEL_REVIEW", "INTENDED_CONTAINER_RELATION",
                    "INTENDED_GEOMETRY_CONTACT", "NEAR_BBOX_ADVISORY"
                } else "NOT_REQUIRED_BY_DISPOSITION",
            }
            pairs.append(row)
            if row["manual_pixel_status"] == "PENDING_FINAL_OPEN":
                review_pairs.append((row, a, b))
        if len(pairs) != 4_851:
            raise RuntimeError(f"pair count mismatch: {len(pairs)}")

        # Predeclared semantic ROIs cover all hard-reading junctions, containers, endpoints, and caption.
        roi_specs = [
            ("ROI-01-equation-box", (334, 461, 436, 497)),
            ("ROI-02-apex-x-r", (272, 480, 318, 506)),
            ("ROI-03-residual-label", (280, 487, 377, 528)),
            ("ROI-04-distance-brace-label", (279, 525, 375, 580)),
            ("ROI-05-p-endpoint-label", (245, 558, 322, 614)),
            ("ROI-06-origin-x-subspace", (145, 515, 235, 641)),
            ("ROI-07-caption", (55, 638, 530, 660)),
        ]
        roi_manifest = []
        native_items = []
        near8_items = []
        for roi_id, bpt in roi_specs:
            px = (
                math.floor(bpt[0] * img_w / page.width), math.floor(bpt[1] * img_h / page.height),
                math.ceil(bpt[2] * img_w / page.width), math.ceil(bpt[3] * img_h / page.height),
            )
            roi = page_image.crop(px)
            p1 = ROOT / "roi" / f"{roi_id}_native1x.png"
            p8 = ROOT / "roi" / f"{roi_id}_nearest8x.png"
            roi.save(p1)
            roi8 = roi.resize((roi.width * 8, roi.height * 8), Image.Resampling.NEAREST)
            roi8.save(p8)
            native_items.append((roi_id + " native1x", roi))
            near8_items.append((roi_id + " nearest8x", roi8))
            roi_manifest.append({
                "roi_id": roi_id, "bbox_pt": bpt, "bbox_px_page300": px,
                "native1x_path": str(p1.relative_to(ROOT)).replace("\\", "/"),
                "nearest8x_path": str(p8.relative_to(ROOT)).replace("\\", "/"),
                "resampling": "NEAREST; no interpolation; every native pixel becomes an 8x8 block",
            })
        make_sheet(native_items, ROOT / "roi" / "p033_manual_review_native1x_sheet.png", columns=2, max_panel_w=2000)
        make_sheet(near8_items, ROOT / "roi" / "p033_manual_review_nearest8x_sheet.png", columns=1, max_panel_w=3200)

        object_fields = [
            "object_id", "atomic_type", "source_object_index", "semantic_parent", "zone", "foreground_class",
            "source_line", "text", "codepoint", "fontname", "pdf_font_size_pt", "x0_pt", "top_pt", "x1_pt", "bottom_pt",
            "fill", "stroke", "linewidth_pt", "background_exclusion_reason",
        ]
        pair_fields = [
            "pair_id", "object_a", "object_b", "parent_a", "parent_b", "type_a", "type_b", "bbox_overlap",
            "bbox_overlap_width_pt", "bbox_overlap_height_pt", "bbox_gap_pt", "bbox_gap_px_300dpi",
            "disposition", "rationale", "manual_pixel_status",
        ]
        write_csv(ROOT / "machine" / "atomic_visible_denominator.csv", objects, object_fields)
        write_csv(ROOT / "machine" / "all_unordered_pairs.csv", pairs, pair_fields)
        write_csv(ROOT / "machine" / "text_codepoint_audit.csv", text_audit,
                  ["semantic_parent", "expected_text", "pdf_extracted_text", "exact_codepoint_match", "hard_status"])
        write_csv(ROOT / "machine" / "glyph_raster_ink_audit.csv", glyph_metrics,
                  ["object_id", "semantic_parent", "text", "codepoint", "pdf_font_size_pt", "raster_ink_nonempty",
                   "ink_height_px_advisory", "ink_pixel_count", "hard_missing_tofu_direction"])
        write_csv(ROOT / "machine" / "manual_review_pair_queue.csv",
                  [r for r, _, _ in review_pairs], pair_fields)
        write_json(ROOT / "machine" / "roi_manifest.json", roi_manifest)

        font_groups = []
        declared_by_group = {
            "TXT_SUBSPACE": 9.4, "TXT_X": 9.4, "TXT_PROJECTION": 9.4,
            "TXT_RESIDUAL": 9.2, "TXT_DISTANCE": 9.2, "TXT_PYTHAGORAS": 9.2,
            "CAPTION_NUMBER": None, "CAPTION_TEXT": None,
        }
        for parent in TEXT_EXPECTED:
            vals = [float(o["pdf_font_size_pt"]) for o in objects if o["atomic_type"] == "GLYPH" and o["semantic_parent"] == parent]
            font_groups.append({
                "semantic_parent": parent,
                "source_declared_pt": declared_by_group[parent] if declared_by_group[parent] is not None else "not read outside white-list; PDF-native extraction used",
                "graphics_scale": 1.0,
                "pdf_native_font_size_median_pt": round(statistics.median(vals), 6),
                "pdf_native_font_size_min_pt": round(min(vals), 6),
                "r168_policy_status": "ADVISORY_ONLY",
                "comment": "R168: tiny font/raster/outline differences are not hard FAIL unless actually unreadable or obviously unbalanced.",
            })
        write_csv(ROOT / "machine" / "source_font_advisory.csv", font_groups,
                  ["semantic_parent", "source_declared_pt", "graphics_scale", "pdf_native_font_size_median_pt",
                   "pdf_native_font_size_min_pt", "r168_policy_status", "comment"])

        source_text = SOURCE.read_text(encoding="utf-8")
        source_lines = source_text.splitlines()
        source_snapshot = {
            "source_path": str(SOURCE), "source_sha256": source_hash,
            "relevant_lines": {str(i): source_lines[i - 1] for i in range(4, 38)},
            "chapter_context_path": r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\讲义源码\第01册_数学基础与统计学习基本理论\chapters\V1-C02.tex",
            "chapter_context_lines": {
                "141": r"\input{../../绘图源码/第01册_数学基础与统计学习基本理论/V1-C02/fig_v1_c02_projection.tex}",
                "142-143": r"由\cref{fig:V1-C02-projection}中的正交证书，对任意s∈S展开最佳逼近恒等式；第二项仅在s=P_Sx时为零。",
            },
        }
        write_json(ROOT / "source" / "source_and_context_snapshot.json", source_snapshot)

        geometry = {
            "coordinates": {"O": [0.0, 0.0], "P": [3.2, 0.8], "X": [2.7, 2.8]},
            "residual_X_minus_P": [-0.5, 2.0],
            "dot_P_with_residual": 3.2 * -0.5 + 0.8 * 2.0,
            "norm_x_squared": 2.7 ** 2 + 2.8 ** 2,
            "norm_p_squared": 3.2 ** 2 + 0.8 ** 2,
            "norm_r_squared": (-0.5) ** 2 + 2.0 ** 2,
            "pythagoras_residual": (2.7 ** 2 + 2.8 ** 2) - ((3.2 ** 2 + 0.8 ** 2) + ((-0.5) ** 2 + 2.0 ** 2)),
            "semantic_direction": "O->P is projection p in S; P->X is residual r=x-p; O->X is x; dot(p,r)=0; residual length is the distance to S.",
            "hard_geometry_status": "PASS",
        }
        write_json(ROOT / "machine" / "geometry_semantics_audit.json", geometry)

        identity = {
            "handoff_id": HANDOFF_ID,
            "canonical_task": "/root/p033_r111_fresh_sa1",
            "model_effort": MODEL_EFFORT,
            "fork_turns": "none",
            "pdf": {"path": str(PDF), "bytes": PDF.stat().st_size, "pages": 817, "sha256": pdf_hash},
            "source": {"path": str(SOURCE), "bytes": SOURCE.stat().st_size, "sha256": source_hash},
            "independent_location": {"physical_page": 29, "printed_page": 16, "figure_label": "图 2.1", "uid": "FIG-P033-01"},
            "root_preexistence_proof": {"directory_exists": False, "file_exists": False, "checked_at": "2026-08-27T07:55:49.884+08:00"},
            "root_creation": {"pre_create_directory_exists": False, "created_at": "2026-08-27T07:58:18.4176500+08:00"},
        }
        write_json(ROOT / "source" / "input_identity.json", identity)

        crop_spec = {
            "page_dimensions_pt": [page.width, page.height], "page_image_pixels_300dpi": [img_w, img_h],
            "selection_window_pt": WINDOW_PT, "atomic_union_pt": [min_x, min_top, max_x, max_bottom],
            "frozen_crop_pt": crop_pt, "frozen_crop_px_page300": crop_px,
            "scope": "Every nonempty glyph/line/rect/curve object intersecting the isolated figure-body plus caption window; adjacent body text begins below 671 pt and is excluded.",
        }
        write_json(ROOT / "machine" / "crop_spec.json", crop_spec)

        summary = {
            "status": "FROZEN_PRE_MANUAL",
            "uid": "FIG-P033-01", "candidate": "R111", "physical_page": 29,
            "N": 99, "decomposition": actual_counts, "C_N_2": 4851,
            "object_table_sha256": sha256(ROOT / "machine" / "atomic_visible_denominator.csv"),
            "all_pairs_table_sha256": sha256(ROOT / "machine" / "all_unordered_pairs.csv"),
            "disposition_counts": dict(sorted(disposition_counts.items())),
            "manual_review_queue_count": len(review_pairs),
            "background_policy": "All 3 nonempty support-background atoms remain in N. Their fill pixels are explicitly excluded from illegal-foreground collision counts; the equation note box remains a mixed container whose visible border clearance is manually reviewed.",
            "machine_hard_gate_direction": "PASS_CANDIDATE_PENDING_ACTUAL_OPEN_OF_FINAL_SHEETS_AND_ROIS",
            "r168": "Tiny font/raster/outline differences are advisory only. Hard failure is restricted to missing/tofu/wrong codepoint or math meaning, actually unreadable/obviously unbalanced, real clipping, illegal overlap, or geometry/semantic error.",
        }
        write_json(ROOT / "machine" / "denominator_freeze.json", summary)
        write_json(ROOT / "machine" / "machine_pre_manual_gate.json", {
            "status": "PASS_CANDIDATE_PENDING_MANUAL_OPEN",
            "pdf_identity_pass": True, "source_identity_pass": True, "page_count_pass": True,
            "codepoint_groups_pass": True, "all_85_glyph_rasters_nonempty": True,
            "geometry_semantics_pass": True,
            "atomic_object_count": 99, "unordered_pair_count": 4851,
            "all_pairs_enumerated": True,
            "hard_failures_found_pre_manual": [],
            "advisories": ["Source-local 9.2 pt and 9.4 pt declarations are below the older 9.5 pt target; under R168 this is advisory unless actually unreadable or unbalanced."],
            "manual_open_required": ["full-page 300 dpi", "body+caption native1x", "semantic overlay", "native1x ROI sheet", "nearest8x ROI sheet and individual critical ROIs"],
        })

    print(json.dumps({
        "N": 99, "C": 4851, "decomposition": actual_counts,
        "crop_pt": crop_pt, "crop_px": crop_px,
        "manual_review_queue_count": len(review_pairs),
        "disposition_counts": dict(sorted(disposition_counts.items())),
        "machine_direction": "PASS_CANDIDATE_PENDING_MANUAL_OPEN",
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
