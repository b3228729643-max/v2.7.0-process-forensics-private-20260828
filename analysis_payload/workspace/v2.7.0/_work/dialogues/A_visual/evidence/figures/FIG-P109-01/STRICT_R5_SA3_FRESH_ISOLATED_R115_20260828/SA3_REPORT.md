# FIG-P109-01 fresh-isolated SA3 report

REPORT_ID=`A-R115-P109-SA3-FRESH-ISOLATED-REPORT-20260828`  
HANDOFF_ID=`A-R115-P109-SA3-FRESH-ISOLATED-20260828`  
CANONICAL_TASK=`/root/p109_r115_fresh_sa3`  
ACTUAL_MODEL_EFFORT=`gpt-5.6-sol/xhigh`  
FORK_TURNS=`none`

## Scope and identity

This is the single fresh isolated SA3 review for canonical UID `FIG-P109-01`. It used only the official R115 PDF, current figure source, exact current chapter, `GOAL.md`, and the directly referenced goal protocols. It did not read or reuse prior P109 pages, crops, metrics, ledgers, verdicts, evidence roots, reports, handoffs, task history, Git history, or Main state/acceptance.

The fixed evidence root was checked with `LiteralPath` before creation and returned `Leaf=false`, `Container=false`, `Any=false`, `Parent=true`. The same instance then created that fixed root exactly once and continued without restart, replacement, duplicate role, or second UID.

## Input identity and target location

All three exact task inputs matched the assigned byte lengths and SHA-256 values. A direct inspection showed that physical page 109 of R115 is a Chapter 6 exercise page. An exact caption search within only the official R115 PDF uniquely located the current target on physical page `116` (printed page `103`). The chapter includes the current figure source at `V1-C07.tex:253`.

## Frozen denominator and observations

The complete reader-visible denominator contains six objects: endpoint labels `x` and `y`, construction formula `z=lambda x+(1-lambda)y`, region label `凸可行域 C`, definition implication, and the full Figure 7.1 caption. All `15` unordered pairs were frozen before manual review.

The reviewer then actually opened the full page, page-integration crop, native-1x figure, nearest-8x figure, raw 300 dpi figure, grayscale figure, denominator overlay, and all eight critical ROIs in both raw 300 dpi and nearest-8x forms. Only afterward were the per-ID element, pair, text, math, geometry, page, and R168 ledgers authored.

## R168 hard-gate findings

Legacy numerical font, pixel-height, ratio, and clearance thresholds were treated as advisory only. The source's declared `9.2 pt` labels therefore did not independently cause failure. Direct observation found:

- no missing glyph, tofu, or wrong codepoint;
- no unreadable or obviously imbalanced reader-visible object;
- no true clip of text, geometry, markers, note border, caption, or page content;
- no illegal visible-ink overlap among any frozen text pair or between text and geometry;
- no mathematical, semantic, or geometry error;
- no grayscale or page-integration failure.

The convex region contains both endpoints, the entire joining segment, and all three interpolation markers. The formula, implication, caption, and adjacent universal-quantifier explanation agree.

## Controls and conclusion

The preseal control found `N=6`, `C=15`, complete element/text/pair coverage, `23` required render controls present and nonempty, and `0` control errors.

RESULT=`PASS`

This PASS is the one fresh-isolated SA3 conclusion for the fixed R115 root. It awaits Main's `A_LOCAL` acceptance and is not self-counted as A_LOCAL, global, or final completion. No source, TeX, PDF, Git, central state, external process, or second-role mutation was performed.
