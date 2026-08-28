from pathlib import Path
from PIL import Image, ImageDraw
import csv

ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P660-01\sa1_r111_fresh_isolated_v1")
PAGE = ROOT / "render" / "page709_native300dpi.png"

img = Image.open(PAGE).convert("RGB")
assert img.size == (2481, 3508), img.size

crops = {
    "figure_local_with_caption_300dpi": (250, 250, 2225, 1415),
    "figure_standalone_300dpi": (250, 250, 2225, 1275),
    "roi_triangle_labels_native1x": (250, 275, 1290, 1235),
    "roi_theta_components_native1x": (475, 600, 1245, 1145),
    "roi_cards_native1x": (1430, 520, 2205, 1235),
    "roi_caption_native1x": (250, 1240, 2225, 1420),
    "roi_e3_two_lines_native1x": (665, 285, 920, 405),
    "roi_e1_two_lines_native1x": (250, 1145, 525, 1275),
    "roi_e2_two_lines_native1x": (1075, 1145, 1345, 1275),
    "roi_definition_two_lines_native1x": (1490, 535, 2120, 680),
}

for name, box in crops.items():
    out = img.crop(box)
    out.save(ROOT / "rois" / f"{name}.png")
    if name.endswith("native1x"):
        out.resize((out.width * 8, out.height * 8), Image.Resampling.NEAREST).save(
            ROOT / "rois" / f"{name.replace('native1x', 'nearest8x')}.png"
        )

standalone = img.crop(crops["figure_standalone_300dpi"])
standalone.convert("L").save(ROOT / "render" / "figure_grayscale_300dpi.png")

# Machine-only object seed table. Geometry/text semantics are declared from the whitelisted source;
# pixel boxes are conservative evidence windows, not reviewer judgments.
objects = [
    ("G01", "GEOMETRY", "simplex_fill", 375, 403, 1230, 1146),
    ("G02", "GEOMETRY", "boundary_left", 375, 402, 786, 1147),
    ("G03", "GEOMETRY", "boundary_right", 786, 402, 1230, 1147),
    ("G04", "GEOMETRY", "boundary_bottom", 375, 1146, 1230, 1147),
    ("G05", "GEOMETRY", "grid_t02_dir1", 540, 848, 1145, 848),
    ("G06", "GEOMETRY", "grid_t02_dir2", 704, 551, 1065, 1147),
    ("G07", "GEOMETRY", "grid_t02_dir3", 458, 996, 872, 402),
    ("G08", "GEOMETRY", "grid_t04_dir1", 623, 699, 1061, 699),
    ("G09", "GEOMETRY", "grid_t04_dir2", 622, 699, 982, 1147),
    ("G10", "GEOMETRY", "grid_t04_dir3", 540, 848, 950, 551),
    ("G11", "GEOMETRY", "grid_t06_dir1", 704, 551, 980, 551),
    ("G12", "GEOMETRY", "grid_t06_dir2", 540, 848, 900, 1147),
    ("G13", "GEOMETRY", "grid_t06_dir3", 623, 699, 1065, 848),
    ("G14", "GEOMETRY", "grid_t08_dir1", 786, 402, 900, 402),
    ("G15", "GEOMETRY", "grid_t08_dir2", 458, 996, 817, 1147),
    ("G16", "GEOMETRY", "grid_t08_dir3", 704, 551, 1145, 996),
    ("G17", "GEOMETRY", "component_theta1", 825, 756, 1116, 678),
    ("G18", "GEOMETRY", "component_theta2", 622, 678, 825, 756),
    ("G19", "GEOMETRY", "component_theta3", 825, 756, 825, 1147),
    ("G20", "MARKER", "theta_marker", 810, 741, 841, 772),
    ("G21", "CONTAINER", "card_definition", 1468, 522, 2190, 684),
    ("G22", "CONTAINER", "card_faces", 1468, 785, 2190, 971),
    ("G23", "CONTAINER", "card_conclusion", 1468, 1040, 2190, 1234),
    ("T01", "TEXT", "theta2_label", 485, 625, 615, 675),
    ("T02", "TEXT", "theta1_label", 980, 625, 1105, 675),
    ("T03", "TEXT", "theta3_label", 850, 1160, 1025, 1215),
    ("T04", "TEXT", "theta_vector", 1015, 730, 1300, 785),
    ("T05", "TEXT", "e3_formula", 680, 282, 900, 330),
    ("T06", "TEXT", "e3_category", 680, 330, 890, 375),
    ("T07", "TEXT", "e1_formula", 270, 1160, 500, 1207),
    ("T08", "TEXT", "e1_category", 270, 1207, 505, 1245),
    ("T09", "TEXT", "e2_formula", 1080, 1160, 1325, 1207),
    ("T10", "TEXT", "e2_category", 1080, 1207, 1325, 1245),
    ("T11", "FORMULA", "simplex_definition", 1510, 555, 2155, 610),
    ("T12", "FORMULA", "simplex_dimension", 1510, 615, 1815, 665),
    ("T13", "TEXT", "faces_interior", 1510, 810, 2025, 855),
    ("T14", "TEXT", "faces_edge", 1510, 860, 1900, 905),
    ("T15", "TEXT", "faces_vertex", 1510, 910, 2070, 955),
    ("T16", "TEXT", "conclusion_line1", 1510, 1070, 2125, 1110),
    ("T17", "TEXT", "conclusion_line2", 1510, 1110, 2125, 1150),
    ("T18", "TEXT", "conclusion_line3", 1510, 1150, 1840, 1200),
    ("T19", "CAPTION", "caption_tag", 250, 1265, 435, 1315),
    ("T20", "CAPTION", "caption_line1", 420, 1265, 2200, 1320),
    ("T21", "CAPTION", "caption_line2", 250, 1320, 1740, 1385),
]

objects = [
    (oid, cls, name, min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1))
    for oid, cls, name, x0, y0, x1, y1 in objects
]

with (ROOT / "machine" / "visible_object_denominator_seed.csv").open("w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f)
    w.writerow(["OBJECT_ID", "CLASS", "NAME", "X0", "Y0", "X1", "Y1"])
    w.writerows(objects)

overlay = img.copy()
d = ImageDraw.Draw(overlay)
colors = {"GEOMETRY": "#e31a1c", "MARKER": "#ff7f00", "CONTAINER": "#6a3d9a", "TEXT": "#1f78b4", "FORMULA": "#33a02c", "CAPTION": "#b15928"}
for oid, cls, name, x0, y0, x1, y1 in objects:
    c = colors[cls]
    d.rectangle((x0, y0, x1, y1), outline=c, width=3)
    d.text((x0 + 2, max(0, y0 - 18)), oid, fill=c)
overlay.crop(crops["figure_local_with_caption_300dpi"]).save(ROOT / "overlays" / "object_id_overlay_300dpi.png")

with (ROOT / "machine" / "all_unordered_pairs_machine.csv").open("w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f)
    w.writerow(["PAIR_ID", "OBJECT_A", "OBJECT_B", "CLASS_A", "CLASS_B", "BBOX_INTERSECTION_AREA_PX", "BBOX_GAP_X_PX", "BBOX_GAP_Y_PX", "BBOX_EUCLIDEAN_GAP_PX"])
    pid = 0
    for i, a in enumerate(objects):
        for b in objects[i + 1:]:
            pid += 1
            ax0, ay0, ax1, ay1 = a[3:]
            bx0, by0, bx1, by1 = b[3:]
            ix = max(0, min(ax1, bx1) - max(ax0, bx0))
            iy = max(0, min(ay1, by1) - max(ay0, by0))
            gx = max(0, max(ax0, bx0) - min(ax1, bx1))
            gy = max(0, max(ay0, by0) - min(ay1, by1))
            gap = (gx * gx + gy * gy) ** 0.5
            w.writerow([f"P{pid:04d}", a[0], b[0], a[1], b[1], ix * iy, gx, gy, f"{gap:.3f}"])
assert pid == len(objects) * (len(objects) - 1) // 2

with (ROOT / "machine" / "render_metadata.txt").open("w", encoding="utf-8") as f:
    f.write(f"page_1based=709\npage_count=817\nnative300_size={img.width}x{img.height}\nobject_count={len(objects)}\nunordered_pair_count={pid}\n")

print(f"objects={len(objects)} pairs={pid} page_size={img.size}")
