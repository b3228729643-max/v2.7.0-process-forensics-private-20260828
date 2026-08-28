from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parent / "affected_pages_150dpi"
page_files = sorted(ROOT.glob("page_*.png"))
groups = (page_files[:9], page_files[9:17], page_files[17:])

for sheet_number, group in enumerate(groups, 1):
    if not group:
        continue
    thumbs: list[tuple[str, Image.Image]] = []
    for path in group:
        with Image.open(path) as source:
            thumb = source.convert("RGB")
            thumb.thumbnail((414, 585))
            thumbs.append((path.stem.removeprefix("page_"), thumb.copy()))
    cell_width = 430
    cell_height = 620
    rows = (len(thumbs) + 2) // 3
    sheet = Image.new("RGB", (3 * cell_width, rows * cell_height), "white")
    draw = ImageDraw.Draw(sheet)
    for index, (label, thumb) in enumerate(thumbs):
        left = (index % 3) * cell_width
        top = (index // 3) * cell_height
        draw.text((left + 8, top + 6), f"PDF page {label}", fill="black")
        sheet.paste(thumb, (left + 8, top + 28))
    sheet.save(ROOT / f"contact_{sheet_number}.png")
