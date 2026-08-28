# Font and visual-harmony audit

Manual review used native 300 dpi full-page/crop/standalone/grayscale views and
the final glyph contact sheets. The 55 text objects in 'after_font_audit.csv'
all retain graphics scale 1.0 and pass their source/effective-size checks:
41 at 9.6 pt, 5 panel titles at 10.2 pt, and 9 caption objects at 10.0 pt.
Minimum effective size is 9.6 pt, above the 9.5 pt hard floor.

The source declares the regular '\fontsize{9.6}{11.6}' style at lines 4 and 10,
panel-title 10.2/12.2 at line 11, and 9.6 pt station/badge/node text in the
figure source. Noto Sans SC Bold is used for role titles, Noto Serif SC
ExtraLight for regular CJK, and STIX Two Text for Latin/math-like glyphs.
Observed PDF sizes agree with their role declarations. The panels have
consistent title hierarchy, consistent title/body weight contrast, matching
baselines and line spacing, and no visually abrupt panel-to-panel scale jump.
Color hierarchy remains readable in grayscale.

The lone failure is not a font-harmony failure: GLY0215's clean visual colon
fails the independently required low-profile same-codepoint area calibration.

FONT_VISUAL_HARMONY_PASS: true
FONT_SIZE_HARD_GATE: PASS
FONT_TERMINAL_EFFECT: GLY0215 calibration independently requires FAIL_TO_SA2
