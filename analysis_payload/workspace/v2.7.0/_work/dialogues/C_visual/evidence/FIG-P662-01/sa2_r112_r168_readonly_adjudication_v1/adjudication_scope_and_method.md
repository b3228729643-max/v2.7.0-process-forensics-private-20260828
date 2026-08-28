# FIG-P662-01 R168 isolated SA2 adjudication

- HANDOFF_ID: `C-FIG-P662-01-R112-SA2-R168-READONLY-ADJUDICATION-V1`
- INSTANCE: `/root/sa2_fig_p662_r112_r168_readonly_adjudication_v1`
- MODEL / EFFORT: `gpt-5.6-sol` / `xhigh`
- UID: `FIG-P662-01`
- CANDIDATE: official frozen R112 full-book PDF
- SOURCE: current `fig_v5_c05_gamma_normalization.tex`
- RESULT ROOT: this directory only

## White-list scope actually used

The adjudication used only the frozen R112 PDF, the current figure source, active root `GOAL.md`, its directly referenced strict pixel/evidence section, and the immediately relevant current V5-C05 definition/theorem/proof context. No prior P662 evidence or conclusion, no other UID evidence, no central acceptance/state/history record, no Git history, and no route-authorization record was read.

The stale/swapped Goal B69/B70 “unique reading conclusion” sentence was not inherited and the card mismatch was not treated as a PDF/source defect. The current figure was adjudicated from its own source/caption, R112 pixels, and current V5-C05 mathematics.

## Frozen identities

The fresh identity check matched the dispatch constants exactly:

- R112 PDF: 4,967,100 bytes; SHA-256 `D4B4DDF5F127D107FB66BF2805F4637D39CDB861F7CBB47BB2CDBB72E4E28FA2`.
- Current figure source: 3,588 bytes; SHA-256 `B5232526402FEF6735DC3F9C07B418D7BF49E0D8C17EAEFB82A54B450B63113E`.

Exact paths, bytes, hashes, and NTFS ticks are preserved in `frozen_input_identities.json`.

## Independent locator

Fresh text extraction from the frozen PDF matched the current source label/caption at one-based PDF page 710, printed page 697, Figure 34.5. The visible figure and caption match `fig:V5-C05-gamma-normalization`.

## R168 decision rule

Source declarations and legacy numeric typography thresholds were treated as advisory. A source-return FAIL was reserved for native evidence of missing glyph/tofu/wrong codepoint or math, unreadability, visibly obvious imbalance, true clipping, illegal overlap, or semantic/geometric error.

## Frozen visible-object denominator

The denominator is frozen at 20 semantic visible objects (`O01`–`O20`). A semantic card is one object whose border/fill/text are internally enumerated as visible subcomponents; this avoids pretending that a label and its own card background are unrelated objects while retaining explicit internal-clearance review. The inventory covers every visible card, badge, connector, icon/annotation, and the complete caption. All `20 choose 2 = 190` unordered object pairs are enumerated as `P001`–`P190` in `all_unordered_object_pairs_machine.csv` and manually adjudicated in `manual_pair_ledger.md`.

## Views actually opened before manual decisions

- full page at 200 dpi and 300 dpi;
- page-integration overlay;
- native 300 dpi figure-only, caption-only, and figure+caption crops;
- native 300 dpi grayscale;
- semantic-object overlay and 78-span text/codepoint overlay;
- all eight risk ROIs at native 1× 300 dpi;
- all eight risk ROIs at nearest-neighbor 8×.

Machine generation created no reviewer, decision, note, verdict, PASS/FAIL, or manual boolean field. All manual ledgers in this root were written only after the views above were opened.
