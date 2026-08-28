# FIG-P656-01 P656 source-font R1 local SA2 report

Result: `LOCAL_SA2_PASS_READY_FOR_MAIN`.

The accepted five-declaration source patch compiled in the one authorized direct LuaLaTeX invocation. Controller PID 22220 started child PID 25712 once; the child exited naturally with code 0 after 62.067 seconds. Retry count and second-start count are zero. The PDF is one A4 page, 35,680 bytes, SHA-256 `1B01C9FFA6E80AEFB79107BFDAE2B7014893BFCAA76654F756DB49AEE7E6C869`. Source and wrapper hashes are unchanged across the build, all recorded exception fields are empty, and both RESULT-time and review-time TeX process counts are zero.

Fresh non-TeX extraction from this PDF produced 90 glyphs and 25 visible drawing components, hence 115 objects and 6,555 unordered pairs. Independent SVG glyph masks eliminate full-page crop contamination. Three pairs share raster ink: the first arrow shaft/head, the count-box/outgoing-shaft endpoint, and the second arrow shaft/head. Each is an intended connector join. Another 115 pairs have overlapping geometric boxes but zero shared ink; they are formula typography or legal text-in-container relations. The remaining 6,437 pairs have disjoint bounding boxes. No object mask is empty and no object leaves the page.

Human review was performed after the final machine render was generated. It covers 115/115 object IDs, 34/34 ranked critical pairs, all pair families totaling 6,555, 12 views, and 15 hard gates. The 300 dpi page/crop, grayscale crop, object overlay, critical contact sheet, and five risk regions at 1x plus arrow/warning 8x show no tofu, wrong codepoint, unreadable or severely imbalanced text, real clipping, illegal overlap, broken connector, or semantic error. The enlarged `同一计数` label and warning text preserve clear separation after the font increase.

The three sequences have the common count `(3,1,2)`, the count-vector equation and support constraints are correct, the warning distinguishes counts from probabilities, and `N!/prod_k n_k!` correctly counts ordered sequences producing the same count. The source gate now has six fontsize declarations with minimum 9.5pt and zero declarations below the required threshold. The 9.4645 value reported by PDF extraction is the PDF-big-point representation of a 9.5 TeX-point declaration, not a source-gate regression.

This local result does not commit the source, update central state/inventory, launch a fresh role, or claim official full-book SA1/SA3. Main acceptance is required before any commit or subsequent route.
