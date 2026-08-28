"""Apply five reviewer-authorized, component-level glyph-mask projections.

The frozen PDF and all raw glyph masks are preserved.  This script builds a
separate final-mask namespace.  It is deliberately limited to the five masks
whose foreign pixels are detached components and visually attributable to a
named neighbouring glyph.  It never clips the real P0717 arrow/zero collision:
the independently replayed A/B object masks are each complete and pure, while
their shared 3 pixels remain a relationship failure.
"""
from __future__ import annotations

import csv
import json
from collections import deque
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent
RAW_MASK = ROOT / "glyph_masks"
ORIGINAL = ROOT / "glyph_original"
FINAL_MASK = ROOT / "glyph_final_masks"
FINAL_OVERLAY = ROOT / "glyph_final_target_overlay"
FINAL_CONTACTS = ROOT / "glyph_final_contact_sheets"
PACKAGES = ROOT / "glyph_integrity_packages"

# Explicit reviewer-authorized raw-mask component signatures: (pixel count,
# local bbox x0,y0,x1,y1).  They were derived from
# glyph_contamination_components.csv and manually inspected in both raw 1x
# and nearest 8x package views.  Using an entire isolated component avoids
# arbitrary rectangular clipping and leaves every connected target stroke.
REMOVE_COMPONENT_SIGNATURES: dict[str, set[tuple[int, int, int, int, int]]] = {
    "G0011": {(6, 5, 29, 9, 31)},
    "G0106": {(2, 34, 33, 35, 35)},
    "G0107": {(15, 3, 38, 9, 41)},
    "G0114": {(29, 44, 11, 45, 40)},
    "G0124": {(8, 42, 13, 46, 15)},
}

SAFE_DIRECT = set(REMOVE_COMPONENT_SIGNATURES)
SAFE_BY_NEIGHBOUR = {"G0016", "G0108", "G0115", "G0125"}
REAL_COLLISION = {"G0029", "G0036"}


def glyph_metadata() -> list[dict[str, str]]:
    with (ROOT / "glyph_file_manifest.csv").open("r", encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def components(mask: Image.Image) -> list[list[tuple[int, int]]]:
    im = mask.convert("L")
    w, h = im.size
    pix = im.load()
    seen: set[tuple[int, int]] = set()
    result: list[list[tuple[int, int]]] = []
    for y in range(h):
        for x in range(w):
            if pix[x, y] >= 128 or (x, y) in seen:
                continue
            q: deque[tuple[int, int]] = deque([(x, y)])
            seen.add((x, y))
            part: list[tuple[int, int]] = []
            while q:
                px, py = q.popleft()
                part.append((px, py))
                for nx, ny in ((px - 1, py), (px + 1, py), (px, py - 1), (px, py + 1)):
                    if 0 <= nx < w and 0 <= ny < h and pix[nx, ny] < 128 and (nx, ny) not in seen:
                        seen.add((nx, ny)); q.append((nx, ny))
            result.append(part)
    return result


def component_signature(part: list[tuple[int, int]]) -> tuple[int, int, int, int, int]:
    xs, ys = [p[0] for p in part], [p[1] for p in part]
    return len(part), min(xs), min(ys), max(xs) + 1, max(ys) + 1


def red_overlay(original: Image.Image, mask: Image.Image) -> Image.Image:
    out = original.convert("RGB")
    mp = mask.convert("L")
    px, mx = out.load(), mp.load()
    for y in range(out.height):
        for x in range(out.width):
            if mx[x, y] < 128:
                px[x, y] = (255, 0, 0)
    return out


def nearest(im: Image.Image) -> Image.Image:
    return im.resize((im.width * 8, im.height * 8), Image.Resampling.NEAREST)


def contact_sheets(rows: list[dict[str, str]]) -> None:
    FINAL_CONTACTS.mkdir(exist_ok=True)
    font = ImageFont.load_default()
    for sheet_no in range(1, 13):
        batch = [r for r in rows if int(r["CELL"]) and r["SHEET"].endswith(f"_{sheet_no:02d}.png")]
        if not batch:
            continue
        batch.sort(key=lambda r: int(r["CELL"]))
        cells: list[tuple[dict[str, str], Image.Image, Image.Image, Image.Image]] = []
        max_w = max_h = 1
        for row in batch:
            gid = row["GLYPH_ID"]
            orig = Image.open(ORIGINAL / f"{gid}_original_1x.png").convert("RGB")
            mask = Image.open(FINAL_MASK / f"{gid}_final_visible_mask_1x.png").convert("L")
            ov = red_overlay(orig, mask)
            cells.append((row, orig, ov, mask))
            max_w, max_h = max(max_w, orig.width), max(max_h, orig.height)
        tile_w, tile_h = max_w * 8 + 18, max_h * 8 + 32
        canvas = Image.new("RGB", (tile_w * 3, tile_h * len(cells)), "white")
        draw = ImageDraw.Draw(canvas)
        for index, (row, orig, ov, mask) in enumerate(cells):
            y = index * tile_h
            for col, (label, im) in enumerate((("ORIGINAL", orig), ("TARGET OVERLAY", ov), ("MASK ONLY", mask.convert("RGB")))):
                x = col * tile_w
                draw.text((x, y), label, fill="black", font=font)
                enlarged = nearest(im)
                canvas.paste(enlarged, (x, y + 14))
            draw.text((tile_w * 3 - 150, y), f"{row['GLYPH_ID']} E={row['ELEMENT_ID']}", fill="black", font=font)
        canvas.save(FINAL_CONTACTS / f"contact_sheet_{sheet_no:02d}_final_visible.png")


def main() -> None:
    rows = glyph_metadata()
    FINAL_MASK.mkdir(exist_ok=True)
    FINAL_OVERLAY.mkdir(exist_ok=True)
    manifest: list[dict[str, str]] = []
    for row in rows:
        gid = row["GLYPH_ID"]
        raw = Image.open(RAW_MASK / f"{gid}_mask_only_1x.png").convert("L")
        out = raw.copy()
        remove_parts = {
            component_signature(part): part
            for part in components(raw)
            if component_signature(part) in REMOVE_COMPONENT_SIGNATURES.get(gid, set())
        }
        expected = REMOVE_COMPONENT_SIGNATURES.get(gid, set())
        if set(remove_parts) != expected:
            raise RuntimeError(f"component signature mismatch for {gid}: expected={expected!r} actual={set(remove_parts)!r}")
        px = out.load()
        for part in remove_parts.values():
            for lx, ly in part:
                px[lx, ly] = 255
        final_path = FINAL_MASK / f"{gid}_final_visible_mask_1x.png"
        out.save(final_path)
        orig = Image.open(ORIGINAL / f"{gid}_original_1x.png").convert("RGB")
        overlay = red_overlay(orig, out)
        overlay_path = FINAL_OVERLAY / f"{gid}_final_visible_target_overlay_1x.png"
        overlay.save(overlay_path)
        status = (
            "ISOLATED_DIRECT_COMPONENT" if gid in SAFE_DIRECT else
            "ISOLATED_BY_NEIGHBOUR_PROJECTION" if gid in SAFE_BY_NEIGHBOUR else
            "INDEPENDENT_OBJECT_REPLAY_REAL_COLLISION" if gid in REAL_COLLISION else
            "RAW_FINAL_VISIBLE_NO_CONTAMINATION"
        )
        manifest.append({
            "GLYPH_ID": gid,
            "FINAL_VISIBLE_MASK": str(final_path.relative_to(ROOT)).replace("\\", "/"),
            "FINAL_TARGET_OVERLAY": str(overlay_path.relative_to(ROOT)).replace("\\", "/"),
            "STATUS": status,
            "REMOVED_RAW_PIXEL_PX": str(sum(len(p) for p in remove_parts.values())),
        })

    contact_sheets(rows)
    with (ROOT / "glyph_final_mask_manifest.csv").open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(manifest[0])); w.writeheader(); w.writerows(manifest)

    # Add isolated final variants to all failure packages, preserving the raw
    # 1x/8x triads already in each package.
    for gid in sorted(SAFE_DIRECT | SAFE_BY_NEIGHBOUR | REAL_COLLISION):
        package = PACKAGES / gid
        final_mask = Image.open(FINAL_MASK / f"{gid}_final_visible_mask_1x.png").convert("L")
        final_overlay = Image.open(FINAL_OVERLAY / f"{gid}_final_visible_target_overlay_1x.png").convert("RGB")
        final_mask.save(package / "final_visible_mask_1x.png")
        nearest(final_mask).save(package / "final_visible_mask_8x_nearest.png")
        final_overlay.save(package / "final_visible_overlay_1x.png")
        nearest(final_overlay).save(package / "final_visible_overlay_8x_nearest.png")
        mp = json.loads((package / "package_manifest.json").read_text(encoding="utf-8"))
        mp["final_projection_status"] = next(x["STATUS"] for x in manifest if x["GLYPH_ID"] == gid)
        mp["final_projection_files"] = [
            "final_visible_mask_1x.png", "final_visible_overlay_1x.png",
            "final_visible_mask_8x_nearest.png", "final_visible_overlay_8x_nearest.png",
        ]
        (package / "package_manifest.json").write_text(json.dumps(mp, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
