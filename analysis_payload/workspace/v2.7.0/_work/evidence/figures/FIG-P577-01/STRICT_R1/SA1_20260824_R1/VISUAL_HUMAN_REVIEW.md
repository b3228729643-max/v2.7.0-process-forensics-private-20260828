# FIG-P577-01 human visual review

Reviewed directly:

- `full_page_300dpi.png`: native page integration, header/footer, caption placement, and surrounding body text (the auxiliary 200-dpi page view was not used for pixel counting).
- `standalone_300dpi.png`: whole standalone figure at native resolution.
- `grayscale_300dpi.png`: solid vs dashed curve, circle vs triangle, and guide-line distinction without colour.
- Native 1:1 and nearest-neighbour 8× focus packages for `TG304`, `TG317`, `TG457`, plus failed glyph `T004_G01`.

## Observations

- Whole-page integration, caption association, support endpoints, curve/area relationships, and grayscale distinguishability are visually coherent. No page clip or raster-resize artifact was seen.
- Font coordination is visually non-dominant and source-effective font declarations are all at least `9.5pt`; that source-level gate passes.
- The strict raster gate nevertheless fails: `glyph_evidence/T004_G01/roi_1to1.png` and `roi_8x_nearest.png` show the visible single `=` glyph at `12 px` ink height versus required `22 px`. This is a real raw-glyph finding and is independent of D/E diagnostics.
- Three raw-mask-separated clearance failures were viewed at both scales:
  - `TG304`: blue legend text `实线 p(y)` to final visible blue curve: `1 px` vs required `3 px`.
  - `TG317`: teal legend `虚线 cq(y)=8/5` to final visible dashed envelope: `1 px` vs required `3 px`.
  - `TG457`: visible y-axis tick `0.8` to accepted-callout border: `2 px` vs required `5 px`.

For each of those packages, `A_raw_mask.png`, `B_raw_mask.png`, `intersection_raw_mask.png`, and overlay show separate masks with zero overlap; the observed failure is clearance, not a fabricated overlap. Intentional guide/border connections are inventoried separately as graphics and are not counted as illegal text relations.
