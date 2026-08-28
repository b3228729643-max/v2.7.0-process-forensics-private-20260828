from pathlib import Path

import fitz
from PIL import Image


BUILD_ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P715-01\STRICT_R17_SA2_R16_GEOMETRY_DIRECT_BUILD_20260826")
ROOT = BUILD_ROOT / "evidence_v3"
PDF = BUILD_ROOT / "build" / "v260_FIG-P715-01_standalone.pdf"
VIEWS = ROOT / "views"
FIGURE_PX = (280, 280, 2238, 1126)
FIGURE_CROP_PX = (258, 280, 2260, 1200)


def render(dpi: int) -> Image.Image:
    doc = fitz.open(PDF)
    if doc.page_count != 1:
        raise RuntimeError(f"unexpected page count {doc.page_count}")
    pix = doc[0].get_pixmap(matrix=fitz.Matrix(dpi / 72.0, dpi / 72.0), alpha=False)
    image = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    doc.close()
    return image


def main() -> None:
    VIEWS.mkdir(parents=True, exist_ok=True)
    native = render(300)
    page_200 = render(200)
    native.save(VIEWS / "full_page_300dpi_native.png", dpi=(300, 300))
    page_200.save(VIEWS / "full_page_200dpi.png", dpi=(200, 200))
    figure = native.crop(FIGURE_PX)
    figure_plus_margin = native.crop(FIGURE_CROP_PX)
    figure.save(VIEWS / "standalone_300dpi.png", dpi=(300, 300))
    figure.convert("L").save(VIEWS / "grayscale_300dpi.png", dpi=(300, 300))
    figure_plus_margin.save(VIEWS / "figure_crop_300dpi.png", dpi=(300, 300))
    print({"native": native.size, "page_200": page_200.size, "figure": figure.size})


if __name__ == "__main__":
    main()
