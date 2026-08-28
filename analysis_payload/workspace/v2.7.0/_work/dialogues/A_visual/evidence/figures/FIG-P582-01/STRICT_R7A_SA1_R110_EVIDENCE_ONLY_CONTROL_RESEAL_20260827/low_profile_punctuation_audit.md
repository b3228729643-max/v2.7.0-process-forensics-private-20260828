# Low-profile punctuation audit

Reviewer: `A-R110-P582-SA1-FRESH-ISOLATED-20260827`

All rows below were opened in their final glyph contact sheets. Every target mask is non-empty, complete, and free of foreign pixels.

| Glyphs | Codepoint/font/size group | H ratio | area ratio | Manual result |
|---|---|---:|---:|---|
| GLY-007/010/013/016/019/022/025 | `.` / STIXTwoMath-Regular / 9.46451 pt | 6/6 = 1.000 | 27/27 = 1.000 | PASS |
| GLY-051/055/059/063 | `.` / STIXTwoText-Regular / 9.46451 pt | 6/6 = 1.000 | 27/25 = 1.080 | PASS at the inclusive upper bound |
| GLY-091/095/099/103 | `.` / STIXTwoMath-Regular / 9.96264 pt | 6/6 = 1.000 | 27/26 = 1.038 | PASS |
| GLY-093/097/101 | `,` / STIXTwoMath-Regular / 9.96264 pt | 11/11 = 1.000 | 45/44 = 1.023 | PASS |
| GLY-082 | `.` / STIXTwoText-Bold / 9.86251 pt | no exact peer | no exact peer | PASS_R168_ADVISORY; complete bold figure-number point and plainly readable |
| GLY-114 | `；` / NotoSerifSC-ExtraLight / 9.96264 pt | no exact peer | no exact peer | PASS_R168_ADVISORY; complete fullwidth semicolon and plainly readable |
| GLY-124 | `，` / NotoSerifSC-ExtraLight / 9.96264 pt | no exact peer | no exact peer | PASS_R168_ADVISORY; complete fullwidth comma and plainly readable |

The three no-peer cases are retained as advisories because this audit is forbidden to compile a synthetic calibration sample, and the task explicitly applies the R168 hard-failure scope: font or micro-grid differences alone do not fail unless they produce missing/tofu/wrong-coded glyphs, mathematical semantic error, actual unreadability, obvious visual imbalance, clipping, or illegal overlap. None of those hard conditions is present.
