from pathlib import Path

from PIL import Image


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P067-01\STRICT_R7_SA2_CDF_STEP_HANDLER_R112_DIRECT_BUILD_20260827")
source = Image.open(ROOT / "views" / "figure_native1x_300dpi.png").convert("RGB")

# The split is taken through the blank inter-panel gutter, so neither crop
# clips visible plot ink.  Nearest-neighbour preserves the native pixel test.
crops = {
    "cdf_panel_native1x_300dpi.png": (0, 0, source.width, 282),
    "pmf_panel_native1x_300dpi.png": (0, 282, source.width, source.height),
}

for name, box in crops.items():
    native = source.crop(box)
    native.save(ROOT / "views" / name)
    native.resize((native.width * 8, native.height * 8), Image.Resampling.NEAREST).save(
        ROOT / "views" / name.replace("native1x_300dpi", "nearest8x")
    )
