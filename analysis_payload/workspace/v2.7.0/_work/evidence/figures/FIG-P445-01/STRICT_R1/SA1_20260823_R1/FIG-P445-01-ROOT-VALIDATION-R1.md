# FIG-P445-01 root validation — STRICT R1

ROOT_RESULT: CONFIRM_SA1_FAIL

- Frozen official input: `strict_current_r93_fullbook/main_full.pdf`, physical page 485, printed page 472, 图 25.1.
- Root inspected the formal report, source/font and pixel tables, all failed relationship rows, the native 300 dpi figure/measurement views, and the five critical-pair images.
- Source floor failure is independently confirmed: 28/69 audit rows trace to explicit 9.4 pt axis/leaf bases, 8.6 pt ticks, 9.2 pt cut annotation, or natural scripts whose parent formula itself is below 9.5 pt. This alone rejects the candidate.
- The unambiguous source-owned pixel failures include all three nonzero ticks at 23 px versus the 24 px digit gate, the cut-annotation `=` at 13 px versus the 22 px base-operator gate, and its decimal point at 6 px versus the punctuation gate. The SA1 table reports eight total pixel failures including caption glyphs; the root disposition does not depend on the more shape-sensitive caption rows.
- Two illegal overlaps are visually and mask-confirmed, not intentional dendrogram junctions: vertical axis title `合并高度` overlaps tick `3` by 42 px, and the central dendrogram branch runs through `C_2` by 48 px. Their independent-mask union is 90 px. Root opened both 1:1 critical images and the full native crop.
- Three additional hard-clearance failures are confirmed: `C_1`, `C_2`, and `C_3` are only 2, 2, and 1 px from their colored cluster-band borders, below the 5 px node-text/border requirement. Clip count is 0.
- Role hierarchy also fails because undersized ticks become the local base: axis-title 1.56522 (>1.18), cluster-label 1.21739 (>1.10), cut-annotation 1.52174 (>1.10), and leaf-label 0.86957 (<0.95). Mathematical semantics, caption/body consistency, grayscale and page integration pass but cannot override hard failures.

Disposition: reject current candidate; next role is SA2 only. SA3 is prohibited until a rebuilt official candidate obtains a fresh strict SA1 PASS.
