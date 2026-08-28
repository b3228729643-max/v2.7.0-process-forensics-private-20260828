from __future__ import annotations

import hashlib
import json
from pathlib import Path

import fitz


ROOT = Path(__file__).resolve().parent
PDF = ROOT.parents[4] / "source" / "v2.7.0" / "src" / "build" / "strict_current_r105_fullbook" / "main_full.pdf"
PAGE_INDEX = 689


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def main() -> None:
    doc = fitz.open(PDF)
    page = doc[PAGE_INDEX]
    rect = page.rect
    metadata = {
        "pdf": str(PDF),
        "sha256": sha256(PDF),
        "size_bytes": PDF.stat().st_size,
        "page_count": doc.page_count,
        "physical_page_1based": PAGE_INDEX + 1,
        "page_pt": [rect.width, rect.height],
    }
    (ROOT / "machine" / "candidate_identity.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    for dpi, name in ((200, "full_page_200dpi.png"), (300, "full_page_300dpi.png")):
        pix = page.get_pixmap(matrix=fitz.Matrix(dpi / 72, dpi / 72), alpha=False)
        pix.save(ROOT / "renders" / name)

    raw = page.get_text("rawdict")
    (ROOT / "machine" / "page_rawdict.json").write_text(
        json.dumps(raw, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    drawings = page.get_drawings()
    serial_drawings = []
    for drawing in drawings:
        item = dict(drawing)
        for key in ("rect", "clip"):
            if key in item and item[key] is not None:
                item[key] = list(item[key])
        serial_items = []
        for primitive in item.get("items", []):
            p = []
            for value in primitive:
                if isinstance(value, (fitz.Point, fitz.Rect, fitz.Quad)):
                    p.append(list(value))
                else:
                    p.append(value)
            serial_items.append(p)
        item["items"] = serial_items
        serial_drawings.append(item)
    (ROOT / "machine" / "page_drawings.json").write_text(
        json.dumps(serial_drawings, ensure_ascii=False, indent=2, default=str) + "\n",
        encoding="utf-8",
    )

    blocks = page.get_text("blocks")
    (ROOT / "machine" / "page_text_blocks.json").write_text(
        json.dumps(blocks, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(metadata, ensure_ascii=False))


if __name__ == "__main__":
    main()
