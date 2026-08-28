from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path

import fitz
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P662-01\sa2_r112_r168_readonly_adjudication_v1")
PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r112_fullbook\main_full.pdf")
SOURCE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C05\fig_v5_c05_gamma_normalization.tex")
GOAL = Path(r"D:\Users\ASUS\Desktop\机器学习\GOAL.md")
PAGE_ONE_BASED = 710
PAGE_INDEX = PAGE_ONE_BASED - 1
SCALE_300 = 300.0 / 72.0
SCALE_200 = 200.0 / 72.0
FIG_CAP_RECT = fitz.Rect(80.0, 250.0, 525.0, 430.0)
FIG_ONLY_RECT = fitz.Rect(80.0, 250.0, 525.0, 394.5)
CAPTION_RECT = fitz.Rect(80.0, 394.0, 525.0, 430.0)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def ticks(path: Path) -> int:
    # NTFS/FILETIME epoch is 1601-01-01; Unix epoch is 11644473600 seconds later.
    return int(path.stat().st_mtime_ns // 100 + 116444736000000000)


def save_direct_render(page: fitz.Page, rect: fitz.Rect, dpi: int, target: Path) -> None:
    pix = page.get_pixmap(matrix=fitz.Matrix(dpi / 72.0, dpi / 72.0), clip=rect, alpha=False)
    pix.save(str(target))


def px_rect(pdf_rect: fitz.Rect, clip: fitz.Rect, scale: float) -> tuple[int, int, int, int]:
    return (
        int(round((pdf_rect.x0 - clip.x0) * scale)),
        int(round((pdf_rect.y0 - clip.y0) * scale)),
        int(round((pdf_rect.x1 - clip.x0) * scale)),
        int(round((pdf_rect.y1 - clip.y0) * scale)),
    )


def bbox_gap(a: fitz.Rect, b: fitz.Rect) -> tuple[float, float, float, float]:
    dx = max(b.x0 - a.x1, a.x0 - b.x1, 0.0)
    dy = max(b.y0 - a.y1, a.y0 - b.y1, 0.0)
    gap = math.hypot(dx, dy)
    ix = max(0.0, min(a.x1, b.x1) - max(a.x0, b.x0))
    iy = max(0.0, min(a.y1, b.y1) - max(a.y0, b.y0))
    return dx, dy, gap, ix * iy


def text_ink_height(gray: Image.Image, bbox: tuple[int, int, int, int]) -> tuple[int, float, int]:
    x0, y0, x1, y1 = bbox
    x0 = max(0, min(gray.width - 1, x0))
    y0 = max(0, min(gray.height - 1, y0))
    x1 = max(x0 + 1, min(gray.width, x1))
    y1 = max(y0 + 1, min(gray.height, y1))
    crop = gray.crop((x0, y0, x1, y1))
    # Estimate the local background from a narrow ring just outside the tight PDF text bbox.
    ex0, ey0 = max(0, x0 - 4), max(0, y0 - 4)
    ex1, ey1 = min(gray.width, x1 + 4), min(gray.height, y1 + 4)
    outer = gray.crop((ex0, ey0, ex1, ey1))
    vals = list(outer.getdata())
    bg = float(sorted(vals)[len(vals) // 2]) if vals else 255.0
    rows = []
    count = 0
    pix = crop.load()
    for y in range(crop.height):
        occupied = False
        for x in range(crop.width):
            if abs(float(pix[x, y]) - bg) >= 20.0:
                occupied = True
                count += 1
        if occupied:
            rows.append(y)
    height = (rows[-1] - rows[0] + 1) if rows else 0
    return height, bg, count


def main() -> None:
    ROOT.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(PDF)
    page = doc[PAGE_INDEX]

    identities = []
    for role, path in (("official_r112_pdf", PDF), ("current_figure_source", SOURCE), ("active_root_goal", GOAL)):
        identities.append(
            {
                "role": role,
                "path": str(path),
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
                "last_write_time_utc_ticks": ticks(path),
            }
        )
    (ROOT / "frozen_input_identities.json").write_text(
        json.dumps(identities, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    locator = {
        "uid": "FIG-P662-01",
        "pdf_page_one_based": PAGE_ONE_BASED,
        "printed_page": 697,
        "figure_number": "34.5",
        "source_label": "fig:V5-C05-gamma-normalization",
        "caption_prefix": "独立且具有共同率参数的 Gamma 变量除以其总和后得到 Dirichlet 随机向量",
        "figure_caption_rect_pdf_pt": list(FIG_CAP_RECT),
        "locator_method": "current source caption/label matched against fresh pdftotext extraction from frozen R112 PDF",
    }
    (ROOT / "pdf_locator.json").write_text(json.dumps(locator, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    save_direct_render(page, FIG_CAP_RECT, 300, ROOT / "figure_caption_native_300dpi.png")
    save_direct_render(page, FIG_ONLY_RECT, 300, ROOT / "figure_only_native_300dpi.png")
    save_direct_render(page, CAPTION_RECT, 300, ROOT / "caption_native_300dpi.png")
    fig_img = Image.open(ROOT / "figure_caption_native_300dpi.png").convert("RGB")
    fig_img.convert("L").save(ROOT / "figure_caption_grayscale_native_300dpi.png")
    gray = fig_img.convert("L")

    objects = [
        ("O01", "SEMANTIC_CARD_GROUP", "Gamma input stack", (85.725, 283.049, 185.071, 392.169), "three rounded cards and formulas; vertical ellipsis; independence/common-rate note"),
        ("O02", "BADGE", "step badge 1", (127.461, 260.797, 143.335, 276.671), "filled circle and numeral 1"),
        ("O03", "SEMANTIC_CARD", "total S block", (197.761, 310.592, 271.463, 341.965), "rounded border, 总量 label, summation formula"),
        ("O04", "BADGE", "step badge 2", (226.675, 285.176, 242.549, 301.050), "filled circle and numeral 2"),
        ("O05", "SEMANTIC_CARD", "divide-by-S operator", (296.975, 312.105, 325.322, 340.452), "gold circle, division sign, S"),
        ("O06", "BADGE", "step badge 3", (303.211, 285.176, 319.085, 301.050), "filled circle and numeral 3"),
        ("O07", "SEMANTIC_CARD", "normalized proportion block", (336.944, 310.688, 419.150, 341.869), "rounded border, 比例 label, Theta_k=Y_k/S"),
        ("O08", "SEMANTIC_CARD", "Dirichlet result block", (431.622, 310.688, 516.663, 341.869), "rounded border, Dirichlet law and simplex sum"),
        ("O09", "ANNOTATION_ICON", "simplex icon and label", (461.387, 280.640, 519.990, 302.750), "triangle outline, interior point, 单纯形点 label"),
        ("O10", "SEMANTIC_CARD", "independence/total-law result", (261.541, 363.980, 400.441, 392.326), "rounded border, S independent of Theta, Gamma total law"),
        ("O11", "SEMANTIC_CARD", "K=2 Beta special case", (413.197, 363.980, 520.915, 392.326), "gold rounded border and two-line Beta statement"),
        ("O12", "LINE_ARROW", "Y1 to total connector", (182.640, 295.097, 196.760, 316.750), "blue line and arrowhead"),
        ("O13", "LINE_ARROW", "Y2 to total connector", (182.627, 323.443, 196.221, 326.592), "blue line and arrowhead"),
        ("O14", "LINE_ARROW", "YK to total connector", (185.071, 335.905, 196.950, 363.980), "blue line and arrowhead"),
        ("O15", "LINE_ARROW", "total to divide connector", (271.463, 325.059, 295.412, 327.497), "blue line and arrowhead"),
        ("O16", "LINE_ARROW", "divide to proportion connector", (325.322, 325.059, 335.381, 327.497), "blue line and arrowhead"),
        ("O17", "LINE_ARROW", "proportion to Dirichlet connector", (419.150, 325.059, 430.059, 327.497), "blue line and arrowhead"),
        ("O18", "AUX_CONNECTOR", "total to independence evidence path", (234.612, 342.313, 291.305, 363.980), "gray dashed orthogonal path"),
        ("O19", "AUX_CONNECTOR", "proportion to independence evidence path", (370.677, 342.218, 378.047, 363.980), "gray dashed orthogonal path"),
        ("O20", "CAPTION", "figure number and two-line caption", (87.477, 395.421, 519.128, 423.068), "bold 图34.5 lead and complete current caption"),
    ]
    with (ROOT / "visible_object_inventory_machine.csv").open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["OBJECT_ID", "SEMANTIC_CLASS", "LABEL", "PDF_X0_PT", "PDF_Y0_PT", "PDF_X1_PT", "PDF_Y1_PT", "COMPLETE_VISIBLE_SUBCOMPONENTS"])
        for oid, cls, label, bbox, components in objects:
            w.writerow([oid, cls, label, *[f"{x:.3f}" for x in bbox], components])

    with (ROOT / "all_unordered_object_pairs_machine.csv").open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["PAIR_ID", "OBJECT_A", "OBJECT_B", "DX_GAP_PX_300", "DY_GAP_PX_300", "EUCLIDEAN_BBOX_GAP_PX_300", "BBOX_INTERSECTION_AREA_PX2_300", "MACHINE_GEOMETRY_CLASS"])
        pair_n = 0
        for i in range(len(objects)):
            for j in range(i + 1, len(objects)):
                pair_n += 1
                ra, rb = fitz.Rect(objects[i][3]), fitz.Rect(objects[j][3])
                dx, dy, gap, overlap = bbox_gap(ra, rb)
                geom = "BBOX_INTERSECTS_OR_TOUCHES" if overlap > 0 or gap == 0 else "BBOX_SEPARATED"
                w.writerow([
                    f"P{pair_n:03d}", objects[i][0], objects[j][0],
                    f"{dx * SCALE_300:.3f}", f"{dy * SCALE_300:.3f}", f"{gap * SCALE_300:.3f}",
                    f"{overlap * SCALE_300 * SCALE_300:.3f}", geom,
                ])

    colors = [
        "#d73027", "#4575b4", "#1a9850", "#984ea3", "#ff7f00",
        "#a65628", "#e7298a", "#66a61e", "#e6ab02", "#7570b3",
    ]
    overlay = fig_img.convert("RGBA")
    draw = ImageDraw.Draw(overlay, "RGBA")
    try:
        font = ImageFont.truetype(r"C:\Windows\Fonts\arial.ttf", 18)
    except OSError:
        font = ImageFont.load_default()
    for idx, (oid, cls, label, bbox, components) in enumerate(objects):
        r = px_rect(fitz.Rect(bbox), FIG_CAP_RECT, SCALE_300)
        color = colors[idx % len(colors)]
        draw.rectangle(r, outline=color, width=4)
        tx, ty = max(0, r[0]), max(0, r[1] - 20)
        draw.rectangle((tx, ty, tx + 50, ty + 19), fill=(255, 255, 255, 220))
        draw.text((tx + 2, ty), oid, fill=color, font=font)
    overlay.convert("RGB").save(ROOT / "semantic_object_overlay_native_300dpi.png")

    spans = []
    raw = page.get_text("dict", clip=FIG_CAP_RECT)
    for block in raw.get("blocks", []):
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                text = span.get("text", "")
                if not text.strip():
                    continue
                r = fitz.Rect(span["bbox"])
                if r.intersects(FIG_CAP_RECT):
                    spans.append((text, span["font"], float(span["size"]), r))
    spans.sort(key=lambda x: (round(x[3].y0, 2), x[3].x0))
    text_overlay = fig_img.convert("RGBA")
    text_draw = ImageDraw.Draw(text_overlay, "RGBA")
    text_rows = []
    for idx, (text, font_name, size, rect) in enumerate(spans, start=1):
        eid = f"E{idx:03d}"
        pr = px_rect(rect, FIG_CAP_RECT, SCALE_300)
        h_ink, bg, ink_count = text_ink_height(gray, pr)
        cps = " ".join(f"U+{ord(ch):04X}" for ch in text if not ch.isspace())
        suspicious = ";".join(
            token for token, present in (
                ("U+FFFD_REPLACEMENT", "\ufffd" in text),
                ("U+25A1_WHITE_SQUARE", "\u25a1" in text),
                ("U+25A0_BLACK_SQUARE", "\u25a0" in text),
            ) if present
        )
        text_rows.append([
            eid, text, font_name, f"{size:.3f}",
            *[f"{v:.3f}" for v in rect], *pr,
            h_ink, f"{bg:.1f}", ink_count, cps, suspicious,
        ])
        color = colors[(idx - 1) % len(colors)]
        text_draw.rectangle(pr, outline=color, width=2)
        text_draw.text((max(0, pr[0]), max(0, pr[1] - 17)), eid, fill=color, font=font)
    with (ROOT / "text_spans_codepoints_and_ink_machine.csv").open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow([
            "ELEMENT_ID", "PDF_EXTRACTED_TEXT", "EMBEDDED_FONT", "PDF_FONT_SIZE_PT",
            "PDF_X0_PT", "PDF_Y0_PT", "PDF_X1_PT", "PDF_Y1_PT",
            "CROP_X0_PX", "CROP_Y0_PX", "CROP_X1_PX", "CROP_Y1_PX",
            "MACHINE_H_INK_PX", "MACHINE_LOCAL_BG_LUMA", "MACHINE_FOREGROUND_PIXEL_COUNT",
            "EXTRACTED_CODEPOINTS", "MACHINE_SUSPICIOUS_CODEPOINT_TOKENS",
        ])
        w.writerows(text_rows)
    text_overlay.convert("RGB").save(ROOT / "text_measurement_overlay_native_300dpi.png")
    extracted_lines = []
    for block in raw.get("blocks", []):
        for line in block.get("lines", []):
            s = "".join(span.get("text", "") for span in line.get("spans", []))
            if s.strip():
                extracted_lines.append(s)
    (ROOT / "pdf_extracted_figure_caption_text.txt").write_text("\n".join(extracted_lines) + "\n", encoding="utf-8")

    risk_rois = [
        ("R01_fan_in_sum_west", fitz.Rect(180, 290, 201, 367), "three fan-in connectors, arrowheads, and sum-card west border"),
        ("R02_simplex_icon_label", fitz.Rect(455, 276, 524, 306), "triangle, point, label, and nearby result card"),
        ("R03_sum_aux_endpoint", fitz.Rect(228, 337, 298, 369), "sum-card south edge, dashed path, independence-card endpoint"),
        ("R04_ratio_aux_endpoint", fitz.Rect(365, 337, 405, 369), "ratio-card south edge, dashed path, independence-card endpoint"),
        ("R05_independence_caption_gap", fitz.Rect(250, 358, 406, 426), "independence result, lower border, and caption clearance"),
        ("R06_beta_caption_gap", fitz.Rect(405, 358, 525, 426), "Beta result, lower border, and caption clearance"),
        ("R07_independence_glyphs", fitz.Rect(270, 368, 397, 389), "double-perpendicular independence relation and Gamma total law"),
        ("R08_main_chain_arrowheads", fitz.Rect(268, 307, 435, 345), "main-chain border contacts and arrowheads"),
    ]
    roi_rows = []
    for rid, rpdf, purpose in risk_rois:
        rp = px_rect(rpdf, FIG_CAP_RECT, SCALE_300)
        crop = fig_img.crop(rp)
        native_name = f"risk_{rid}_native1x_300dpi.png"
        nearest_name = f"risk_{rid}_nearest8x.png"
        crop.save(ROOT / native_name)
        crop.resize((crop.width * 8, crop.height * 8), Image.Resampling.NEAREST).save(ROOT / nearest_name)
        roi_rows.append([rid, *[f"{v:.3f}" for v in rpdf], *rp, crop.width, crop.height, native_name, nearest_name, purpose])
    with (ROOT / "risk_roi_index_machine.csv").open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow([
            "RISK_ID", "PDF_X0_PT", "PDF_Y0_PT", "PDF_X1_PT", "PDF_Y1_PT",
            "CROP_X0_PX", "CROP_Y0_PX", "CROP_X1_PX", "CROP_Y1_PX", "NATIVE_WIDTH_PX", "NATIVE_HEIGHT_PX",
            "NATIVE1X_FILE", "NEAREST8X_FILE", "MACHINE_PURPOSE",
        ])
        w.writerows(roi_rows)

    full200 = Image.open(ROOT / "page_710_full_200dpi.png").convert("RGBA")
    d200 = ImageDraw.Draw(full200, "RGBA")
    page_box = tuple(int(round(v * SCALE_200)) for v in FIG_CAP_RECT)
    d200.rectangle(page_box, outline=(215, 48, 39, 255), width=6)
    d200.rectangle((page_box[0], max(0, page_box[1] - 36), page_box[0] + 330, page_box[1] - 2), fill=(255, 255, 255, 220))
    d200.text((page_box[0] + 4, max(0, page_box[1] - 34)), "FIG-P662-01 figure+caption", fill=(215, 48, 39, 255), font=font)
    full200.convert("RGB").save(ROOT / "page_710_integration_overlay_200dpi.png")

    metadata = {
        "pdf_page_count": doc.page_count,
        "page_rect_pdf_pt": list(page.rect),
        "direct_render_dpi": 300,
        "figure_caption_crop_pdf_pt": list(FIG_CAP_RECT),
        "figure_only_crop_pdf_pt": list(FIG_ONLY_RECT),
        "caption_crop_pdf_pt": list(CAPTION_RECT),
        "visible_object_count": len(objects),
        "unordered_pair_count": len(objects) * (len(objects) - 1) // 2,
        "text_span_count": len(spans),
        "risk_roi_count": len(risk_rois),
        "machine_fields_only": "No reviewer, decision, note, verdict, PASS/FAIL, or manual boolean fields were generated by this script.",
    }
    (ROOT / "machine_evidence_metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
