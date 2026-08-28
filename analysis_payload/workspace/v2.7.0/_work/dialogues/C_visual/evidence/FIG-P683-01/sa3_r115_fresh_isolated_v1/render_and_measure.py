from __future__ import annotations

import csv
import hashlib
import json
import math
import unicodedata
from itertools import combinations
from pathlib import Path

import fitz
import numpy as np
from PIL import Image, ImageDraw, ImageFont


HANDOFF_ID = "C-FIG-P683-01-R115-SA3-FRESH-ISOLATED-V1"
PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r115_fullbook\main_full.pdf")
SOURCE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C06\fig_v5_c06_plate_graph.tex")
CHAPTER = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\讲义源码\第05册_采样方法主题模型与图排序\chapters\V5-C06.tex")
ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P683-01\sa3_r115_fresh_isolated_v1")
ART = ROOT / "artifacts"
ROIS = ART / "rois"

PHYSICAL_PAGE = 732
PAGE_INDEX = PHYSICAL_PAGE - 1
FIGURE_CLIP_PT = (70.0, 182.0, 535.0, 415.0)

# Frozen reader-visible denominator. Text and formula ink is intentionally split
# from node/plate borders and arrows so every semantically independent foreground
# object participates in the unordered-pair ledger.
ELEMENTS = [
    # Text/formula foreground.
    dict(id="T01", category="FORMULA", role="hyperparameter", text="α", bbox=(93.606, 228.610, 99.201, 238.174), source_line=25, declared_pt=9.6, script="GREEK_LOWER"),
    dict(id="T02", category="FORMULA", role="latent_node_label", text="θ_m", bbox=(172.417, 228.771, 184.417, 239.660), source_line=26, declared_pt=9.6, script="MATH_MIXED"),
    dict(id="T03", category="FORMULA", role="latent_node_label", text="z_mn", bbox=(238.160, 227.575, 254.738, 238.465), source_line=27, declared_pt=9.6, script="MATH_MIXED"),
    dict(id="T04", category="FORMULA", role="observed_node_label", text="w_mn", bbox=(302.089, 227.633, 321.202, 238.522), source_line=28, declared_pt=9.6, script="MATH_MIXED"),
    dict(id="T05", category="FORMULA", role="hyperparameter", text="β", bbox=(93.630, 323.743, 98.890, 333.307), source_line=29, declared_pt=9.6, script="GREEK_LOWER"),
    dict(id="T06", category="FORMULA", role="latent_node_label", text="φ_k", bbox=(241.110, 322.633, 251.788, 333.522), source_line=30, declared_pt=9.6, script="MATH_MIXED"),
    dict(id="T07", category="TEXT", role="plate_label", text="N_m 个词位", bbox=(288.202, 194.901, 332.799, 205.685), source_line=43, declared_pt=9.2, script="CJK_MATH_MIXED"),
    dict(id="T08", category="TEXT", role="plate_label", text="M 篇文档", bbox=(312.717, 284.443, 352.120, 294.260), source_line=44, declared_pt=9.2, script="CJK_MATH_MIXED"),
    dict(id="T09", category="TEXT", role="plate_label", text="K 个主题", bbox=(234.004, 357.224, 271.546, 367.041), source_line=45, declared_pt=9.2, script="CJK_MATH_MIXED"),
    dict(id="T10", category="TEXT", role="legend_label", text="观测变量", bbox=(442.430, 238.329, 479.092, 248.145), source_line=47, declared_pt=9.2, script="CJK"),
    dict(id="T11", category="TEXT", role="legend_label", text="潜变量", bbox=(442.430, 265.258, 469.927, 275.074), source_line=49, declared_pt=9.2, script="CJK"),
    dict(id="T12", category="FORMULA", role="legend_hyperparameter", text="α,β", bbox=(412.013, 291.144, 426.799, 300.708), source_line=50, declared_pt=9.6, script="GREEK_PUNCT"),
    dict(id="T13", category="TEXT", role="legend_label", text="超参数（plate 外）", bbox=(442.430, 291.729, 518.587, 301.545), source_line=51, declared_pt=9.2, script="CJK_LATIN_MIXED"),
    dict(id="T14", category="TEXT", role="caption_number", text="图35.2", bbox=(87.477, 368.454, 116.686, 382.880), source_line=55, declared_pt=9.0, script="CJK_DIGIT"),
    dict(id="T15", category="TEXT", role="caption_line", text="完整Bayes LDA盘式图把超参数、潜变量和观测变量分开：每篇文档共享一个主题比例，每", bbox=(126.648, 372.041, 519.142, 382.711), source_line=55, declared_pt=9.0, script="CJK_LATIN_MIXED"),
    dict(id="T16", category="TEXT", role="caption_line", text="个词位拥有一个主题指派，所有文档共享带Dirichlet先验的主题词分布；盘框标明重复次数，箭头", bbox=(87.477, 385.430, 519.144, 396.100), source_line=55, declared_pt=9.0, script="CJK_LATIN_MIXED"),
    dict(id="T17", category="TEXT", role="caption_line", text="只表示条件依赖方向", bbox=(87.477, 398.820, 177.141, 409.490), source_line=55, declared_pt=9.0, script="CJK"),
    # Node/plate/legend marker borders and fills.
    dict(id="O01", category="NODE_BORDER", role="latent_node", text="theta node", bbox=(166.985, 222.052, 190.229, 245.297), source_line=26),
    dict(id="O02", category="NODE_BORDER", role="latent_node", text="z node", bbox=(235.018, 222.052, 258.262, 245.297), source_line=27),
    dict(id="O03", category="NODE_BORDER", role="observed_node", text="w node", bbox=(300.215, 222.052, 323.459, 245.297), source_line=28),
    dict(id="O04", category="NODE_BORDER", role="latent_node", text="phi node", bbox=(235.018, 317.014, 258.262, 340.259), source_line=30),
    dict(id="O05", category="PANEL_BORDER", role="N_m plate", text="inner word-position plate", bbox=(221.580, 209.156, 336.922, 258.193), source_line=32),
    dict(id="O06", category="PANEL_BORDER", role="M plate", text="outer document plate", bbox=(151.846, 189.552, 351.991, 277.797), source_line=33),
    dict(id="O07", category="PANEL_BORDER", role="K plate", text="topic plate", bbox=(221.863, 306.694, 271.417, 350.579), source_line=34),
    dict(id="O08", category="MARKER", role="legend_observed_marker", text="observed marker", bbox=(410.484, 233.108, 428.626, 251.250), source_line=46),
    dict(id="O09", category="MARKER", role="legend_latent_marker", text="latent marker", bbox=(410.484, 260.037, 428.626, 278.179), source_line=48),
    # Arrow shaft and head are one semantic object per declared draw command.
    dict(id="A01", category="LINE_ARROW", role="alpha_to_theta", text="α→θ_m", bbox=(100.395, 232.599, 165.179, 234.750), source_line=36),
    dict(id="A02", category="LINE_ARROW", role="theta_to_z", text="θ_m→z_mn", bbox=(190.628, 232.599, 233.212, 234.750), source_line=37),
    dict(id="A03", category="LINE_ARROW", role="z_to_w", text="z_mn→w_mn", bbox=(258.660, 232.599, 298.384, 234.750), source_line=38),
    dict(id="A04", category="LINE_ARROW", role="beta_to_phi", text="β→φ_k", bbox=(100.371, 327.561, 233.212, 329.712), source_line=39),
    dict(id="A05", category="LINE_ARROW", role="phi_to_w", text="φ_k→w_mn", bbox=(253.443, 244.764, 304.224, 318.727), source_line=40),
]

CRITICAL_ROIS = [
    ("R01_alpha_theta", (88.0, 218.0, 195.0, 248.0)),
    ("R02_theta_z", (162.0, 216.0, 265.0, 249.0)),
    ("R03_z_w", (230.0, 216.0, 330.0, 249.0)),
    ("R04_beta_phi", (88.0, 313.0, 265.0, 344.0)),
    ("R05_phi_w_diagonal", (228.0, 240.0, 316.0, 326.0)),
    ("R06_nested_plate_labels", (274.0, 186.0, 363.0, 307.0)),
    ("R07_k_plate_label", (218.0, 302.0, 280.0, 375.0)),
    ("R08_legend", (400.0, 226.0, 525.0, 308.0)),
    ("R09_caption", (82.0, 364.0, 525.0, 413.0)),
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def px_box(pt_box, sx, sy):
    x0, y0, x1, y1 = pt_box
    return (
        int(math.floor(x0 * sx)),
        int(math.floor(y0 * sy)),
        int(math.ceil(x1 * sx)),
        int(math.ceil(y1 * sy)),
    )


def relative_px_box(pt_box, clip_pt, sx, sy):
    x0, y0, x1, y1 = pt_box
    cx0, cy0, _, _ = clip_pt
    return (
        int(math.floor((x0 - cx0) * sx)),
        int(math.floor((y0 - cy0) * sy)),
        int(math.ceil((x1 - cx0) * sx)),
        int(math.ceil((y1 - cy0) * sy)),
    )


def ink_measure(rgb: Image.Image, box):
    x0, y0, x1, y1 = box
    x0 = max(0, x0)
    y0 = max(0, y0)
    x1 = min(rgb.width, x1)
    y1 = min(rgb.height, y1)
    arr = np.asarray(rgb.crop((x0, y0, x1, y1)).convert("RGB"), dtype=np.int16)
    if arr.size == 0:
        return 0, 0, 0
    edge = np.concatenate((arr[0], arr[-1], arr[:, 0], arr[:, -1]), axis=0)
    bg = np.median(edge, axis=0)
    diff = np.max(np.abs(arr - bg), axis=2)
    mask = diff >= 20
    ys, xs = np.where(mask)
    if len(ys) == 0:
        return 0, 0, 0
    return int(ys.max() - ys.min() + 1), int(xs.max() - xs.min() + 1), int(mask.sum())


def draw_overlay(base: Image.Image, categories, filename: Path):
    out = base.copy().convert("RGBA")
    draw = ImageDraw.Draw(out, "RGBA")
    palette = {
        "TEXT": (230, 35, 60, 220),
        "FORMULA": (255, 120, 0, 220),
        "NODE_BORDER": (0, 90, 255, 220),
        "PANEL_BORDER": (110, 0, 180, 220),
        "MARKER": (0, 145, 85, 220),
        "LINE_ARROW": (0, 150, 190, 220),
    }
    font = ImageFont.load_default()
    for e in ELEMENTS:
        if e["category"] not in categories:
            continue
        box = relative_px_box(e["bbox"], FIGURE_CLIP_PT, sx, sy)
        color = palette[e["category"]]
        draw.rectangle(box, outline=color, width=3)
        lx = max(0, box[0])
        ly = max(0, box[1] - 12)
        draw.rectangle((lx, ly, lx + 27, ly + 11), fill=(255, 255, 255, 225))
        draw.text((lx + 1, ly), e["id"], fill=color, font=font)
    out.convert("RGB").save(filename, dpi=(300, 300))


ART.mkdir(parents=True, exist_ok=True)
ROIS.mkdir(parents=True, exist_ok=True)

doc = fitz.open(PDF)
page = doc[PAGE_INDEX]
pix = page.get_pixmap(dpi=300, alpha=False)
full_path = ART / "full_page_300dpi.png"
pix.save(full_path)
full = Image.open(full_path).convert("RGB")
sx = full.width / page.rect.width
sy = full.height / page.rect.height

crop_px = px_box(FIGURE_CLIP_PT, sx, sy)
figure = full.crop(crop_px)
figure_path = ART / "figure_caption_300dpi.png"
figure.save(figure_path, dpi=(300, 300))
figure.convert("L").save(ART / "figure_caption_grayscale_300dpi.png", dpi=(300, 300))

draw_overlay(figure, {"TEXT", "FORMULA"}, ART / "text_overlay_300dpi.png")
draw_overlay(figure, {"NODE_BORDER", "PANEL_BORDER", "MARKER", "LINE_ARROW"}, ART / "object_overlay_300dpi.png")
draw_overlay(figure, {"TEXT", "FORMULA", "NODE_BORDER", "PANEL_BORDER", "MARKER", "LINE_ARROW"}, ART / "semantic_overlay_300dpi.png")

for roi_name, roi_pt in CRITICAL_ROIS:
    one = full.crop(px_box(roi_pt, sx, sy))
    one.save(ROIS / f"{roi_name}_native1x.png", dpi=(300, 300))
    eight = one.resize((one.width * 8, one.height * 8), Image.Resampling.NEAREST)
    eight.save(ROIS / f"{roi_name}_nearest8x.png", dpi=(2400, 2400), optimize=True)

with (ROOT / "reader_visible_denominator.csv").open("w", newline="", encoding="utf-8-sig") as f:
    fields = ["ELEMENT_ID", "CATEGORY", "ROLE", "TEXT_OR_OBJECT", "SOURCE_FILE", "SOURCE_LINE", "BBOX_X0_PT", "BBOX_Y0_PT", "BBOX_X1_PT", "BBOX_Y1_PT"]
    w = csv.DictWriter(f, fieldnames=fields)
    w.writeheader()
    for e in ELEMENTS:
        x0, y0, x1, y1 = e["bbox"]
        w.writerow({
            "ELEMENT_ID": e["id"], "CATEGORY": e["category"], "ROLE": e["role"], "TEXT_OR_OBJECT": e["text"],
            "SOURCE_FILE": SOURCE.name, "SOURCE_LINE": e["source_line"],
            "BBOX_X0_PT": f"{x0:.3f}", "BBOX_Y0_PT": f"{y0:.3f}", "BBOX_X1_PT": f"{x1:.3f}", "BBOX_Y1_PT": f"{y1:.3f}",
        })

with (ROOT / "pair_enumeration_base.csv").open("w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["PAIR_ID", "A_ID", "B_ID"])
    for idx, (a, b) in enumerate(combinations(ELEMENTS, 2), start=1):
        w.writerow([f"P{idx:03d}", a["id"], b["id"]])

with (ROOT / "mechanical_text_metrics.csv").open("w", newline="", encoding="utf-8-sig") as f:
    fields = ["ELEMENT_ID", "ROLE", "TEXT_SAMPLE", "SCRIPT_CLASS", "DECLARED_PT", "GRAPHICS_SCALE", "EFFECTIVE_PT", "BBOX_X0_PX", "BBOX_Y0_PX", "BBOX_X1_PX", "BBOX_Y1_PX", "BBOX_H_PX", "H_INK_PX", "W_INK_PX", "INK_PIXEL_COUNT"]
    w = csv.DictWriter(f, fieldnames=fields)
    w.writeheader()
    for e in ELEMENTS:
        if e["category"] not in {"TEXT", "FORMULA"}:
            continue
        box = px_box(e["bbox"], sx, sy)
        h_ink, w_ink, ink_count = ink_measure(full, box)
        effective_pt = e.get("declared_pt", 0.0)
        w.writerow({
            "ELEMENT_ID": e["id"], "ROLE": e["role"], "TEXT_SAMPLE": e["text"], "SCRIPT_CLASS": e.get("script", ""),
            "DECLARED_PT": f"{effective_pt:.2f}", "GRAPHICS_SCALE": "1.000", "EFFECTIVE_PT": f"{effective_pt:.2f}",
            "BBOX_X0_PX": box[0], "BBOX_Y0_PX": box[1], "BBOX_X1_PX": box[2], "BBOX_Y1_PX": box[3],
            "BBOX_H_PX": box[3] - box[1], "H_INK_PX": h_ink, "W_INK_PX": w_ink, "INK_PIXEL_COUNT": ink_count,
        })

with (ROOT / "glyph_codepoint_inventory_machine.csv").open("w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["ELEMENT_ID", "CHAR_INDEX", "GLYPH", "CODEPOINT", "UNICODE_NAME"])
    for e in ELEMENTS:
        if e["category"] not in {"TEXT", "FORMULA"}:
            continue
        for idx, ch in enumerate(e["text"], start=1):
            w.writerow([e["id"], idx, ch, f"U+{ord(ch):04X}", unicodedata.name(ch, "UNNAMED")])

locator = {
    "HANDOFF_ID": HANDOFF_ID,
    "physical_page": PHYSICAL_PAGE,
    "printed_page": 719,
    "page_count": len(doc),
    "locator_method": "independent full-PDF text-layer search for caption and cross-check against current source caption",
    "caption_match": "图35.2 完整Bayes LDA盘式图把超参数、潜变量和观测变量分开",
    "page_rect_pt": list(page.rect),
    "figure_caption_clip_pt": list(FIGURE_CLIP_PT),
    "render_width_px": full.width,
    "render_height_px": full.height,
    "render_dpi": 300,
    "denominator_N": len(ELEMENTS),
    "unordered_pair_count": len(ELEMENTS) * (len(ELEMENTS) - 1) // 2,
}
(ROOT / "target_location.json").write_text(json.dumps(locator, ensure_ascii=False, indent=2), encoding="utf-8")

identity = {
    "HANDOFF_ID": HANDOFF_ID,
    "official_pdf": {"path": str(PDF), "bytes": PDF.stat().st_size, "sha256": sha256(PDF)},
    "current_source": {"path": str(SOURCE), "bytes": SOURCE.stat().st_size, "sha256": sha256(SOURCE)},
    "chapter_context": {"path": str(CHAPTER), "bytes": CHAPTER.stat().st_size, "sha256": sha256(CHAPTER)},
}
(ROOT / "input_identity.json").write_text(json.dumps(identity, ensure_ascii=False, indent=2), encoding="utf-8")

print(json.dumps(locator, ensure_ascii=False))
