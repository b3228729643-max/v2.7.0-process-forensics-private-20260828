from __future__ import annotations

import csv
import json
import math
from datetime import datetime, timezone
from pathlib import Path

import fitz
import numpy as np
from PIL import Image, ImageDraw

from build_evidence import FIGURE_CROP_PX, PDF, ROOT, SCALE_300, isolated_drawing_mask


PAGE_INDEX = 631
GRAPHIC_SPECS = {
    1: "G001", 2: "G002", 3: "G003", 4: "G004", 5: "G005", 6: "G006",
    7: "G007", 8: "G008", 9: "G009", 10: "G010", 11: "G011", 12: "G012",
    13: "G013", 14: "G014", 15: "G015", 16: "G016", 17: "G017",
}
TILE = 176
OVERLAP = 16


def main() -> None:
    out_dir = ROOT / "04_glyphs/graphic_8x_tiles"
    out_dir.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(PDF)
    page = doc[PAGE_INDEX]
    drawings = page.get_drawings()
    page_pix = page.get_pixmap(matrix=fitz.Matrix(SCALE_300, SCALE_300), alpha=False, annots=False)
    page_np = np.frombuffer(page_pix.samples, dtype=np.uint8).reshape(page_pix.height, page_pix.width, page_pix.n)[:, :, :3]
    fx0, fy0, fx1, fy1 = FIGURE_CROP_PX
    figure = page_np[fy0:fy1, fx0:fx1]
    index_rows = []
    sheet_paths = []
    for draw_i, safe_id in GRAPHIC_SPECS.items():
        full_mask = isolated_drawing_mask(page.rect, drawings[draw_i], SCALE_300)[fy0:fy1, fx0:fx1]
        ys, xs = np.nonzero(full_mask)
        x0, y0, x1, y1 = int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1
        tiles = []
        coverage = np.zeros_like(full_mask)
        step = TILE - OVERLAP
        for ty in range(y0, y1, step):
            for tx in range(x0, x1, step):
                ex = min(tx + TILE, figure.shape[1])
                ey = min(ty + TILE, figure.shape[0])
                if not np.any(full_mask[ty:ey, tx:ex]):
                    continue
                coverage[ty:ey, tx:ex] |= full_mask[ty:ey, tx:ex]
                pad = 6
                cx0, cy0 = max(0, tx-pad), max(0, ty-pad)
                cx1, cy1 = min(figure.shape[1], ex+pad), min(figure.shape[0], ey+pad)
                original = figure[cy0:cy1, cx0:cx1].copy()
                mask = full_mask[cy0:cy1, cx0:cx1]
                overlay = original.copy()
                overlay[mask] = np.array([255, 0, 0], dtype=np.uint8)
                mask_only = np.full_like(original, 255)
                mask_only[mask] = np.array([0, 0, 0], dtype=np.uint8)
                strip = np.concatenate([original, overlay, mask_only], axis=1)
                tile_img = Image.fromarray(strip, mode="RGB").resize((strip.shape[1]*8, strip.shape[0]*8), Image.Resampling.NEAREST)
                header = Image.new("RGB", (tile_img.width, 32), "white")
                ImageDraw.Draw(header).text((4, 5), f"{safe_id} tile {len(tiles)+1} raw=({cx0},{cy0},{cx1},{cy1}) | O / TARGET / MASK", fill="black")
                cell = Image.new("RGB", (tile_img.width, tile_img.height+32), "white")
                cell.paste(header, (0, 0))
                cell.paste(tile_img, (0, 32))
                tiles.append((cell, [cx0, cy0, cx1, cy1], int(np.count_nonzero(mask))))
        for sheet_no, start in enumerate(range(0, len(tiles), 2), start=1):
            group = tiles[start:start+2]
            width = max(t[0].width for t in group)
            height = sum(t[0].height for t in group) + 4 * (len(group)-1)
            sheet = Image.new("RGB", (width, height), (225, 225, 225))
            yy = 0
            for tile_no_offset, (cell, rect, pixels) in enumerate(group):
                sheet.paste(cell, (0, yy))
                tile_no = start + tile_no_offset + 1
                index_rows.append({
                    "SAFE_ID": safe_id,
                    "DRAWING_INDEX": draw_i,
                    "TILE_NO": tile_no,
                    "RAW_RECT_FIGURE_CROP": json.dumps(rect),
                    "TARGET_PIXEL_COUNT_IN_PADDED_TILE": pixels,
                    "SHEET_NO_FOR_OBJECT": sheet_no,
                    "SHEET_FILE": f"04_glyphs/graphic_8x_tiles/{safe_id}_8x_tiles_{sheet_no:02d}.png",
                })
                yy += cell.height + 4
            path = out_dir / f"{safe_id}_8x_tiles_{sheet_no:02d}.png"
            sheet.save(path)
            sheet_paths.append(str(path.relative_to(ROOT)).replace("\\", "/"))
        index_rows.append({
            "SAFE_ID": safe_id,
            "DRAWING_INDEX": draw_i,
            "TILE_NO": "COVERAGE_SUMMARY",
            "RAW_RECT_FIGURE_CROP": json.dumps([x0, y0, x1, y1]),
            "TARGET_PIXEL_COUNT_IN_PADDED_TILE": int(np.count_nonzero(full_mask)),
            "SHEET_NO_FOR_OBJECT": "",
            "SHEET_FILE": "",
        })
        if not np.array_equal(coverage, full_mask):
            raise RuntimeError(f"8x tile coverage incomplete for {safe_id}")
    with (out_dir / "graphic_8x_tile_index.csv").open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(index_rows[0].keys()))
        w.writeheader()
        w.writerows(index_rows)
    gate = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "graphic_object_count": len(GRAPHIC_SPECS),
        "tile_size_native_px": TILE,
        "tile_overlap_native_px": OVERLAP,
        "all_native_mask_pixels_covered": True,
        "sheet_count": len(sheet_paths),
        "sheet_files": sheet_paths,
        "resampling": "8x nearest-neighbour only",
        "machine_manual_fields_emitted": False,
        "oversized_monolithic_8x_sheets": "non-authoritative navigation artifacts; authoritative manual review uses this complete tiled set",
    }
    (ROOT / "07_machine/graphic_8x_tile_gate.json").write_text(json.dumps(gate, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(gate, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
