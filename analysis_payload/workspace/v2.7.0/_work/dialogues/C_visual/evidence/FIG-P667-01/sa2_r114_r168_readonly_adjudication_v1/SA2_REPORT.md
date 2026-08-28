# SA2 R114/R168 read-only adjudication report

HANDOFF_ID: `C-FIG-P667-01-R114-SA2-R168-READONLY-ADJUDICATION-V1`

UID: `FIG-P667-01`

Instance: `/root/sa2_fig_p667_r114_r168_readonly_adjudication_v1`

Role: one isolated, read-only SA2 adjudicator

## Frozen input identity

- Official R114 PDF: 4,967,122 bytes; SHA-256 `C3BB9B1C7FC9D7AF9178CD33F227F24899AA505FAB81840DB6E3AD8BD6CE78A6`.
- Current main P667 source: 3,252 bytes; SHA-256 `1E2D755428EC466C6DF44B7684B81A354352653AE60476B4F717AD19F9D6CE15`.
- Both identities exactly match the task-frozen values.

## Startup-absence and isolation

Before any artifact write, the exact evidence root was independently tested as a leaf, a container, and any path; all three results were `False`. The root was then created once. No old P667 evidence, other UID evidence, role result, central acceptance/state/history, Git history, or agent/task enumeration was used.

## Independent figure location

The current source caption supplied the normalized search needle `保留归一化常数还可得到Dirichlet–多项边缘分布`. A scan of all 817 R114 pages found exactly one match: physical page 714, printed page 701, section `34.5 Dirichlet–多项共轭`. The source labels, formulas, caption, and the necessary adjacent V5-C05 prose all occur there.

## Complete denominator and pairs

The reader-visible semantic denominator contains 22 objects: 15 text/formula/caption objects and 7 semantic graphic foreground objects. Pale fills are backgrounds rather than independent semantic foreground; underbrace strokes remain part of their compound formula objects. `M07_object_denominator.csv` records every ID and scope. `M09_all_unordered_pairs.csv` enumerates all `22*21/2 = 231` unordered pairs exactly once.

Ten pairs have bbox intersections. Manual review of the native raster, 8x ROIs, source geometry, and vector inventory classifies all ten as compound-bbox or container-bbox contamination. Three connector contacts are intentional arrow-to-boundary attachments. The closest independent text pair, T13–T14, has 15 empty thresholded-ink pixels. Canonical true illegal overlap is 0 pixels.

## Required visual evidence actually inspected

The full physical page, native 300 dpi figure+caption, native grayscale, object-bbox overlay, dark-ink mask, nonwhite-structure mask, and all six native1x/nearest-neighbor8x ROI pairs were opened before any manual ledger was authored. `A00_post_observation_view_log.md` records the full list and observations.

## Codepoint and clipping findings

- Figure+caption codepoint occurrences: 223; unique codepoints: 87.
- U+FFFD occurrences: 0; U+0000 occurrences: 0.
- Correct exact query `Dir(𝛼+𝑛)` occurs twice on the target page. The earlier style-mismatched query in the raw machine summary has count 0 only because it asked for different Mathematical Alphanumeric Symbols codepoints; it is not a PDF glyph failure.
- The hollow square at the far right of the preceding proof is the QED end mark and is outside the figure.
- Foreground pixels on the figure-crop edge: 0.
- Objects crossing the crop boundary: 0.
- Minimum object-to-crop margin: 24.417 px.
- True clipped semantic foreground pixels: 0.

## Mathematics, semantics, arrows, and context

Independent recomputation gives the posterior kernel `product theta_i^(alpha_i+n_i-1)`, posterior `Dir(alpha+n)`, and marginal count probability `N!/(product n_i!) * B(alpha+n)/B(alpha)`. The figure shows exactly these relations. The multiplication sign, two-row brace, rightward posterior arrow, and dashed normalization-constant branch preserve the correct derivation. Caption and adjacent prose agree that componentwise addition occurs in parameters/exponents rather than between probability vectors.

## R168 decision

The 8.5, 8.8, and 9.4 pt source values are advisory-only under R168. Native 300 dpi and page-scale inspection shows that they are actually readable, not clipped, not tofu, not semantically wrong, and not visibly imbalanced. Therefore the old 9.5 pt threshold cannot cause a hard failure or source return here.

No R168 hard trigger exists: no actual missing/tofu/wrong codepoint or meaning, no actual unreadability, no visibly severe imbalance, no true clipping, no illegal visible-ink overlap, and no semantic/geometric error.

## Scope integrity

No source file, PDF, build, Git state, central state, inventory, or other UID was changed. No TeX-family build or process-management action occurred.

## Final verdict

`SA2_NO_SOURCE_CHANGE_READY_FOR_FRESH_SA1`
