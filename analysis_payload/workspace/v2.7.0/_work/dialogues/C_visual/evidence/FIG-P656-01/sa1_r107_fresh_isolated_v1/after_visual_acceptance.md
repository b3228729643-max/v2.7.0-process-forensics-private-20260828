# Fresh isolated SA1 visual acceptance

## Views actually opened

I opened the official full page at 200 dpi and native 300 dpi; the native figure-plus-caption crop; the standalone figure-body crop; the grayscale crop; the sequence, count, and coefficient panels; the complete 90-glyph overlay; and the complete 25-drawing overlay. I also opened all six glyph contact sheets and all six critical-relation sheets. The individual corrected cards for `G010`, `G016`, `G021`, and `G086`, plus the final affected relation ROIs `CR004`, `CR010`, `CR015`, `CR020`, `CR021`, and `CR027`–`CR030`, were reopened after the final mask definition was frozen.

## Manual findings

- All 90 glyph IDs map once to the intended visible codepoint and semantic parent. Every mask is nonempty, complete, and pure; missing-stroke and foreign-pixel counts are zero. The corrected patterned digits exclude teal hatch pixels. `G086` shows the complete product symbol, including its top bar, stems, and feet.
- All 25 drawing/path IDs map once to the intended visible node border/pattern, rounded box, shaft, or arrowhead. No visible formula rule is missing.
- All 34 critical semantic relations were opened and decided per ID. Text-to-node, text-to-arrow, and independent-text clearances satisfy the applicable hard gates. The only raw intersections are the three intentional graphic connections totaling 97 px; illegal overlap is zero.
- All 115 leaf objects are inside the standalone crop; `CLIP_PIXEL_COUNT=0`.
- The complete left-to-right visual story is readable and balanced. The heading is appropriately emphasized without dominating. Formula, warning, annotations, nodes, and arrows have coherent weight and spacing.
- Grayscale retains category distinction through outline, hatch, fill value, and spatial role. No information relies on color alone.
- The caption is complete and integrates naturally with surrounding page prose. No page-edge, caption, or adjacent-text collision is visible.

Under R168, the 1–2 px glyph-height differences, intrinsic low-profile punctuation/one-stroke shapes, exact-peer gaps, and small source-font metadata deviations are advisory only. They do not represent missing ink, wrong codepoints, unreadability, or severe imbalance here.

`FONT_VISUAL_HARMONY_PASS=true`

`SEMANTIC_CONTENT_PASS=true`

`GRAYSCALE_PASS=true`

`PAGE_INTEGRATION_PASS=true`

`OVERLAP_PIXEL_COUNT=0`

`CLIP_PIXEL_COUNT=0`

Manual decision: `PASS`.
