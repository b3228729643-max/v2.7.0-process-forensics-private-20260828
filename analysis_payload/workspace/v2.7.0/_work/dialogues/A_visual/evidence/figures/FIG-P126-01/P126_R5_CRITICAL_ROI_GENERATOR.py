from pathlib import Path

from PIL import Image

ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\STRICT_R5_SA2_LEGEND_SEGMENT_PATCH_R115_DIRECT_BUILD_20260828")
RENDER = ROOT / "review" / "render"
ROI = ROOT / "review" / "roi"
SCALE = 2481 / 595.276

BOXES_PT = {
    "PLOT": (195, 63, 407, 216),
    "START_CLUSTER": (202, 65, 270, 108),
    "UPDATE_CLUSTER": (214, 80, 307, 140),
    "OPTIMUM_CLUSTER": (286, 124, 326, 160),
    "AXIS_LABELS": (296, 64, 407, 146),
    "LABEL6_AXIS": (297, 102, 310, 122),
}


def to_pixels(box, size, padding=8):
    return (
        max(0, int(box[0] * SCALE) - padding),
        max(0, int(box[1] * SCALE) - padding),
        min(size[0], int(box[2] * SCALE + 0.999) + padding),
        min(size[1], int(box[3] * SCALE + 0.999) + padding),
    )


def main():
    color = Image.open(RENDER / "full_page_300dpi.png").convert("RGB")
    gray = Image.open(RENDER / "full_page_300dpi_gray.png").convert("L")
    for name, box in BOXES_PT.items():
        if (ROI / f"{name}_NEAREST8X.png").exists():
            continue
        pixels = to_pixels(box, color.size)
        color_crop = color.crop(pixels)
        gray_crop = gray.crop(pixels)
        color_crop.save(ROI / f"{name}_NATIVE1X.png")
        gray_crop.save(ROI / f"{name}_GRAY_NATIVE1X.png")
        color_crop.resize(
            (color_crop.width * 8, color_crop.height * 8), Image.Resampling.NEAREST
        ).save(ROI / f"{name}_NEAREST8X.png")
        gray_crop.resize(
            (gray_crop.width * 8, gray_crop.height * 8), Image.Resampling.NEAREST
        ).save(ROI / f"{name}_GRAY_NEAREST8X.png")


if __name__ == "__main__":
    main()
