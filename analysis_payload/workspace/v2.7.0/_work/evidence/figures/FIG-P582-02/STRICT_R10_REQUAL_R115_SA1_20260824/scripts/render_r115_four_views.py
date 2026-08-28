from pathlib import Path

import fitz
from PIL import Image, ImageOps


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\evidence\figures\FIG-P582-02\STRICT_R10_REQUAL_R115_SA1_20260824")
PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r95_fullbook\main_full.pdf")
OUT = ROOT / "views"
PAGE_NUMBER_1_BASED = 630


def render(page, dpi):
    scale = dpi / 72.0
    pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=False)
    return Image.frombytes("RGB", (pix.width, pix.height), pix.samples)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(PDF)
    page = doc[PAGE_NUMBER_1_BASED - 1]
    page200 = render(page, 200)
    page300 = render(page, 300)
    page200.save(OUT / "full_page_200dpi.png")
    # Coordinates are native-300 pixel bounds determined from the current official PDF.
    chart = page300.crop((680, 2140, 2070, 2840))
    chart.save(OUT / "standalone_chart_300dpi.png")
    figure = page300.crop((250, 2120, 2250, 2990))
    figure.save(OUT / "figure_crop_300dpi.png")
    ImageOps.grayscale(figure).save(OUT / "figure_crop_grayscale_300dpi.png")
    doc.close()


if __name__ == "__main__":
    main()
