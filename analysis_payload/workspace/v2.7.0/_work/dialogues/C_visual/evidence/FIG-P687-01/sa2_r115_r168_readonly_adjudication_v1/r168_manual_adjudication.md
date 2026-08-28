# FIG-P687-01 — fresh R115 SA2 / R168 read-only adjudication

HANDOFF_ID: `C-FIG-P687-01-R115-SA2-R168-READONLY-ADJUDICATION-V1`

## Identity and isolation

- The exact zero-existence gate passed before creation: both the UID parent and fixed root were absent as Leaf, Container and Any; the parent of the UID parent existed.
- The UID parent and fixed root were then created exactly once. No alternate root or restart was used.
- The three external inputs matched the required byte counts and SHA-256 identities before inspection:
  - `main_full.pdf`: 4,967,161 bytes; `93ADF6E1FBF9EED2A392FA150C81738DD60FC50F50C00EBDF99C0F4168D4726F`.
  - `fig_v5_c06_collapsed_gibbs_counts.tex`: 3,401 bytes; `FEB76B03845B3EA01ECD53768AA99AAF618519268667AA065A29848207AB398A`.
  - `V5-C06.tex`: 120,809 bytes; `7276DDB767246292D0924D1651D560975E0FE6D2ACE47CBAEC4EE45CEB4A0029`.
- No TeX, chapter, build, Git, central state, process, or second UID was written or managed.

## Independent current-figure localization

The UID token `P687` was not treated as proof of the current page. Literal physical page 687 in R115 is printed page 674 and contains Fig. 33.4, not this source. Starting only from the current source caption and its direct chapter inclusion, the unique current caption was found at R115 physical page 737, printed page 724, as Fig. 35.4. All substantive current-figure judgments therefore use physical page 737. The p.687 renders are retained only as explicit identity-disambiguation evidence.

## Views actually opened

The manual view ledger records 26 actually opened artifacts. It includes the current target full page at 200 dpi, 300 dpi and 300 dpi grayscale; native 300 dpi figure+caption color and grayscale; object, semantic and text overlays; the visible-ink candidate mask; and all six selected critical ROIs at both native1x and nearest8x. The original 300 dpi files were never resized before measurement/cropping; nearest8x views use nearest-neighbor enlargement solely for pixel-edge observation.

## Frozen denominator and exact all-pairs closure

The complete reader-visible semantic-object denominator is frozen at `N=19`:

- 5 step badges: R01, R03, R05, R07, R09;
- 5 cards with their internal reader-visible text/formulas: R02, R04, R06, R08, R10;
- 6 directed connectors including the outer loop: R11-R16;
- loop annotation R17;
- leave-one-out note R18;
- caption R19.

Thus `C(19,2)=171`. The machine file contains IDs only. The separately authored manual pair file contains genuine post-observation judgments for all 171 unordered pairs. Mechanical and manual `(PAIR_ID,A_ID,B_ID)` sequences match exactly; there are 171 unique pair keys and no blank manual fields. Results are 159 `CLEAR` pairs and 12 `ALLOWED_TOPOLOGY_CONTACT` pairs. The 12 allowed contacts are only arrow endpoints meeting their source or destination card border; none is an illegal visible-ink overlap.

## R168 manual findings

### Glyphs and codepoints

No missing glyph, tofu, substituted semantic character, or wrong mathematical codepoint was observed. The p.737 text extraction preserves the visible Chinese, badges 1-5, `Gibbs`, `n`, `m`, `k`, `v`, `i`, alpha, beta, the centered dot, proportional sign, conditioning bar, superscripts/subscripts and U+2212 mathematical minus. All fonts used on p.737 are embedded, subsetted and Unicode-mapped. Native1x and nearest8x ROIs show intact strokes, fraction bars and arrowheads.

### Readability and balance under R168

The source declares 9.2 pt for the main figure/card text, 9.0 pt for badges and bottom note, and 8.8 pt for the loop annotation, with no enclosing resize/scalebox in the direct chapter inclusion. These legacy numerical values are advisory under R168 and are not used alone as failures. In the actually opened full-page 200/300 dpi, native figure, grayscale and native1x/nearest8x ROI views, all reader-visible text and mathematics are plainly readable. The smaller gray loop annotation and bottom note remain legible and subordinate rather than actually unreadable. The two evidence cards are balanced, the central formula remains the visual focus, and no severe role or panel imbalance is present.

### Illegal overlap and clipping

Every one of the 171 unordered pairs was checked after opening the native/overlay/ROI evidence. No text-text, text-formula, text-line/arrow, formula-line/arrow, badge-text, annotation-loop, note-caption, or unrelated connector pair has confirmed shared illegal visible ink. The 12 arrow/card endpoint contacts are required graph topology and do not obscure text or create ambiguity. No card, glyph, formula, fraction bar, arrow shaft/head, note or caption is clipped. Therefore confirmed illegal visible-ink overlap pairs = 0; true clipping objects/pairs = 0; unresolved pairs = 0.

### Collapsed Gibbs semantics and formulas

The diagram implements the correct leave-one-out update:

1. remove the current token's old assignment from both count tables;
2. read the document-topic factor `(n_mk^{-i}+alpha_k)/(n_mdot^{-i}+alpha_0)`;
3. read the topic-word factor `(n_kv^{-i}+beta_v)/(n_kdot^{-i}+beta_0)`;
4. multiply the two positive factors and normalize over `k`;
5. sample the new `k*` and restore the token to both tables.

The chapter proposition and equation present the topic-word factor before the document-topic factor, while the figure presents the document-topic factor first. This is mathematically identical by commutativity and matches the adjacent prose's pedagogical reading order. The `-i` superscript is correctly retained through the sampling step, preventing self-counting.

### Arrows and relations

R11-R12 split from removal to the two count tables; R13-R14 merge both evidence branches into the conditional card; R15 proceeds from the normalized conditional to sampling/restoration; R16 returns from the sample card to removal for the next token. All arrowheads face the required direction. The loop annotation sits inside a broad corridor and does not touch the loop shaft.

### Caption and chapter consistency

The caption, the immediately preceding chapter sentence, proposition 35.2, equation 35.6 and the figure agree on removal, the two factor roles, multiplication/normalization, new-topic sampling, restoration and prevention of self-counting. No variable, index, direction, or count-table role conflicts.

### Grayscale and page integration

The workflow remains unambiguous in grayscale because its hierarchy is carried by geometry, card grouping, badge numbering and arrow direction rather than color alone. The figure and two-line caption fit fully on printed page 724 with the derivation above and posterior-mean formulas below; there is no crop, collision, orphaned caption, abnormal whitespace, or severe page imbalance.

## Hard-defect decision

R168 hard failures are limited to missing/tofu/wrong codepoint or mathematics, actual unreadability/severe imbalance, true clipping, confirmed illegal visible-ink overlap, or semantic/geometric/mathematical error. None is present.

`VERDICT=SA2_NO_SOURCE_CHANGE_READY_FOR_FRESH_SA1`

No source change, build, or repair is authorized or required by this adjudication.

