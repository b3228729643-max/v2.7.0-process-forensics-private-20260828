# Superseded T03/G04 mask result

The first preflight value `T03_MINIMUM_KEY <-> G04_MINIMUM_MARKER: overlap=4, clearance=0` is **superseded and must not be used for acceptance**.

## Reproduction of the false result

The four pixels are reproducible only with the superseded mask construction:

- superseded T03 TEXT mask: the final-PDF text span was padded by 3 pixels;
- superseded G04 MARKER mask: the filled Bezier marker was first stroked with a 15-pixel support and then dilated by an additional 11x11 kernel;
- because T03 and G04 use the same gold RGB foreground, the broadened object supports admitted the marker's top antialias pixels into the T03 object range.

The four superseded intersection coordinates in the native 2481x3508 page coordinate system are:

`(1352,941), (1353,941), (1354,941), (1355,941)`.

These pixels are not T03 glyph pixels. They are adjacent G04 marker antialias pixels misclassified by the padded T03 object extent.

## Corrected object masks

- T03 now uses the unpadded final-PDF glyph span and the >=20/255 local-background foreground rule.
- G04 now uses the marker's own Bezier fill, with only one raster pixel of antialias tolerance; it does not borrow any same-colour label pixels.
- corrected intersection count: `0`;
- corrected nearest foreground coordinates: T03 `(1350,927)` and G04 `(1350,942)`;
- corrected Euclidean foreground clearance: `15.000 px`.

The corrected current files are `mask_T03_MINIMUM_KEY_native_300dpi.png`, `mask_G04_MINIMUM_MARKER_native_300dpi.png`, `mask_overlap_T03_MINIMUM_KEY__G04_MINIMUM_MARKER_current_native_300dpi.png`, and `roi_minimum_label_vs_marker_raw_1to1_300dpi.png`. The files containing `superseded` in their names exist only to document the invalid preflight algorithm.
