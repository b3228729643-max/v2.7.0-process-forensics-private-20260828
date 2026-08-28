from pathlib import Path
import json
import math

from PIL import Image, ImageOps

ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P641-01\sa1_r110_fresh_isolated_v1")
SCALE = 300 / 72.0


def px_rect(pt_rect):
    x0, y0, x1, y1 = pt_rect
    return [math.floor(x0 * SCALE), math.floor(y0 * SCALE), math.ceil(x1 * SCALE), math.ceil(y1 * SCALE)]


def main():
    page = Image.open(ROOT / "full_page_native300dpi.png").convert("RGB")
    regions = {
        "figure_crop_300dpi.png": [71.0, 553.0, 513.0, 730.0],
        "standalone_300dpi.png": [117.0, 553.0, 470.0, 696.0],
    }
    metadata = {}
    for name, pt in regions.items():
        box = px_rect(pt)
        crop = page.crop(tuple(box))
        crop.save(ROOT / name)
        metadata[name] = {
            "source": "full_page_native300dpi.png",
            "crop_pt": pt,
            "crop_px_in_full_page": box,
            "native_dimensions_px": list(crop.size),
            "resize_performed": False,
        }
    gray = ImageOps.grayscale(Image.open(ROOT / "figure_crop_300dpi.png"))
    gray.save(ROOT / "grayscale_300dpi.png")
    metadata["grayscale_300dpi.png"] = {
        "source": "figure_crop_300dpi.png",
        "native_dimensions_px": list(gray.size),
        "resize_performed": False,
        "conversion": "Pillow RGB-to-L grayscale only; geometry unchanged",
    }
    (ROOT / "machine_view_geometry.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(metadata, ensure_ascii=True))


if __name__ == "__main__":
    main()
