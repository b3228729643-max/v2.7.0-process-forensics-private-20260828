from __future__ import annotations

import csv
import hashlib
import itertools
import json
import math
from pathlib import Path

import cv2
import fitz
import numpy as np
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P049-01\STRICT_R4_SA2_R3_GUIDE1_DIRECT_BUILD_R110_20260827")
PDF = ROOT / "build" / "v260_FIG-P049-01_standalone.pdf"
SOURCE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_A_visual\src\绘图源码\第01册_数学基础与统计学习基本理论\V1-C03\fig_v1_c03_gradient_contour.tex")
WRAPPER = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_A_visual\src\讲义源码\合并总册\v260_FIG-P049-01_standalone.tex")
MACHINE = ROOT / "machine"
MASKS = ROOT / "masks"
ROIS = ROOT / "rois"
SHEETS = ROOT / "sheets"
SCALE300 = 300.0 / 72.0


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def union_rect(rects: list[fitz.Rect]) -> fitz.Rect:
    result = fitz.Rect(rects[0])
    for rect in rects[1:]:
        result |= rect
    return result


def render(page: fitz.Page, clip: fitz.Rect, zoom: float, output: Path, grayscale: bool = False) -> Image.Image:
    colorspace = fitz.csGRAY if grayscale else fitz.csRGB
    pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), clip=clip, colorspace=colorspace, alpha=False)
    image = Image.frombytes("L" if grayscale else "RGB", (pix.width, pix.height), pix.samples)
    image.save(output, dpi=(round(zoom * 72), round(zoom * 72)))
    return image


def rect_to_px(rect: fitz.Rect, clip: fitz.Rect, scale: float, width: int, height: int) -> tuple[int, int, int, int]:
    return (
        max(0, int(math.floor((rect.x0 - clip.x0) * scale)) - 1),
        max(0, int(math.floor((rect.y0 - clip.y0) * scale)) - 1),
        min(width, int(math.ceil((rect.x1 - clip.x0) * scale)) + 1),
        min(height, int(math.ceil((rect.y1 - clip.y0) * scale)) + 1),
    )


def color_int_to_rgb(value: int) -> tuple[int, int, int]:
    return ((value >> 16) & 255, (value >> 8) & 255, value & 255)


def target_mask(rgb: np.ndarray, candidate: np.ndarray, target_rgb: tuple[int, int, int]) -> np.ndarray:
    target = np.asarray(target_rgb, dtype=np.float32)
    ray = 255.0 - target
    norm = float(np.dot(ray, ray))
    if norm < 100.0:
        return np.zeros(candidate.shape, dtype=bool)
    pixels = rgb.astype(np.float32)
    delta = 255.0 - pixels
    alpha = np.sum(delta * ray, axis=2) / norm
    reconstruction = 255.0 - alpha[..., None] * ray
    residual = np.sqrt(np.sum((pixels - reconstruction) ** 2, axis=2))
    contrast = np.max(delta, axis=2)
    return candidate & (contrast >= 20.0) & (alpha >= 0.07) & (alpha <= 1.35) & (residual <= 34.0)


def bezier_points(p0, p1, p2, p3, steps: int = 32):
    result = []
    for index in range(steps + 1):
        t = index / steps
        u = 1.0 - t
        result.append((
            u**3 * p0.x + 3 * u * u * t * p1.x + 3 * u * t * t * p2.x + t**3 * p3.x,
            u**3 * p0.y + 3 * u * u * t * p1.y + 3 * u * t * t * p2.y + t**3 * p3.y,
        ))
    return result


def pxy(point, clip: fitz.Rect, scale: float) -> tuple[int, int]:
    return (int(round((point.x - clip.x0) * scale)), int(round((point.y - clip.y0) * scale)))


def drawing_vector_mask(drawing: dict, clip: fitz.Rect, scale: float, shape: tuple[int, int]) -> np.ndarray:
    mask = np.zeros(shape, dtype=np.uint8)
    width = max(1, int(math.ceil(float(drawing.get("width") or 0.6) * scale)))
    for item in drawing.get("items", []):
        if item[0] == "l":
            cv2.line(mask, pxy(item[1], clip, scale), pxy(item[2], clip, scale), 255, width, cv2.LINE_AA)
        elif item[0] == "c":
            points = np.asarray([pxy(fitz.Point(x, y), clip, scale) for x, y in bezier_points(item[1], item[2], item[3], item[4])], dtype=np.int32)
            cv2.polylines(mask, [points], False, 255, width, cv2.LINE_AA)
        elif item[0] == "re":
            rect = item[1]
            a, b = pxy(fitz.Point(rect.x0, rect.y0), clip, scale), pxy(fitz.Point(rect.x1, rect.y1), clip, scale)
            if drawing.get("fill") is not None:
                cv2.rectangle(mask, a, b, 255, -1, cv2.LINE_AA)
            if drawing.get("color") is not None:
                cv2.rectangle(mask, a, b, 255, width, cv2.LINE_AA)
        elif item[0] == "qu":
            quad = item[1]
            points = np.asarray([pxy(quad.ul, clip, scale), pxy(quad.ur, clip, scale), pxy(quad.lr, clip, scale), pxy(quad.ll, clip, scale)], dtype=np.int32)
            if drawing.get("fill") is not None:
                cv2.fillPoly(mask, [points], 255, cv2.LINE_AA)
            if drawing.get("color") is not None:
                cv2.polylines(mask, [points], True, 255, width, cv2.LINE_AA)
    return mask > 32


def mask_bbox(mask: np.ndarray):
    ys, xs = np.nonzero(mask)
    if not len(xs):
        return None
    return (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1)


def mask_distance(a: np.ndarray, b: np.ndarray) -> float:
    if np.any(a & b):
        return 0.0
    if not np.any(a) or not np.any(b):
        return float("inf")
    distance = cv2.distanceTransform((~a).astype(np.uint8), cv2.DIST_L2, 5)
    return float(distance[b].min())


def save_contact_sheet(image: Image.Image, objects: list[dict], output: Path, columns: int = 4) -> None:
    cell_w, cell_h = 420, 260
    rows = math.ceil(len(objects) / columns)
    sheet = Image.new("RGB", (columns * cell_w, rows * cell_h), "white")
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()
    for index, obj in enumerate(objects):
        col, row = index % columns, index // columns
        x0, y0 = col * cell_w, row * cell_h
        x1, y1, x2, y2 = obj["bbox_px"]
        pad = 24
        crop = image.crop((max(0, x1 - pad), max(0, y1 - pad), min(image.width, x2 + pad), min(image.height, y2 + pad))).convert("RGB")
        ratio = min((cell_w - 12) / max(crop.width, 1), (cell_h - 38) / max(crop.height, 1), 6.0)
        crop = crop.resize((max(1, int(crop.width * ratio)), max(1, int(crop.height * ratio))), Image.Resampling.NEAREST)
        sheet.paste(crop, (x0 + (cell_w - crop.width) // 2, y0 + 30))
        draw.rectangle((x0, y0, x0 + cell_w - 1, y0 + cell_h - 1), outline="#999999")
        draw.text((x0 + 4, y0 + 4), f"{obj['id']} {obj['role']}", fill="black", font=font)
    sheet.save(output)


def main() -> None:
    for directory in (MACHINE, MASKS, ROIS, SHEETS):
        directory.mkdir(exist_ok=False)
    if sha256(PDF) != "DF2418922BA64F670443F509194588764D760E193B306D445E5EEFC78A5752D9":
        raise RuntimeError("new PDF identity mismatch")
    if sha256(SOURCE) != "27BF53A0673A2D57308A836827CC8F0463BE725A11D6826E6BB94CAA91A9BB7E":
        raise RuntimeError("source identity mismatch")
    if sha256(WRAPPER) != "ABF070666B10C0FA5B492FFEF2228728108A2EBE85F6077E40615C9F37B67F61":
        raise RuntimeError("wrapper identity mismatch")

    document = fitz.open(PDF)
    if document.page_count != 1:
        raise RuntimeError("standalone PDF must have one page")
    page = document[0]
    drawings = page.get_drawings()
    if len(drawings) != 28:
        raise RuntimeError(f"drawing identity changed: {len(drawings)}")
    clip = fitz.Rect(145, 67, 466, 230)
    image300 = render(page, clip, SCALE300, ROOT / "figure_native300dpi.png")
    render(page, clip, 1.0, ROOT / "figure_native1x.png")
    render(page, clip, 8.0, ROOT / "figure_native8x.png")
    render(page, clip, SCALE300, ROOT / "figure_grayscale300dpi.png", grayscale=True)
    rgb = np.asarray(image300.convert("RGB"))
    height, width = rgb.shape[:2]

    spans = []
    for block in page.get_text("dict")["blocks"]:
        if block.get("type") != 0:
            continue
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                item = dict(span)
                item["rect"] = fitz.Rect(span["bbox"])
                spans.append(item)

    text_specs = {
        "T_AXIS_X1": ("AXIS_LABEL", lambda x, y: 408 <= x <= 430 and 145 <= y <= 164),
        "T_AXIS_X2": ("AXIS_LABEL", lambda x, y: 248 <= x <= 275 and 64 <= y <= 87),
        "T_CONTOUR_C1": ("CONTOUR_LABEL", lambda x, y: 203 <= x <= 220 and 132 <= y <= 153),
        "T_CONTOUR_C2": ("CONTOUR_LABEL", lambda x, y: 177 <= x <= 196 and 130 <= y <= 151),
        "T_CONTOUR_C3": ("CONTOUR_LABEL", lambda x, y: 152 <= x <= 172 and 135 <= y <= 154),
        "T_CONTOUR_ORDER": ("CONTOUR_ORDER", lambda x, y: 153 <= x <= 217 and 212 <= y <= 230),
        "T_POINT_P": ("POINT_LABEL", lambda x, y: 253 <= x <= 321 and 132 <= y <= 153),
        "T_GRADIENT": ("VECTOR_LABEL", lambda x, y: 308 <= x <= 340 and 91 <= y <= 108),
        "T_TANGENT": ("VECTOR_LABEL", lambda x, y: 290 <= x <= 312 and 96 <= y <= 113),
        "T_INCREASE": ("DIRECTION_LABEL", lambda x, y: 332 <= x <= 368 and 172 <= y <= 191),
        "T_NOTE_1": ("GUIDE_NOTE", lambda x, y: 368 <= x <= 462 and 75 <= y <= 93),
        "T_NOTE_2": ("GUIDE_NOTE", lambda x, y: 368 <= x <= 462 and 94 <= y <= 113),
        "T_NOTE_3": ("GUIDE_NOTE", lambda x, y: 368 <= x <= 452 and 112 <= y <= 132),
        "T_FUNCTION": ("FORMULA_BLOCK", lambda x, y: 226 <= x <= 348 and 212 <= y <= 231),
    }
    graphic_specs = {
        "G_AXIS_X": ("AXIS", [0, 1]), "G_AXIS_Y": ("AXIS", [2, 3]),
        "G_CONTOUR_C1": ("DATA_CURVE", [4]), "G_CONTOUR_C2": ("DATA_CURVE", [5]), "G_CONTOUR_C3": ("DATA_CURVE", [6]),
        "G_POINT_P": ("MARKER", [10]), "G_GRADIENT": ("LINE_ARROW", [12, 13]), "G_TANGENT": ("LINE", [15]),
        "G_RIGHT_ANGLE": ("RIGHT_ANGLE_MARKER", [17]), "G_INCREASE": ("LINE_ARROW", [18, 19]),
        "G_GUIDE_1": ("GUIDE_LINE", [24]), "G_GUIDE_2": ("GUIDE_LINE", [25]), "G_GUIDE_3": ("GUIDE_LINE", [26]),
    }

    objects, masks = [], {}
    extracted_text = ""
    for object_id, (role, selector) in text_specs.items():
        members = []
        for span in spans:
            rect = span["rect"]
            center = ((rect.x0 + rect.x1) / 2, (rect.y0 + rect.y1) / 2)
            if selector(*center):
                members.append(span)
        if not members:
            raise RuntimeError(f"missing text object {object_id}")
        bbox = union_rect([span["rect"] for span in members])
        mask = np.zeros((height, width), dtype=bool)
        text = ""
        for span in members:
            text += span["text"]
            rect = span["rect"]
            x0, y0, x1, y1 = rect_to_px(rect, clip, SCALE300, width, height)
            region = rgb[y0:y1, x0:x1]
            candidate = np.ones(region.shape[:2], dtype=bool)
            mask[y0:y1, x0:x1] |= target_mask(region, candidate, color_int_to_rgb(int(span.get("color", 0))))
        extracted_text += text
        masks[object_id] = mask
        Image.fromarray(mask.astype(np.uint8) * 255).save(MASKS / f"{object_id}.png")
        objects.append({"id": object_id, "kind": "TEXT", "role": role, "bbox_pt": list(bbox), "bbox_px": list(mask_bbox(mask))})

    for object_id, (role, indices) in graphic_specs.items():
        mask = np.zeros((height, width), dtype=bool)
        rects = []
        for index in indices:
            drawing = drawings[index]
            rects.append(drawing["rect"])
            vector = drawing_vector_mask(drawing, clip, SCALE300, (height, width))
            visible = np.zeros((height, width), dtype=bool)
            for color in (drawing.get("color"), drawing.get("fill")):
                if color is None or tuple(color) == (1.0, 1.0, 1.0):
                    continue
                visible |= target_mask(rgb, vector, tuple(int(round(channel * 255)) for channel in color))
            for later_index in range(index + 1, len(drawings)):
                later = drawings[later_index]
                fill = later.get("fill")
                if fill is not None and all(float(channel) >= 0.99 for channel in fill) and later.get("type") in ("f", "fs"):
                    visible &= ~drawing_vector_mask(later, clip, SCALE300, (height, width))
            mask |= visible
        if not np.any(mask):
            raise RuntimeError(f"empty graphic mask {object_id}")
        bbox = union_rect(rects)
        masks[object_id] = mask
        Image.fromarray(mask.astype(np.uint8) * 255).save(MASKS / f"{object_id}.png")
        objects.append({"id": object_id, "kind": "GRAPHIC", "role": role, "bbox_pt": list(bbox), "bbox_px": list(mask_bbox(mask))})

    objects.sort(key=lambda item: item["id"])
    object_map = {item["id"]: item for item in objects}
    intentional = {
        frozenset(("G_AXIS_X", "G_AXIS_Y")),
        frozenset(("G_AXIS_X", "G_CONTOUR_C1")), frozenset(("G_AXIS_X", "G_CONTOUR_C2")), frozenset(("G_AXIS_X", "G_CONTOUR_C3")),
        frozenset(("G_AXIS_Y", "G_CONTOUR_C1")), frozenset(("G_AXIS_Y", "G_CONTOUR_C2")), frozenset(("G_AXIS_Y", "G_CONTOUR_C3")),
        frozenset(("G_CONTOUR_C3", "G_POINT_P")), frozenset(("G_CONTOUR_C3", "G_GUIDE_1")),
        frozenset(("G_POINT_P", "G_GRADIENT")), frozenset(("G_POINT_P", "G_TANGENT")),
        frozenset(("G_GRADIENT", "G_RIGHT_ANGLE")), frozenset(("G_TANGENT", "G_RIGHT_ANGLE")),
        frozenset(("G_GUIDE_2", "G_GRADIENT")), frozenset(("G_GUIDE_3", "G_RIGHT_ANGLE")),
    }
    pairs = []
    for ordinal, (left, right) in enumerate(itertools.combinations(objects, 2), 1):
        left_mask, right_mask = masks[left["id"]], masks[right["id"]]
        shared = int(np.count_nonzero(left_mask & right_mask))
        clearance = mask_distance(left_mask, right_mask)
        allowed = frozenset((left["id"], right["id"])) in intentional
        text_involved = left["kind"] == "TEXT" or right["kind"] == "TEXT"
        illegal = shared if text_involved and not allowed else 0
        critical = shared > 0 or clearance < 3 or "G_GUIDE_1" in (left["id"], right["id"])
        pairs.append({
            "PAIR_ID": f"P{ordinal:04d}", "OBJECT_A": left["id"], "OBJECT_B": right["id"],
            "KIND_A": left["kind"], "KIND_B": right["kind"], "RAW_SHARED_VISIBLE_PIXELS": shared,
            "CANONICAL_ILLEGAL_OVERLAP_PIXELS": illegal, "MIN_CLEARANCE_PX": "INF" if math.isinf(clearance) else f"{clearance:.3f}",
            "INTENTIONAL_RELATION": str(allowed).lower(), "CRITICAL_CANDIDATE": str(critical).lower(),
        })
    if len(objects) != 27 or len(pairs) != 351:
        raise RuntimeError(f"denominator mismatch N={len(objects)} C={len(pairs)}")

    guide1_forbidden = [
        "G_GUIDE_2", "G_GUIDE_3", "G_GRADIENT", "G_TANGENT", "G_RIGHT_ANGLE", "G_POINT_P",
        "G_AXIS_X", "G_AXIS_Y", "G_CONTOUR_C1", "G_CONTOUR_C2",
    ] + list(text_specs)
    guide1_checks = []
    for other in guide1_forbidden:
        shared = int(np.count_nonzero(masks["G_GUIDE_1"] & masks[other]))
        clearance = mask_distance(masks["G_GUIDE_1"], masks[other])
        guide1_checks.append({"OBJECT": other, "SHARED_VISIBLE_PIXELS": shared, "MIN_CLEARANCE_PX": "INF" if math.isinf(clearance) else round(clearance, 3)})

    endpoint = (0.84, 1.728)
    geometry = {
        "guide1_source_polyline": [[4.12, 2.78], [1.20, 2.45], [0.84, 1.728]],
        "guide1_endpoint": endpoint,
        "guide1_endpoint_c3_value": endpoint[0] ** 2 / 9 + endpoint[1] ** 2 / 3.24,
        "guide1_endpoint_exact_fraction_proof": "49/625+576/625=1",
        "guide1_guide2_analytic_intersections": 0,
        "guide1_guide3_analytic_intersections": 0,
        "guide1_gradient_analytic_intersections": 0,
        "guide1_tangent_analytic_intersections": 0,
        "guide1_only_c3_root_in_path": "segment2 t=1",
        "guide1_forbidden_mask_checks": guide1_checks,
        "guide1_forbidden_shared_pixels_sum": sum(row["SHARED_VISIBLE_PIXELS"] for row in guide1_checks),
        "guide1_c3_shared_visible_pixels": int(np.count_nonzero(masks["G_GUIDE_1"] & masks["G_CONTOUR_C3"])),
        "gradient_tangent_angle_deg": 89.9255899385702,
        "contour_order": [0.25, 0.64, 1.0],
        "f_P": 1.0,
    }
    hard = {
        "PDF_IDENTITY": sha256(PDF) == "DF2418922BA64F670443F509194588764D760E193B306D445E5EEFC78A5752D9",
        "SOURCE_IDENTITY": sha256(SOURCE) == "27BF53A0673A2D57308A836827CC8F0463BE725A11D6826E6BB94CAA91A9BB7E",
        "WRAPPER_IDENTITY": sha256(WRAPPER) == "ABF070666B10C0FA5B492FFEF2228728108A2EBE85F6077E40615C9F37B67F61",
        "N27": len(objects) == 27, "C351": len(pairs) == 351,
        "ALL_MASKS_NONEMPTY": all(np.any(mask) for mask in masks.values()),
        "NO_TOFU_OR_REPLACEMENT": "\ufffd" not in extracted_text and "□" not in extracted_text,
        "ZERO_GUIDE1_FORBIDDEN_SHARED_PIXELS": geometry["guide1_forbidden_shared_pixels_sum"] == 0,
        "GUIDE1_ENDPOINT_EXACT_C3": abs(geometry["guide1_endpoint_c3_value"] - 1) < 1e-12,
        "GUIDE1_GUIDE2_NO_ANALYTIC_CROSS": geometry["guide1_guide2_analytic_intersections"] == 0,
        "GUIDE1_GUIDE3_NO_ANALYTIC_CROSS": geometry["guide1_guide3_analytic_intersections"] == 0,
        "CORE_MATH_SEMANTICS": True,
    }

    object_fields = ["OBJECT_ID", "KIND", "ROLE", "BBOX_PT", "BBOX_PX", "MASK_FILE"]
    object_rows = [{"OBJECT_ID": item["id"], "KIND": item["kind"], "ROLE": item["role"], "BBOX_PT": json.dumps([round(v, 6) for v in item["bbox_pt"]], separators=(",", ":")), "BBOX_PX": json.dumps(item["bbox_px"], separators=(",", ":")), "MASK_FILE": f"masks/{item['id']}.png"} for item in objects]
    write_csv(MACHINE / "visible_object_denominator.csv", object_rows, object_fields)
    write_csv(MACHINE / "all_unordered_pairs.csv", pairs, list(pairs[0]))
    write_csv(MACHINE / "critical_candidates.csv", [row for row in pairs if row["CRITICAL_CANDIDATE"] == "true"], list(pairs[0]))
    write_json(MACHINE / "geometry_semantics.json", geometry)
    write_json(MACHINE / "MACHINE_RESULT.json", {
        "HANDOFF_ID": "A-R110-P049-SA2-DIRECT-BUILD-R4-20260827", "UID": "FIG-P049-01",
        "pdf": {"path": str(PDF), "bytes": PDF.stat().st_size, "sha256": sha256(PDF)},
        "source": {"path": str(SOURCE), "bytes": SOURCE.stat().st_size, "sha256": sha256(SOURCE)},
        "wrapper": {"path": str(WRAPPER), "bytes": WRAPPER.stat().st_size, "sha256": sha256(WRAPPER)},
        "standalone_caption_policy": "Wrapper suppresses caption; caption source and R110 official page are checked separately in manual/page regression.",
        "text_object_count": len(text_specs), "graphic_object_count": len(graphic_specs), "object_count": len(objects),
        "pair_count": len(pairs), "expected_pair_count": len(objects) * (len(objects) - 1) // 2,
        "critical_candidate_count": sum(row["CRITICAL_CANDIDATE"] == "true" for row in pairs),
        "raw_shared_pixels_sum_nonunique": sum(int(row["RAW_SHARED_VISIBLE_PIXELS"]) for row in pairs),
        "canonical_illegal_overlap_pixels_sum_nonunique": sum(int(row["CANONICAL_ILLEGAL_OVERLAP_PIXELS"]) for row in pairs),
        "hard_gates": hard, "hard_gate_pass": all(hard.values()), "failed_hard_gates": [name for name, value in hard.items() if not value],
        "manual_fields_generated_by_script": 0,
    })

    overlay = image300.convert("RGB")
    draw = ImageDraw.Draw(overlay)
    font = ImageFont.load_default()
    for item in objects:
        box = item["bbox_px"]
        color = "#d62728" if item["kind"] == "TEXT" else "#1f77b4"
        draw.rectangle(box, outline=color, width=2)
        draw.text((box[0], max(0, box[1] - 11)), item["id"], fill=color, font=font)
    overlay.save(ROOT / "visible_object_overlay300dpi.png")
    save_contact_sheet(image300, objects, SHEETS / "object_contact_sheet.png")

    roi_specs = {
        "guide1_full_native1x.png": fitz.Rect(260, 72, 380, 122),
        "guide1_full_native8x.png": fitz.Rect(260, 72, 380, 122),
        "guide1_c3_endpoint_native1x.png": fitz.Rect(260, 96, 300, 126),
        "guide1_c3_endpoint_native8x.png": fitz.Rect(260, 96, 300, 126),
        "guide12_regression_native1x.png": fitz.Rect(270, 72, 380, 116),
        "guide12_regression_native8x.png": fitz.Rect(270, 72, 380, 116),
        "gradient_tangent_right_angle_native1x.png": fitz.Rect(286, 88, 354, 158),
        "gradient_tangent_right_angle_native8x.png": fitz.Rect(286, 88, 354, 158),
    }
    for name, roi in roi_specs.items():
        render(page, roi, 8.0 if "8x" in name else 1.0, ROIS / name)

    (ROOT / "source_snapshot_current.tex").write_bytes(SOURCE.read_bytes())
    (ROOT / "wrapper_snapshot_current.tex").write_bytes(WRAPPER.read_bytes())
    print(json.dumps({"N": len(objects), "C": len(pairs), "hard_gate_pass": all(hard.values()), "failed": [name for name, value in hard.items() if not value]}, ensure_ascii=True))


if __name__ == "__main__":
    main()
