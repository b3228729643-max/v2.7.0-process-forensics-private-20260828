# FIG-P602-01 — R103 fresh isolated SA3 review

## Outcome

**PASS — C_LOCAL_PASS only.** No hard-failure ID was found. This SA3 result does not update any central inventory or state; it waits for `/root` to accept or reject the local evidence recordset.

- HANDOFF_ID: `C-FIG-P602-01-R103-SA3-FRESH-ISOLATED-V1`
- recordset ID: `FIG-P602-01-R103-SA3-FRESH-ISOLATED-V1-RECORDSET-01`
- reviewer instance: `/root/sa3_fig_p602_r103_fresh_isolated`
- review mode: fresh, isolated, read-only business inputs
- source writer required: **NO**
- TeX rebuild required: **NO**
- failed object/glyph/pair/critical/role/clip/view/hard-gate IDs: **NONE**

## Independent location

The candidate was located from the 817-page official PDF itself by form-feed page indexing, direct page-text confirmation, and native rendering. No supplied or historical page number was used.

- PDF physical page: **653**
- printed page: **640**
- figure number: **32.5**
- full page: **595.276 × 841.890 pt**
- native 300dpi page render: **2481 × 3508 px**
- native 200dpi page render: **1654 × 2339 px**
- integer figure/caption crop on 300dpi page: **[312, 1444, 2122, 3008]**
- crop size: **1810 × 1564 px**

## Candidate and source identity

Official R103 PDF:

- path: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r103_fullbook\main_full.pdf`
- bytes: **4,967,184**
- SHA256: `9379a489e0c2a57a7da670c98029bb27b3f1a385bf8e4c3bd14fe9b606aa0f23`
- UTC mtime: `2026-08-25T09:22:37.2025732Z`
- NTFS 100ns file time: `134321233572025732`

Single current figure source:

- path: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C03\fig_v5_c03_mh_accept_reject.tex`
- bytes: **2,869**
- SHA256: `6c4e8f156709c0ff384f9e7b7f2bd5d9cb586e24206bf0bcd2e58933ed3db47d`
- UTC mtime: `2026-08-25T08:50:37.7391657Z`
- NTFS 100ns file time: `134321214377391657`

## Frozen foreground denominator

The composite-parent gate split every visible text/formula unit that can independently clip, overlap, or carry a relation. No TikZ-node grouping was allowed to swallow independent semantic rows.

| Category | Count |
|---|---:|
| text/formula/edge-label/caption objects | 20 |
| node borders | 6 |
| directed arrows | 5 |
| reject self-loop arrow | 1 |
| independent math rule | 1 |
| **total N** | **33** |
| **all unordered pairs C(33,2)** | **528** |

`SA3_COMPOSITE_PARENT_GATE.md` records each text parent’s exact visible content, PDF text-run count, bbox, and keep/split reason. The final split produces four independent two-line node contents, two independent decision lines, and separate caption label/text objects rather than composite containers.

## Record closure

| Record | Machine denominator | Manual closure |
|---|---:|---:|
| foreground objects | 33 | 33/33 |
| visible nonspace glyphs | 194 | 194/194 |
| PDF text runs | 65 | 65/65 mapped by machine; glyph/object manual closure complete |
| PDF drawing records | 28 | 28/28 primitive dispositions |
| unordered object pairs | 528 | 528/528 at 1x |
| critical pair ROIs | 37 | 37/37 at 1x and 8x |
| clip objects | 33 | 33/33 |
| text role/peer objects | 20 | 20/20 |
| actual render/image files | 717 | 717/717 exact-path closure |
| primary integrated views | 7 | 7/7 direct view rows |
| semantic statements | 10 | 10/10 |
| hard gates | 19 | 19/19 |

The eleven formal manual TSV ledgers contain **1,173** auditable rows: 909 individual judgment rows plus 264 exact render-path closure rows. The render denominator is **717 actual PNG files**: 7 primary views are direct rows, while the other 710 files are linked one-for-one through 194 glyph IDs, 33 object IDs, and 37 critical-pair IDs with exact relative paths. The covered unique path set equals the on-disk render set; missing and extra paths are both empty. Object notes are 33/33 unique, glyph notes 194/194 unique, pair notes 528/528 unique, and critical notes 37/37 unique. Machine validation reports exact object/glyph/pair/critical identity alignment, no duplicate identifiers, no failed invariant, and no non-PASS manual row.

## Primitive and text alignment

- all **65** figure/caption PDF text runs map to the 20 text parents;
- all **194** visible nonspace glyphs map to those runs and parents;
- **8** PDF spaces are excluded as whitespace with no visible foreground;
- all **28** page drawing records are closed:
  - **19** drawing records support 13 foreground objects (6 borders, 5 directed arrows, 1 self-loop arrow, 1 fraction rule);
  - **7** are final-invisible white label halos or the reject double-border white separator;
  - **2** are page-level primitives outside the figure crop.

No text run, visible glyph, or drawing record remains unmapped or unexplained. No object or glyph mask is empty.

## Pair, overlap, and clip result

All 528 unordered pairs were reviewed. Thirty-seven machine-critical ROIs were opened at both 1x and 8x. Eight pairs have non-zero raw foreground intersection; every one is an intended arrow-to-node endpoint anchor:

`P0456`, `P0468`, `P0479`, `P0489`, `P0490`, `P0497`, `P0505`, `P0506`.

No text–text, text–line, formula–unrelated-line, unrelated-border, or unrelated-edge collision exists. Every object has zero crop-boundary pixels. The smallest crop-edge margin is B05’s 7px left margin; its complete rounded border is visible and is not clipped.

## Glyph, role, and R168 result

Every glyph contact was examined as original, overlay, mask-only, and 8x-nearest views. There is no tofu, missing character, wrong codepoint, wrong mathematical glyph, unreadable content, genuine missing stroke, or foreign-pixel contamination.

- default figure text and labels: source **9.6pt**, PDF **9.564pt**;
- core ratio formula: source **11.2pt**, PDF **11.158pt**, with normal **7.811pt** scripts;
- caption: PDF **9.963pt**, about **1.042×** the default figure text.

The explicit core-formula enlargement is semantically appropriate. Caption/default micro-ratio, 1px raster height differences, and 1–2px endpoint alias gaps are R168 advisories only. Specifically, P0467 and P0478 have 1px final alias gaps and P0488 has 2px; all three retain clear arrow direction and endpoint reading. None is a hard failure.

### Role and peer denominators

The **role denominator is 20/20** and closes these exact IDs:

`T01_CURRENT_NODE_TITLE`, `T02_CURRENT_NODE_VARIABLE`, `T03_CANDIDATE_NODE_ACTION`, `T04_CANDIDATE_NODE_VARIABLE`, `T05_RATIO_HEADER`, `T06_RATIO_FORMULA`, `T07_DECISION_DRAW`, `T08_DECISION_COMPARE`, `T09_ACCEPT_NODE_ACTION`, `T10_ACCEPT_NODE_ASSIGNMENT`, `T11_REJECT_NODE_ACTION`, `T12_REJECT_NODE_ASSIGNMENT`, `T13_PROPOSAL_LABEL`, `T14_CALCULATE_LABEL`, `T15_DECISION_LABEL`, `T16_ACCEPT_LABEL`, `T17_REJECT_LABEL`, `T18_SELFLOOP_LABEL`, `T19_CAPTION_LABEL`, `T20_CAPTION_TEXT`.

The **peer denominator is independently 20/20**, with an explicit peer reference for every same ID:

- `T01→NODE_TEXT_9.564`, `T02→NODE_TEXT_9.564`, `T03→NODE_TEXT_9.564`, `T04→NODE_TEXT_9.564`;
- `T05→NODE_TEXT_9.564`, `T06→CORE_FORMULA_11.158`, `T07→NODE_TEXT_9.564`, `T08→NODE_TEXT_9.564`;
- `T09→NODE_TEXT_9.564`, `T10→NODE_TEXT_9.564`, `T11→NODE_TEXT_9.564`, `T12→NODE_TEXT_9.564`;
- `T13→EDGE_LABEL_9.564`, `T14→EDGE_LABEL_9.564`, `T15→EDGE_LABEL_9.564`, `T16→EDGE_LABEL_9.564`;
- `T17→EDGE_LABEL_9.564`, `T18→EDGE_LABEL_9.564`, `T19→CAPTION_9.963`, `T20→CAPTION_9.963`.

Thus neither the role gate nor the peer gate relies on a combined total or an implicit default.

## Mathematical and relation semantics

The visual flow is correct and agrees with the minimal adjacent explanatory context:

1. current state is `X_t`;
2. propose `Y` from the proposal kernel;
3. for positive forward flow, compute
   `α_t(Y)=min{1, π_u(Y)q(X_t|Y)/(π_u(X_t)q(Y|X_t))}`;
4. draw uniform `U∈[0,1]` and accept when `U≤α_t(Y)`;
5. acceptance sets `X_{t+1}=Y`;
6. rejection keeps `X_{t+1}=X_t` and is represented by the reject self-loop.

The numerator/denominator order, proposal-condition arguments, inequality direction, next-state assignments, branch directions, self-loop target, and caption are all correct.

## Page and grayscale review

The 200dpi and 300dpi full-page views show stable integration on printed page 640: no collision with equations 32.7–32.9, preceding prose, the figure caption, the following reading-order paragraph, or the footer. Figure-level and full-page grayscale views retain all relationship distinctions, including the dashed/dot-dashed paths, double reject border, self-loop, arrowheads, and text.

## Isolation and control attestation

Only the enumerated official PDF, current single source, goal, strict protocol, evidence schema, and the minimum adjacent semantic paragraph were read. No old P602/P600 evidence, role output, handoff, state/inventory, route log, task packet, figure scope, git history/diff/log, R103 freeze report, visual precheck, or other agent output was read. No source, PDF, central state, inventory, or shared file was modified. No TeX, LuaLaTeX, latexmk, or texlua command was run.

## Final disposition

**C_LOCAL_PASS.** Failed IDs: **NONE**. No source-writer or TeX action is indicated. The only authorized next step is for `/root` to verify the sealed manifest/marker and decide whether to accept this isolated local PASS into the main workflow.
