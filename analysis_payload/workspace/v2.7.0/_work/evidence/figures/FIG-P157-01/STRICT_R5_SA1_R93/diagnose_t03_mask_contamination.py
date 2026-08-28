from collections import Counter
from pathlib import Path

import cv2
import fitz
import numpy as np
from PIL import Image, ImageDraw


OUT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\evidence\figures\FIG-P157-01\STRICT_R5_SA1_R93")
PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r93_fullbook\main_full.pdf")
SCALE = 300.0 / 72.0
image = Image.open(OUT / "full_page_300dpi.png").convert("RGB")
rgb = np.asarray(image)
height, width = rgb.shape[:2]

# The superseded implementation padded the final-PDF span by three pixels.
bbox_pt = (294.15, 214.07, 355.74, 225.07)
x0 = max(0, int(np.floor(bbox_pt[0] * SCALE)) - 3)
y0 = max(0, int(np.floor(bbox_pt[1] * SCALE)) - 3)
x1 = min(width, int(np.ceil(bbox_pt[2] * SCALE)) + 4)
y1 = min(height, int(np.ceil(bbox_pt[3] * SCALE)) + 4)
patch = rgb[y0:y1, x0:x1]
bg = np.array(Counter(map(tuple, patch.reshape(-1, 3))).most_common(1)[0][0], dtype=np.int16)
local = np.max(np.abs(patch.astype(np.int16) - bg), axis=2) >= 20
n, labels, stats, _ = cv2.connectedComponentsWithStats(local.astype(np.uint8), 8)
clean = np.zeros_like(local)
for i in range(1, n):
    if stats[i, cv2.CC_STAT_AREA] >= 2:
        clean[labels == i] = True
old_text = np.zeros((height, width), dtype=bool)
old_text[y0:y1, x0:x1] = clean

current_text = np.asarray(Image.open(OUT / "mask_T03_MINIMUM_KEY_native_300dpi.png")) > 0
current_marker = np.asarray(Image.open(OUT / "mask_G04_MINIMUM_MARKER_native_300dpi.png")) > 0

# Recreate the superseded filled-object support exactly: a 15-pixel stroked
# Bezier support followed by an 11x11 dilation.  This support is intentionally
# too broad for adjacent same-colour objects and is the second half of the bug.
drawing = fitz.open(PDF)[169].get_drawings()[15]
old_support = np.zeros((height, width), dtype=np.uint8)
poly_points = []
for item in drawing["items"]:
    if item[0] != "c":
        continue
    p0, p1, p2, p3 = item[1:5]
    curve = []
    for t in np.linspace(0.0, 1.0, 33):
        q = (
            ((1 - t) ** 3) * np.array([p0.x, p0.y])
            + 3 * ((1 - t) ** 2) * t * np.array([p1.x, p1.y])
            + 3 * (1 - t) * (t**2) * np.array([p2.x, p2.y])
            + (t**3) * np.array([p3.x, p3.y])
        )
        curve.append((int(round(q[0] * SCALE)), int(round(q[1] * SCALE))))
    pts = np.asarray(curve, dtype=np.int32).reshape(-1, 1, 2)
    cv2.polylines(old_support, [pts], False, 255, thickness=15, lineType=cv2.LINE_AA)
    poly_points.extend(curve)
hull = cv2.convexHull(np.asarray(poly_points, dtype=np.int32))
cv2.fillConvexPoly(old_support, hull, 255, lineType=cv2.LINE_AA)
old_support = cv2.dilate(old_support, np.ones((11, 11), np.uint8)) > 0

BGS = np.array([(255, 255, 255), (248, 250, 251), (251, 248, 244), (253, 249, 250)], dtype=np.float32)
base = np.array((183, 121, 31), dtype=np.float32)
yx = np.argwhere(old_support)
p = rgb[yx[:, 0], yx[:, 1]].astype(np.float32)
match = np.zeros(len(p), dtype=bool)
for bgf in BGS:
    v = base - bgf
    alpha = np.sum((p - bgf) * v, axis=1) / float(np.dot(v, v))
    recon = bgf + np.clip(alpha, 0.0, 1.0)[:, None] * v
    match |= (
        (alpha >= -0.02)
        & (alpha <= 1.05)
        & (np.linalg.norm(p - recon, axis=1) <= 8.0)
        & (np.linalg.norm(p - bgf, axis=1) >= 20.0)
    )
old_marker = np.zeros((height, width), dtype=bool)
old_marker[yx[match, 0], yx[match, 1]] = True

old_overlap = old_text & old_marker
current_overlap = current_text & current_marker

Image.fromarray((old_text * 255).astype(np.uint8)).save(
    OUT / "mask_T03_MINIMUM_KEY_superseded_pad3_native_300dpi.png"
)
Image.fromarray((old_overlap * 255).astype(np.uint8)).save(
    OUT / "mask_overlap_T03__G04_superseded_pad3_native_300dpi.png"
)
Image.fromarray((old_marker * 255).astype(np.uint8)).save(
    OUT / "mask_G04_MINIMUM_MARKER_superseded_overexpanded_native_300dpi.png"
)

mask_roi = (1180, 860, 1520, 990)
Image.fromarray((current_text * 255).astype(np.uint8)).crop(mask_roi).save(
    OUT / "roi_mask_T03_MINIMUM_KEY_current_1to1_300dpi.png"
)
Image.fromarray((current_marker * 255).astype(np.uint8)).crop(mask_roi).save(
    OUT / "roi_mask_G04_MINIMUM_MARKER_current_1to1_300dpi.png"
)
Image.fromarray((current_overlap * 255).astype(np.uint8)).crop(mask_roi).save(
    OUT / "roi_mask_overlap_T03__G04_current_1to1_300dpi.png"
)
Image.fromarray((old_overlap * 255).astype(np.uint8)).crop(mask_roi).save(
    OUT / "roi_mask_overlap_T03__G04_superseded_1to1_300dpi.png"
)

coords_yx = np.argwhere(old_overlap)
coords_xy = [(int(x), int(y)) for y, x in coords_yx]
current_coords_yx = np.argwhere(current_overlap)

rx0, ry0, rx1, ry1 = 1315, 900, 1390, 980
raw = image.crop((rx0, ry0, rx1, ry1))
raw.save(OUT / "roi_T03_G04_mask_diagnostic_raw_1to1_300dpi.png")
overlay = raw.copy()
draw = ImageDraw.Draw(overlay)
for x, y in coords_xy:
    draw.rectangle((x - rx0 - 2, y - ry0 - 2, x - rx0 + 2, y - ry0 + 2), outline=(255, 0, 255), width=1)
draw.line((0, 38, 74, 38), fill=(255, 0, 0), width=1)
draw.text((2, 2), f"old false overlap={len(coords_xy)}; current={len(current_coords_yx)}", fill=(0, 0, 0))
overlay.save(OUT / "roi_T03_G04_mask_diagnostic_overlay_1to1_300dpi.png")

with (OUT / "T03_G04_MASK_DIAGNOSTIC.txt").open("w", encoding="utf-8") as f:
    f.write("SUPERSEDED_PAD3_INTERSECTION_COUNT=" + str(len(coords_xy)) + "\n")
    f.write("SUPERSEDED_PAD3_INTERSECTION_XY=" + repr(coords_xy) + "\n")
    f.write("CURRENT_INTERSECTION_COUNT=" + str(len(current_coords_yx)) + "\n")
    f.write("CAUSE=old T03 span padding admitted the top antialias pixels of the adjacent same-colour marker into the TEXT mask\n")

print("old_count", len(coords_xy), "old_xy", coords_xy)
print("current_count", len(current_coords_yx))
