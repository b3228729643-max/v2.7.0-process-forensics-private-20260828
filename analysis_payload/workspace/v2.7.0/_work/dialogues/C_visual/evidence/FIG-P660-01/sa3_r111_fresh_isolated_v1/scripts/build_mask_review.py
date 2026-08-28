from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P660-01\sa3_r111_fresh_isolated_v1")
BASE = Image.open(ROOT / "renders" / "full_page_709_native300dpi.png").convert("RGB")
PAGE_W_PT = 595.2760009765625
PAGE_H_PT = 841.8900146484375
SX = BASE.width / PAGE_W_PT
SY = BASE.height / PAGE_H_PT
LOCAL_PDF = (55.0, 60.0, 530.0, 338.0)
COLORS = [
    (220, 20, 60), (0, 110, 255), (255, 140, 0), (120, 50, 180),
    (0, 150, 120), (210, 80, 160), (120, 120, 0), (40, 160, 210),
    (160, 80, 20), (0, 80, 160), (180, 0, 0), (80, 0, 180),
    (220, 100, 0), (0, 130, 80), (120, 0, 120), (40, 40, 40),
]


def px_box(box):
    return tuple(int(round(v * s)) for v, s in zip(box, (SX, SY, SX, SY)))


def read_mask(oid):
    return np.asarray(Image.open(ROOT / "masks" / f"object_{oid}.png").convert("L")) < 128


local_px = px_box(LOCAL_PDF)
lx0, ly0, lx1, ly1 = local_px
local = BASE.crop(local_px)
layer = np.full((local.height, local.width, 3), 255, dtype=np.uint8)
for i in range(16):
    oid = f"O{i + 1:02d}"
    mask = read_mask(oid)[ly0:ly1, lx0:lx1]
    layer[mask] = COLORS[i]

mask_img = Image.fromarray(layer)
canvas = Image.new("RGB", (local.width * 2, local.height + 48), "white")
canvas.paste(local, (0, 48))
canvas.paste(mask_img, (local.width, 48))
draw = ImageDraw.Draw(canvas)
font = ImageFont.load_default()
draw.text((8, 16), "native 300 dpi local figure", fill="black", font=font)
draw.text((local.width + 8, 16), "16-object semantic foreground-mask composite", fill="black", font=font)
canvas.save(ROOT / "overlays" / "semantic_mask_composite_native300dpi.png")

# Candidate P001: O01 simplex geometry versus O02 component construction.
cand_pdf = (85.0, 95.0, 296.0, 277.0)
cx0, cy0, cx1, cy1 = px_box(cand_pdf)
orig = np.asarray(BASE.crop((cx0, cy0, cx1, cy1))).copy()
m1 = read_mask("O01")[cy0:cy1, cx0:cx1]
m2 = read_mask("O02")[cy0:cy1, cx0:cx1]
vis = orig.copy()
vis[m1] = (0.30 * vis[m1] + 0.70 * np.array((255, 40, 40))).astype(np.uint8)
vis[m2] = (0.30 * vis[m2] + 0.70 * np.array((20, 80, 255))).astype(np.uint8)
both = m1 & m2
vis[both] = np.array((255, 0, 255), dtype=np.uint8)
tile = Image.new("RGB", (orig.shape[1] * 2, orig.shape[0] + 48), "white")
tile.paste(Image.fromarray(orig), (0, 48))
tile.paste(Image.fromarray(vis), (orig.shape[1], 48))
td = ImageDraw.Draw(tile)
td.text((8, 16), "P001 native pixels", fill="black", font=font)
td.text((orig.shape[1] + 8, 16), "O01 red / O02 blue / coordinate intersection magenta", fill="black", font=font)
native_path = ROOT / "overlays" / "candidate_P001_O01_O02_native1x.png"
tile.save(native_path)
tile.resize((tile.width * 8, tile.height * 8), Image.Resampling.NEAREST).save(
    ROOT / "overlays" / "candidate_P001_O01_O02_nearest8x.png"
)

print("mask_review_generated")
