from pathlib import Path

from PIL import Image, ImageDraw


root = Path(__file__).resolve().parent / "affected_pages_150dpi"
pages = [
    141, 152, 168, 202, 211, 212, 232, 233, 273,
    311, 338, 454, 492, 512, 534, 557, 558, 604,
    609, 633, 640, 662, 667, 682, 690, 717, 719,
    720, 721, 722, 751, 752, 753, 777, 778,
]

for sheet_number, start in enumerate(range(0, len(pages), 9), 1):
    group = pages[start : start + 9]
    thumbs = []
    for page in group:
        with Image.open(root / f"page_{page}.png") as source:
            thumb = source.convert("RGB")
            thumb.thumbnail((414, 585))
            thumbs.append((page, thumb.copy()))
    cell_width, cell_height = 430, 620
    rows = (len(thumbs) + 2) // 3
    sheet = Image.new("RGB", (3 * cell_width, rows * cell_height), "white")
    draw = ImageDraw.Draw(sheet)
    for index, (page, thumb) in enumerate(thumbs):
        left = (index % 3) * cell_width
        top = (index // 3) * cell_height
        draw.text((left + 8, top + 6), f"PDF page {page}", fill="black")
        sheet.paste(thumb, (left + 8, top + 28))
    sheet.save(root / f"contact_{sheet_number}.png")
