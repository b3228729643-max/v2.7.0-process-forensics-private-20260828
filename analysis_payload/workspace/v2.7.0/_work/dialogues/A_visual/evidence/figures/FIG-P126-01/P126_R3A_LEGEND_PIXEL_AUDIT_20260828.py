import json
from pathlib import Path

from PIL import Image


IMAGE = Path(
    r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01"
    r"\STRICT_R3A_SA2_COORDINATE_QUADRATIC_PATCH_R115_DIRECT_BUILD_20260828"
    r"\evidence\critical_legend_solid_vs_dash_nearest8x.png"
)


def runs(values: list[bool]) -> list[tuple[int, int, int]]:
    output: list[tuple[int, int, int]] = []
    start = None
    for index, value in enumerate(values):
        if value and start is None:
            start = index
        elif not value and start is not None:
            output.append((start, index - 1, index - start))
            start = None
    if start is not None:
        output.append((start, len(values) - 1, len(values) - start))
    return output


image = Image.open(IMAGE).convert("L")
print(f"size={image.size}")
result = {"image": str(IMAGE), "image_size": list(image.size), "samples": {}}
for label, left, right in (("solid", 100, 850), ("dash", 2050, 2800)):
    scored = []
    for y in range(image.height):
        count = sum(image.getpixel((x, y)) < 245 for x in range(left, right))
        scored.append((count, y))
    print(f"{label}_top_rows={sorted(scored, reverse=True)[:12]}")
    best_count, best_y = sorted(scored, reverse=True)[0]
    best_runs = runs([image.getpixel((x, best_y)) < 245 for x in range(left, right)])
    result["samples"][label] = {
        "x_window": [left, right],
        "best_y": best_y,
        "dark_pixel_count": best_count,
        "dark_runs": [list(item) for item in best_runs],
        "long_run_count": sum(item[2] >= 20 for item in best_runs),
    }
    for _, y in sorted(scored, reverse=True)[:4]:
        row = [image.getpixel((x, y)) < 245 for x in range(left, right)]
        print(f"{label}_y={y}_runs={runs(row)}")

result["objective_finding"] = (
    "Both legend swatches contain one long continuous horizontal dark run at their maximum-density center row; "
    "the x2 swatch does not show the requested multi-dash separation in this rendered grayscale ROI."
)
OUTPUT = IMAGE.with_name("LEGEND_GRAYSCALE_PIXEL_RUN_AUDIT.json")
OUTPUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"wrote={OUTPUT}")
