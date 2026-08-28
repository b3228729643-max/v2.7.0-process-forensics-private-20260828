# FIG-P467-01 root validation — STRICT R1

ROOT_RESULT: CONFIRM_SA1_FAIL

- Frozen official input: `strict_current_r93_fullbook/main_full.pdf`, physical page 509, printed page 496, 图 26.1.
- Root read the formal report and all aggregate CSVs, opened the native 300 dpi figure crop, measurement overlay and grayscale view, and checked the source-size groups.
- The decisive source-font failure is confirmed: 47/76 visible glyph rows derive from 9.0 pt annotation or 9.4 pt panel-title bases (with the title superscript naturally derived from an already-invalid parent). They are below the mandatory 9.5 pt effective-source floor; no overlap/geometry result can override this.
- SA1 also reports three per-glyph pixel failures for the naturally shallow CJK stroke `一` and punctuation in the figure number/caption. These rows are preserved as shape-sensitive measurements for SA2/reviewer follow-up; root rejection does not rely on them because the source-font failure is independently sufficient.
- All 399 independent text--text/text--graphic relations pass: illegal foreground overlap 0; text--text PDF/vector bbox minimum 20 px, text--text foreground minimum 43.788 px, text--graphic foreground minimum 54.197 px. All 61 edge objects pass and clip count is 0.
- Root confirms the four-panel semantic sequence (unit circle → `V^T` rotation → `Σ` axial scaling → `U` rotation), grayscale structure and page integration. Visual harmony nevertheless cannot pass while reader-facing title/annotation bases violate the hard source floor.

Disposition: reject current candidate; next role is SA2 only. Raise the local reader-facing bases without global shrinkage, rebuild an official candidate, then run a fresh strict SA1 before any SA3.
