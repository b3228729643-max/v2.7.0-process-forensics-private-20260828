from __future__ import annotations

import csv
import hashlib
import itertools
import json
from pathlib import Path

import pdfplumber
from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\STRICT_R5_SA2_LEGEND_SEGMENT_PATCH_R115_DIRECT_BUILD_20260828")
PDF = ROOT / "build" / "v260_FIG-P126-01_standalone.pdf"
REVIEW = ROOT / "review"
RENDER = REVIEW / "render"
MACHINE = REVIEW / "machine"
ROI = REVIEW / "roi"
PDF_SHA = "58BA180DBC92ED6DFEECCA2D77FE021C55B9D9B5DE0A1F6DB5F4B8D7316CAD06"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest().upper()


def bbox_from_obj(obj: dict) -> tuple[float, float, float, float]:
    return (float(obj["x0"]), float(obj["top"]), float(obj["x1"]), float(obj["bottom"]))


def intersection(a, b):
    x0, y0 = max(a[0], b[0]), max(a[1], b[1])
    x1, y1 = min(a[2], b[2]), min(a[3], b[3])
    if x1 <= x0 or y1 <= y0:
        return 0.0, 0.0, 0.0
    return x1 - x0, y1 - y0, (x1 - x0) * (y1 - y0)


def crop_box_px(box_pt, scale, pad_px, image_size):
    x0 = max(0, int(box_pt[0] * scale) - pad_px)
    y0 = max(0, int(box_pt[1] * scale) - pad_px)
    x1 = min(image_size[0], int(box_pt[2] * scale + 0.999) + pad_px)
    y1 = min(image_size[1], int(box_pt[3] * scale + 0.999) + pad_px)
    return (x0, y0, x1, y1)


def nonwhite_bbox(image: Image.Image, threshold: int = 248):
    gray = image.convert("L")
    mask = gray.point(lambda value: 255 if value < threshold else 0)
    return mask.getbbox()


def write_csv(path: Path, rows: list[dict], fields: list[str]):
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main():
    if PDF.stat().st_size != 33952 or sha256(PDF) != PDF_SHA:
        raise RuntimeError("PDF identity mismatch")
    MACHINE.mkdir(parents=True, exist_ok=False)
    ROI.mkdir(parents=True, exist_ok=False)

    with pdfplumber.open(PDF) as document:
        if len(document.pages) != 1:
            raise RuntimeError("expected one page")
        page = document.pages[0]
        raw: list[dict] = []
        counters = {"char": 0, "line": 0, "curve": 0, "rect": 0}
        for kind, objects in (
            ("char", page.chars),
            ("line", page.lines),
            ("curve", page.curves),
            ("rect", page.rects),
        ):
            for obj in objects:
                counters[kind] += 1
                ident = f"{kind[0].upper()}{counters[kind]:03d}"
                x0, top, x1, bottom = bbox_from_obj(obj)
                raw.append(
                    {
                        "object_id": ident,
                        "kind": kind,
                        "x0_pt": f"{x0:.6f}",
                        "top_pt": f"{top:.6f}",
                        "x1_pt": f"{x1:.6f}",
                        "bottom_pt": f"{bottom:.6f}",
                        "width_pt": f"{x1-x0:.6f}",
                        "height_pt": f"{bottom-top:.6f}",
                        "text": obj.get("text", ""),
                        "stroking_color": repr(obj.get("stroking_color")),
                        "non_stroking_color": repr(obj.get("non_stroking_color")),
                    }
                )

        fields = list(raw[0].keys())
        write_csv(MACHINE / "RAW_VISIBLE_OBJECTS.csv", raw, fields)
        pairs: list[dict] = []
        for index, (left, right) in enumerate(itertools.combinations(raw, 2), 1):
            a = tuple(float(left[k]) for k in ("x0_pt", "top_pt", "x1_pt", "bottom_pt"))
            b = tuple(float(right[k]) for k in ("x0_pt", "top_pt", "x1_pt", "bottom_pt"))
            iw, ih, area = intersection(a, b)
            pairs.append(
                {
                    "pair_id": f"P{index:05d}",
                    "left_id": left["object_id"],
                    "right_id": right["object_id"],
                    "bbox_intersects": int(area > 0),
                    "intersection_width_pt": f"{iw:.6f}",
                    "intersection_height_pt": f"{ih:.6f}",
                    "intersection_area_pt2": f"{area:.6f}",
                }
            )
        write_csv(
            MACHINE / "RAW_ALL_UNORDERED_PAIRS.csv",
            pairs,
            ["pair_id", "left_id", "right_id", "bbox_intersects", "intersection_width_pt", "intersection_height_pt", "intersection_area_pt2"],
        )

        words = page.extract_words(keep_blank_chars=False, use_text_flow=True)
        legend_chars = [char for char in page.chars if float(char["top"]) > 240 and float(char["bottom"]) < 275]
        if not legend_chars:
            raise RuntimeError("legend characters not located")
        legend_pt = (
            max(0.0, min(float(c["x0"]) for c in legend_chars) - 35.0),
            min(float(c["top"]) for c in legend_chars) - 8.0,
            min(float(page.width), max(float(c["x1"]) for c in legend_chars) + 8.0),
            max(float(c["bottom"]) for c in legend_chars) + 8.0,
        )

    color = Image.open(RENDER / "full_page_300dpi.png").convert("RGB")
    gray = Image.open(RENDER / "full_page_300dpi_gray.png").convert("L")
    scale = color.width / 595.276
    ink_box = nonwhite_bbox(color)
    if ink_box is None:
        raise RuntimeError("empty rendered page")
    figure_box = (
        max(0, ink_box[0] - 30),
        max(0, ink_box[1] - 30),
        min(color.width, ink_box[2] + 30),
        min(color.height, ink_box[3] + 30),
    )
    color.crop(figure_box).save(ROI / "FIGURE_NATIVE300.png")
    gray.crop(figure_box).save(ROI / "FIGURE_GRAY_NATIVE300.png")

    legend_px = crop_box_px(legend_pt, scale, 8, color.size)
    legend_color = color.crop(legend_px)
    legend_gray = gray.crop(legend_px)
    legend_color.save(ROI / "LEGEND_NATIVE1X.png")
    legend_gray.save(ROI / "LEGEND_GRAY_NATIVE1X.png")
    legend_color.resize((legend_color.width * 8, legend_color.height * 8), Image.Resampling.NEAREST).save(ROI / "LEGEND_NEAREST8X.png")
    legend_gray.resize((legend_gray.width * 8, legend_gray.height * 8), Image.Resampling.NEAREST).save(ROI / "LEGEND_GRAY_NEAREST8X.png")

    overlay = color.copy()
    draw = ImageDraw.Draw(overlay)
    for obj in raw:
        box = tuple(float(obj[k]) for k in ("x0_pt", "top_pt", "x1_pt", "bottom_pt"))
        px = crop_box_px(box, scale, 0, overlay.size)
        draw.rectangle(px, outline=(220, 0, 170), width=1)
        draw.text((px[0], max(0, px[1] - 10)), obj["object_id"], fill=(140, 0, 100))
    overlay.crop(figure_box).save(ROI / "RAW_OBJECT_OVERLAY.png")

    bbox_candidates = sum(int(row["bbox_intersects"]) for row in pairs)
    summary = {
        "schema": "P126_R5_MACHINE_EVIDENCE_V1",
        "pdf_path": str(PDF),
        "pdf_bytes": PDF.stat().st_size,
        "pdf_sha256": PDF_SHA,
        "page_count": 1,
        "page_width_pt": 595.276,
        "page_height_pt": 841.89,
        "render_width_px_300dpi": color.width,
        "render_height_px_300dpi": color.height,
        "render_scale_px_per_pt": scale,
        "raw_counts": counters,
        "raw_visible_object_count": len(raw),
        "raw_unordered_pair_count": len(pairs),
        "raw_bbox_candidate_count": bbox_candidates,
        "nonwhite_page_bbox_px": list(ink_box),
        "figure_crop_bbox_px": list(figure_box),
        "legend_bbox_pt": list(legend_pt),
        "legend_bbox_px": list(legend_px),
        "extracted_words": words,
        "manual_fields_generated": 0,
    }
    (MACHINE / "MACHINE_SUMMARY.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
