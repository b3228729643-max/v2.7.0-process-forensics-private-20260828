from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P637-01\sa3_r103_fresh_isolated_v1")
MACHINE = ROOT / "machine"
CARDS = ROOT / "cards"
FULL = ROOT / "renders" / "full_page_300dpi.png"


def read_csv(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def concatenate_exact(paths: list[Path], output: Path, gap: int = 8) -> None:
    images = [Image.open(p).convert("RGB") for p in paths]
    canvas = Image.new("RGB", (max(i.width for i in images), sum(i.height for i in images) + gap * (len(images) - 1)), "white")
    y = 0
    for im in images:
        canvas.paste(im, (0, y))
        y += im.height + gap
    output.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output)


def main() -> None:
    glyphs = read_csv(MACHINE / "glyph_inventory.csv")
    parents: dict[str, list[dict]] = {}
    for row in glyphs:
        parents.setdefault(row["parent_id"], []).append(row)
    parent_rows = []
    for parent_id, rows in parents.items():
        boxes = [json.loads(r["bbox_px_page"]) for r in rows]
        parent_rows.append(
            {
                "parent_id": parent_id,
                "role": rows[0]["role"],
                "visible_text": "".join(r["char"] for r in rows),
                "glyph_count": len(rows),
                "glyph_ids": "|".join(r["glyph_id"] for r in rows),
                "bbox_px_page": json.dumps([min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes), max(b[3] for b in boxes)]),
                "foreground_pair_denominator_included": False,
                "exclusion_reason": "semantic container only; all rendered foreground is exhaustively represented by child glyph masks",
            }
        )
    write_csv(MACHINE / "text_parent_inventory.csv", parent_rows)

    full = Image.open(FULL).convert("RGB")
    graphic_rows = read_csv(MACHINE / "graphic_inventory.csv")
    card_dir = CARDS / "graphic"
    card_dir.mkdir(parents=True, exist_ok=True)
    card_index = []
    for row in graphic_rows:
        x0, y0, x1, y1 = json.loads(row["mask_bbox_px"])
        mask = np.array(Image.open(row["mask_path"]).convert("L")) < 128
        pad = 5
        cx0, cy0, cx1, cy1 = max(0, x0 - pad), max(0, y0 - pad), min(full.width, x1 + pad), min(full.height, y1 + pad)
        original = full.crop((cx0, cy0, cx1, cy1)).convert("RGB")
        placed = np.zeros((cy1 - cy0, cx1 - cx0), dtype=bool)
        placed[y0 - cy0 : y1 - cy0, x0 - cx0 : x1 - cx0] = mask
        overlay = np.array(original).copy()
        overlay[placed] = [255, 0, 0]
        only = np.full_like(overlay, 255)
        only[placed] = [0, 0, 0]
        panels = [original, Image.fromarray(overlay), Image.fromarray(only)]
        gap, title_h, footer_h = 8, 30, 18
        card = Image.new("RGB", (sum(i.width for i in panels) + gap * 2, title_h + max(i.height for i in panels) + footer_h), "white")
        d = ImageDraw.Draw(card)
        d.text((4, 4), f"{row['object_id']} | native 300dpi 1x | ORIGINAL / TARGET OVERLAY / MASK ONLY", fill="black")
        x = 0
        for lab, im in zip(("ORIGINAL", "TARGET OVERLAY", "MASK ONLY"), panels):
            card.paste(im, (x, title_h))
            d.text((x + 2, title_h + im.height + 1), lab, fill="black")
            x += im.width + gap
        out = card_dir / f"{row['safe_filename']}_card_1x.png"
        card.save(out)
        card_index.append({"object_id": row["object_id"], "excluded_background": row["pair_denominator_included"].lower() == "false", "card_path": str(out.resolve()), "native_scale": "1x"})
    write_csv(MACHINE / "graphic_card_index.csv", card_index)

    critical = read_csv(MACHINE / "critical_pair_inventory.csv")
    contact_dir = CARDS / "critical_pair_contact_sheets"
    index_rows = []
    for start in range(0, len(critical), 4):
        batch = critical[start : start + 4]
        paths = [Path(r["evidence_dir"]) / "card_8x_nearest.png" for r in batch]
        sheet_no = start // 4 + 1
        output = contact_dir / f"critical_pair_contact_sheet_{sheet_no:03d}.png"
        concatenate_exact(paths, output)
        for cell, row in enumerate(batch, 1):
            index_rows.append({"pair_id": row["pair_id"], "sheet": output.name, "cell": cell, "card_path": str(paths[cell - 1].resolve())})
    write_csv(MACHINE / "critical_pair_contact_sheet_index.csv", index_rows)

    absence = {
        "math_rule_objects": 0,
        "loop_objects": 0,
        "legend_objects": 0,
        "panel_border_objects": 0,
        "rationale": "Official PDF vector/text inventory on physical page 687 contains no formula rule path, loop, legend, or panel border within the figure body. The note-card border is mapped as D_NOTE_BORDER; ellipse contours and every line/arrow/marker are mapped separately.",
        "source_of_claim": "machine/graphic_inventory.csv plus machine/machine_summary.json dual PDF drawing-index accounting",
    }
    (MACHINE / "explicit_absence_inventory.json").write_text(json.dumps(absence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
