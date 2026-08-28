from __future__ import annotations

import hashlib
import json
from pathlib import Path

import fitz


PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r104_fullbook\main_full.pdf")
ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P598-02\STRICT_R1_SA1_FRESH_R104_R168_20260826")
PAGE_INDEX = 649


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def main() -> None:
    (ROOT / "views").mkdir(parents=True, exist_ok=True)
    (ROOT / "machine").mkdir(parents=True, exist_ok=True)
    doc = fitz.open(PDF)
    page = doc[PAGE_INDEX]
    pix300 = page.get_pixmap(dpi=300, alpha=False)
    pix200 = page.get_pixmap(dpi=200, alpha=False)
    pix300.save(ROOT / "views" / "full_page_300dpi.png")
    pix200.save(ROOT / "views" / "full_page_200dpi.png")

    raw = page.get_text("rawdict")
    drawings = page.get_drawings(extended=True)
    words = page.get_text("words")
    text = page.get_text("text")
    (ROOT / "machine" / "page_text.txt").write_text(text, encoding="utf-8")

    compact_drawings = []
    for i, drawing in enumerate(drawings):
        rect = drawing.get("rect")
        compact_drawings.append(
            {
                "drawing_index": i,
                "type": drawing.get("type"),
                "rect_pt": [round(v, 5) for v in rect] if rect is not None else None,
                "fill": drawing.get("fill"),
                "color": drawing.get("color"),
                "width": drawing.get("width"),
                "layer": drawing.get("layer"),
                "seqno": drawing.get("seqno"),
                "items": [str(item) for item in drawing.get("items", [])],
            }
        )

    chars = []
    for block_index, block in enumerate(raw.get("blocks", [])):
        if block.get("type") != 0:
            continue
        for line_index, line in enumerate(block.get("lines", [])):
            for span_index, span in enumerate(line.get("spans", [])):
                for char_index, char in enumerate(span.get("chars", [])):
                    chars.append(
                        {
                            "block": block_index,
                            "line": line_index,
                            "span": span_index,
                            "char": char_index,
                            "c": char.get("c"),
                            "bbox_pt": [round(v, 5) for v in char.get("bbox", [])],
                            "origin_pt": [round(v, 5) for v in char.get("origin", [])],
                            "font": span.get("font"),
                            "size_pt": span.get("size"),
                            "color": span.get("color"),
                            "flags": span.get("flags"),
                        }
                    )

    identity = {
        "figure_uid": "FIG-P598-02",
        "candidate_round": "R104",
        "pdf": str(PDF),
        "pdf_size_bytes": PDF.stat().st_size,
        "pdf_sha256": sha256(PDF),
        "page_count": doc.page_count,
        "physical_page": PAGE_INDEX + 1,
        "page_index_zero_based": PAGE_INDEX,
        "page_pt": [page.rect.width, page.rect.height],
        "full_page_300dpi_px": [pix300.width, pix300.height],
        "full_page_200dpi_px": [pix200.width, pix200.height],
        "raw_text_char_count": len(chars),
        "drawing_count": len(drawings),
    }
    (ROOT / "machine" / "candidate_identity.json").write_text(
        json.dumps(identity, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (ROOT / "machine" / "page_chars.json").write_text(
        json.dumps(chars, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (ROOT / "machine" / "page_words.json").write_text(
        json.dumps(words, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (ROOT / "machine" / "page_drawings.json").write_text(
        json.dumps(compact_drawings, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(identity, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
