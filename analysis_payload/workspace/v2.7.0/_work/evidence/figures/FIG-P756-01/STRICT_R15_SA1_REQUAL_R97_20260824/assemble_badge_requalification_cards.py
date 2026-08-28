from pathlib import Path
import csv
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "badge_fill_border_requalification.csv"
DST = ROOT / "badge_requalification_review_cards"
DST.mkdir(exist_ok=True)

try:
    FONT = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 20)
except OSError:
    FONT = ImageFont.load_default()


def make_card(title: str, paths: list[str], out_name: str) -> None:
    labels = ["native 1x", "mask A", "mask B", "overlay", "8x nearest"]
    panels = [Image.open(ROOT / rel).convert("RGBA") for rel in paths]
    pad, head, gap = 16, 56, 8
    top_h = max(im.height for im in panels[:4])
    top_w = sum(im.width for im in panels[:4]) + gap * 3
    bot_w, bot_h = panels[4].size
    width = max(top_w, bot_w) + 2 * pad
    height = head + top_h + gap + 28 + bot_h + 2 * pad
    canvas = Image.new("RGBA", (width, height), "white")
    draw = ImageDraw.Draw(canvas)
    draw.text((pad, 8), title, fill="black", font=FONT)
    x = pad
    for label, panel in zip(labels[:4], panels[:4]):
        draw.text((x, head - 24), label, fill="black", font=FONT)
        canvas.alpha_composite(panel, (x, head))
        x += panel.width + gap
    by = head + top_h + gap + 28
    draw.text((pad, by - 24), labels[4], fill="black", font=FONT)
    canvas.alpha_composite(panels[4], (pad, by))
    canvas.convert("RGB").save(DST / out_name)


with SRC.open(newline="", encoding="utf-8-sig") as fh:
    rows = list(csv.DictReader(fh))

index = []
for row in rows:
    n = int(row["DRAWING_INDEX"]) - 16
    split = row["FILL_BORDER_PIXEL_EVIDENCE"].split(";")
    padding = row["DIGIT_BORDER_PIXEL_EVIDENCE"].split(";")
    split_name = f"BADGE_{n}_FILL_BORDER_5up.png"
    padding_name = f"BADGE_{n}_DIGIT_BORDER_5up.png"
    make_card(
        f"BADGE {n}  FILL / STROKE (same PDF fs path; intentional paint-order components)",
        split,
        split_name,
    )
    make_card(
        f"BADGE {n}  DIGIT / true STROKE border  [clearance={row['DIGIT_BORDER_CLEARANCE_PX']} px; {row['DIGIT_BORDER_STATUS']}]",
        padding,
        padding_name,
    )
    index.append({
        "DRAWING_INDEX": row["DRAWING_INDEX"],
        "FILL_BORDER_CARD": f"badge_requalification_review_cards/{split_name}",
        "DIGIT_BORDER_CARD": f"badge_requalification_review_cards/{padding_name}",
        "DIGIT_BORDER_STATUS_MACHINE": row["DIGIT_BORDER_STATUS"],
        "DIGIT_BORDER_CLEARANCE_PX": row["DIGIT_BORDER_CLEARANCE_PX"],
    })

with (ROOT / "badge_requalification_review_card_index.csv").open("w", newline="", encoding="utf-8") as fh:
    writer = csv.DictWriter(fh, fieldnames=list(index[0]))
    writer.writeheader()
    writer.writerows(index)
