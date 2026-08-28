# D/E method note

The D gate is intentionally two-tiered, without relaxing either tier. `D_same_role_scale_audit.csv` compares the actual PDF-emitted point size for all characters in the same semantic role, font/script, and baseline level. Same-panel maximum/minimum is limited to 1.03 with absolute difference <=0.25 pt, and cross-panel median ratio to 1.05. Thus unlike characters are not made incomparable merely by their codepoint.

`D_raw_pixel_object_role_audit.csv` separately compares native H and area only where semantic role, exact concrete glyph, font, emitted point size, and baseline level match. This is the required comparable-outline condition: raw height of an italic `j`, a CJK ideograph, a delimiter, and a subscript must not be treated as a font-size proxy for one another. Exact-outline element/median H and area must each be within [0.92,1.08], and the cross-panel comparable-outline median ratio must be <=1.10. Low-profile punctuation additionally remains bound to its independent same-codepoint/same-font/same-size calibration.

E compares semantic-role hierarchy from actual emitted PDF point sizes, with raw ink-height medians retained only as diagnostics. All non-script visible font runs are separately checked against the 9.5 pt base floor; natural TeX scripts are traced to their >=9.5pt parent formula.
