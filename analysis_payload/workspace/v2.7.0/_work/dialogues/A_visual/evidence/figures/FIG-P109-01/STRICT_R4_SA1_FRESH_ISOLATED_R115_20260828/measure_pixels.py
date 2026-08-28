from pathlib import Path
import csv
import numpy as np
from PIL import Image


ROOT = Path(__file__).resolve().parent
PAGE = np.asarray(Image.open(ROOT / "r115_p116_full_300dpi.png").convert("RGB"))
SCALE = 300.0 / 72.0

# Exact word-union boxes from pdftotext -bbox on official R115 physical page 116.
TEXTS = {
    "E08": ("O08", "ENDPOINT_LABEL", "x", (197.900, 488.157468, 203.469116, 498.120108)),
    "E09": ("O09", "ENDPOINT_LABEL", "y", (405.804, 398.737468, 410.884946, 408.700108)),
    "E10": ("O10", "CONVEX_COMBINATION_LABEL", "z=lambda*x+(1-lambda)*y", (228.579, 430.867790, 303.013081, 440.033420)),
    "E11A": ("O11", "REGION_LABEL_CN", "convex feasible region", (378.261, 388.352496, 414.923520, 398.168886)),
    "E11B": ("O11", "REGION_LABEL_MATH", "C", (417.077, 388.700790, 423.951222, 397.866420)),
    "E13": ("O13", "CONCLUSION_TEXT", "x,y in C; lambda in [0,1] => lambda*x+(1-lambda)*y in C", (213.102, 535.713790, 393.133304, 544.879420)),
    "E14A": ("O14", "CAPTION_NUMBER_CN", "Figure", (201.195, 551.752338, 211.157640, 566.178240)),
    "E14B": ("O14", "CAPTION_NUMBER_DIGITS", "7.1", (213.499, 555.717468, 226.091777, 565.680108)),
    "E15": ("O15", "CAPTION_TEXT", "convex-set caption conclusion", (236.054, 555.338888, 405.418880, 566.008875)),
}


def pxbox(ptbox, pad=2):
    x0, y0, x1, y1 = ptbox
    return (max(0, int(np.floor(x0 * SCALE)) - pad),
            max(0, int(np.floor(y0 * SCALE)) - pad),
            min(PAGE.shape[1], int(np.ceil(x1 * SCALE)) + pad),
            min(PAGE.shape[0], int(np.ceil(y1 * SCALE)) + pad))


rows = []
for eid, (oid, role, sample, ptbox) in TEXTS.items():
    x0, y0, x1, y1 = pxbox(ptbox)
    crop = PAGE[y0:y1, x0:x1]
    gray = np.rint(0.299 * crop[:, :, 0] + 0.587 * crop[:, :, 1] + 0.114 * crop[:, :, 2])
    spread = crop.max(axis=2).astype(np.int16) - crop.min(axis=2).astype(np.int16)
    mask = (gray < 200) & (spread <= 24)
    yy, xx = np.nonzero(mask)
    if len(xx):
        ix0, iy0, ix1, iy1 = x0 + int(xx.min()), y0 + int(yy.min()), x0 + int(xx.max()) + 1, y0 + int(yy.max()) + 1
        h, w = iy1 - iy0, ix1 - ix0
    else:
        ix0 = iy0 = ix1 = iy1 = h = w = 0
    rows.append({
        "ELEMENT_ID": eid,
        "OBJECT_ID": oid,
        "ROLE": role,
        "TEXT_SAMPLE_ASCII": sample,
        "PDF_BBOX_PT": " ".join(f"{v:.6f}" for v in ptbox),
        "MEASUREMENT_WINDOW_300DPI": f"{x0} {y0} {x1} {y1}",
        "INK_BBOX_300DPI_GRAY_LT_200": f"{ix0} {iy0} {ix1} {iy1}",
        "H_INK_PX": h,
        "W_INK_PX": w,
        "INK_PIXEL_COUNT": int(mask.sum()),
        "AUTO_METHOD": "official_R115_page116_300dpi; Rec709_gray<200; exact_pdftotext_word_union",
    })

with (ROOT / "automated_text_pixel_observations.csv").open("w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=rows[0].keys(), lineterminator="\n")
    w.writeheader()
    w.writerows(rows)

for row in rows:
    print(row)
