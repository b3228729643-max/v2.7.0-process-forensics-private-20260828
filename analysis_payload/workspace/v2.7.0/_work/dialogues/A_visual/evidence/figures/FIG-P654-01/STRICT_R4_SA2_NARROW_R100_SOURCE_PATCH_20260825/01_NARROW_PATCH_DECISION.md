# Narrow source-patch decision

- `TARGET_OBJECT`: `FRM_TRIAL_005`
- `TARGET_SOURCE_NODE`: line 22, `\node[aux,text width=28mm] (trial) ... {类别计数\\$\boldsymbol n$};`
- `PATCH_BOUNDARY`: change only the local typesetting size of the standalone mathematical `n`; retain `\boldsymbol n`, all text, node coordinates, dimensions, styles, graph paths and every other object.
- `SELECTED_LOCAL_SIZE`: `10.7pt` with the existing `12.2pt` leading, scoped in a TeX group around the second-line formula only.

## Quantitative expectation

The accepted mask height is 21px at 10.1pt. Under the unchanged 300 dpi rasterization and font, the local linear size ratio is `10.7 / 10.1 = 1.059406`; the first-order expected ink height is `21 * 1.059406 = 22.2475px`, which crosses the strict 22px floor with a small rasterization margin. The local formula/base source ratio becomes `10.7 / 10.1 = 1.059406`, inside the protocol's `[1.00, 1.18]` formula-to-base band and below the existing 11.6pt formula-block emphasis.

The change is narrower than resizing the trial node or the global node style: the four CJK glyphs, the paired Gamma/Beta node, every other formula, and all graph geometry remain source-identical. The 28mm text width and 12mm minimum node height dominate layout; the glyph is centered with ample accepted R100 clearance, so the roughly 1.25px first-order width growth should not move the node boundary or threaten neighboring objects.

## Residual risks requiring the next build

- Raster quantization and the `20/255` foreground threshold may still yield 21px; only a new native 300 dpi candidate measurement can decide.
- The enlarged glyph could change its own bbox by about 1–2px; new evidence must recheck its node-border clearance, text pair clearances, ownership, overlap and clip.
- Font harmony/source-role checks must confirm the explicit local formula emphasis remains acceptable.

No threshold, audit rule, semantic token, font family, global style or geometry is changed. No TeX process is authorized in this source-patch stage.
