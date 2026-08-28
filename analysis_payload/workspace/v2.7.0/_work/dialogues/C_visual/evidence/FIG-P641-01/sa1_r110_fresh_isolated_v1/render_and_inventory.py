from __future__ import annotations

import hashlib
import json
from pathlib import Path

import fitz


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P641-01\sa1_r110_fresh_isolated_v1")
PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r110_fullbook\main_full.pdf")
SOURCE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C04\fig_v5_c04_bayes_markov_blanket.tex")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def text_blocks(page: fitz.Page) -> list[dict]:
    result = []
    raw = page.get_text("rawdict")
    for block_index, block in enumerate(raw.get("blocks", [])):
        if block.get("type") != 0:
            continue
        for line_index, line in enumerate(block.get("lines", [])):
            spans = []
            line_text = ""
            for span_index, span in enumerate(line.get("spans", [])):
                chars = []
                for char_index, char in enumerate(span.get("chars", [])):
                    value = char.get("c", "")
                    line_text += value
                    chars.append(
                        {
                            "char_index": char_index,
                            "char": value,
                            "codepoint": f"U+{ord(value):04X}" if value else None,
                            "bbox_pt": [round(v, 4) for v in char.get("bbox", [])],
                            "origin_pt": [round(v, 4) for v in char.get("origin", [])],
                        }
                    )
                spans.append(
                    {
                        "span_index": span_index,
                        "font": span.get("font"),
                        "size_pt": round(float(span.get("size", 0.0)), 4),
                        "color": span.get("color"),
                        "flags": span.get("flags"),
                        "bbox_pt": [round(v, 4) for v in span.get("bbox", [])],
                        "chars": chars,
                    }
                )
            result.append(
                {
                    "block_index": block_index,
                    "line_index": line_index,
                    "bbox_pt": [round(v, 4) for v in line.get("bbox", [])],
                    "text": line_text,
                    "spans": spans,
                }
            )
    return result


def drawing_inventory(page: fitz.Page) -> list[dict]:
    rows = []
    for draw_index, drawing in enumerate(page.get_drawings(extended=True)):
        items = []
        for item in drawing.get("items", []):
            kind = item[0]
            values = []
            for value in item[1:]:
                if hasattr(value, "x") and hasattr(value, "y"):
                    values.append([round(value.x, 4), round(value.y, 4)])
                elif hasattr(value, "x0"):
                    values.append([round(value.x0, 4), round(value.y0, 4), round(value.x1, 4), round(value.y1, 4)])
                else:
                    values.append(value)
            items.append([kind, *values])
        rect = drawing.get("rect")
        rows.append(
            {
                "draw_index": draw_index,
                "seqno": drawing.get("seqno"),
                "type": drawing.get("type"),
                "rect_pt": [round(rect.x0, 4), round(rect.y0, 4), round(rect.x1, 4), round(rect.y1, 4)] if rect else None,
                "color": drawing.get("color"),
                "fill": drawing.get("fill"),
                "width_pt": drawing.get("width"),
                "dashes": drawing.get("dashes"),
                "close_path": drawing.get("closePath"),
                "items": items,
            }
        )
    return rows


def main() -> None:
    expected = {
        "pdf": {"bytes": 4_967_063, "sha256": "B49C5CA920DDEF6C0CD004B2581EAF710F4D1E1115BB459A324A84594B3831F3"},
        "source": {"bytes": 3_008, "sha256": "8773FF1EFFCB79DDD44734E72F0B0101292F135165021B32A760A6151DC0DE15"},
    }
    actual = {
        "pdf": {"path": str(PDF), "bytes": PDF.stat().st_size, "sha256": sha256(PDF)},
        "source": {"path": str(SOURCE), "bytes": SOURCE.stat().st_size, "sha256": sha256(SOURCE)},
    }
    for key in ("pdf", "source"):
        if actual[key]["bytes"] != expected[key]["bytes"] or actual[key]["sha256"] != expected[key]["sha256"]:
            raise RuntimeError(f"identity mismatch for {key}: {actual[key]}")

    doc = fitz.open(PDF)
    matches = []
    required_fragments = ("因子图中更新", "Markov毯变量")
    for page_index in range(doc.page_count):
        compact = doc[page_index].get_text("text").replace(" ", "").replace("\n", "")
        if all(fragment in compact for fragment in required_fragments):
            matches.append(page_index)
    if len(matches) != 1:
        raise RuntimeError(f"expected one independent caption match, found {matches}")
    page_index = matches[0]
    page = doc[page_index]
    page_rect = page.rect

    for dpi, name in ((200, "full_page_200dpi.png"), (300, "full_page_native300dpi.png")):
        matrix = fitz.Matrix(dpi / 72.0, dpi / 72.0)
        pix = page.get_pixmap(matrix=matrix, alpha=False, colorspace=fitz.csRGB)
        pix.save(ROOT / name)

    inventory = {
        "handoff_id": "C-FIG-P641-01-R110-SA1-FRESH-ISOLATED-V1",
        "uid": "FIG-P641-01",
        "identity": {"expected": expected, "actual": actual},
        "location_method": "unique current-PDF page whose compact extracted text contains both exact fragments 因子图中更新 and Markov毯变量",
        "physical_page_1_based": page_index + 1,
        "printed_page_extracted": 678,
        "pdf_page_count": doc.page_count,
        "page_pt": [round(page_rect.width, 4), round(page_rect.height, 4)],
        "native_grids": {
            "200dpi": [round(page_rect.width * 200 / 72), round(page_rect.height * 200 / 72)],
            "300dpi": [round(page_rect.width * 300 / 72), round(page_rect.height * 300 / 72)],
        },
        "text_lines": text_blocks(page),
        "drawings": drawing_inventory(page),
    }
    (ROOT / "machine_page_inventory.json").write_text(json.dumps(inventory, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: inventory[k] for k in ("physical_page_1_based", "printed_page_extracted", "pdf_page_count", "page_pt", "native_grids")}, ensure_ascii=True))


if __name__ == "__main__":
    main()
