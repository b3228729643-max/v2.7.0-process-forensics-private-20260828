# Four-view inspection basis

- `full_page_200dpi.png`: direct R95 page render, page integration.
- `figure_crop_300dpi.png`: integer crop from direct native 300dpi full page; canonical pixel-measurement context.
- `standalone_300dpi.png`: identical unscaled native crop because the official R95 final PDF is the sole allowed input; no independent source render is substituted.
- `grayscale_300dpi.png`: native crop converted only for visual grayscale hierarchy inspection; never used for measurement.
- `glyph_contact_sheets/`: all glyphs as native source crops enlarged with nearest-neighbour solely for manual char↔shape checking.
