from pathlib import Path

from PIL import Image

path = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\STRICT_R5_SA2_LEGEND_SEGMENT_PATCH_R115_DIRECT_BUILD_20260828\review\roi\LEGEND_GRAY_NATIVE1X.png")
image = Image.open(path).convert("L")

for y in range(image.height):
    xs = [x for x in range(image.width) if image.getpixel((x, y)) < 235]
    if not xs:
        continue
    runs = []
    start = previous = xs[0]
    for x in xs[1:]:
        if x != previous + 1:
            runs.append((start, previous))
            start = x
        previous = x
    runs.append((start, previous))
    long_runs = [(start, end) for start, end in runs if end - start + 1 >= 3]
    if long_runs:
        print(f"y={y:03d} runs={long_runs}")
