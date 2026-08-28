from __future__ import annotations

import csv
import hashlib
import json
import math
import shutil
from collections import Counter
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy.spatial import cKDTree


ROOT = Path(__file__).resolve().parent
WORKSPACE = Path(r"D:\Users\ASUS\Desktop\机器学习")
OLD = WORKSPACE / r"v2.7.0\_work\evidence\figures\FIG-P580-01\STRICT_R2_SA2_R95_LOCAL_20260824"
SOURCE = WORKSPACE / r"v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C02\fig_v5_c02_is_support.tex"
INPUT_MASK_DIR = ROOT / "input_graphic_masks"
PACKAGE_ROOT = ROOT / "critical_pairs"
FULL_W, FULL_H = 2481, 3508
PAD = 12


LEGAL_OVERLAP = {
    "PAIR_GR001_GR003": (
        "AXIS_TICK_CONNECTION",
        "左图横轴刻度短线有意落在承载它们的横轴描边上；交集只位于刻度—横轴接点，不遮挡数据或文字。",
    ),
    "PAIR_GR001_GR005": (
        "AXIS_ORIGIN_CONNECTION",
        "左图 x=0 的横轴刻度与纵轴在坐标原点共用框架接点；交集是坐标系结构连接。",
    ),
    "PAIR_GR001_GR007": (
        "CURVE_AXIS_ENDPOINT_CONNECTION",
        "左图目标密度满足 p(0)=0，蓝色目标曲线在定义域左端收束到 x=0 刻度；单像素交集是函数端点接轴。",
    ),
    "PAIR_GR001_GR010": (
        "BOUNDARY_TICK_CONNECTION",
        "左图支撑边界 x=5/2 的点线从同名横轴刻度起画；交集是边界线锚定到 5/2 刻度的设计连接。",
    ),
    "PAIR_GR001_GR025": (
        "TICK_REGION_BOUNDARY_CONNECTION",
        "左图缺失支撑斜线区以横轴为下边界，横轴刻度穿过该边界；交集局限于纹理区下边界的刻度接点。",
    ),
    "PAIR_GR002_GR003": (
        "AXIS_ORIGIN_CONNECTION",
        "左图 y=0 纵轴刻度与横轴在原点共用坐标框架接点；交集不是独立数据图形碰撞。",
    ),
    "PAIR_GR002_GR005": (
        "AXIS_TICK_CONNECTION",
        "左图各纵轴刻度短线有意横跨其承载纵轴；交集仅为刻度—纵轴连接。",
    ),
    "PAIR_GR003_GR010": (
        "BOUNDARY_AXIS_CONNECTION",
        "左图 x=5/2 支撑边界从横轴起始；交集是支撑边界与坐标轴的语义锚点。",
    ),
    "PAIR_GR003_GR025": (
        "AXIS_REGION_BOUNDARY_CONNECTION",
        "左图斜线缺失区的下边界就是横轴；交集表示区域闭合到 y=0，而非区域覆盖独立数据。",
    ),
    "PAIR_GR004_GR025": (
        "DOMAIN_ENDPOINT_REGION_ARROW_CONNECTION",
        "左图斜线区在定义域右端 x=5 随 p(5)=0 收束到横轴箭头端点；交集局限于共同域端点的区域尖端—轴箭头连接。",
    ),
    "PAIR_GR005_GR006": (
        "AXIS_ARROWHEAD_CONNECTION",
        "左图纵轴描边与其箭头头部必须共接形成连续坐标轴；交集位于轴端连接。",
    ),
    "PAIR_GR007_GR025": (
        "CURVE_REGION_BOUNDARY_CONNECTION",
        "左图蓝色 p(x) 曲线正是斜线缺失区的上边界；交集表示区域沿目标曲线闭合。",
    ),
    "PAIR_GR008_GR011": (
        "CURVE_MARKER_CONNECTION",
        "左图青色实方块标记 q_L 在 x=5/2 的已包含端点，中心落在 q_L=2/5 虚线上；交集是曲线—自身端点标记连接。",
    ),
    "PAIR_GR009_GR012": (
        "CURVE_MARKER_CONNECTION",
        "左图青色空心圆标记 x=5/2 后 q_L=0 的排除端点，中心落在零线；交集是曲线—自身端点标记连接。",
    ),
    "PAIR_GR010_GR025": (
        "BOUNDARY_REGION_CONNECTION",
        "左图 x=5/2 点线是斜线缺失区的左边界；交集表示区域从支撑截止线开始。",
    ),
    "PAIR_GR013_GR015": (
        "AXIS_TICK_CONNECTION",
        "右图横轴刻度短线有意落在其承载横轴上；交集仅为刻度—横轴接点。",
    ),
    "PAIR_GR013_GR017": (
        "AXIS_ORIGIN_CONNECTION",
        "右图 x=0 横轴刻度与纵轴在原点共用坐标框架接点；交集是结构连接。",
    ),
    "PAIR_GR013_GR019": (
        "CURVE_AXIS_ENDPOINT_CONNECTION",
        "右图目标密度满足 p(0)=0，蓝色目标曲线在左端收束到 x=0 刻度；交集是函数端点接轴。",
    ),
    "PAIR_GR014_GR015": (
        "AXIS_ORIGIN_CONNECTION",
        "右图 y=0 纵轴刻度与横轴在原点共用坐标框架接点；交集不是数据遮挡。",
    ),
    "PAIR_GR014_GR017": (
        "AXIS_TICK_CONNECTION",
        "右图各纵轴刻度短线有意横跨其承载纵轴；交集仅为刻度—纵轴连接。",
    ),
    "PAIR_GR015_GR016": (
        "AXIS_ARROWHEAD_CONNECTION",
        "右图横轴描边与其箭头头部共接形成连续坐标轴；交集位于轴端连接。",
    ),
    "PAIR_GR017_GR018": (
        "AXIS_ARROWHEAD_CONNECTION",
        "右图纵轴描边与其箭头头部共接形成连续坐标轴；交集位于轴端连接。",
    ),
    "PAIR_GR019_GR022": (
        "CURVE_MARKER_CONNECTION",
        "右图 x=1 的蓝色圆标记用于读取 p(1)，中心落在蓝色 p 曲线上；交集是曲线—自身采样标记连接。",
    ),
    "PAIR_GR019_GR023": (
        "CURVE_MARKER_CONNECTION",
        "右图 x=5/2 的蓝色方标记用于读取 p(5/2)，中心落在蓝色 p 曲线上；交集是曲线—自身采样标记连接。",
    ),
    "PAIR_GR019_GR024": (
        "CURVE_MARKER_CONNECTION",
        "右图 x=4 的蓝色三角标记用于读取 p(4)，中心落在蓝色 p 曲线上；交集是曲线—自身采样标记连接。",
    ),
    "PAIR_GR020_GR024": (
        "PROPOSAL_CURVE_TARGET_MARKER_COMPARISON",
        "右图 q_R(4)=1/5 与 p(4)=24/125 仅差 1/125；位于真实 p(4) 的有限尺寸三角标记上缘与 q_R 虚线相接，2 像素接点直观呈现 w(4)=24/25 的近单位比率且不改变任一数值。",
    ),
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def parse_bbox(value: str) -> tuple[int, int, int, int]:
    parsed = json.loads(value)
    if len(parsed) != 4:
        raise ValueError(value)
    return tuple(int(item) for item in parsed)


def save_bool_mask(mask: np.ndarray, path: Path) -> None:
    Image.fromarray(np.where(mask, 0, 255).astype(np.uint8), mode="L").save(path)


def save_nearest_8x(source: Path, destination: Path) -> None:
    with Image.open(source) as image:
        image.resize((image.width * 8, image.height * 8), Image.Resampling.NEAREST).save(destination)


def make_review_sheet(paths: list[tuple[str, Path]], destination: Path) -> None:
    images = [(label, Image.open(path).convert("RGB")) for label, path in paths]
    width, height = images[0][1].size
    label_height = 18
    if width >= height:
        sheet = Image.new("RGB", (width, len(images) * (height + label_height)), "white")
        draw = ImageDraw.Draw(sheet)
        y = 0
        for label, image in images:
            draw.text((2, y + 2), label, fill="black")
            sheet.paste(image, (0, y + label_height))
            y += height + label_height
    else:
        sheet = Image.new("RGB", (len(images) * width, height + label_height), "white")
        draw = ImageDraw.Draw(sheet)
        x = 0
        for label, image in images:
            draw.text((x + 2, 2), label, fill="black")
            sheet.paste(image, (x, label_height))
            x += width
    sheet.save(destination)
    for _, image in images:
        image.close()


def local_mask(mask: np.ndarray, bbox: tuple[int, int, int, int], roi: tuple[int, int, int, int]) -> np.ndarray:
    rx0, ry0, rx1, ry1 = roi
    output = np.zeros((ry1 - ry0, rx1 - rx0), dtype=bool)
    bx0, by0, bx1, by1 = bbox
    ix0, iy0 = max(rx0, bx0), max(ry0, by0)
    ix1, iy1 = min(rx1, bx1), min(ry1, by1)
    if ix0 < ix1 and iy0 < iy1:
        output[iy0 - ry0 : iy1 - ry0, ix0 - rx0 : ix1 - rx0] = mask[
            iy0 - by0 : iy1 - by0, ix0 - bx0 : ix1 - bx0
        ]
    return output


def main() -> int:
    if ROOT == OLD or OLD in ROOT.parents:
        raise RuntimeError("new closeout root must not be the sealed R2 package")
    INPUT_MASK_DIR.mkdir(parents=True, exist_ok=True)
    PACKAGE_ROOT.mkdir(parents=True, exist_ok=True)

    full_page_source = OLD / "full_page_300dpi.png"
    full_page_copy = ROOT / "input_full_page_300dpi.png"
    shutil.copy2(full_page_source, full_page_copy)
    with Image.open(full_page_copy) as image:
        if image.size != (FULL_W, FULL_H):
            raise RuntimeError(f"unexpected full-page grid: {image.size}")
        full_page = image.convert("RGB")

    inventory = [row for row in read_csv(OLD / "object_inventory.csv") if row["KIND"] == "GRAPHIC"]
    if len(inventory) != 25 or len({row["OBJECT_ID"] for row in inventory}) != 25:
        raise RuntimeError("graphic inventory is not 25 unique objects")
    by_id = {row["OBJECT_ID"]: row for row in inventory}

    masks: dict[str, np.ndarray] = {}
    bboxes: dict[str, tuple[int, int, int, int]] = {}
    coords: dict[str, np.ndarray] = {}
    linear: dict[str, np.ndarray] = {}
    trees: dict[str, cKDTree] = {}
    input_inventory_rows: list[dict[str, object]] = []
    for row in inventory:
        object_id = row["OBJECT_ID"]
        source_mask = OLD / row["RAW_MASK"]
        target_mask = INPUT_MASK_DIR / f"{object_id}_raw.png"
        shutil.copy2(source_mask, target_mask)
        bbox = parse_bbox(row["BBOX_FULL_PAGE_PX"])
        with Image.open(target_mask) as image:
            mask = np.array(image.convert("L")) < 128
        if mask.shape != (bbox[3] - bbox[1], bbox[2] - bbox[0]):
            raise RuntimeError(f"mask/bbox mismatch: {object_id}")
        if int(mask.sum()) != int(row["PIXELS"]):
            raise RuntimeError(f"pixel-count mismatch: {object_id}")
        local_coords = np.argwhere(mask)
        full_coords = local_coords + np.array([bbox[1], bbox[0]])
        masks[object_id] = mask
        bboxes[object_id] = bbox
        coords[object_id] = full_coords
        linear[object_id] = np.sort(full_coords[:, 0].astype(np.int64) * FULL_W + full_coords[:, 1])
        trees[object_id] = cKDTree(full_coords.astype(float))
        input_inventory_rows.append({
            "OBJECT_ID": object_id,
            "ROLE": row["ROLE"],
            "PANEL": row["PANEL"],
            "TEXT_OR_LABEL": row["TEXT_OR_LABEL"],
            "BBOX_FULL_PAGE_PX": row["BBOX_FULL_PAGE_PX"],
            "PIXELS": int(mask.sum()),
            "RAW_MASK": f"input_graphic_masks/{object_id}_raw.png",
            "RAW_MASK_SHA256": sha256(target_mask),
            "SOURCE_R2_MASK": str(source_mask),
        })
    write_csv(
        ROOT / "graphic_object_inventory.csv",
        input_inventory_rows,
        ["OBJECT_ID", "ROLE", "PANEL", "TEXT_OR_LABEL", "BBOX_FULL_PAGE_PX", "PIXELS", "RAW_MASK", "RAW_MASK_SHA256", "SOURCE_R2_MASK"],
    )

    all_pairs = read_csv(OLD / "all_unordered_pairs.csv")
    old_graphic_pairs = [row for row in all_pairs if row["RELATION_TYPE"] == "GRAPHIC_GRAPHIC_DECLARED_GEOMETRY"]
    if len(old_graphic_pairs) != 300:
        raise RuntimeError(f"expected 300 old graphic pairs, got {len(old_graphic_pairs)}")

    machine_rows: list[dict[str, object]] = []
    package_rows: list[dict[str, object]] = []
    for old_row in old_graphic_pairs:
        a, b = old_row["OBJECT_A"], old_row["OBJECT_B"]
        pair_id = old_row["PAIR_ID"]
        overlap_linear = np.intersect1d(linear[a], linear[b], assume_unique=True)
        overlap = int(overlap_linear.size)
        distance_to_a, nearest_a_index = trees[a].query(coords[b].astype(float), k=1)
        min_center_distance = float(distance_to_a.min())
        clearance = 0.0 if overlap else max(min_center_distance - 1.0, 0.0)
        old_overlap = int(old_row["OVERLAP_PIXEL_COUNT"])
        old_clearance = float(old_row["CLEARANCE_PX"])
        old_numeric_match = old_overlap == overlap and math.isclose(old_clearance, clearance, rel_tol=0.0, abs_tol=1e-6)

        if overlap:
            critical_kind = "OVERLAP"
        elif math.isclose(clearance, 0.0, rel_tol=0.0, abs_tol=1e-12):
            critical_kind = "ZERO_CLEARANCE_NO_OVERLAP"
        else:
            critical_kind = "NONCRITICAL_DISJOINT"
        if old_overlap:
            old_critical_kind = "OVERLAP"
        elif math.isclose(old_clearance, 0.0, rel_tol=0.0, abs_tol=1e-12):
            old_critical_kind = "ZERO_CLEARANCE_NO_OVERLAP"
        else:
            old_critical_kind = "NONCRITICAL_DISJOINT"

        package_reference = "NOT_REQUIRED_CLEARANCE_GT_0"
        closest_a = coords[a][int(nearest_a_index[int(np.argmin(distance_to_a))])]
        closest_b = coords[b][int(np.argmin(distance_to_a))]
        contact_point_count = 0
        if critical_kind != "NONCRITICAL_DISJOINT":
            package_dir = PACKAGE_ROOT / pair_id
            package_dir.mkdir(parents=True, exist_ok=True)
            package_reference = f"critical_pairs/{pair_id}/package_manifest.json"
            if overlap:
                iy = overlap_linear // FULL_W
                ix = overlap_linear % FULL_W
                interaction = np.column_stack((iy, ix)).astype(int)
                contact_point_count = overlap
            else:
                touch_points: set[tuple[int, int]] = set()
                for b_index in np.flatnonzero(np.isclose(distance_to_a, min_center_distance, atol=1e-12, rtol=0.0)):
                    b_coord = coords[b][b_index]
                    a_coord = coords[a][int(nearest_a_index[b_index])]
                    touch_points.add((int(a_coord[0]), int(a_coord[1])))
                    touch_points.add((int(b_coord[0]), int(b_coord[1])))
                reverse_distance, reverse_index = trees[b].query(coords[a].astype(float), k=1)
                for a_index in np.flatnonzero(np.isclose(reverse_distance, min_center_distance, atol=1e-12, rtol=0.0)):
                    a_coord = coords[a][a_index]
                    b_coord = coords[b][int(reverse_index[a_index])]
                    touch_points.add((int(a_coord[0]), int(a_coord[1])))
                    touch_points.add((int(b_coord[0]), int(b_coord[1])))
                interaction = np.array(sorted(touch_points), dtype=int)
                contact_point_count = len(touch_points) // 2
            rx0 = max(0, int(interaction[:, 1].min()) - PAD)
            ry0 = max(0, int(interaction[:, 0].min()) - PAD)
            rx1 = min(FULL_W, int(interaction[:, 1].max()) + PAD + 1)
            ry1 = min(FULL_H, int(interaction[:, 0].max()) + PAD + 1)
            roi = (rx0, ry0, rx1, ry1)
            a_roi = local_mask(masks[a], bboxes[a], roi)
            b_roi = local_mask(masks[b], bboxes[b], roi)
            intersection_roi = a_roi & b_roi
            raw_roi = full_page.crop(roi)
            raw_1x = package_dir / "raw_roi_1x.png"
            a_1x = package_dir / "mask_A_1x.png"
            b_1x = package_dir / "mask_B_1x.png"
            intersection_1x = package_dir / "intersection_1x.png"
            overlay_1x = package_dir / "overlay_1x.png"
            raw_roi.save(raw_1x)
            save_bool_mask(a_roi, a_1x)
            save_bool_mask(b_roi, b_1x)
            save_bool_mask(intersection_roi, intersection_1x)
            overlay = np.array(raw_roi, dtype=np.uint8)
            overlay[a_roi] = np.array([230, 45, 45], dtype=np.uint8)
            overlay[b_roi] = np.array([40, 105, 235], dtype=np.uint8)
            overlay[intersection_roi] = np.array([255, 215, 0], dtype=np.uint8)
            Image.fromarray(overlay, mode="RGB").save(overlay_1x)
            one_x_paths = [
                ("RAW ROI 1X", raw_1x),
                (f"A {a} 1X", a_1x),
                (f"B {b} 1X", b_1x),
                ("INTERSECTION 1X", intersection_1x),
                ("OVERLAY 1X", overlay_1x),
            ]
            eight_x_paths: list[tuple[str, Path]] = []
            for label, source_path in one_x_paths:
                target = source_path.with_name(source_path.stem.replace("_1x", "_8x_nearest") + ".png")
                save_nearest_8x(source_path, target)
                eight_x_paths.append((label.replace("1X", "8X NEAREST"), target))
            review_1x = package_dir / "review_1x_sheet.png"
            review_8x = package_dir / "review_8x_nearest_sheet.png"
            make_review_sheet(one_x_paths, review_1x)
            make_review_sheet(eight_x_paths, review_8x)
            evidence_files = [path for _, path in one_x_paths + eight_x_paths] + [review_1x, review_8x]
            package_manifest = {
                "pair_id": pair_id,
                "object_a": a,
                "object_b": b,
                "critical_kind": critical_kind,
                "native_grid": [FULL_W, FULL_H],
                "measurement_dpi": 300,
                "resize_after_render": False,
                "roi_full_page_px": list(roi),
                "overlap_pixel_count": overlap,
                "minimum_pixel_center_distance_px": round(min_center_distance, 12),
                "clearance_formula": "max(minimum pixel-centre distance - 1, 0)",
                "clearance_px": round(clearance, 12),
                "closest_a_full_page_yx": [int(closest_a[0]), int(closest_a[1])],
                "closest_b_full_page_yx": [int(closest_b[0]), int(closest_b[1])],
                "interaction_point_or_contact_pair_count": contact_point_count,
                "mask_a_source": f"input_graphic_masks/{a}_raw.png",
                "mask_b_source": f"input_graphic_masks/{b}_raw.png",
                "file_hashes": {path.name: sha256(path) for path in evidence_files},
                "manual_review_required": True,
            }
            (package_dir / "package_manifest.json").write_text(
                json.dumps(package_manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )
            package_rows.append({
                "PAIR_ID": pair_id,
                "CRITICAL_KIND": critical_kind,
                "OVERLAP_PIXEL_COUNT": overlap,
                "MIN_CENTER_DISTANCE_PX": f"{min_center_distance:.12f}",
                "CLEARANCE_PX": f"{clearance:.12f}",
                "ROI_FULL_PAGE_PX": json.dumps(list(roi)),
                "PACKAGE_MANIFEST": package_reference,
                "REVIEW_1X": f"critical_pairs/{pair_id}/review_1x_sheet.png",
                "REVIEW_8X": f"critical_pairs/{pair_id}/review_8x_nearest_sheet.png",
                "EVIDENCE_IMAGE_COUNT": len(evidence_files),
                "PACKAGE_JSON_COUNT": 1,
            })

        hint_class, hint_reason = LEGAL_OVERLAP.get(pair_id, ("NOT_APPLICABLE", "No overlap; no intentional geometry claimed."))
        machine_rows.append({
            "PAIR_ID": pair_id,
            "OBJECT_A": a,
            "ROLE_A": by_id[a]["ROLE"],
            "LABEL_A": by_id[a]["TEXT_OR_LABEL"],
            "PANEL_A": by_id[a]["PANEL"],
            "OBJECT_B": b,
            "ROLE_B": by_id[b]["ROLE"],
            "LABEL_B": by_id[b]["TEXT_OR_LABEL"],
            "PANEL_B": by_id[b]["PANEL"],
            "RAW_MASK_A": f"input_graphic_masks/{a}_raw.png",
            "RAW_MASK_B": f"input_graphic_masks/{b}_raw.png",
            "ACTUALLY_RECOMPUTED": "true",
            "OVERLAP_PIXEL_COUNT": overlap,
            "MIN_CENTER_DISTANCE_PX": f"{min_center_distance:.12f}",
            "CLEARANCE_PX": f"{clearance:.12f}",
            "CRITICAL_KIND": critical_kind,
            "OLD_OVERLAP_PIXEL_COUNT": old_overlap,
            "OLD_CLEARANCE_PX": f"{old_clearance:.6f}",
            "OLD_OVERLAP_MATCH": str(old_overlap == overlap).lower(),
            "OLD_CRITICAL_KIND": old_critical_kind,
            "OLD_CRITICAL_MEMBERSHIP_MATCH": str(old_critical_kind == critical_kind).lower(),
            "OLD_POSITIVE_CLEARANCE_EXACT_MATCH": str(old_numeric_match).lower(),
            "OLD_TO_NATIVE_CLEARANCE_DELTA_PX": f"{old_clearance - clearance:.12f}",
            "PROVISIONAL_SEMANTIC_CLASS": hint_class,
            "PROVISIONAL_SPECIFIC_REASON": hint_reason,
            "EVIDENCE_REFERENCE": f"input_graphic_masks/{a}_raw.png|input_graphic_masks/{b}_raw.png|{package_reference}",
            "CRITICAL_PACKAGE": package_reference,
        })

    if len(machine_rows) != 300 or len({row["PAIR_ID"] for row in machine_rows}) != 300:
        raise RuntimeError("machine pair coverage mismatch")
    overlap_rows = [row for row in machine_rows if int(row["OVERLAP_PIXEL_COUNT"]) > 0]
    touching_rows = [row for row in machine_rows if row["CRITICAL_KIND"] == "ZERO_CLEARANCE_NO_OVERLAP"]
    if len(overlap_rows) != 26 or len(touching_rows) != 24 or set(LEGAL_OVERLAP) != {row["PAIR_ID"] for row in overlap_rows}:
        raise RuntimeError("critical pair identity mismatch")
    if not all(row["OLD_OVERLAP_MATCH"] == "true" for row in machine_rows):
        raise RuntimeError("independent raw-mask overlap recomputation disagrees with sealed overlap fields")
    if not all(row["OLD_CRITICAL_MEMBERSHIP_MATCH"] == "true" for row in machine_rows):
        raise RuntimeError("independent raw-mask critical membership disagrees with sealed fields")

    machine_fields = list(machine_rows[0])
    write_csv(ROOT / "graphic_pair_machine_measurements.csv", machine_rows, machine_fields)
    write_csv(
        ROOT / "critical_pair_package_manifest.csv",
        package_rows,
        ["PAIR_ID", "CRITICAL_KIND", "OVERLAP_PIXEL_COUNT", "MIN_CENTER_DISTANCE_PX", "CLEARANCE_PX", "ROI_FULL_PAGE_PX", "PACKAGE_MANIFEST", "REVIEW_1X", "REVIEW_8X", "EVIDENCE_IMAGE_COUNT", "PACKAGE_JSON_COUNT"],
    )
    source_hash = sha256(SOURCE)
    sealed_terminal = json.loads((OLD / "machine_final_check.json").read_text(encoding="utf-8"))
    sealed_source_hash = sealed_terminal["freeze_hashes"]["business_source_sha256"]
    identity = {
        "uid": "FIG-P580-01",
        "closeout_scope": "graphic-graphic unordered-pair evidence only",
        "schema_revision": 111,
        "sealed_r2_input_root": str(OLD),
        "sealed_r2_was_not_modified": True,
        "business_source": str(SOURCE),
        "current_source_sha256": source_hash,
        "sealed_r2_source_sha256": sealed_source_hash,
        "source_hash_unchanged": source_hash == sealed_source_hash,
        "input_full_page_300dpi_sha256": sha256(full_page_copy),
        "native_grid": [FULL_W, FULL_H],
        "measurement_dpi": 300,
        "resize_after_render": False,
        "graphic_masks": 25,
    }
    (ROOT / "input_identity.json").write_text(json.dumps(identity, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    summary = {
        "graphic_pairs_total": len(machine_rows),
        "actually_recomputed": sum(row["ACTUALLY_RECOMPUTED"] == "true" for row in machine_rows),
        "overlapped": len(overlap_rows),
        "zero_overlap_zero_clearance": len(touching_rows),
        "noncritical_disjoint": sum(row["CRITICAL_KIND"] == "NONCRITICAL_DISJOINT" for row in machine_rows),
        "critical_packages": len(package_rows),
        "critical_evidence_images": sum(int(row["EVIDENCE_IMAGE_COUNT"]) for row in package_rows),
        "old_overlap_mismatch_count": sum(row["OLD_OVERLAP_MATCH"] != "true" for row in machine_rows),
        "old_critical_membership_mismatch_count": sum(row["OLD_CRITICAL_MEMBERSHIP_MATCH"] != "true" for row in machine_rows),
        "old_positive_clearance_exact_difference_count": sum(row["OLD_POSITIVE_CLEARANCE_EXACT_MATCH"] != "true" for row in machine_rows),
        "clearance_basis_note": "R2B recomputes exact foreground-pixel centre distance from both native raw masks; sealed positive-clearance proxy values are retained only as comparison fields.",
        "provisional_overlap_classification_counts": dict(Counter(row["PROVISIONAL_SEMANTIC_CLASS"] for row in overlap_rows)),
        "manual_review_status": "PENDING_EXPLICIT_SA2_LEDGER",
    }
    (ROOT / "machine_recomputation_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
