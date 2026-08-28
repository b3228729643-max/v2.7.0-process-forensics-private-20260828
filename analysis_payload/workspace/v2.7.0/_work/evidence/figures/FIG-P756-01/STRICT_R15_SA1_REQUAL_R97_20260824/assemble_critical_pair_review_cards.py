from pathlib import Path
import csv
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "critical_pair_index.csv"
DST = ROOT / "critical_pair_review_cards"
DST.mkdir(exist_ok=True)

try:
    FONT = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 20)
except OSError:
    FONT = ImageFont.load_default()

def open_rgba(rel):
    return Image.open(ROOT / rel).convert("RGBA")

with SRC.open(newline="", encoding="utf-8-sig") as fh:
    rows = list(csv.DictReader(fh))

index_rows = []
for row in rows:
    files = row["PIXEL_EVIDENCE"].split(";")
    labels = ["native 1x", "mask A", "mask B", "overlay", "8x nearest"]
    panels = [open_rgba(p) for p in files]
    pad, head, gap = 16, 56, 8
    top_h = max(im.height for im in panels[:4])
    top_w = sum(im.width for im in panels[:4]) + gap * 3
    bot_w, bot_h = panels[4].size
    width = max(top_w, bot_w) + 2 * pad
    height = head + top_h + gap + 28 + bot_h + 2 * pad
    canvas = Image.new("RGBA", (width, height), "white")
    draw = ImageDraw.Draw(canvas)
    title = f'{row["PAIR_ID"]}  {row["OBJECT_A"]}  /  {row["OBJECT_B"]}  [{row["STATUS"]}]'
    draw.text((pad, 8), title, fill="black", font=FONT)
    x = pad
    for label, panel in zip(labels[:4], panels[:4]):
        draw.text((x, head - 24), label, fill="black", font=FONT)
        canvas.alpha_composite(panel, (x, head))
        x += panel.width + gap
    by = head + top_h + gap + 28
    draw.text((pad, by - 24), labels[4], fill="black", font=FONT)
    canvas.alpha_composite(panels[4], (pad, by))
    out = DST / f'{row["PAIR_ID"]}_5up.png'
    canvas.convert("RGB").save(out)
    index_rows.append({
        "PAIR_ID": row["PAIR_ID"],
        "OBJECT_A": row["OBJECT_A"],
        "OBJECT_B": row["OBJECT_B"],
        "STATUS_MACHINE": row["STATUS"],
        "CARD": str(out.relative_to(ROOT)).replace("\\\\", "/"),
    })

with (ROOT / "critical_pair_review_card_index.csv").open("w", newline="", encoding="utf-8") as fh:
    writer = csv.DictWriter(fh, fieldnames=list(index_rows[0]))
    writer.writeheader()
    writer.writerows(index_rows)
