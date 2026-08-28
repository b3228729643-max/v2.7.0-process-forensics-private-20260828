"""Make non-geometric review views and pixel-exact crops from the official 300 dpi page."""
from pathlib import Path
from PIL import Image, ImageOps

ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\evidence\figures\FIG-P186-01\STRICT_R1B")
source = ROOT / "renders" / "official_p200_300dpi.png"
page = Image.open(source).convert("RGB")
assert page.size == (2481, 3508), page.size

# All ROI rectangles are native raster coordinates (left, upper, right, lower),
# and Image.crop performs no scale or resampling.
rois = {
    "figure_and_caption_native_1x.png": (500, 1700, 1980, 3000),
    "plot_native_1x.png": (690, 1760, 1840, 2860),
    "labels_and_normal_native_1x.png": (1180, 1800, 1690, 2330),
    "boundary_samples_native_1x.png": (720, 1920, 1830, 2810),
    "boundary_label_native_1x.png": (1420, 2335, 1730, 2430),
    "misclassified_triangle_native_1x.png": (1540, 2380, 1700, 2540),
}
for filename, box in rois.items():
    page.crop(box).save(ROOT / "roi" / filename, dpi=(300, 300))

# This fit-page derivative is solely a human-review view, explicitly excluded
# from every pixel geometry measurement.
fit_width = 708
fit_height = round(page.height * fit_width / page.width)
page.resize((fit_width, fit_height), Image.Resampling.LANCZOS).save(
    ROOT / "renders" / "official_p200_fitpage_review_only.png", dpi=(85.5, 85.5)
)

# Grayscale preserves the native 2481 x 3508 grid (no resampling).
ImageOps.grayscale(page).save(
    ROOT / "renders" / "official_p200_300dpi_grayscale_native.png", dpi=(300, 300)
)

print("source", page.size)
for filename, box in rois.items():
    print(filename, box, (box[2] - box[0], box[3] - box[1]))
print("fit", (fit_width, fit_height))
