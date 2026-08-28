from __future__ import annotations

import json
from pathlib import Path

import fitz


PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r98_fullbook\main_full.pdf")
OUT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\evidence\figures\FIG-P547-01\STRICT_R12_SA3_BLIND_R98_20260824\03_objects")


def main() -> None:
    doc = fitz.open(PDF)
    page = doc[590]
    raw = page.get_text("rawdict", flags=fitz.TEXT_PRESERVE_LIGATURES | fitz.TEXT_PRESERVE_WHITESPACE)
    drawings = page.get_drawings(extended=True)
    serial = {
        "page_rect_pt": list(page.rect),
        "rotation": page.rotation,
        "text_blocks": raw["blocks"],
        "drawings": [
            {
                **{k: v for k, v in d.items() if k not in {"items", "rect", "scissor", "layer"}},
                "rect": list(d["rect"]),
                "scissor": list(d["scissor"]) if d.get("scissor") else None,
                "layer": d.get("layer", ""),
                "items": [repr(item) for item in d["items"]],
            }
            for d in drawings
        ],
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "page591_rawdict_drawings.json").write_text(
        json.dumps(serial, ensure_ascii=False, indent=2, default=str), encoding="utf-8"
    )
    print(f"page_rect={page.rect} text_blocks={len(raw['blocks'])} drawings={len(drawings)}")
    for block in raw["blocks"]:
        if block.get("type") != 0:
            continue
        bbox = fitz.Rect(block["bbox"])
        if bbox.y0 >= 520 or bbox.y1 <= 245:
            continue
        print(f"BLOCK {block['number']} bbox={tuple(round(v, 3) for v in bbox)}")
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                text = "".join(ch.get("c", "") for ch in span.get("chars", []))
                print(
                    "  bbox={} size={:.3f} font={} color={} text={!r}".format(
                        tuple(round(v, 3) for v in span["bbox"]),
                        span["size"],
                        span["font"],
                        span["color"],
                        text,
                    )
                )


if __name__ == "__main__":
    main()
