# Source-effective font and semantics audit

The audited source is `fig_v5_c02_running_mean.tex`, not a reconstructed standalone figure.

- Lines 7/12: `tick label style={font=\fontsize{8.6pt}{10.3pt}\selectfont}`. All tick-label general-reader text is 8.6pt effective, below 9.5pt.
- Lines 8/13: axis label style is 9.6pt, above the floor.
- Line 25: `h(U_i)=U_i^2` node uses 9.2pt. Its TeX scripts are approximately 6.416pt effective; neither can satisfy a 9.5pt base/script hard floor.
- Lines 27/29/31/33: explanatory arrows/labels and `真值 1/3` use 9.2pt, below the floor.
- Lines 37/39/41/43: `.640`, `.325`, `.380`, `.325` use 8.5pt, below the floor.
- The common style's caption setting (`statlearnbook.sty` line 305) is rendered around 9.96pt and is not the source of the figure-font failure.

`after_font_audit.csv` records 29 source-font-failing visible elements. At the native final-PDF 300dpi coordinate, `after_pixel_measurements.csv` records six failed general glyph pixel/calibration gates. Revision 111 separately calibrates all 21 low-profile punctuation glyphs by same-codepoint/font/weight/pt raw masks: G0082 and G0114 fail the H_INK-and-area comparison, while eleven otherwise calibrated dots remain below the 9.5pt source floor. The hard font verdict is therefore false. The actual final-mask H_INK audit also has three D failures and two applicable same-script E failures; it uses neither a PDF-span nor a cross-script proxy (`role_hierarchy_audit.csv`, `role_e_actual_hink_audit.csv`).

Semantic check: the source and visible caption agree on samples 0.8, 0.1, 0.7, 0.4; their squares 0.64, 0.01, 0.49, 0.16; running means `.640`, `.325`, `.380`, `.325`; and the dashed target `1/3`. The curve descends, then rises, then descends. See `semantic_reviewer_ledger.csv`.
