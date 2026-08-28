from pathlib import Path
import csv
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\STRICT_R3A_SA2_COORDINATE_QUADRATIC_PATCH_R115_DIRECT_BUILD_20260828")
E = ROOT / "evidence"
COLOR = Image.open(E / "full_page_native300dpi.png").convert("RGB")
SCALE = 300.0 / 72.0
FONT = ImageFont.load_default()

with (E / "LOGICAL_OBJECTS.csv").open(encoding="utf-8-sig", newline="") as stream:
    objects = list(csv.DictReader(stream))

for part, rows in enumerate((objects[:7], objects[7:]), 1):
    sheet = Image.new("RGB", (1200, 1400), "white")
    draw = ImageDraw.Draw(sheet)
    for i, row in enumerate(rows):
        x0, top, x1, bottom = [float(row[k]) for k in ("x0_pt", "top_pt", "x1_pt", "bottom_pt")]
        pad = 35
        box = (max(0, int(x0*SCALE)-pad), max(0, int(top*SCALE)-pad), min(COLOR.width, int(x1*SCALE)+pad), min(COLOR.height, int(bottom*SCALE)+pad))
        crop = COLOR.crop(box)
        crop.thumbnail((1150, 155), Image.Resampling.LANCZOS)
        y = i * 195
        sheet.paste(crop, ((1200-crop.width)//2, y+30))
        draw.text((10, y+8), f"{row['object_id']} {row['role']} atoms={row['atom_count']}", fill="black", font=FONT)
        draw.rectangle((0, y, 1199, y+194), outline="#aaaaaa", width=1)
    sheet.save(E / f"logical_object_contact_sheet_part{part}.png")

candidate_dir = E / "pair_candidates"
native = sorted(candidate_dir.glob("*_native1x.png"))
for part_index in range(0, len(native), 9):
    rows = native[part_index:part_index+9]
    sheet = Image.new("RGB", (1800, 1200), "white")
    draw = ImageDraw.Draw(sheet)
    for i, path in enumerate(rows):
        image = Image.open(path).convert("RGB")
        image = image.resize((min(image.width*2, 550), min(image.height*2, 330)), Image.Resampling.NEAREST)
        col, row = i % 3, i // 3
        x = col*600 + (600-image.width)//2
        y = row*400 + 48 + (340-image.height)//2
        sheet.paste(image, (x, y))
        draw.text((col*600+8, row*400+10), path.stem.replace("_native1x", ""), fill="black", font=FONT)
        draw.rectangle((col*600, row*400, (col+1)*600-1, (row+1)*400-1), outline="#aaaaaa", width=1)
    sheet.save(E / f"candidate_pair_contact_sheet_part{part_index//9+1:02d}.png")

critical = sorted(E.glob("critical_*_native1x.png"))
sheet = Image.new("RGB", (1800, 1200), "white")
draw = ImageDraw.Draw(sheet)
for i, path in enumerate(critical):
    image = Image.open(path).convert("RGB")
    image = image.resize((image.width*4, image.height*4), Image.Resampling.NEAREST)
    image.thumbnail((850, 330), Image.Resampling.NEAREST)
    col, row = i % 2, i // 2
    x = col*900 + (900-image.width)//2
    y = row*400 + 48 + (340-image.height)//2
    sheet.paste(image, (x, y))
    draw.text((col*900+8, row*400+10), path.stem.replace("_native1x", ""), fill="black", font=FONT)
    draw.rectangle((col*900, row*400, (col+1)*900-1, (row+1)*400-1), outline="#aaaaaa", width=1)
sheet.save(E / "critical_relation_contact_sheet.png")

print(f"object_sheets=2 candidate_sheets={(len(native)+8)//9} critical_sheet=1 candidates={len(native)}")
