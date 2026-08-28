from pathlib import Path
import csv
import math
import numpy as np
from PIL import Image


ROOT = Path(__file__).resolve().parent
PAGE = np.asarray(Image.open(ROOT / "r115_p116_full_300dpi.png").convert("RGB"))
SCALE = 300.0 / 72.0

TEXT_BOXES_PT = {
    "E08": (197.900, 488.157468, 203.469116, 498.120108),
    "E09": (405.804, 398.737468, 410.884946, 408.700108),
    "E10": (228.579, 430.867790, 303.013081, 440.033420),
    "E11A": (378.261, 388.352496, 414.923520, 398.168886),
    "E11B": (417.077, 388.700790, 423.951222, 397.866420),
    "E13": (213.102, 535.713790, 393.133304, 544.879420),
    "E14A": (201.195, 551.752338, 211.157640, 566.178240),
    "E14B": (213.499, 555.717468, 226.091777, 565.680108),
    "E15": (236.054, 555.338888, 405.418880, 566.008875),
}


def coords_from_box(box, selector):
    x0, y0, x1, y1 = box
    crop = PAGE[y0:y1, x0:x1]
    local = selector(crop)
    yy, xx = np.nonzero(local)
    return np.column_stack((yy + y0, xx + x0)).astype(np.int32)


def text_coords(ptbox):
    x0, y0, x1, y1 = ptbox
    box = (int(math.floor(x0 * SCALE)) - 2, int(math.floor(y0 * SCALE)) - 2,
           int(math.ceil(x1 * SCALE)) + 2, int(math.ceil(y1 * SCALE)) + 2)
    def sel(c):
        gray = 0.299 * c[:, :, 0] + 0.587 * c[:, :, 1] + 0.114 * c[:, :, 2]
        spread = c.max(axis=2).astype(np.int16) - c.min(axis=2).astype(np.int16)
        return (gray < 200) & (spread <= 24)
    return coords_from_box(box, sel)


def saturated_blue(c):
    ci = c.astype(np.int16)
    return ((ci[:, :, 2] - ci[:, :, 0]) > 28) & ((ci[:, :, 2] - ci[:, :, 1]) > 7) & (ci[:, :, 2] < 225)


def dark_neutral(c):
    gray = 0.299 * c[:, :, 0] + 0.587 * c[:, :, 1] + 0.114 * c[:, :, 2]
    spread = c.max(axis=2).astype(np.int16) - c.min(axis=2).astype(np.int16)
    return (gray < 120) & (spread <= 35)


def pale_blue(c):
    ci = c.astype(np.int16)
    gray = 0.299 * c[:, :, 0] + 0.587 * c[:, :, 1] + 0.114 * c[:, :, 2]
    return ((ci[:, :, 2] - ci[:, :, 0]) > 8) & (gray > 135) & (gray < 245)


def min_gap(a, b):
    if not len(a) or not len(b):
        return None
    best = float("inf")
    for start in range(0, len(a), 256):
        aa = a[start:start + 256]
        d2 = ((aa[:, None, :] - b[None, :, :]) ** 2).sum(axis=2)
        best = min(best, float(d2.min()))
    # Pixel-center distance minus one pixel gives the count of intervening pixels.
    return max(0.0, math.sqrt(best) - 1.0)


texts = {eid: text_coords(box) for eid, box in TEXT_BOXES_PT.items()}
graphics = {
    "G_X_MARKER": coords_from_box((860, 1970, 920, 2040), dark_neutral),
    "G_Y_MARKER": coords_from_box((1605, 1690, 1685, 1770), dark_neutral),
    "G_CHORD": coords_from_box((870, 1700, 1680, 2050), saturated_blue),
    "G_REGION_BOUNDARY_NEAR_C_Y": coords_from_box((1500, 1520, 1850, 1810), saturated_blue),
    "G_NOTE_BORDER": coords_from_box((830, 2170, 1720, 2320), pale_blue),
}

checks = [
    ("C01", "E08", "G_X_MARKER", "x-label to x-marker/chord junction"),
    ("C02", "E09", "G_Y_MARKER", "y-label to y-marker/chord junction"),
    ("C03", "E10", "G_CHORD", "z-formula ink to chord"),
    ("C04", "E11A", "G_REGION_BOUNDARY_NEAR_C_Y", "Chinese region-label ink to visible region boundary"),
    ("C05", "E11B", "G_REGION_BOUNDARY_NEAR_C_Y", "math C ink to visible region boundary"),
    ("C06", "E09", "E11A", "y-label ink to Chinese region-label ink"),
    ("C07", "E09", "E11B", "y-label ink to math C ink"),
    ("C08", "E13", "G_NOTE_BORDER", "conclusion formula ink to rounded border"),
    ("C09", "E14A", "G_NOTE_BORDER", "caption-number Chinese ink to note border"),
    ("C10", "E14B", "G_NOTE_BORDER", "caption-number digits to note border"),
    ("C11", "E15", "G_NOTE_BORDER", "caption text ink to note border"),
    ("C12", "E14B", "E15", "caption number digits to caption text"),
]

all_masks = {**texts, **graphics}
rows = []
for cid, a, b, description in checks:
    gap = min_gap(all_masks[a], all_masks[b])
    rows.append({
        "CHECK_ID": cid,
        "ELEMENT_A": a,
        "ELEMENT_B": b,
        "AUTO_MIN_INTERVENING_PIXEL_GAP": "" if gap is None else f"{gap:.3f}",
        "DESCRIPTION": description,
        "AUTO_METHOD": "final_R115_300dpi_color-separated visible-ink masks; Euclidean center distance minus 1",
    })

with (ROOT / "automated_critical_clearances.csv").open("w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=rows[0].keys(), lineterminator="\n")
    w.writeheader()
    w.writerows(rows)

for row in rows:
    print(row)
