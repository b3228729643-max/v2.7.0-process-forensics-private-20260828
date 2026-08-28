from __future__ import annotations

import sys
from pathlib import Path

import pdfplumber


PDF = Path(
    r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0"
    r"\src\build\strict_current_r114_fullbook\main_full.pdf"
)
PAGE_INDEX = 78


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    with pdfplumber.open(PDF) as document:
        page = document.pages[PAGE_INDEX]
        print(f"page={PAGE_INDEX + 1} width_pt={page.width:.3f} height_pt={page.height:.3f}")
        words = page.extract_words(
            x_tolerance=1,
            y_tolerance=2,
            keep_blank_chars=False,
            use_text_flow=False,
        )
        for word in words:
            if 420 <= word["top"] <= 680:
                print(
                    f"{word['x0']:.2f}\t{word['top']:.2f}\t{word['x1']:.2f}\t"
                    f"{word['bottom']:.2f}\t{word['text']}"
                )
        for kind in ("lines", "curves", "rects"):
            objects = getattr(page, kind)
            print(f"-- {kind} in figure band --")
            for index, obj in enumerate(objects, start=1):
                top = obj.get("top", 0)
                bottom = obj.get("bottom", 0)
                if bottom >= 420 and top <= 590:
                    print(
                        index,
                        {
                            key: obj.get(key)
                            for key in (
                                "x0",
                                "top",
                                "x1",
                                "bottom",
                                "linewidth",
                                "stroking_color",
                                "non_stroking_color",
                                "fill",
                                "dash",
                            )
                        },
                    )


if __name__ == "__main__":
    main()
