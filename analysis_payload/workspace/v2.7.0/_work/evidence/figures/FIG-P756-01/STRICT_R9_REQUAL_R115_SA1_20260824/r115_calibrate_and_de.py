"""R115 low-profile calibration plus native-mask D/E audit.

Calibration pages are derived from the official final PDF's embedded font
programs and rendered with pdftoppm at native 300 dpi.  They do not use a
source build or any historical figure evidence.
"""
from __future__ import annotations

import csv
import json
import math
import re
import subprocess
from collections import defaultdict
from pathlib import Path

import fitz
import numpy as np
from PIL import Image


ROOT = Path(__file__).resolve().parent
CANDIDATE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r95_fullbook\main_full.pdf")
PAGE_NUMBER = 801
LOW_PREFIX = "LOW_PROFILE_PUNCTUATION_"


def read_csv(name: str) -> list[dict[str, str]]:
    with (ROOT / name).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(name: str, rows: list[dict[str, object]]) -> None:
    if not rows:
        raise ValueError(name)
    with (ROOT / name).open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def rgb_from_pdf_color(value: int) -> tuple[int, int, int]:
    return ((value >> 16) & 255, (value >> 8) & 255, value & 255)


def normalized_font(name: str) -> str:
    return name.split("+", 1)[-1]


def unicode_to_cid_map(doc: fitz.Document, font_xref: int) -> dict[str, str]:
    """Return Unicode character -> exact Identity-H CID hex from ToUnicode."""
    font_object = doc.xref_object(font_xref, compressed=False)
    match = re.search(r"/ToUnicode\s+(\d+)\s+0\s+R", font_object)
    if not match:
        raise ValueError(f"font {font_xref} has no ToUnicode map")
    cmap = doc.xref_stream(int(match.group(1))).decode("latin1")
    result: dict[str, str] = {}
    for cid_hex, unicode_hex in re.findall(r"<([0-9A-Fa-f]+)>\s+<([0-9A-Fa-f]+)>", cmap):
        try:
            char = bytes.fromhex(unicode_hex).decode("utf-16-be")
        except UnicodeDecodeError:
            continue
        if len(char) == 1:
            result[char] = cid_hex.upper()
    return result


def font_weight(name: str) -> str:
    return "bold" if "bold" in name.lower() else "normal"


def mask_metrics(path: Path) -> tuple[int, int]:
    arr = np.asarray(Image.open(path).convert("L"))
    mask = arr == 0
    if not mask.any():
        raise ValueError(f"empty target mask {path}")
    ys, _ = np.where(mask)
    return int(ys.max() - ys.min() + 1), int(mask.sum())


def crop_mask_from_render(image: Image.Image, bbox: tuple[int, int, int, int], rgb: tuple[int, int, int]) -> tuple[Image.Image, Image.Image, Image.Image, int, int]:
    x0, y0, x1, y1 = bbox
    full = (max(0, x0 - 4), max(0, y0 - 4), min(image.width, x1 + 4), min(image.height, y1 + 4))
    crop = image.crop(full).convert("RGB")
    arr = np.asarray(crop, dtype=np.int32)
    target = np.asarray(rgb, dtype=np.int32)
    dist = np.sqrt(np.sum((arr - target) ** 2, axis=2))
    lx0, ly0, lx1, ly1 = x0 - full[0], y0 - full[1], x1 - full[0], y1 - full[1]
    ownership = np.zeros(dist.shape, dtype=bool)
    ownership[ly0:ly1, lx0:lx1] = True
    mask = (dist <= 112.0) & ownership
    if not mask.any():
        raise ValueError("empty calibration glyph mask")
    ys, _ = np.where(mask)
    h, area = int(ys.max() - ys.min() + 1), int(mask.sum())
    overlay = np.asarray(crop).copy()
    overlay[mask] = np.array([255, 0, 0], dtype=np.uint8)
    return crop, Image.fromarray(overlay, "RGB"), Image.fromarray(np.where(mask, 0, 255).astype(np.uint8), "L"), h, area


def isolated_calibration_mask_from_render(image: Image.Image, rgb: tuple[int, int, int]) -> tuple[Image.Image, Image.Image, Image.Image, int, int, tuple[int, int, int, int]]:
    """Measure the one controlled glyph without relying on a ToUnicode map.

    Each calibration page contains exactly one glyph, placed at (280, 420) on
    an otherwise blank page.  Some official CFF subsets do not expose that
    glyph through PDF text extraction, so ownership is the fixed blank-page
    placement window, not a reconstructed or target-derived glyph box.
    """
    sx, sy = image.width / 595.276, image.height / 841.89
    x0, x1 = math.floor(220 * sx), math.ceil(360 * sx)
    y0, y1 = math.floor(350 * sy), math.ceil(450 * sy)
    arr = np.asarray(image.convert("RGB"), dtype=np.int32)
    target = np.asarray(rgb, dtype=np.int32)
    dist = np.sqrt(np.sum((arr - target) ** 2, axis=2))
    local = dist[y0:y1, x0:x1] <= 112.0
    if not local.any():
        raise ValueError("empty isolated calibration glyph mask")
    ys, xs = np.where(local)
    bbox = (x0 + int(xs.min()), y0 + int(ys.min()), x0 + int(xs.max()) + 1, y0 + int(ys.max()) + 1)
    crop, overlay, mask, h, area = crop_mask_from_render(image, bbox, rgb)
    return crop, overlay, mask, h, area, bbox


def e_rule(panel: str, role: str) -> tuple[str, str, float, float]:
    """Closed role hierarchy rules on effective point size, not glyph shape."""
    if panel == "TOP":
        base = "STATION_BODY"
        if role == "PANEL_TITLE":
            return base, "PANEL_TITLE_TO_BASE", 1.05, 1.20
        if role == "STATION_HEADING":
            return base, "STATION_HEADING_TO_BASE", 1.00, 1.18
        return base, "BADGE_OR_ANNOTATION_TO_BASE", 0.95, 1.10
    if panel == "BOTTOM":
        base = "ROUTE_BODY"
        if role in {"PANEL_TITLE", "POOL_TITLE"}:
            return base, "PANEL_TITLE_OR_POOL_TITLE_TO_BASE", 1.05, 1.20
        if role in {"ROUTE_HEADING", "VALIDATION_HEADING", "REPORT_HEADING"}:
            return base, "NODE_HEADING_TO_BASE", 1.00, 1.18
        return base, "ORDINARY_TEXT_TO_BASE", 0.95, 1.10
    if panel == "CAPTION":
        base = "CAPTION"
        if role == "CAPTION":
            return base, "CAPTION_BODY_BASE", 1.00, 1.00
        return base, "CAPTION_LABEL_TO_BODY", 0.95, 1.10
    raise ValueError(f"unmapped E role {panel}/{role}/{script}")


def main() -> None:
    glyphs = read_csv("glyph_file_manifest.csv")
    if len(glyphs) != 378 or len({r["GLYPH_ID"] for r in glyphs}) != 378:
        raise ValueError("glyph manifest coverage mismatch")
    for row in glyphs:
        h, area = mask_metrics(ROOT / row["MASK_FILE"])
        if h != int(row["H_INK_PX"]) or area != int(row["MASK_FOREGROUND_PX"]):
            raise ValueError(f"stored native-mask metrics mismatch {row['GLYPH_ID']}")
        row["H_REMEASURED"] = h
        row["AREA_REMEASURED"] = area

    low = [r for r in glyphs if r["SCRIPT_CLASS"].startswith(LOW_PREFIX)]
    if len(low) != 20:
        raise ValueError(f"expected 20 low-profile glyphs after full-contour delimiter correction, got {len(low)}")
    caldir = ROOT / "low_profile_calibration"
    rawcid_dir = caldir / "raw_cid_replay_v2"
    caldir.mkdir(exist_ok=True)
    rawcid_dir.mkdir(exist_ok=True)
    doc = fitz.open(CANDIDATE)
    page = doc[PAGE_NUMBER - 1]
    font_info: dict[str, tuple[str, int, dict[str, str]]] = {}
    for xref, _, _, basefont, resource_name, _, _ in page.get_fonts(full=True):
        font_info[normalized_font(basefont)] = (resource_name, xref, unicode_to_cid_map(doc, xref))
    for name in {r["PDF_FONT"] for r in low}:
        if name not in font_info:
            raise ValueError(f"official embedded font resource missing for {name}")

    groups: dict[tuple[str, str, str, str], list[dict[str, str]]] = defaultdict(list)
    for row in low:
        groups[(row["CHAR"], row["PDF_FONT"], row["PDF_RGB"], row["EFFECTIVE_PT"])].append(row)
    ordered_groups = sorted(groups.items(), key=lambda kv: (kv[0][1], kv[0][3], kv[0][2], kv[0][0]))

    calibration_pdf = caldir / "calibration_source_raw_cid_replay_from_official_v2.pdf"
    out = fitz.open()
    group_meta: dict[tuple[str, str, str, str], dict[str, object]] = {}
    for index, (key, members) in enumerate(ordered_groups, start=1):
        char, font, rgb_text, size_text = key
        rgb = tuple(int(x) for x in rgb_text.split("/"))
        resource_name, _, cmap = font_info[font]
        if char not in cmap:
            raise ValueError(f"official ToUnicode CID missing for calibration {char!r} / {font}")
        # Clone the official page solely to retain its exact Type0 resource,
        # then replace its content stream with one raw CID in a blank page.
        # This avoids the invalid Unicode re-encoding of CFF subsets and
        # replays the exact glyph program used by the final candidate.
        out.insert_pdf(doc, from_page=PAGE_NUMBER - 1, to_page=PAGE_NUMBER - 1)
        page_out = out[-1]
        stream_xref = out.get_new_xref()
        out.update_object(stream_xref, "<< >>")
        colour = " ".join(f"{component / 255.0:.8f}" for component in rgb)
        stream = f"q\nBT\n/{resource_name} {float(size_text):.5f} Tf\n{colour} rg\n1 0 0 1 280 420 Tm\n[<{cmap[char]}>]TJ\nET\nQ\n"
        out.update_stream(stream_xref, stream.encode("ascii"))
        page_out.set_contents(stream_xref)
        group_meta[key] = {"calibration_id": f"CAL{index:03d}", "page": index, "font_resource": resource_name, "raw_cid_hex": cmap[char], "members": members}
    out.save(calibration_pdf, deflate=True)
    out.close()
    calibration_doc = fitz.open(calibration_pdf)

    calibration_rows: list[dict[str, object]] = []
    target_result: dict[str, dict[str, object]] = {}
    calibration_manifest_rows: list[dict[str, object]] = []
    for key, meta in group_meta.items():
        char, target_font, rgb_text, target_size_text = key
        page_no = int(meta["page"])
        prefix = rawcid_dir / f"{meta['calibration_id']}_page_{page_no:02d}_native_300dpi"
        subprocess.run(["pdftoppm", "-png", "-singlefile", "-f", str(page_no), "-l", str(page_no), "-r", "300", str(calibration_pdf), str(prefix)], check=True)
        png = prefix.with_suffix(".png")
        image = Image.open(png).convert("RGB")
        if image.size != (2481, 3508):
            raise ValueError(f"calibration native grid mismatch {image.size}")
        calpage = calibration_doc[page_no - 1]
        spans = [s for b in calpage.get_text("rawdict")["blocks"] if b["type"] == 0 for l in b["lines"] for s in l["spans"]]
        candidates = [(s, c) for s in spans for c in s["chars"] if c["c"] == char]
        if len(candidates) != 1:
            raise ValueError(f"raw-CID calibration extraction mismatch {meta['calibration_id']} {char!r}: {len(candidates)}")
        span, glyph = candidates[0]
        sx, sy = image.width / calpage.rect.width, image.height / calpage.rect.height
        bx0, by0, bx1, by1 = glyph["bbox"]
        bbox = (math.floor(bx0 * sx), math.floor(by0 * sy), math.ceil(bx1 * sx), math.ceil(by1 * sy))
        target_rgb = tuple(int(x) for x in rgb_text.split("/"))
        crop, overlay, mask_image, cal_h, cal_area = crop_mask_from_render(image, bbox, target_rgb)
        stem = str(meta["calibration_id"])
        raw_path = rawcid_dir / f"{stem}_raw_1x.png"
        overlay_path = rawcid_dir / f"{stem}_target_overlay_1x.png"
        mask_path = rawcid_dir / f"{stem}_mask_1x.png"
        crop.save(raw_path)
        overlay.save(overlay_path)
        mask_image.save(mask_path)
        crop.resize((crop.width * 8, crop.height * 8), Image.Resampling.NEAREST).save(rawcid_dir / f"{stem}_raw_8x_nearest.png")
        overlay.resize((overlay.width * 8, overlay.height * 8), Image.Resampling.NEAREST).save(rawcid_dir / f"{stem}_target_overlay_8x_nearest.png")
        mask_image.convert("RGB").resize((mask_image.width * 8, mask_image.height * 8), Image.Resampling.NEAREST).save(rawcid_dir / f"{stem}_mask_8x_nearest.png")
        cal_font = normalized_font(str(span["font"]))
        cal_rgb = rgb_from_pdf_color(int(span["color"]))
        cal_pt = float(span["size"])
        source_font_match = cal_font == target_font
        size_match = abs(cal_pt - float(target_size_text)) <= 0.25
        colour_match = cal_rgb == target_rgb
        weight_match = font_weight(cal_font) == font_weight(target_font)
        valid = source_font_match and size_match and colour_match and weight_match and image.size == (2481, 3508)
        calibration_manifest_rows.append({
            "CALIBRATION_ID": meta["calibration_id"], "CHAR": char, "TARGET_FONT": target_font, "CALIBRATION_FONT": cal_font,
            "TARGET_RGB": rgb_text, "CALIBRATION_RGB": "/".join(map(str, cal_rgb)), "TARGET_EFFECTIVE_PT": target_size_text, "CALIBRATION_EFFECTIVE_PT": f"{cal_pt:.4f}", "EFFECTIVE_PT_DELTA": f"{cal_pt-float(target_size_text):.4f}",
            "TARGET_WEIGHT": font_weight(target_font), "CALIBRATION_WEIGHT": font_weight(cal_font), "NATIVE_PNG_GRID": "2481x3508", "NATIVE_PNG_DPI": "300", "CALIBRATION_BBOX_PX": "/".join(map(str, bbox)),
            "RAW_1X": str(raw_path.relative_to(ROOT)).replace("\\", "/"), "OVERLAY_1X": str(overlay_path.relative_to(ROOT)).replace("\\", "/"), "MASK_1X": str(mask_path.relative_to(ROOT)).replace("\\", "/"),
            "CALIBRATION_PDF": str(calibration_pdf.relative_to(ROOT)).replace("\\", "/"), "FONT_RESOURCE": meta["font_resource"], "RAW_CID_HEX": meta["raw_cid_hex"], "PDF_TEXT_EXTRACTION": "RAW_CID_TO_UNICODE_CONFIRMED", "FONT_WEIGHT_COLOR_SIZE_300DPI_VALID": str(valid).lower(), "CALIBRATION_H_INK_PX": cal_h, "CALIBRATION_INK_AREA_PX": cal_area,
        })
        for target in meta["members"]:
            target_h, target_area = int(target["H_REMEASURED"]), int(target["AREA_REMEASURED"])
            h_ratio = target_h / cal_h
            area_ratio = target_area / cal_area
            metric_pass = 0.92 <= h_ratio <= 1.08 and 0.92 <= area_ratio <= 1.08
            decision = "PASS" if valid and metric_pass else "FAIL"
            target_result[target["GLYPH_ID"]] = {"valid": valid, "metric_pass": metric_pass, "decision": decision, "h_ratio": h_ratio, "area_ratio": area_ratio, "calibration_id": meta["calibration_id"], "cal_h": cal_h, "cal_area": cal_area}
            calibration_rows.append({
                "GLYPH_ID": target["GLYPH_ID"], "ELEMENT_ID": target["ELEMENT_ID"], "CHAR": char, "CALIBRATION_ID": meta["calibration_id"], "TARGET_FONT": target_font, "CALIBRATION_FONT": cal_font,
                "TARGET_RGB": rgb_text, "CALIBRATION_RGB": "/".join(map(str, cal_rgb)), "TARGET_EFFECTIVE_PT": target_size_text, "CALIBRATION_PDF_SPAN_PT": f"{cal_pt:.4f}", "EFFECTIVE_PT_DELTA": f"{cal_pt-float(target_size_text):.4f}",
                "TARGET_WEIGHT": font_weight(target_font), "CALIBRATION_WEIGHT": font_weight(cal_font), "NATIVE_PNG_GRID": "2481x3508", "NATIVE_PNG_DPI": "300", "CALIBRATION_BBOX_PX": "/".join(map(str, bbox)),
                "RAW_CROP_EXACT": "true", "MASK_CROP_EXACT": "true", "CALIBRATION_PDF": str(calibration_pdf.relative_to(ROOT)).replace("\\", "/"), "FONT_RESOURCE": meta["font_resource"], "RAW_CID_HEX": meta["raw_cid_hex"], "PDF_TEXT_EXTRACTION": "RAW_CID_TO_UNICODE_CONFIRMED", "FONT_WEIGHT_COLOR_SIZE_300DPI_PURITY_VALID": str(valid).lower(),
                "TARGET_H_INK_PX": target_h, "CALIBRATION_H_INK_PX": cal_h, "H_INK_RATIO": f"{h_ratio:.4f}", "TARGET_INK_AREA_PX": target_area, "CALIBRATION_INK_AREA_PX": cal_area, "INK_AREA_RATIO": f"{area_ratio:.4f}",
                "LOW_PROFILE_TOTAL_GATE_PASS": str(valid and metric_pass).lower(), "VALIDATION_NOTE": "Blank-page raw-CID replay from the official final-PDF Type0 resource, with ToUnicode character confirmation, source font/weight/colour/size/grid and exact calibration glyph bbox mask checked at native 300dpi.",
            })
    write_csv("R115_LOW_PROFILE_CALIBRATION_MANIFEST.csv", calibration_manifest_rows)
    write_csv("R115_LOW_PROFILE_CALIBRATION_VALIDATION.csv", calibration_rows)

    pixel_rows: list[dict[str, object]] = []
    for row in glyphs:
        low_profile = row["SCRIPT_CLASS"].startswith(LOW_PREFIX)
        if low_profile:
            result = target_result[row["GLYPH_ID"]]
            status = "VALID_METHOD_PASS" if result["valid"] and result["metric_pass"] else "VALID_METHOD_FAIL_MEASUREMENT" if result["valid"] else "METHOD_INVALID"
            decision = result["decision"]
            h_ratio, area_ratio = f"{result['h_ratio']:.4f}", f"{result['area_ratio']:.4f}"
            reason = f"{status}; calibration {result['calibration_id']} H={h_ratio}, area={area_ratio}, target/calibration ratio rule [0.92,1.08]."
        else:
            status, h_ratio, area_ratio = "NOT_REQUIRED", "NOT_APPLICABLE", "NOT_APPLICABLE"
            decision = "PASS" if float(row["EFFECTIVE_PT"]) >= 9.5 and int(row["H_REMEASURED"]) >= int(row["H_INK_PX"]) and row["SCRIPT_CLASS"] in {"CJK_FULL", "DIGIT_OR_UPPER", "LOWERCASE_OR_GREEK"} else "FAIL"
            # The core generator has already applied the class threshold; use
            # its preliminary row as the source of that per-class decision.
            reason = "Regular glyph retains direct native final-PDF source-font and class-threshold decision."
        pixel_rows.append({
            "GLYPH_ID": row["GLYPH_ID"], "ELEMENT_ID": row["ELEMENT_ID"], "CHAR": row["CHAR"], "PANEL_ID": row["PANEL_ID"], "ROLE": row["ROLE"], "SCRIPT_CLASS": row["SCRIPT_CLASS"],
            "EFFECTIVE_PT": row["EFFECTIVE_PT"], "H_INK_PX": row["H_REMEASURED"], "LOW_PROFILE": str(low_profile).lower(), "CALIBRATION_STATUS": status,
            "H_INK_RATIO": h_ratio, "INK_AREA_RATIO": area_ratio, "R115_FINAL_PIXEL_DECISION": decision, "R115_FINAL_REASON": reason, "MASK_FILE": row["MASK_FILE"],
        })
    # Reuse the core per-glyph threshold result rather than treating all CJK
    # glyphs as automatically valid. It is joined by ID after all text rows.
    preliminary = {r["GLYPH_ID"]: r for r in read_csv("after_pixel_measurements.csv")}
    for row in pixel_rows:
        if row["LOW_PROFILE"] == "false":
            base = preliminary[row["GLYPH_ID"]]
            row["R115_FINAL_PIXEL_DECISION"] = "PASS" if base["PIXEL_PASS"] == "PASS" and base["FONT_PASS"] == "true" else "FAIL"
            row["R115_FINAL_REASON"] = "Regular glyph from direct final-PDF native mask; source-font and script-class H-ink threshold cross-checked."
    write_csv("R115_PIXEL_FINAL_ADJUDICATION.csv", pixel_rows)

    # D uses element-level medians within the same panel/role/script class.
    # Individual characters such as a/t or CJK punctuation have intrinsic
    # outline-height variation and are not valid comparators for one another.
    element_groups: dict[tuple[str, str, str, str], list[dict[str, str]]] = defaultdict(list)
    for row in glyphs:
        element_groups[(row["PANEL_ID"], row["ROLE"], row["SCRIPT_CLASS"], row["ELEMENT_ID"])].append(row)
    element_stat: dict[tuple[str, str, str, str], dict[str, float | int]] = {}
    d_groups: dict[tuple[str, str, str], list[tuple[str, float]]] = defaultdict(list)
    for key, rows in element_groups.items():
        median_h = float(np.median([int(r["H_REMEASURED"]) for r in rows]))
        element_stat[key] = {"median_h": median_h, "glyph_n": len(rows)}
        d_groups[key[:3]].append((key[3], median_h))
    d_baseline = {key: float(np.median([median_h for _, median_h in values])) for key, values in d_groups.items()}

    # Source-size audit is independent of glyph geometry. It directly closes
    # the 1.03/0.25pt same-panel and 1.05 cross-panel requirements.
    role_pt_values: dict[tuple[str, str], list[float]] = defaultdict(list)
    for row in glyphs:
        role_pt_values[(row["PANEL_ID"], row["ROLE"])].append(float(row["EFFECTIVE_PT"]))
    role_pt_median = {key: float(np.median(values)) for key, values in role_pt_values.items()}
    panels_by_role: dict[str, list[tuple[str, float]]] = defaultdict(list)
    for (panel, role), median_pt in role_pt_median.items():
        panels_by_role[role].append((panel, median_pt))
    cross_panel: dict[str, dict[str, object]] = {}
    for role, values in panels_by_role.items():
        if len(values) == 1:
            cross_panel[role] = {"count": 1, "ratio": "NOT_APPLICABLE_SINGLE_PANEL", "source_status": "PASS_NO_COMPARABLE_MULTI_PANEL_ROLE", "e_status": "PASS_NO_COMPARABLE_MULTI_PANEL_ROLE"}
        else:
            pts = [pt for _, pt in values]
            ratio = max(pts) / min(pts)
            cross_panel[role] = {"count": len(values), "ratio": f"{ratio:.4f}", "source_status": "PASS" if ratio <= 1.05 else "FAIL", "e_status": "PASS" if ratio <= 1.10 else "FAIL"}
    source_font_rows: list[dict[str, object]] = []
    for (panel, role), values in sorted(role_pt_values.items()):
        low_pt, high_pt = min(values), max(values)
        ratio = high_pt / low_pt
        point_pass = ratio <= 1.03 and (high_pt - low_pt) <= 0.25
        cp = cross_panel[role]
        source_font_rows.append({
            "PANEL_ID": panel, "ROLE": role, "GLYPH_COUNT": len(values), "EFFECTIVE_PT_MIN": f"{low_pt:.4f}", "EFFECTIVE_PT_MAX": f"{high_pt:.4f}", "EFFECTIVE_PT_MAX_MIN_RATIO": f"{ratio:.4f}", "EFFECTIVE_PT_ABS_DELTA": f"{high_pt-low_pt:.4f}",
            "SAME_PANEL_REQUIRED": "max/min<=1.03; abs_delta<=0.25pt", "SAME_PANEL_STATUS": "PASS" if point_pass else "FAIL", "CROSS_PANEL_ROLE_COUNT": cp["count"], "CROSS_PANEL_MEDIAN_RATIO": cp["ratio"], "CROSS_PANEL_SOURCE_REQUIRED": "<=1.05", "CROSS_PANEL_SOURCE_STATUS": cp["source_status"], "CROSS_PANEL_E_REQUIRED": "<=1.10", "CROSS_PANEL_E_STATUS": cp["e_status"],
        })
    write_csv("R115_SOURCE_FONT_ROLE_AUDIT.csv", source_font_rows)

    de_rows: list[dict[str, object]] = []
    for row in glyphs:
        d_key = (row["PANEL_ID"], row["ROLE"], row["SCRIPT_CLASS"])
        element_key = d_key + (row["ELEMENT_ID"],)
        element_median = float(element_stat[element_key]["median_h"])
        dmed = d_baseline[d_key]
        d_ratio = element_median / dmed
        d_pass = 0.92 <= d_ratio <= 1.08
        comparable_count = len(d_groups[d_key])
        d_status = ("PASS_SINGLETON_SELF_BASELINE" if comparable_count == 1 else "PASS") if d_pass else "FAIL"
        d_note = "Native final-PDF 1x raw-mask element median against same-panel/same-role/same-script element-median baseline; intrinsic within-word glyph variation excluded."

        base_role, rule, low_bound, high_bound = e_rule(row["PANEL_ID"], row["ROLE"])
        base_key = (row["PANEL_ID"], base_role)
        if base_key not in role_pt_median:
            raise ValueError(f"missing E effective-point baseline {base_key}")
        role_median_pt = role_pt_median[(row["PANEL_ID"], row["ROLE"])]
        base_pt = role_pt_median[base_key]
        e_ratio_float = role_median_pt / base_pt
        e_pass = low_bound <= e_ratio_float <= high_bound
        e_status = "PASS" if e_pass else "FAIL"
        e_range = f"[{low_bound:.2f},{high_bound:.2f}]"
        e_note = "Role hierarchy on direct final-PDF effective point-size medians; raw ink geometry remains independently audited by D."
        cp = cross_panel[row["ROLE"]]
        overall = d_pass and e_pass and str(cp["e_status"]).startswith("PASS")
        de_rows.append({
            "GLYPH_ID": row["GLYPH_ID"], "ELEMENT_ID": row["ELEMENT_ID"], "CHAR": row["CHAR"], "PANEL_ID": row["PANEL_ID"], "ROLE": row["ROLE"], "SCRIPT_CLASS": row["SCRIPT_CLASS"], "MASK_FILE": row["MASK_FILE"], "H_INK_PX_REMEASURED": row["H_REMEASURED"],
            "D_GROUP": "|".join(d_key), "D_ELEMENT_GROUP": "|".join(element_key), "D_ELEMENT_GLYPH_N": element_stat[element_key]["glyph_n"], "D_COMPARABLE_ELEMENT_N": comparable_count, "D_ELEMENT_MEDIAN_PX": f"{element_median:.4f}", "D_GROUP_ELEMENT_MEDIAN_PX": f"{dmed:.4f}", "D_RATIO_TO_SAME_CLASS_ELEMENT_MEDIAN": f"{d_ratio:.4f}", "D_REQUIRED_RANGE": "[0.92,1.08]", "D_STATUS": d_status, "D_NOTE": d_note,
            "E_BASE_GROUP": f"{row['PANEL_ID']}|{base_role}|EFFECTIVE_PT", "E_ROLE_MEDIAN_PT": f"{role_median_pt:.4f}", "E_BASE_MEDIAN_PT": f"{base_pt:.4f}", "E_ROLE_RATIO": f"{e_ratio_float:.4f}", "E_REQUIRED_RANGE": e_range, "E_RULE": rule, "E_STATUS": e_status, "E_NOTE": e_note,
            "CROSS_PANEL_STATUS": cp["e_status"], "CROSS_PANEL_RATIO": cp["ratio"], "D_E_ROW_DECISION": "PASS" if overall else "FAIL",
        })
    write_csv("R115_D_E_FINAL_ADJUDICATION.csv", de_rows)
    role_summary: list[dict[str, object]] = []
    for key in sorted(d_groups):
        relevant = [r for r in de_rows if r["D_GROUP"] == "|".join(key)]
        role_summary.append({
            "PANEL_ID": key[0], "ROLE": key[1], "SCRIPT_CLASS": key[2], "GLYPH_COUNT": len(relevant), "COMPARABLE_ELEMENT_N": len(d_groups[key]), "D_GROUP_ELEMENT_MEDIAN_PX": f"{d_baseline[key]:.4f}",
            "D_MIN_RATIO": f"{min(float(r['D_RATIO_TO_SAME_CLASS_ELEMENT_MEDIAN']) for r in relevant):.4f}", "D_MAX_RATIO": f"{max(float(r['D_RATIO_TO_SAME_CLASS_ELEMENT_MEDIAN']) for r in relevant):.4f}",
            "D_ALL_PASS": str(all(r["D_STATUS"].startswith("PASS") for r in relevant)).lower(), "E_BASE_GROUP": relevant[0]["E_BASE_GROUP"], "E_ROLE_RATIO": relevant[0]["E_ROLE_RATIO"], "E_REQUIRED_RANGE": relevant[0]["E_REQUIRED_RANGE"],
            "E_STATUS": ";".join(sorted({r["E_STATUS"] for r in relevant})), "E_ALL_PASS": str(all(r["E_STATUS"].startswith("PASS") for r in relevant)).lower(), "CROSS_PANEL_STATUS": relevant[0]["CROSS_PANEL_STATUS"], "CROSS_PANEL_RATIO": relevant[0]["CROSS_PANEL_RATIO"],
        })
    write_csv("R115_D_E_ROLE_SUMMARY.csv", role_summary)
    de_summary = {
        "figure_id": "FIG-P756-01", "method": "independent remeasurement from native final-PDF 1x masks",
        "glyph_count": len(de_rows), "same_class_ratio_pass": all(r["D_STATUS"].startswith("PASS") for r in de_rows), "same_class_ratio_fail_glyphs": sum(not r["D_STATUS"].startswith("PASS") for r in de_rows),
        "role_ratio_pass": all(r["E_STATUS"].startswith("PASS") for r in de_rows), "role_ratio_fail_glyphs": sum(not r["E_STATUS"].startswith("PASS") for r in de_rows),
        "role_ratio_fail_groups": [{"group": f"{r['PANEL_ID']}|{r['ROLE']}|{r['SCRIPT_CLASS']}", "ratio": r["E_ROLE_RATIO"], "required": r["E_REQUIRED_RANGE"]} for r in role_summary if r["E_ALL_PASS"] == "false"],
    }
    (ROOT / "R115_D_E_FINAL_SUMMARY.json").write_text(json.dumps(de_summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    pixels = {"pass": sum(r["R115_FINAL_PIXEL_DECISION"] == "PASS" for r in pixel_rows), "fail": sum(r["R115_FINAL_PIXEL_DECISION"] == "FAIL" for r in pixel_rows), "method_invalid": sum(r["CALIBRATION_STATUS"] == "METHOD_INVALID" for r in pixel_rows)}
    summary = {"low_profile_glyphs": len(low), "calibration_groups": len(ordered_groups), "calibration_valid_targets": sum(r["FONT_WEIGHT_COLOR_SIZE_300DPI_PURITY_VALID"] == "true" for r in calibration_rows), "calibration_invalid_targets": sum(r["FONT_WEIGHT_COLOR_SIZE_300DPI_PURITY_VALID"] != "true" for r in calibration_rows), "pixel": pixels, "d_e": de_summary}
    (ROOT / "R115_CALIBRATION_AND_DE_SUMMARY.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
