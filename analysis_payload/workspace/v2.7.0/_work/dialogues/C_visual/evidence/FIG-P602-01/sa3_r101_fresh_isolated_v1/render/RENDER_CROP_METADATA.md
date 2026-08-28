# Render and crop metadata

| View | Direct source | DPI | Native output / crop | Dimensions | Resize |
|---|---|---:|---|---:|---|
| `full_page_200dpi.png` | official PDF physical page 651 | 200 | whole page | 1654×2339 | none |
| `figure_crop_300dpi.png` | direct native 300 dpi page render | 300 | integer xyxy `[300,1430,2135,2995]` | 1835×1565 | none |
| `standalone_300dpi.png` | direct native 300 dpi page render | 300 | integer xyxy `[300,1430,2135,2910]` | 1835×1480 | none |
| `grayscale_300dpi.png` | direct grayscale native page render | 300 | integer xyxy `[300,1430,2135,2995]` | 1835×1565 | none |
| `measurement_figure_crop_300dpi_fitz_native.png` | PyMuPDF direct pixmap | 300 | integer xyxy `[300,1430,2135,2995]` | 1835×1565 | none |

All object/glyph masks use the PyMuPDF native-300 dpi crop coordinate system. Every pair card contains a 1× native full-pair overlay (A red, B cyan, intersection yellow) plus independently displayed nearest-point native 1× and nearest-neighbor 8× raw-mask panels. `all_pairs_machine.csv` records the two mask paths, closest points, raw overlap, illegal overlap, metric, clearance and applicable threshold for all 496 pairs.

