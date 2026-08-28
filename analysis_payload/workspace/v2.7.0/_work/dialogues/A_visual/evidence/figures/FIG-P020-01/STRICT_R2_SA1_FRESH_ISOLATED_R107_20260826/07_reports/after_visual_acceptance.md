# After visual acceptance

Final machine artifacts were fixed before manual review. The reviewer then actually opened:

- 12/12 glyph contact sheets covering 108/108 visible glyphs
- 4/4 graphic contact sheets covering 14/14 visible foreground paths
- 6/6 required page/crop/standalone/grayscale/measurement-overlay/foreground-overlay views
- 22/22 critical-relation panels: 11 raw 1× five-panel views and 11 nearest-neighbor 8× five-panel views
- 2/2 actual embedded-font punctuation calibration views for G053 and G068

The hand-authored ledgers close at: glyph 108/108, graphic 14/14, relation 11/11, view 8/8, role 4/4, and source-font element 10/10. Every row has a row-specific note and `PASS`; every boolean/note/decision field was authored only after the final visual artifacts were opened.

Visual findings:

- Every red target overlay matches the intended visible glyph or path; every mask-only view is nonempty and pure, with 0 missing-stroke pixels and 0 foreign pixels in the manual ledgers.
- All visible Chinese, Latin, digits, punctuation, and arrow notation are readable at direct native 300 dpi and remain readable in the 200 dpi full-page view.
- G053 `：` and G068 `.` were calibrated against their actual embedded PDF font glyphs; both have equal target/reference ink height and complete visible forms. Their area differences are R168 raster/engine advisories, not hard defects.
- G091 `一` is a complete single horizontal stroke. Its 5 px raster height is an R168 advisory and cannot alone trigger failure.
- Nominal source sizes are 10.0 or 10.5 pt with graphics scale 1.0. PDF metadata deviations of roughly 0.037–0.039 pt are R168 advisories only.
- The four node headings use a controlled 10.5 pt bold emphasis. Ordinary CJK role medians are 41 px for headings and 36 px for node body, annotation, and caption. The resulting hierarchy is deliberate and not severely imbalanced.
- Grayscale preserves structure: solid main arrows and the dashed feedback route remain distinguishable without relying on color alone.
- The full page is balanced and integrated with the surrounding prose and caption; no clipping, unreadable text, tofu, wrong codepoint, semantic reversal, or geometry error was found.

R168 was applied exactly: micro `[0.92,1.08]` ratios, font-metadata differences, single-horizontal-stroke CJK pixel height, and 1–2 px raster differences were treated as advisory and never used alone to trigger failure or rebuild.

Manual visual verdict: `PASS`.
