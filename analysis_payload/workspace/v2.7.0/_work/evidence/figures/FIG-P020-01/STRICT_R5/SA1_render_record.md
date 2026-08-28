# SA1 R90 render record

- Official input: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r90_fullbook\main_full.pdf`
- Physical page: `17` (1-based)
- Page extraction: `pypdf.PdfWriter.add_page(reader.pages[16])`; one-page PDF saved as `SA1_official_page17.pdf`.
- 200 dpi command: `pdftoppm -f 17 -l 17 -singlefile -r 200 -png main_full.pdf SA1_full_page_200dpi`; result 1654 x 2339 px.
- 300 dpi command: `pdftoppm -f 17 -l 17 -singlefile -r 300 -png main_full.pdf SA1_full_page_300dpi`; result 2481 x 3508 px.
- All crops use Pillow `Image.crop` only. No `resize`, resampling, browser screenshot, preview image, or second rasterization was used.
- Coordinates are `x0,y0,x1,y1` in the native 2481 x 3508 page raster.

## Crops

- `SA1_figure_crop_300dpi.png`: crop=(236, 1205, 2197, 1684); size=(1961, 479); dpi=300; resize=False
- `SA1_figure_1to1_300dpi.png`: crop=(236, 1205, 2197, 1615); size=(1961, 410); dpi=300; resize=False
- `SA1_standalone_300dpi.png`: crop=(236, 1205, 2197, 1615); size=(1961, 410); dpi=300; resize=False
- `SA1_roi_relation_inline_arrow_300dpi_1to1.png`: crop=(890, 1328, 1235, 1423); size=(345, 95); dpi=300; resize=False
- `SA1_roi_main_arrows_300dpi_1to1.png`: crop=(790, 1310, 1765, 1375); size=(975, 65); dpi=300; resize=False
- `SA1_roi_node_object_300dpi_1to1.png`: crop=(420, 1245, 815, 1445); size=(395, 200); dpi=300; resize=False
- `SA1_roi_node_relation_300dpi_1to1.png`: crop=(865, 1245, 1260, 1445); size=(395, 200); dpi=300; resize=False
- `SA1_roi_node_logic_300dpi_1to1.png`: crop=(1310, 1245, 1705, 1445); size=(395, 200); dpi=300; resize=False
- `SA1_roi_node_task_300dpi_1to1.png`: crop=(1755, 1245, 2150, 1445); size=(395, 200); dpi=300; resize=False
- `SA1_roi_audit_return_300dpi_1to1.png`: crop=(245, 1425, 1985, 1605); size=(1740, 180); dpi=300; resize=False
- `SA1_roi_caption_300dpi_1to1.png`: crop=(315, 1580, 2140, 1685); size=(1825, 105); dpi=300; resize=False
- `SA1_grayscale_300dpi.png`: crop=(236, 1205, 2197, 1684); size=(1961, 479); dpi=300; resize=False
