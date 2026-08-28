import csv
import hashlib
import json
import math
from pathlib import Path

import pdfplumber
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\STRICT_R7_SA2_ABSOLUTE_LEGEND_KEY_PATCH_R115_DIRECT_BUILD_20260828")
PDF = ROOT / "build" / "v260_FIG-P126-01_standalone.pdf"
RENDER = ROOT / "render"
MACHINE = ROOT / "machine"
MACHINE.mkdir(parents=True, exist_ok=True)


def f6(value):
    return f"{float(value):.6f}"


def bbox_clearance(a, b):
    dx = max(float(a[0]) - float(b[2]), float(b[0]) - float(a[2]), 0.0)
    dy = max(float(a[1]) - float(b[3]), float(b[1]) - float(a[3]), 0.0)
    return math.hypot(dx, dy)


def bbox_overlap(a, b):
    w = max(0.0, min(float(a[2]), float(b[2])) - max(float(a[0]), float(b[0])))
    h = max(0.0, min(float(a[3]), float(b[3])) - max(float(a[1]), float(b[1])))
    return w, h, w * h


def visible_color(value):
    if value is None or value is False:
        return ""
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


with pdfplumber.open(PDF) as document:
    page = document.pages[0]
    page_w = float(page.width)
    page_h = float(page.height)
    objects = []

    for i, item in enumerate(page.chars, 1):
        objects.append({
            "object_id": f"G{i:03d}", "object_type": "glyph", "source_index": i - 1,
            "text": item.get("text", ""), "x0": float(item["x0"]), "top": float(item["top"]),
            "x1": float(item["x1"]), "bottom": float(item["bottom"]),
            "stroke": visible_color(item.get("stroking_color")),
            "fill": visible_color(item.get("non_stroking_color")),
            "linewidth": "", "font": item.get("fontname", ""), "font_size": item.get("size", ""),
        })
    for prefix, kind, collection in (
        ("L", "line", page.lines), ("R", "rect", page.rects), ("C", "curve", page.curves)
    ):
        for i, item in enumerate(collection, 1):
            objects.append({
                "object_id": f"{prefix}{i:03d}", "object_type": kind, "source_index": i - 1,
                "text": "", "x0": float(item["x0"]), "top": float(item["top"]),
                "x1": float(item["x1"]), "bottom": float(item["bottom"]),
                "stroke": visible_color(item.get("stroking_color")),
                "fill": visible_color(item.get("non_stroking_color")),
                "linewidth": item.get("linewidth", ""), "font": "", "font_size": "",
            })

for item in objects:
    item["width"] = float(item["x1"]) - float(item["x0"])
    item["height"] = float(item["bottom"]) - float(item["top"])

object_fields = [
    "object_id", "object_type", "source_index", "text", "x0", "top", "x1", "bottom",
    "width", "height", "stroke", "fill", "linewidth", "font", "font_size",
]
with (MACHINE / "MACHINE_OBJECTS.csv").open("w", newline="", encoding="utf-8-sig") as handle:
    writer = csv.DictWriter(handle, fieldnames=object_fields)
    writer.writeheader()
    for item in objects:
        writer.writerow({key: f6(item[key]) if key in {"x0", "top", "x1", "bottom", "width", "height"} else item[key] for key in object_fields})

pairs = []
candidate_pairs = []
pair_index = 0
for left_index, left in enumerate(objects):
    a = (left["x0"], left["top"], left["x1"], left["bottom"])
    for right in objects[left_index + 1:]:
        pair_index += 1
        b = (right["x0"], right["top"], right["x1"], right["bottom"])
        ow, oh, oa = bbox_overlap(a, b)
        clearance = bbox_clearance(a, b)
        row = {
            "pair_id": f"P{pair_index:05d}", "left_id": left["object_id"], "right_id": right["object_id"],
            "left_type": left["object_type"], "right_type": right["object_type"],
            "bbox_overlap_width_pt": f6(ow), "bbox_overlap_height_pt": f6(oh),
            "bbox_overlap_area_pt2": f6(oa), "bbox_clearance_pt": f6(clearance),
        }
        pairs.append(row)
        if oa > 0.0 or clearance <= 1.5:
            candidate_pairs.append(row)

pair_fields = list(pairs[0].keys())
with (MACHINE / "MACHINE_ALL_PAIRS.csv").open("w", newline="", encoding="utf-8-sig") as handle:
    writer = csv.DictWriter(handle, fieldnames=pair_fields)
    writer.writeheader()
    writer.writerows(pairs)
with (MACHINE / "MACHINE_PAIR_CANDIDATES.csv").open("w", newline="", encoding="utf-8-sig") as handle:
    writer = csv.DictWriter(handle, fieldnames=pair_fields)
    writer.writeheader()
    writer.writerows(candidate_pairs)

page300 = Image.open(RENDER / "full_page_300.png").convert("RGB")
scale = page300.width / page_w
draw = ImageDraw.Draw(page300)
try:
    font = ImageFont.truetype("arial.ttf", 13)
except OSError:
    font = ImageFont.load_default()
for item in objects:
    x0, y0, x1, y1 = [round(v * scale) for v in (item["x0"], item["top"], item["x1"], item["bottom"])]
    color = (220, 30, 30) if item["object_type"] == "glyph" else (30, 90, 220)
    draw.rectangle((x0, y0, x1, y1), outline=color, width=2)
    draw.text((x0, max(0, y0 - 14)), item["object_id"], fill=color, font=font)
page300.save(RENDER / "object_overlay_300.png")

gray = Image.open(RENDER / "grayscale_300.png").convert("L")
gray_pixels = gray.load()
xs, ys = [], []
for y in range(gray.height):
    for x in range(gray.width):
        if gray_pixels[x, y] < 248:
            xs.append(x)
            ys.append(y)
ink_bbox = (min(xs), min(ys), max(xs) + 1, max(ys) + 1)
margin = 35
crop_bbox = (
    max(0, ink_bbox[0] - margin), max(0, ink_bbox[1] - margin),
    min(gray.width, ink_bbox[2] + margin), min(gray.height, ink_bbox[3] + margin),
)
Image.open(RENDER / "full_page_300.png").crop(crop_bbox).save(RENDER / "figure_native300.png")
Image.open(RENDER / "grayscale_300.png").crop(crop_bbox).save(RENDER / "figure_grayscale_native300.png")
Image.open(RENDER / "object_overlay_300.png").crop(crop_bbox).save(RENDER / "object_overlay_native300.png")


def crop_pdf_box(image, box_pt, pad_px, output_name):
    box = (
        max(0, round(box_pt[0] * scale) - pad_px), max(0, round(box_pt[1] * scale) - pad_px),
        min(image.width, round(box_pt[2] * scale) + pad_px), min(image.height, round(box_pt[3] * scale) + pad_px),
    )
    crop = image.crop(box)
    crop.save(RENDER / output_name)
    crop.resize((crop.width * 8, crop.height * 8), Image.Resampling.NEAREST).save(RENDER / output_name.replace("native1x", "nearest8x"))
    return box


color300 = Image.open(RENDER / "full_page_300.png").convert("RGB")
x1_box = crop_pdf_box(color300, (245.5, 227.0, 266.8, 237.0), 16, "legend_x1_native1x.png")
x2_box = crop_pdf_box(color300, (299.8, 227.0, 321.2, 237.0), 16, "legend_x2_native1x.png")
crop_pdf_box(color300, (205.0, 65.0, 405.0, 214.0), 20, "plot_native1x.png")
crop_pdf_box(color300, (215.0, 78.0, 300.0, 136.0), 20, "trajectory_left_native1x.png")
crop_pdf_box(color300, (265.0, 108.0, 323.0, 154.0), 20, "trajectory_right_native1x.png")


def horizontal_runs(image_path, target_y_fraction=0.5):
    image = Image.open(image_path).convert("RGB")
    center = int(round((image.height - 1) * target_y_fraction))
    band = range(max(0, center - 5), min(image.height, center + 6))
    active = []
    for x in range(image.width):
        is_ink = False
        for y in band:
            r, g, b = image.getpixel((x, y))
            if min(r, g, b) < 225 and (max(r, g, b) - min(r, g, b) > 8 or max(r, g, b) < 180):
                is_ink = True
                break
        active.append(is_ink)
    runs = []
    start = None
    for index, value in enumerate(active + [False]):
        if value and start is None:
            start = index
        elif not value and start is not None:
            runs.append([start, index - 1, index - start])
            start = None
    return {"width": image.width, "height": image.height, "band_center": center, "runs": runs}


legend = {
    "scale_px_per_pt": scale,
    "x1_crop_box_px": x1_box,
    "x2_crop_box_px": x2_box,
    "x1_runs": horizontal_runs(RENDER / "legend_x1_native1x.png"),
    "x2_runs": horizontal_runs(RENDER / "legend_x2_native1x.png"),
}
with (MACHINE / "LEGEND_RUN_MEASUREMENT.json").open("w", encoding="utf-8") as handle:
    json.dump(legend, handle, ensure_ascii=False, indent=2)
    handle.write("\n")

hessian = [[1.0, 1.0], [1.0, 2.0]]
det = hessian[0][0] * hessian[1][1] - hessian[0][1] * hessian[1][0]
trace = hessian[0][0] + hessian[1][1]
disc = math.sqrt(trace * trace - 4.0 * det)
eig = [(trace - disc) / 2.0, (trace + disc) / 2.0]
q = [(-3.20, 2.20), (-3.20, 1.60), (-1.60, 1.60), (-1.60, .80), (-.80, .80), (-.80, .40), (-.40, .40), (-.40, .20)]


def objective(point):
    x1, x2 = point
    return 0.5 * x1 * x1 + x1 * x2 + x2 * x2


steps = []
for index, point in enumerate(q):
    updated = "initial" if index == 0 else ("x2" if index % 2 == 1 else "x1")
    residual = None
    if updated == "x1":
        residual = point[0] + point[1]
    elif updated == "x2":
        residual = point[0] + 2.0 * point[1]
    steps.append({"q": index, "x1": point[0], "x2": point[1], "updated_coordinate": updated, "stationarity_residual": residual, "objective": objective(point)})
math_result = {
    "objective": "0.5*x1^2 + x1*x2 + x2^2",
    "hessian": hessian, "determinant": det, "eigenvalues": eig,
    "positive_definite": det > 0 and min(eig) > 0,
    "steps": steps,
    "strictly_decreasing": all(steps[i + 1]["objective"] < steps[i]["objective"] for i in range(len(steps) - 1)),
}
with (MACHINE / "MATH_SEMANTIC_CHECK.json").open("w", encoding="utf-8") as handle:
    json.dump(math_result, handle, ensure_ascii=False, indent=2)
    handle.write("\n")

summary = {
    "pdf": str(PDF), "pdf_sha256": hashlib.sha256(PDF.read_bytes()).hexdigest().upper(),
    "page_width_pt": page_w, "page_height_pt": page_h,
    "glyph_count": sum(1 for item in objects if item["object_type"] == "glyph"),
    "line_count": sum(1 for item in objects if item["object_type"] == "line"),
    "rect_count": sum(1 for item in objects if item["object_type"] == "rect"),
    "curve_count": sum(1 for item in objects if item["object_type"] == "curve"),
    "N": len(objects), "C": len(pairs), "candidate_count": len(candidate_pairs),
    "ink_bbox_px": ink_bbox, "figure_crop_bbox_px": crop_bbox,
    "math_check": math_result, "legend_measurement": legend,
}
with (MACHINE / "MACHINE_SUMMARY.json").open("w", encoding="utf-8") as handle:
    json.dump(summary, handle, ensure_ascii=False, indent=2)
    handle.write("\n")
print(json.dumps(summary, ensure_ascii=False, indent=2))
