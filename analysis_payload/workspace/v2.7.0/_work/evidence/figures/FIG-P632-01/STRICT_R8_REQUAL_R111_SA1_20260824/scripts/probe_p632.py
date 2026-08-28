from __future__ import annotations

import argparse
import fitz


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf")
    parser.add_argument("--page", type=int, default=680)
    parser.add_argument("--y0", type=float, default=55.0)
    parser.add_argument("--y1", type=float, default=465.0)
    args = parser.parse_args()
    page = fitz.open(args.pdf)[args.page - 1]
    raw = page.get_text("rawdict")
    count = 0
    for block in raw["blocks"]:
        if block["type"] != 0:
            continue
        for line in block["lines"]:
            for span in line["spans"]:
                text = "".join(ch["c"] for ch in span["chars"])
                x0, y0, x1, y1 = span["bbox"]
                if y1 <= args.y0 or y0 >= args.y1:
                    continue
                count += len([ch for ch in span["chars"] if not ch.get("synthetic", False) and not ch["c"].isspace()])
                print(
                    f"{x0:7.2f} {y0:7.2f} {x1:7.2f} {y1:7.2f} "
                    f"{span['font']:<30} {span['size']:6.3f} #{span['color']:06X} {text}"
                )
    print(f"VISIBLE_NONSPACE_GLYPHS={count}")


if __name__ == "__main__":
    main()
