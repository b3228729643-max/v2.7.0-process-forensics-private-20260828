# R5 SA1 page, crop, grayscale, and identity review

Canonical evidence directory: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\evidence\figures\FIG-P602-01\STRICT_R5_REQUAL_R96_SA1_CONT_20260824`.

- Frozen official PDF: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r96_fullbook\main_full.pdf`.
- PDF SHA-256: `8EED8765A4856C4C197262DEA06E283790FBA8DA906C70C26FC7BD56F6F7E5E8`.
- Page identity: physical 651 of 813; printed page 638; figure 32.5.
- Frozen figure source SHA-256: `18B88F4BC48A21D3FD1A246AC5B6909DEEB19900A3D0721C65F9A44369444084`.
- Native direct render: `official_R96_physical_651_full_page_300dpi.png`, 2481×3508 px; the supplemental 200 dpi render is retained only for page context.
- Figure/caption crop: `figure_crop_300dpi.png`, direct crop rectangle `[250,1416,2230,3000]`; `standalone_300dpi.png` is the same official-PDF crop, not a separate build.
- Grayscale review: `grayscale_300dpi.png`.

Manual visual review of the full native crop, grayscale crop, and glyph-bounding overlay found complete node borders, arrows, arrowheads, fraction rule, decision diamond, loop, labels, caption number, and caption text.  No clipping, crop truncation, unexpected opaque obstruction, or misleading visual connection was found.  The red boxes in `after_text_measurement_overlay_300dpi.png` identify measured glyph-gate failures; they are evidence annotations and not a rendering defect.

**Page/crop/grayscale/integrity result: PASS.**  The final terminal result remains controlled by the independent glyph-floor gate.
