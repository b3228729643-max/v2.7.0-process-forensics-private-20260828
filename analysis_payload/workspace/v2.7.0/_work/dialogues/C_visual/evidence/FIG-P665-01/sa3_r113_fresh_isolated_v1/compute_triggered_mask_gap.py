import csv
import math
from pathlib import Path

import numpy as np
from PIL import Image


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P665-01\sa3_r113_fresh_isolated_v1")


def mask_points(object_id: str) -> np.ndarray:
    arr = np.asarray(Image.open(ROOT / "masks" / f"{object_id}_collision_mask.png").convert("L"))
    return np.argwhere(arr == 0).astype(np.int32)


def min_center_distance(a: np.ndarray, b: np.ndarray) -> float:
    if len(a) == 0 or len(b) == 0:
        return float("nan")
    best = float("inf")
    for start in range(0, len(a), 256):
        chunk = a[start:start + 256]
        diff = chunk[:, None, :] - b[None, :, :]
        dist2 = np.sum(diff.astype(np.int64) ** 2, axis=2)
        local = int(dist2.min())
        if local < best:
            best = local
        if best == 0:
            break
    return math.sqrt(best)


rows = []
with (ROOT / "all_unordered_pairs_machine.csv").open("r", encoding="utf-8", newline="") as f:
    for pair in csv.DictReader(f):
        threshold = float(pair["RULE_THRESHOLD_PX"])
        logical_clearance = float(pair["CLEARANCE_METRIC_PX"])
        if threshold <= 0 or logical_clearance > 20:
            continue
        a = mask_points(pair["OBJECT_A"])
        b = mask_points(pair["OBJECT_B"])
        center_distance = min_center_distance(a, b)
        rows.append({
            "PAIR_ID": pair["PAIR_ID"],
            "OBJECT_A": pair["OBJECT_A"],
            "OBJECT_B": pair["OBJECT_B"],
            "LOGICAL_BBOX_CLEARANCE_PX": pair["CLEARANCE_METRIC_PX"],
            "RULE_THRESHOLD_PX": pair["RULE_THRESHOLD_PX"],
            "MACHINE_RISK_TRIGGER": pair["MACHINE_RISK_TRIGGER"],
            "RASTER_FOREGROUND_CENTER_DISTANCE_PX": round(center_distance, 6),
            "RASTER_BLANK_PIXEL_GAP_ESTIMATE_PX": round(max(0.0, center_distance - 1.0), 6),
        })

out = ROOT / "near_threshold_mask_gaps_machine.csv"
fields = list(rows[0].keys()) if rows else ["PAIR_ID"]
with out.open("w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=fields)
    w.writeheader()
    w.writerows(rows)

triggered = [row for row in rows if row["MACHINE_RISK_TRIGGER"] == "NUMERIC_CLEARANCE_RISK"]
triggered_out = ROOT / "triggered_mask_gap_machine.csv"
triggered_fields = list(triggered[0].keys()) if triggered else ["PAIR_ID"]
with triggered_out.open("w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=triggered_fields)
    w.writeheader()
    w.writerows(triggered)
