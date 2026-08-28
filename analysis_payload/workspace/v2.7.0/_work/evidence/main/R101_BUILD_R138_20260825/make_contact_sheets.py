from pathlib import Path

from PIL import Image, ImageDraw


root = Path(__file__).resolve().parent / "affected_pages_150dpi"
pages = [223, 227, 228, 247, 248, 262, 263, 291, 292,
         382, 389, 390, 406, 407, 416, 417, 437, 438, 659]
groups = (pages[:9], pages[9:18], pages[18:])

for sheet_number, group in enumerate(groups, 1):
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
