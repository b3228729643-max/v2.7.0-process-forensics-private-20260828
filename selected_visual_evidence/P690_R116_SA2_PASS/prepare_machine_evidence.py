from __future__ import annotations

import csv
import hashlib
import itertools
import json
import subprocess
from pathlib import Path

import pdfplumber
from PIL import Image, ImageDraw, ImageFont
from pypdf import PdfReader


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P690-01\sa2_r116_r168_readonly_adjudication_v1")
PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r116_fullbook\main_full.pdf")
SOURCE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C06\fig_v5_c06_mean_field_graph.tex")
CHAPTER = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\讲义源码\第05册_采样方法主题模型与图排序\chapters\V5-C06.tex")

EXPECTED = {
    "pdf": (PDF, 4_967_281, "19F3D0413AD8C72B4D855B2C23246F10DD7ACECF2FD1E984AEE9F25E1051D3DC"),
    "source": (SOURCE, 3_684, "EC708EA11DAFD53994568CB8675A99E853D6A788046F4CF2CE4159697ACD8A2A"),
    "chapter": (CHAPTER, 120_809, "7276DDB767246292D0924D1651D560975E0FE6D2ACE47CBAEC4EE45CEB4A0029"),
}

CAPTION_NEEDLE = "平均场近似把单文档后验"
SOURCE_LABEL = "fig:V5-C06-mean-field-graph"
PHYSICAL_PAGE = 740
PRINTED_PAGE = 727
FIGURE_NUMBER = "35.6"
PAGE_WIDTH_PT = 595.276
PAGE_HEIGHT_PT = 841.89
FIGURE_CAPTION_BBOX_PT = (60.0, 58.0, 542.0, 310.0)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


identity_rows = []
for role, (path, expected_size, expected_sha) in EXPECTED.items():
    actual_size = path.stat().st_size
    actual_sha = sha256(path)
    if actual_size != expected_size or actual_sha != expected_sha:
        raise RuntimeError(f"identity mismatch for {role}: size={actual_size}, sha={actual_sha}")
    identity_rows.append(
        {
            "role": role,
            "path": str(path),
            "bytes": actual_size,
            "sha256": actual_sha,
            "expected_match": True,
        }
    )

source_text = SOURCE.read_text(encoding="utf-8")
chapter_text = CHAPTER.read_text(encoding="utf-8")
if SOURCE_LABEL not in source_text or CAPTION_NEEDLE not in source_text:
    raise RuntimeError("current source label/caption not found")
if SOURCE_LABEL not in chapter_text or "近似族主动切断了后验中" not in chapter_text:
    raise RuntimeError("current chapter reference/context not found")

reader = PdfReader(PDF)
hit_pages = []
for page_index, page in enumerate(reader.pages, start=1):
    page_text = page.extract_text() or ""
    if CAPTION_NEEDLE in page_text and "图 35.6" in page_text:
        hit_pages.append(page_index)
if hit_pages != [PHYSICAL_PAGE]:
    raise RuntimeError(f"caption locator not unique: {hit_pages}")

with pdfplumber.open(PDF) as document:
    if hit_pages != [PHYSICAL_PAGE]:
        raise RuntimeError(f"caption locator not unique: {hit_pages}")
    page = document.pages[PHYSICAL_PAGE - 1]
    words = page.extract_words(x_tolerance=2, y_tolerance=2, keep_blank_chars=False)
    figure_words = [
        {
            "text": word["text"],
            "x0": round(float(word["x0"]), 3),
            "x1": round(float(word["x1"]), 3),
            "top": round(float(word["top"]), 3),
            "bottom": round(float(word["bottom"]), 3),
        }
        for word in words
        if 58.0 <= float(word["top"]) <= 310.0
    ]
    extracted_page_text = reader.pages[PHYSICAL_PAGE - 1].extract_text() or ""

page_caption = "图 35.6 固定主题 – 词参数 φ 时，平均场近似把单文档后验中耦合的 θ_m 与 z_mn 替换为两个变分因子族；被切断的是近似后验中的直接依赖，固定参数仍通过词似然进入责任度更新"
if "图 35.6" not in extracted_page_text or "被切断的是近似后验中的直接依赖" not in extracted_page_text:
    raise RuntimeError("located PDF page does not contain the current caption")

objects = [
    ("O001", "text", "左标题：真实后验 θ_m 与 z_mn 耦合", "left_title", (116, 67, 240, 89)),
    ("O002", "composite_node", "左 θ_m 潜变量节点", "theta_true", (104, 109, 139, 148)),
    ("O003", "composite_node", "左 z_mn 潜变量节点", "z_true", (159, 109, 194, 148)),
    ("O004", "composite_node", "左 w_mn 观测节点", "w_observed_left", (215, 109, 250, 148)),
    ("O005", "composite_node", "左 φ 固定参数框", "phi_fixed_left", (144, 158, 212, 190)),
    ("O006", "edge", "θ_m—z_mn 真实后验耦合边", "true_coupling", (137, 124, 160, 136)),
    ("O007", "directed_edge", "w_mn→z_mn 左输入箭头", "word_input_left", (191, 115, 216, 143)),
    ("O008", "directed_edge", "φ→z_mn 左输入箭头", "phi_input_left", (169, 144, 188, 160)),
    ("O009", "panel_boundary", "左虚线面板边界", "left_panel", (87, 92, 267, 199)),
    ("O010", "math_text", "p(θ_m,z_mn∣w_m,φ)", "true_posterior_formula", (132, 201, 224, 224)),
    ("O011", "text", "右标题：平均场切断近似后验依赖", "right_title", (365, 67, 490, 89)),
    ("O012", "composite_node", "右 q(θ_m) 变分因子节点", "q_theta", (351, 104, 399, 153)),
    ("O013", "composite_node", "右 q(z_mn) 变分因子节点", "q_z", (406, 104, 454, 153)),
    ("O014", "composite_node", "右 w_mn 观测节点", "w_observed_right", (469, 109, 504, 148)),
    ("O015", "composite_node", "右 φ 固定参数框", "phi_fixed_right", (393, 158, 463, 190)),
    ("O016", "cut_edge", "切断边左虚线段", "cut_segment_left", (396, 122, 403, 138)),
    ("O017", "cut_edge", "切断边右虚线段", "cut_segment_right", (409, 122, 416, 138)),
    ("O018", "cut_mark", "切断斜杠一", "cut_mark_1", (402, 120, 409, 139)),
    ("O019", "cut_mark", "切断斜杠二", "cut_mark_2", (404, 120, 412, 139)),
    ("O020", "directed_edge", "右 w_mn→q(z_mn) 输入箭头", "word_input_right", (454, 115, 470, 143)),
    ("O021", "directed_edge", "右 φ→q(z_mn) 输入箭头", "phi_input_right", (421, 145, 441, 160)),
    ("O022", "panel_boundary", "右虚线面板边界", "right_panel", (335, 92, 520, 199)),
    ("O023", "math_text", "q(θ_m)∏_n q(z_mn)", "factorized_formula", (383, 200, 472, 224)),
    ("O024", "directed_edge", "左面板→右面板转换箭头", "approximation_transition", (265, 136, 336, 153)),
    ("O025", "text", "选择可计算的／乘积分布族", "transition_label", (264, 112, 334, 141)),
    ("O026", "composite_callout", "底部蓝色结论框及两行结论", "semantic_summary", (120, 236, 500, 276)),
    ("O027", "caption_label", "图 35.6", "caption_number", (70, 277, 108, 307)),
    ("O028", "caption_text", "题注正文", "caption_body", (108, 277, 541, 307)),
]

object_rows = [
    {
        "object_id": oid,
        "category": category,
        "reader_visible_content": content,
        "semantic_role": role,
        "bbox_points": ",".join(str(v) for v in bbox),
    }
    for oid, category, content, role, bbox in objects
]
pair_rows = []
for pair_index, ((a, *_), (b, *_)) in enumerate(itertools.combinations(objects, 2), start=1):
    pair_rows.append({"pair_id": f"P{pair_index:04d}", "object_a": a, "object_b": b})
if len(objects) != 28 or len(pair_rows) != 378:
    raise RuntimeError("frozen denominator arithmetic mismatch")

glyph_rows = [
    ("G001", "O001", "θ_m,z_mn", "left title"),
    ("G002", "O002", "θ_m", "left latent node"),
    ("G003", "O003", "z_mn", "left latent node"),
    ("G004", "O004", "w_mn", "left observed node"),
    ("G005", "O005", "φ", "left fixed parameter"),
    ("G006", "O010", "p(θ_m,z_mn∣w_m,φ)", "true posterior formula"),
    ("G007", "O012", "q(θ_m)", "right factor node"),
    ("G008", "O013", "q(z_mn)", "right factor node"),
    ("G009", "O014", "w_mn", "right observed node"),
    ("G010", "O015", "φ", "right fixed parameter"),
    ("G011", "O023", "q(θ_m)∏_nq(z_mn)", "factorization formula"),
    ("G012", "O026", "w_mn", "summary observed symbol"),
    ("G013", "O026", "φ", "summary fixed parameter"),
    ("G014", "O026", "q(z_mn)", "summary responsibility factor"),
    ("G015", "O028", "φ", "caption fixed parameter"),
    ("G016", "O028", "θ_m", "caption topic mixture"),
    ("G017", "O028", "z_mn", "caption assignment"),
]
math_rows = [
    ("M001", "O001", "true posterior couples θ_m and z_mn"),
    ("M002", "O010", "p(θ_m,z_mn∣w_m,φ)"),
    ("M003", "O012", "q(θ_m)"),
    ("M004", "O013", "q(z_mn)"),
    ("M005", "O023", "q(θ_m)∏_n q(z_mn)"),
    ("M006", "O026", "w_mn and φ enter q(z_mn) responsibility update"),
    ("M007", "O028", "caption states coupled posterior replaced by two variational-factor families"),
]

write_json(ROOT / "00_input_identity.json", {"handoff_id": "C-FIG-P690-01-R116-SA2-R168-READONLY-ADJUDICATION-V1", "inputs": identity_rows})
write_json(
    ROOT / "01_locator_machine.json",
    {
        "label": SOURCE_LABEL,
        "caption_needle": CAPTION_NEEDLE,
        "hit_pages": hit_pages,
        "physical_page": PHYSICAL_PAGE,
        "printed_page": PRINTED_PAGE,
        "figure_number": FIGURE_NUMBER,
        "page_caption_normalized": page_caption,
        "page_width_points": float(page.width),
        "page_height_points": float(page.height),
        "figure_caption_bbox_points": FIGURE_CAPTION_BBOX_PT,
        "figure_words": figure_words,
    },
)
write_csv(ROOT / "02_object_inventory_frozen.csv", ["object_id", "category", "reader_visible_content", "semantic_role", "bbox_points"], object_rows)
write_csv(ROOT / "03_pair_inventory_frozen.csv", ["pair_id", "object_a", "object_b"], pair_rows)
write_csv(ROOT / "04_glyph_inventory_frozen.csv", ["glyph_id", "object_id", "glyph_or_expression", "context"], [dict(zip(["glyph_id", "object_id", "glyph_or_expression", "context"], row)) for row in glyph_rows])
write_csv(ROOT / "05_math_inventory_frozen.csv", ["math_id", "object_id", "claim_or_expression"], [dict(zip(["math_id", "object_id", "claim_or_expression"], row)) for row in math_rows])
(ROOT / "06_denominator_freeze.txt").write_text(
    "HANDOFF_ID=C-FIG-P690-01-R116-SA2-R168-READONLY-ADJUDICATION-V1\n"
    "PHYSICAL_PAGE=740\nPRINTED_PAGE=727\nFIGURE_NUMBER=35.6\n"
    "DENOMINATOR_GRANULARITY=top-level reader-visible semantic components; composite node/box ink is one object; glyph/math subinstances are separately frozen; page chrome is covered by the page ledger\n"
    "N=28\nC=378\nPAIR_FORMULA=N(N-1)/2\n"
    "MACHINE_SKELETON_MANUAL_VERDICT_FIELDS=0\n",
    encoding="utf-8",
    newline="\n",
)


def run_render(dpi: int, prefix_name: str) -> Path:
    prefix = ROOT / prefix_name
    command = [
        "pdftoppm",
        "-f",
        str(PHYSICAL_PAGE),
        "-l",
        str(PHYSICAL_PAGE),
        "-r",
        str(dpi),
        "-png",
        "-singlefile",
        str(PDF),
        str(prefix),
    ]
    subprocess.run(command, check=True, capture_output=True)
    output = prefix.with_suffix(".png")
    if not output.is_file():
        raise RuntimeError(f"renderer did not create {output}")
    return output


page72_path = run_render(72, "10_full_page_native72")
page200_path = run_render(200, "11_full_page_color200")
page300_path = run_render(300, "12_full_page_color300")

with Image.open(page300_path) as page300_source:
    page300 = page300_source.convert("RGB")
with Image.open(page72_path) as page72_source:
    page72 = page72_source.convert("RGB")

page300.convert("L").save(ROOT / "13_full_page_gray300.png")


def point_box_to_pixels(box: tuple[float, float, float, float], image: Image.Image) -> tuple[int, int, int, int]:
    sx = image.width / PAGE_WIDTH_PT
    sy = image.height / PAGE_HEIGHT_PT
    x0, y0, x1, y1 = box
    return (round(x0 * sx), round(y0 * sy), round(x1 * sx), round(y1 * sy))


crop300_px = point_box_to_pixels(FIGURE_CAPTION_BBOX_PT, page300)
crop72_px = point_box_to_pixels(FIGURE_CAPTION_BBOX_PT, page72)
figure300 = page300.crop(crop300_px)
figure72 = page72.crop(crop72_px)
figure72.save(ROOT / "14_figure_caption_native72.png")
figure300.save(ROOT / "15_figure_caption_native300.png")
figure300.convert("L").save(ROOT / "16_figure_caption_gray300.png")

font = ImageFont.load_default()


def local_pixel_box(box: tuple[float, float, float, float], image: Image.Image) -> tuple[int, int, int, int]:
    x0, y0, x1, y1 = box
    cx0, cy0, _, _ = FIGURE_CAPTION_BBOX_PT
    sx = image.width / (FIGURE_CAPTION_BBOX_PT[2] - FIGURE_CAPTION_BBOX_PT[0])
    sy = image.height / (FIGURE_CAPTION_BBOX_PT[3] - FIGURE_CAPTION_BBOX_PT[1])
    return (round((x0 - cx0) * sx), round((y0 - cy0) * sy), round((x1 - cx0) * sx), round((y1 - cy0) * sy))


object_overlay = figure300.convert("RGBA")
odraw = ImageDraw.Draw(object_overlay, "RGBA")
palette = [(255, 0, 0, 220), (0, 120, 255, 220), (0, 160, 70, 220), (180, 60, 220, 220)]
for index, (oid, _, _, _, bbox) in enumerate(objects):
    box = local_pixel_box(bbox, figure300)
    color = palette[index % len(palette)]
    odraw.rectangle(box, outline=color, width=3)
    odraw.rectangle((box[0], max(0, box[1] - 12), box[0] + 33, box[1]), fill=(255, 255, 255, 220))
    odraw.text((box[0] + 1, max(0, box[1] - 12)), oid[1:], fill=color, font=font)
object_overlay.convert("RGB").save(ROOT / "17_object_overlay.png")

semantic_overlay = figure300.convert("RGBA")
sdraw = ImageDraw.Draw(semantic_overlay, "RGBA")
regions = [
    ((87, 64, 267, 224), (0, 100, 255, 45), "TRUE POSTERIOR / COUPLED"),
    ((335, 64, 520, 224), (0, 180, 100, 45), "MEAN FIELD / FACTORIZED"),
    ((394, 112, 415, 147), (255, 120, 0, 90), "CUT"),
    ((120, 236, 500, 276), (80, 70, 200, 45), "SEMANTIC CONCLUSION"),
    ((70, 277, 541, 307), (220, 30, 80, 35), "CAPTION"),
]
for bbox, fill, label in regions:
    box = local_pixel_box(bbox, figure300)
    sdraw.rectangle(box, fill=fill, outline=fill[:3] + (220,), width=4)
    sdraw.rectangle((box[0], box[1], min(box[2], box[0] + 180), box[1] + 14), fill=(255, 255, 255, 220))
    sdraw.text((box[0] + 2, box[1] + 1), label, fill=fill[:3] + (255,), font=font)
semantic_overlay.convert("RGB").save(ROOT / "18_semantic_overlay.png")

text_overlay = figure300.convert("RGBA")
tdraw = ImageDraw.Draw(text_overlay, "RGBA")
for word in figure_words:
    bbox = (float(word["x0"]), float(word["top"]), float(word["x1"]), float(word["bottom"]))
    box = local_pixel_box(bbox, figure300)
    tdraw.rectangle(box, outline=(230, 0, 170, 220), width=2)
text_overlay.convert("RGB").save(ROOT / "19_text_overlay.png")

rois = [
    ("R01_cut_corridor", (392, 108, 418, 151)),
    ("R02_left_coupling", (101, 106, 197, 151)),
    ("R03_left_word_arrow", (154, 106, 253, 151)),
    ("R04_right_word_arrow", (402, 103, 507, 155)),
    ("R05_right_phi_input", (389, 143, 466, 193)),
    ("R06_transition_label_arrow", (248, 107, 351, 160)),
    ("R07_bottom_summary_math", (188, 241, 418, 274)),
    ("R08_caption_first_line", (68, 275, 543, 295)),
    ("R09_caption_second_line", (68, 290, 410, 309)),
    ("R10_true_posterior_formula", (127, 198, 228, 226)),
    ("R11_factorized_formula", (378, 197, 476, 226)),
]
roi_index = []
for roi_name, bbox in rois:
    box = point_box_to_pixels(bbox, page300)
    crop = page300.crop(box)
    native_path = ROOT / f"20_{roi_name}_native1x.png"
    nearest_path = ROOT / f"21_{roi_name}_nearest8x.png"
    crop.save(native_path)
    crop.resize((crop.width * 8, crop.height * 8), Image.Resampling.NEAREST).save(nearest_path)
    roi_index.append(
        {
            "roi_id": roi_name,
            "bbox_points": bbox,
            "native_pixel_size": [crop.width, crop.height],
            "native_file": native_path.name,
            "nearest8x_file": nearest_path.name,
        }
    )
write_json(ROOT / "22_roi_index.json", roi_index)

render_identity = []
for path in [
    page72_path,
    page200_path,
    page300_path,
    ROOT / "13_full_page_gray300.png",
    ROOT / "14_figure_caption_native72.png",
    ROOT / "15_figure_caption_native300.png",
    ROOT / "16_figure_caption_gray300.png",
    ROOT / "17_object_overlay.png",
    ROOT / "18_semantic_overlay.png",
    ROOT / "19_text_overlay.png",
]:
    with Image.open(path) as image:
        render_identity.append({"file": path.name, "width": image.width, "height": image.height, "mode": image.mode, "bytes": path.stat().st_size})
write_json(ROOT / "23_render_index.json", render_identity)

print("STATUS=MACHINE_EVIDENCE_READY")
print("PHYSICAL_PAGE=740")
print("PRINTED_PAGE=727")
print("FIGURE_NUMBER=35.6")
print("N=28")
print("C=378")
print("ROIS=11")
