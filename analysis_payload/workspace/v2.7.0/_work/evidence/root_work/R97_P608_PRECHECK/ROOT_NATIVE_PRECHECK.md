# FIG-P608-01 root native-pixel precheck on official R97

- Official candidate: `strict_current_r97_fullbook/main_full.pdf`, SHA-256 `062AD81020CB19A5C6688A45C73E00965F5060E0960A69AF820D7DC154DEE814`.
- Scope: physical page 659 / printed page 646 / figure 32.8.
- Root opened the page rendered directly at 300 dpi (`2481 × 3508`) and a native 1× crop from source rectangle `[1350,1240,1770,1430]`.
- The upper-panel horizontal axis and the overbar of the lower-panel title `\overline X_{6:t}` are visibly contiguous in the native 1× raster; the 8× nearest-neighbour view preserves that contact. Visible foreground clearance is therefore 0 px.
- Root independently inspected the official page's PyMuPDF drawing list. Drawing 8 is the horizontal axis at centerline `y=311.025024 pt`, stroke width `0.647570 pt`; drawing 62 is the title overbar at `y=311.670044 pt`, stroke width `0.732000 pt`. Their centerline separation is `0.645020 pt` (`2.687581 px` at 300 dpi), smaller than their half-stroke-width sum `0.689785 pt` (`2.874104 px`), leaving a vector-stroke penetration of `0.044765 pt`. Drawing 61 is the rotated lower-y-label overbar and is separate from this failing pair.
- This is a hard visual failure candidate and the current figure must not pass. Exact shared-pixel count remains pending the independent SA1's two unique raw masks; this precheck does not substitute for its complete glyph/object/pair ledger.
- Files: `P608_title_axis_native300dpi_crop.png`, `P608_Xbar_axis_native1x.png`, `P608_Xbar_axis_8x_nearest.png`.

Verdict: `ROOT_PRECHECK_FAIL_CANDIDATE__REQUIRES_SA1_MASK_CONFIRMATION_THEN_SA2`.
