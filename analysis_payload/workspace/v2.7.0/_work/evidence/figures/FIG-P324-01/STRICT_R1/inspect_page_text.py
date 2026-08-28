from pathlib import Path

import fitz


PDF = Path(
    r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build"
    r"\strict_current_r92_fullbook\main_full.pdf"
)


def main() -> None:
    with fitz.open(PDF) as doc:
        page = doc[348]
        print("=== TEXT ===")
        for block in page.get_text("dict")["blocks"]:
            for line in block.get("lines", []):
                for span in line["spans"]:
                    x0, y0, x1, y1 = span["bbox"]
                    if 250 < y0 < 520:
                        print(
                            f"{x0:.2f},{y0:.2f},{x1:.2f},{y1:.2f} "
                            f"size={span['size']:.2f} font={span['font']} color={span['color']} "
                            f"text={span['text']!r}"
                        )
        print("=== DRAWINGS ===")
        for index, drawing in enumerate(page.get_drawings()):
            rect = drawing["rect"]
            if rect.y1 < 275 or rect.y0 > 450:
                continue
            print(
                f"D{index:04d} rect=({rect.x0:.2f},{rect.y0:.2f},"
                f"{rect.x1:.2f},{rect.y1:.2f}) width={drawing['width']:.3f} "
                f"color={drawing['color']} fill={drawing['fill']} "
                f"close={drawing['closePath']} items={drawing['items']}"
            )
        print("=== FONTS ===")
        for font in page.get_fonts(full=True):
            print(font)
        print("=== RAW CHARS ===")
        for block in page.get_text("rawdict")["blocks"]:
            for line in block.get("lines", []):
                for span in line["spans"]:
                    for char in span["chars"]:
                        x0, y0, x1, y1 = char["bbox"]
                        if 280 < y0 < 448:
                            print(
                                f"{char['c']!r} bbox=({x0:.2f},{y0:.2f},"
                                f"{x1:.2f},{y1:.2f}) origin={char['origin']} "
                                f"size={span['size']:.2f} font={span['font']}"
                            )


if __name__ == "__main__":
    main()
