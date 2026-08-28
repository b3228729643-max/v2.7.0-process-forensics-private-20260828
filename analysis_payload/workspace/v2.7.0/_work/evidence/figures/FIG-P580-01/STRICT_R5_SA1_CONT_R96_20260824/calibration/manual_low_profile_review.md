# Manual low-profile calibration review — FIG-P580-01

Native-final-PDF controls `G0199_control_01` through `G0199_control_08` were
opened as their paired original and mask images at 8x nearest on 2026-08-24.
Each has the same compact period silhouette as target G0199: a 7 px native
ink height and 41 px owned area.  The original crops include neighbouring page
ink only outside the target mask; every mask contains the period only.

- Target: G0199 `.`; `STIXTwoText-Bold`, exact PDF size 9.9626 pt.
- Controls: 8/8 visually reviewed; exact-codepoint/font/weight/colour/size
  cohort retained in `low_profile_calibration.csv`.
- Manual result: PASS.  No clipped, hollow, enlarged, or foreign-pixel mask
  condition was observed.
