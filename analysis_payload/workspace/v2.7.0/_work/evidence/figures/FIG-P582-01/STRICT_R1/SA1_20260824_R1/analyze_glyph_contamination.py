"""Read-only geometry attribution for impure raw glyph masks.

The output does not alter any mask.  It records which neighbouring glyph masks
share raw native 300-dpi pixels and whether a shared region is connected to the
target's visible component.  This is the evidence used for a conservative
manual safe-isolation decision.
"""
from __future__ import annotations

import csv
from collections import deque
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parent


def load_meta() -> dict[str, dict[str, str]]:
    with (ROOT / "after_pixel_measurements.csv").open("r", encoding="utf-8-sig", newline="") as fh:
        meta = {
            r["GLYPH_ID"]: r
            for r in csv.DictReader(fh)
            if r["LEVEL"] == "GLYPH"
        }
    with (ROOT / "glyph_file_manifest.csv").open("r", encoding="utf-8-sig", newline="") as fh:
        for r in csv.DictReader(fh):
            meta[r["GLYPH_ID"]]["ROI_X0"] = r["NATIVE_ROI_X0"]
            meta[r["GLYPH_ID"]]["ROI_Y0"] = r["NATIVE_ROI_Y0"]
    return meta


def binary(path: Path) -> list[list[bool]]:
    im = Image.open(path).convert("L")
    return [[im.getpixel((x, y)) < 128 for x in range(im.width)] for y in range(im.height)]


def components(mask: list[list[bool]]) -> list[list[tuple[int, int]]]:
    h, w = len(mask), len(mask[0])
    seen: set[tuple[int, int]] = set()
    out: list[list[tuple[int, int]]] = []
    for y in range(h):
        for x in range(w):
            if not mask[y][x] or (x, y) in seen:
                continue
            q: deque[tuple[int, int]] = deque([(x, y)])
            seen.add((x, y))
            part: list[tuple[int, int]] = []
            while q:
                px, py = q.popleft()
                part.append((px, py))
                for nx, ny in ((px - 1, py), (px + 1, py), (px, py - 1), (px, py + 1)):
                    if 0 <= nx < w and 0 <= ny < h and mask[ny][nx] and (nx, ny) not in seen:
                        seen.add((nx, ny))
                        q.append((nx, ny))
            out.append(part)
    return out


def main() -> None:
    meta = load_meta()
    masks = {gid: binary(ROOT / row["MASK_FILE"]) for gid, row in meta.items()}
    with (ROOT / "glyph_machine_integrity.csv").open("r", encoding="utf-8-sig", newline="") as fh:
        failures = [r for r in csv.DictReader(fh) if r["PASS_FAIL"] == "FAIL"]

    overlap_rows: list[dict[str, object]] = []
    component_rows: list[dict[str, object]] = []
    for fail in failures:
        gid = fail["GLYPH_ID"]
        target = meta[gid]
        tx0, ty0 = int(target["ROI_X0"]), int(target["ROI_Y0"])
        tm = masks[gid]
        foreign_positions: dict[tuple[int, int], list[str]] = {}
        for other_id, other in meta.items():
            if other_id == gid:
                continue
            ox0, oy0 = int(other["ROI_X0"]), int(other["ROI_Y0"])
            om = masks[other_id]
            count = 0
            positions: list[tuple[int, int]] = []
            for y, row in enumerate(tm):
                gy = ty0 + y
                oy = gy - oy0
                if not (0 <= oy < len(om)):
                    continue
                for x, on in enumerate(row):
                    gx = tx0 + x
                    ox = gx - ox0
                    if on and 0 <= ox < len(om[0]) and om[oy][ox]:
                        count += 1
                        positions.append((x, y))
                        foreign_positions.setdefault((x, y), []).append(other_id)
            if count:
                overlap_rows.append({
                    "TARGET_GLYPH_ID": gid,
                    "TARGET_ELEMENT_ID": fail["ELEMENT_ID"],
                    "TARGET_CHAR": fail["CHAR"],
                    "OTHER_GLYPH_ID": other_id,
                    "OTHER_ELEMENT_ID": other["ELEMENT_ID"],
                    "OTHER_CHAR": other["TEXT_SAMPLE"],
                    "SHARED_RAW_PIXEL_PX": count,
                    "SHARED_GLOBAL_XY": " ".join(f"{tx0+x}:{ty0+y}" for x, y in positions),
                })
        for index, comp in enumerate(components(tm), start=1):
            overlaps: list[str] = []
            hit = 0
            for pos in comp:
                if pos in foreign_positions:
                    hit += 1
                    overlaps.extend(foreign_positions[pos])
            xs = [p[0] for p in comp]
            ys = [p[1] for p in comp]
            component_rows.append({
                "TARGET_GLYPH_ID": gid,
                "COMPONENT": index,
                "COMPONENT_PIXEL_PX": len(comp),
                "COMPONENT_GLOBAL_BBOX_XYXY": f"{tx0+min(xs)},{ty0+min(ys)},{tx0+max(xs)+1},{ty0+max(ys)+1}",
                "SHARED_PIXEL_IN_COMPONENT": hit,
                "OTHER_GLYPH_IDS": ";".join(sorted(set(overlaps))),
                "COMPONENT_ISOLATED_FROM_FOREIGN": str(hit == 0).lower(),
            })

    with (ROOT / "glyph_overlap_attribution.csv").open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(overlap_rows[0]) if overlap_rows else [])
        if overlap_rows:
            w.writeheader(); w.writerows(overlap_rows)
    with (ROOT / "glyph_contamination_components.csv").open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(component_rows[0]) if component_rows else [])
        if component_rows:
            w.writeheader(); w.writerows(component_rows)


if __name__ == "__main__":
    main()
