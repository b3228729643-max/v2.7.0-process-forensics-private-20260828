# P126 R9 local SA2 review

HANDOFF_ID=A-R115-P126-SA2-DIRECT-BUILD-R9-20260828  
UID=FIG-P126-01  
VERDICT=LOCAL_SA2_FAIL_RETURN_TO_MAIN_SOURCE_SCOPE

## Frozen identities

- Source: D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_A_visual\src\绘图源码\第01册_数学基础与统计学习基本理论\V1-C08\fig_v1_c08_coordinate.tex — 4361 bytes — SHA256 85FA5D73BD816149EE77968512C708C58CEE1AB90D59EDEBBDA550F232EE0D81
- PDF: D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\STRICT_R9_SA2_THREE_HARD_PATCH_R115_DIRECT_BUILD_20260828\build\v260_FIG-P126-01_standalone.pdf — 34051 bytes — SHA256 CE80FD14D39FE32269BF8535B0381006338AD14D9490292FB5B07230AFDA5573
- Build slot: released after one controller and one direct LuaLaTeX child; no TeX was run during this review.

## Denominator and coverage

The final current-PDF denominator is N=60: 25 glyphs, 9 lines, 2 reader-visible protective backgrounds, 4 square markers, and 20 curves. All unordered pairs were enumerated exactly once: C=1770. There are 218 machine candidates. Manual ledgers cover 60/60 objects, 1770/1770 pairs, 25/25 glyph-codepoint rows, 9 math/semantic checks, 5 hard-gate checks, and 23 actually opened final views/ROI sheets. Candidate relation sheets 01--11 were all opened after machine enumeration.

## Hard findings

1. `HARD-LEGEND-X2-CONTINUOUS`: rendered object C020 is a single 73 px occupied run with zero internal blank runs. Native1x, nearest8x, color, and grayscale views show the x2 legend sample as continuous, so the intended dashed distinction from x1 is absent.
2. `HARD-LABEL6-Q4-MARKER-CONTACT`: pair P00541 (T010 digit 6 versus C016 blue q4 marker) has center-distance 1 px, blank gap 0 px, and bbox overlap 8.938406 pt^2. Native1x and nearest8x views confirm real visible-ink contact.

The digit 7 regression is resolved: final native/nearest8x evidence shows an 8 px blank gap. Clip count and missing/tofu/wrong-codepoint count are zero. The quadratic, alternating coordinate-minimizer updates, strictly decreasing objective sequence, optimum placement, caption semantics, and page integration pass.

## Narrow return facts

Only the current P126 single source is implicated. A future static scope, if Main authorizes it, must (a) make the actual rendered x2 legend sample contain genuine separated teal segments rather than relying on a style ignored by the effective legend handler, and (b) move/protect digit 6 without contacting q4 marker or any other object. No source edit, build, commit, role transition, or central write was performed in this phase.
