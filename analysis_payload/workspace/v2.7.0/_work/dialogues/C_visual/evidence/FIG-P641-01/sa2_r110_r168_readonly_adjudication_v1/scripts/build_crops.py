from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P641-01\sa2_r110_r168_readonly_adjudication_v1")
RENDERS = ROOT / "renders"
ROIS = ROOT / "rois"

PAGE_300 = RENDERS / "full_page_300dpi.png"
PAGE_GRAY_300 = RENDERS / "full_page_grayscale_300dpi.png"

# Integer coordinates in the direct 300 dpi rendering of physical PDF page 691.
FIGURE_CAPTION_BOX = (285, 2280, 2195, 3045)
STANDALONE_BOX = (420, 2290, 2160, 2915)

CRITICAL_ROIS = {
    "CR01_blanket_annotation": (1120, 2300, 1770, 2415),
    "CR02_left_chain_and_cancel_arrow": (430, 2420, 1260, 2855),
    "CR03_focus_and_active_factors": (1090, 2430, 1810, 2740),
    "CR04_right_branch_z_y": (1550, 2380, 2170, 2845),
    "CR05_full_conditional_formula": (920, 2780, 1690, 2915),
    "CR06_caption": (285, 2890, 2195, 3045),
}


def save_crop(src: Image.Image, box: tuple[int, int, int, int], path: Path) -> None:
    crop = src.crop(box)
    crop.save(path)


def save_8x(src: Image.Image, path: Path) -> None:
    src.resize((src.width * 8, src.height * 8), Image.Resampling.NEAREST).save(path)


def main() -> None:
    page = Image.open(PAGE_300).convert("RGB")
    gray = Image.open(PAGE_GRAY_300).convert("L")
    assert page.size == (2481, 3508), page.size
    assert gray.size == page.size, gray.size

    save_crop(page, FIGURE_CAPTION_BOX, RENDERS / "figure_crop_300dpi.png")
    save_crop(page, STANDALONE_BOX, RENDERS / "standalone_300dpi.png")
    save_crop(gray, FIGURE_CAPTION_BOX, RENDERS / "grayscale_300dpi.png")

    overlay = page.crop(FIGURE_CAPTION_BOX).copy()
    draw = ImageDraw.Draw(overlay)
    for name, box in CRITICAL_ROIS.items():
        local = (
            box[0] - FIGURE_CAPTION_BOX[0],
            box[1] - FIGURE_CAPTION_BOX[1],
            box[2] - FIGURE_CAPTION_BOX[0],
            box[3] - FIGURE_CAPTION_BOX[1],
        )
        draw.rectangle(local, outline=(220, 30, 30), width=3)
        draw.text((local[0] + 4, local[1] + 4), name, fill=(180, 0, 0))
    overlay.save(RENDERS / "critical_roi_overlay_300dpi.png")

    for name, box in CRITICAL_ROIS.items():
        roi = page.crop(box)
        roi.save(ROIS / f"{name}_1x.png")
        save_8x(roi, ROIS / f"{name}_8x_nearest.png")


if __name__ == "__main__":
    main()
