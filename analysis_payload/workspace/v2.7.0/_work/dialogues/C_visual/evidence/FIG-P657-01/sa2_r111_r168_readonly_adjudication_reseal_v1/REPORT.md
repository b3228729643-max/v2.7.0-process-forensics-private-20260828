# SA2 read-only adjudication report — FIG-P657-01 / Fig. 34.3

## Sealed decision

`SA2_NO_SOURCE_CHANGE_READY_FOR_FRESH_SA1`

No R168 hard defect was found. No source edit or build is warranted. This SA2 does not start SA1.

## Identity and isolation

- Handoff ID: `C-FIG-P657-01-R111-SA2-R168-READONLY-ADJUDICATION-V1`
- Actual instance: `/root/sa2_fig_p657_r111_r168_readonly_v1`
- Model / effort / fork turns: `gpt-5.6-sol` / `xhigh` / `none`
- Assigned UID / figure: `FIG-P657-01` / Fig. 34.3
- Evidence root was absent immediately before creation and was created only for this adjudication.
- Official R111 PDF: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r111_fullbook\main_full.pdf`; 4,967,076 bytes; SHA256 `DAB1062500E39DD2C34C6B4A9FF51CAC2BE0A4C84B2F45F5FB8E645C4BC012D6`.
- Current single source: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C05\fig_v5_c05_distribution_relations.tex`; 2,927 bytes; SHA256 `B2B3A8748133B55169F08A543DF39E238E2FB3DFFF67EA0067C543CD9FDE31D2`.
- Forbidden counters: old P657 evidence/role/root/report/handoff/state/inventory/chat/Git-history/main-acceptance reads 0; other-UID conclusion reads 0; route-authorization reads 0; Git calls 0; source/chapter/PDF writes 0; TeX/LuaLaTeX/latexmk/build calls 0; commits 0; central state/inventory writes 0; second UID/role starts 0; process-management calls 0; collaboration status/identity/enumeration/history calls 0; subagents spawned 0.

## Independent localization and views

The current source/caption text was searched independently in the verified R111 PDF. Fig. 34.3 is on physical PDF page 706, printed page 693. The page is A4-sized at 595.276 × 841.890 pt. Direct Poppler renders are 1654 × 2339 at 200 dpi and 2481 × 3508 at 300 dpi.

The figure body, complete figure-plus-caption, and caption were integer-cropped from the direct 300 dpi render without resampling. The standalone body is therefore derivable without TeX. The 200 dpi full page, 300 dpi full page, figure crop, standalone body, grayscale figure-plus-caption, caption, text-measurement overlay, and semantic-object overlay were all opened and visually reviewed. Page integration is coherent; the complete caption is present; grayscale preserves hierarchy and the thick-versus-thin arrow distinction.

## Mathematical and semantic adjudication

All six nodes are present and correct:

1. Dirichlet prior family.
2. Beta prior family with `K=2`.
3. Multinomial likelihood family.
4. Binomial likelihood family with `K=2`.
5. Categorical single-trial family with `N=1`.
6. Bernoulli family with `K=2, N=1`.

All displayed relations are correct:

- Thick filled Dirichlet → multinomial: Dirichlet is a conjugate prior family for the multinomial likelihood family.
- Thick filled Beta → binomial: Beta is a conjugate prior family for the binomial likelihood family.
- Thin open Dirichlet → Beta: `K=2` special case.
- Thin open multinomial → binomial: `K=2` special case.
- Thin open multinomial → categorical: `N=1` special case.
- Thin open binomial → Bernoulli: `N=1` special case.
- Thin open categorical → Bernoulli: `K=2` special case.

The legend correctly maps the thick filled arrow to conjugacy and the thin open arrow to special case. The thick downward arrow means prior-family-to-likelihood-family conjugacy; it is not set inclusion. This direction and meaning were recomputed from the current source and narrow current chapter context, and the caption explicitly agrees.

## Frozen visible-object denominator and exhaustive pairs

- Visible non-space glyphs: 186.
- Foreground drawing primitives: 24.
- Node fills catalogued separately as backgrounds: 6.
- Total visible records including backgrounds: 216.
- Frozen foreground denominator: `N=210`.
- Expected unordered pairs: `C(210,2)=21,945`.
- Actual enumerated unordered-pair rows: 21,945.
- Nonzero raw intersections: 17.
- Critical relations: 36 = 19 clearance/semantic relations + all 17 nonzero-pair relations.
- Sum of critical raw intersection pixels: 1,378.

Every one of the 17 intersections is visibly intentional: eight arrow-to-own-node endpoint connections and nine shaft-to-own-arrowhead joins. No glyph-glyph intersection remains. During machine-evidence refinement, five exact adjacent-glyph boundary pixels were recognized after opening as ownership duplication, not contour collision; half-open rounded x ownership removed those duplicates without changing the visible union. The final denominator and pair table use unique pixel ownership.

## Typography, codepoints, clipping, and manual review

- Text parents: 17; positional codepoint mismatches: 0.
- Glyph masks with zero ink: 0; graphic masks with zero ink: 0.
- Page-clipped foreground pixels across all 210 denominator objects: 0.
- Foreground extent outside the complete figure-plus-caption crop: 0.
- Glyph contact sheets opened: 19/19, covering 186/186 cells.
- Graphic contact sheets opened: 6/6, covering 24/24 cells.
- Critical native 300 dpi/1× ROIs opened: 36/36.
- Critical nearest-neighbor 8× overlays opened: 36/36.
- Genuine manual ledgers: glyph 186 rows; drawing 24; critical 36; views 8; semantics 16; hard gates 12.

All glyph/codepoint forms are present, including Latin distribution names, CJK labels/caption, math `K`, `N`, equals signs, digits, commas, colon, and the Fig. 34.3 punctuation. Low-profile punctuation has naturally smaller ink height but is intact and readable. There is no missing glyph, tofu, wrong codepoint, wrong mathematical label, true clipping, illegal overlap, or actual unreadability.

## R168 application

Current-source values are base 9.2 pt, node 9.4 pt, edge label 8.8 pt, and role heading 9.5 pt. Under R168, the 8.8/9.2/9.4 pt values below the old 9.5 pt threshold are `ADVISORY_ONLY` by value alone and cannot cause a failure or source return. The rendered result was judged for actual symptoms. No missing/tofu/wrong codepoint or math meaning, unreadability, visibly obvious severe imbalance, true clipping, illegal overlap, or semantic/geometric error exists.

## Outcome and next action

No source files changed; no build was run. There are no unresolved hard candidates. The sealed outcome is `SA2_NO_SOURCE_CHANGE_READY_FOR_FRESH_SA1`. A fresh SA1 may independently consume this sealed evidence; this SA2 does not start or self-count any later role.
