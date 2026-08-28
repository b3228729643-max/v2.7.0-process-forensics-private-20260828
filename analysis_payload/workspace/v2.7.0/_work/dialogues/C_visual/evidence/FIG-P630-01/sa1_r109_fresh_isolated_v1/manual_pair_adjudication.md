# FIG-P630-01 R109 isolated SA1 manual pair adjudication

The complete unordered-pair denominator is `C(36,2)=630`; every identity is present once in `unordered_object_pairs.csv` and the machine summary independently reports expected and actual counts as 630.

## Pair coverage and candidates

- 598 pairs have zero machine bbox intersection. This includes every text-text pair and every text-flow/leader pair. The actual-ink table independently covers all `C(20,2)=190` text pairs: all have zero ink-bbox intersection.
- 18 bbox candidates are text nested inside its own node rectangle: P0016, P0051, P0052, P0086, P0087, P0120, P0121, P0153, P0184, P0185, P0215, P0216, P0217, P0218, P0247, P0248, P0249, P0277. The rectangle bbox includes its interior by construction, but the semantic foreground is the border stroke. Source-coordinate border clearance is positive for every one; the minimum is T14--B07 at 8.96 px, above the 5 px requirement. These are not foreground collisions and are not mask contamination.
- 14 bbox candidates are designed graph junctions where an edge/leader terminates on a node border: P0009, P0014, P0043, P0044, P0077, P0078, P0110, P0111, P0114, P0142, P0143, P0173, P0203, P0232. They are intentional structural contacts between graphics, not illegal text/semantic overlaps. Native and nearest8x views show intact arrowheads/leader endpoints with no clipping.
- No mandatory text/line, text/arrowhead, text/marker, text/node-border, text/panel-border, caption/data, or text/text foreground candidate remains. There are no data curves, markers, legends, or panel borders in this concept graph.

## Clearance and clipping adjudication

- Minimum actual text-text ink clearance: 4 px, pair T02--T03; zero shared ink pixels. This meets the 4 px rule. The font-bbox gap is conservatively smaller because both lines contain lowered TeX scripts; native and nearest8x evidence confirms actual ink separation.
- Minimum conservative text-to-flow bbox gap: 6 px, pair F01--T01; this exceeds the 3 px text/line requirement, and visible ink clearance is larger.
- Minimum text-to-node-border clearance: 8.96 px, pair T14--B07; this exceeds the 5 px requirement.
- Text to figure/image crop edges and caption to page edges exceed 6 px. There is one panel, so the adjacent-panel 8 px rule is not applicable.
- Every visible object and every arrowhead is fully present in the native crop and full page. Confirmed clipped foreground pixels: 0.

Canonical adjudication totals:

- `OVERLAP_CANDIDATE_PIXEL_COUNT = 0`
- `MASK_CONTAMINATION_PIXEL_COUNT = 0`
- `OVERLAP_PIXEL_COUNT = 0`
- `PIXEL_ADJUDICATION_STATUS = CLEAR`
- `CLIP_PIXEL_COUNT = 0`
- `MIN_TEXT_CLEARANCE_PX = 4`

No unresolved cluster exists.
