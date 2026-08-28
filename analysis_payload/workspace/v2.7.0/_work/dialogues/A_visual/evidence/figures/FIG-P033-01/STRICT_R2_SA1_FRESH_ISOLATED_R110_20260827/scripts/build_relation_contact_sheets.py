from pathlib import Path
import csv
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P033-01\STRICT_R2_SA1_FRESH_ISOLATED_R110_20260827")
PAYLOAD = ROOT / "payload"
OUT = PAYLOAD / "contact_sheets"


def panel(path: Path, max_w=320, max_h=390):
    im = Image.open(path).convert("RGB")
    if path.name.endswith("_1x.png"):
        im = im.resize((im.width * 8, im.height * 8), Image.Resampling.NEAREST)
    # Evidence retains nearest-neighbour 8x; only crop the display window, never resample it.
    return im.crop((0, 0, min(im.width, max_w), min(im.height, max_h)))


with (PAYLOAD / "critical_relations_index.csv").open("r", encoding="utf-8-sig", newline="") as f:
    rows = list(csv.DictReader(f))

index = []
for start in range(0, len(rows), 2):
    sheet_no = start // 2 + 1
    sheet = Image.new("RGB", (1800, 1000), (238, 238, 238))
    draw = ImageDraw.Draw(sheet)
    for local, row in enumerate(rows[start:start + 2]):
        rid = row["relation_id"]
        y = local * 500
        draw.rectangle((0, y, 1799, y + 499), fill="white")
        draw.text((10, y + 8), f"{rid} {row['a_id']}--{row['b_id']} overlap={row['overlap_pixel_count']} clearance={row['clearance_px']} required={row['required_clearance_px']} {row['machine_decision']}", fill="black", font=ImageFont.load_default())
        relation_dir = PAYLOAD / row["evidence_dir"]
        files = [
            ("RAW 8x NN", relation_dir / "raw_1x.png"),
            ("MASK A 8x NN", relation_dir / "mask_A_1x.png"),
            ("MASK B 8x NN", relation_dir / "mask_B_1x.png"),
            ("INTERSECTION 8x NN", relation_dir / "intersection_1x.png"),
            ("OVERLAY 8x NN", relation_dir / "overlay_8x_nearest.png"),
        ]
        for j, (label, p) in enumerate(files):
            x = 10 + j * 355
            draw.text((x, y + 28), label, fill="black", font=ImageFont.load_default())
            sheet.paste(panel(p), (x, y + 48))
        index.append({"relation_id": rid, "sheet": f"critical_relation_contact_sheet_{sheet_no:02d}.png", "cell": local + 1})
    sheet.save(OUT / f"critical_relation_contact_sheet_{sheet_no:02d}.png")

with (PAYLOAD / "critical_relation_contact_index.csv").open("w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["relation_id", "sheet", "cell"])
    w.writeheader()
    w.writerows(index)

print(f"critical_relation_contact_sheets={((len(rows) + 1) // 2)} relations={len(rows)}")
