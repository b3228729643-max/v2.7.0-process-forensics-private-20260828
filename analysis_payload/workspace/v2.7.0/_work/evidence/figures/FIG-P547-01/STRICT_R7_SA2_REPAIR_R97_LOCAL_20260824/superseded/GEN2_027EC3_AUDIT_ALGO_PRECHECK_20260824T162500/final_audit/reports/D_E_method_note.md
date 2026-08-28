# D/E method note

D compares actual PDF-emitted point sizes for the same semantic role, script class and font. Same-panel maximum/minimum is limited to 1.03 with absolute difference <=0.25 pt, and cross-panel median ratio to 1.05. Raw-pixel ink height is retained as a diagnostic, while C independently enforces the strict raw H thresholds. Low-profile punctuation is decided by its separate independently-rendered matching-font H/area calibration.

E compares role hierarchy from actual emitted PDF font sizes, with raw ink-height medians retained as diagnostics. This avoids treating different glyph outlines (for example a CJK ideograph, a digit, and a descending italic mathematical glyph) as a font-size measurement. All non-script visible font runs are separately checked against the 9.5 pt base floor.
