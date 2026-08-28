# FIG-P657-01 SA3 manual text/glyph judgments

These per-element judgments were written after opening `text_measurement_overlay_300dpi.png`, both foreground/vector masks, `local_figure_native300dpi.png`, `local_figure_grayscale_300dpi.png`, full-page/page-integration views, and native1x/nearest8x ROIs R01--R06. Pixel heights come from `pixel_measurements_machine.csv`; codepoints were independently checked in `codepoint_inventory_machine.csv` and visually against the opened render.

- T01 (`先验族`, source line 18): 33 px CJK ink. U+5148/U+9A8C/U+65CF render with complete strokes; bold blue heading is readable and has a broad gutter to O02.
- T02 (`Dirichlet分布`, line 19): 34 px mixed ink. ASCII `Dirichlet` plus U+5206/U+5E03 are intact, centered, and 36.63 px or more from the node border by bbox lower bound.
- T03 (`Beta分布`, line 20): 34 px mixed ink. `Beta` and both CJK glyphs render without substitution; the first line is centered and vertically balanced above T04.
- T04 (`𝐾=2`, line 20): 26 px mathematical-base ink. Extracted italic K is U+1D43E, followed by U+003D/U+0032; all three glyphs are clear at native1x, and the bbox lower-bound to the bottom node border is 12.08 px.
- T05 (`似然族`, line 21): 33 px CJK ink. U+4F3C/U+7136/U+65CF are complete; size and weight visually match T01.
- T06 (`多项分布`, line 22): 33 px CJK ink. U+591A/U+9879/U+5206/U+5E03 are intact and centered with 36.63 px minimum bbox clearance to the border.
- T07 (`二项分布`, line 23): 32 px CJK ink. U+4E8C/U+9879/U+5206/U+5E03 render cleanly; the one-pixel anatomy difference from T06 is not a visible imbalance.
- T08 (`𝐾=2`, line 23): 26 px mathematical-base ink. U+1D43E/U+003D/U+0032 match T04 exactly in glyph form and perceived size; bottom border bbox clearance is 12.13 px.
- T09 (`单次试验`, line 24): 33 px CJK ink. U+5355/U+6B21/U+8BD5/U+9A8C are complete; the four-character heading remains aligned with the two three-character row headings without crowding O08.
- T10 (`类别分布`, line 25): 32 px CJK ink. U+7C7B/U+522B/U+5206/U+5E03 are complete, centered, and maintain 27.13 px or more bbox clearance to the node border.
- T11 (`𝑁=1`, line 25): 27 px mathematical-base ink. Extracted N is U+1D441 with U+003D/U+0031; native and R04 8x views show no tofu, truncation, baseline fault, or collision, and the bottom border bbox clearance is 12.25 px.
- T12 (`Bernoulli分布`, line 26): 34 px mixed ink. ASCII `Bernoulli` and U+5206/U+5E03 are intact; the longer label remains centered with 23.38 px or more bbox clearance.
- T13 (`𝐾=2,𝑁=1`, line 26): 31 px mathematical-base ink. U+1D43E and U+1D441 are correct, comma is U+002C, digits/operators are correct, and R04 8x shows a clean single baseline. Its larger ink height versus the short K-only labels comes from glyph anatomy (`N` and comma), not a source-size change or visible emphasis defect.
- T14 (`特殊情形`, line 30): 31 px CJK ink. U+7279/U+6B8A/U+60C5/U+5F62 are complete; R01 1x/8x shows the label clearly above the thin open arrow with generous line clearance.
- T15 (`特殊情形`, line 31): 31 px CJK ink. Codepoints and stroke shapes match T14; R03 confirms identical placement above the middle thin open arrow.
- T16 (`𝑁=1`, line 32): 27 px mathematical-base ink. U+1D441/U+003D/U+0031 are correct; the label sits right of the left vertical special-case arrow with no line contact.
- T17 (`𝑁=1`, line 33): 27 px mathematical-base ink. Codepoints match T16; R04 shows balanced placement and clear separation from both arrow and Bernoulli node.
- T18 (`𝐾=2`, line 34): 26 px mathematical-base ink. U+1D43E/U+003D/U+0032 are correct; R04 shows the label centered above the thin horizontal arrow without touching either endpoint node.
- T19 (`共轭`, line 36): 31 px CJK ink. U+5171/U+8F6D render correctly; R05 1x/8x shows clear whitespace after the thick filled arrow and no dependence on color alone.
- T20 (`特殊情形`, line 38): 30 px CJK ink. All four codepoints are correct and fully formed; although its source declaration is 8.8 pt, the native render is plainly readable, the 30 px full-CJK hard pixel floor is met exactly, and the label clears the thin open arrow.
- T21 (caption line 1, line 41): 40 px mixed ink. `图 34.3`, Chinese text, `Beta`, and `Dirichlet` are visibly complete in R06; the line begins and ends inside the official page, with no clipping or abnormal spacing.
- T22 (caption line 2, line 41): 41 px mixed ink. `Bernoulli` and all Chinese conclusion glyphs, including U+FF1B semicolon, render intact; R06 confirms the phrase distinguishing thick conjugacy arrows from set inclusion is complete and readable.

R168 advisory application: T02--T13 use 9.4 pt and T14--T20 use 8.8 pt declarations, below the older 9.5 pt source threshold. Those source/ratio differences are recorded as advisory only. Every visible element is actually readable at native scale, all measured ink heights meet their script-class floor, and no missing glyph, tofu, wrong codepoint, severe imbalance, clipping, illegal overlap, or semantic/geometry defect is present.
