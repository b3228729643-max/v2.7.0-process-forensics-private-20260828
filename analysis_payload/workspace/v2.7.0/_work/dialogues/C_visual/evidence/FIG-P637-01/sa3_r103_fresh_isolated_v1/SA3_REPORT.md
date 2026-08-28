# FIG-P637-01 / R103 fresh isolated SA3 report

## Decision

`C_LOCAL_PASS_ONLY`

This is a local independent SA3 result only. It is not a global PASS, does not update any central inventory or state, and awaits mainline acceptance. No source writer or TeX execution is requested. Hard-failure IDs: none.

## Identity and isolation

- HANDOFF_ID: `C-FIG-P637-01-R103-SA3-FRESH-ISOLATED-V1`
- Role: `SA3_FRESH_ISOLATED`
- Evidence root: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P637-01\sa3_r103_fresh_isolated_v1`
- Evidence root was absent before dispatch and was created only for this audit.
- TeX: `DISABLED`; business-source writer: `NONE`; source/PDF/main: read-only.
- No subagent or second SA3 was used.
- No prior P637 evidence, conclusion, page mapping, denominator, failure ID, handoff, state, inventory, route log, chat/history, mainline report, other UID evidence, or agent output was read or inherited.
- The optional adjacent chapter source was not needed. The official PDF itself supplied the contextual consistency evidence.

## Independent candidate identity and page mapping

The official R103 PDF was verified directly before review:

- path: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r103_fullbook\main_full.pdf`
- bytes: 4,967,184
- pages: 817
- page size: A4 595.276 x 841.890 pt
- SHA256: `9379A489E0C2A57A7DA670C98029BB27B3F1A385BF8E4C3BD14FE9B606AA0F23`
- independent unique match: physical PDF page 687; printed page 674; figure 33.4

The figure was located from the PDF text and page image itself. The caption and immediately adjacent PDF prose both say that x1 updates move horizontally, x2 updates move vertically, and coordinate-wise short-axis motion causes slow progress along the tilted long axis.

## Render paths actually reviewed

All review images derive from physical PDF page 687; none derives from a TeX build.

1. V01 full page at native 200 dpi, direct `pdftoppm`, no resize.
2. V02 full page at native 300 dpi, 2481 x 3508, direct `pdftoppm`, no resize.
3. V03 figure plus caption at 300 dpi, integer crop of V02, no resize.
4. V04 standalone figure body at 300 dpi, integer crop of V02, no resize.
5. V05 grayscale 300 dpi view, color conversion only, no resize.
6. V06 native-grid object/text measurement overlay.

All six were opened and visually reviewed. Full-page placement is clean; the figure, caption, note, axes, contours, arrows, markers, and terminal strokes are complete. Grayscale preserves the path and axis semantics.

## Exact inventories and denominators

- visible glyph objects: 131
- semantic text parents: 16; containers only and excluded from the foreground pair denominator
- foreground graphic objects: 21
- explicitly excluded background fill objects: 2
- foreground object denominator: n = 131 + 21 = 152
- complete unordered pairs: C(152,2) = 11,476
- enumerated unique pair rows: 11,476
- critical candidate pairs: 42
- text-text critical pairs: 0
- text-graphic critical pairs: 0
- graphic-graphic critical pairs: 42
- per-object clip rows: 152
- crop-edge touch candidates: 0
- empty glyph masks: 0
- empty foreground graphic masks: 0
- visible whitespace exclusions: 3
- PDF drawing indices mapped: every index 1 through 31; unmapped: none
- glyph 8x cards: 131
- glyph contact sheets: 33
- graphic 1x cards: 23 including two excluded fills
- critical-pair 8x cards: 42
- critical-pair contact sheets: 11

Every foreground object participates in the full C(n,2) table. Every critical pair has raw crop, mask A, mask B, exact intersection, overlay, and nearest-neighbor 8x card. All visible drawing elements are either mapped to a foreground graphic object or explicitly excluded as a uniform background fill. Explicitly absent classes are math rules, loops, legends, and panel borders; the rounded note border is positively mapped rather than omitted.

## Manual review closure

Machine scripts produced only identity/inventory/mask/pair/render material. They did not generate, fill, or overwrite any manual reviewer, boolean, decision, or note field.

- glyph review: 131 individually authored rows; each original/overlay/mask-only card reviewed; all masks complete and pure; zero missing-stroke and zero foreign-pixel findings
- critical-pair review: 42 individually authored rows; all raw intersections are legal structural intersections; true collision count 0; illegal-overlap pixel count 0
- object clip review: 152 individually authored rows; every exact ID reviewed; no crop-edge touch
- graphic review: 23 individually authored rows; 21 foreground PASS and two background-fill exclusions
- render-path review: 6 individually authored rows
- text-parent review: 16 individually authored rows
- peer/role review: 12 individually authored rows
- semantic/content review: 24 individually authored rows
- hard-gate review: 12 individually authored rows

Cross-checking found no missing, extra, duplicate, or field-mismatched glyph, critical-pair, clip, graphic, render-view, or text-parent IDs. All referenced glyph cards, graphic cards, render views, and 42 critical-pair cards exist.

## Hard-gate findings

### Geometry, relationship, and content

The target is a tilted narrow ellipse family. x1 is horizontal and x2 vertical. States 0 through 6 are present exactly once. The six directed moves alternate horizontal and vertical in the sequence 0→1→2→3→4→5→6. The long-axis and short-axis arrows have the correct major/minor directions and cross approximately perpendicularly. Color labels agree with the corresponding update direction, and the reading remains valid in grayscale.

### Mathematical semantics

Every x variable is the intended mathematical italic x codepoint, with the correct 1 or 2 subscript. The figure, note, caption, and adjacent official-PDF prose make the same coordinate-wise Gibbs and slow-mixing claim. No wrong glyph, wrong codepoint, or contradictory mathematical relation was found.

### Font and typography under R168

No tofu, missing glyph, actual unreadability, or visibly severe font imbalance was found. All 131 glyph cards and all 16 parent roles are legible. The 8.8 pt state labels, 9.2 pt figure labels, approximately 9.96 pt caption spans, small peer ratios, script morphology differences, punctuation height, and 1–2 px raster effects are advisory under R168 and do not independently create a hard failure. Their actual full-page and crop appearance is balanced.

### Crop and overlap

All 152 foreground objects have nonempty masks and positive crop clearance; the minimum is 8 px for the complete note border. No text-text or text-graphic hard candidate exists. The 42 graphic intersections are intentional coordinate-axis crossings, contour overlays, arrow-marker endpoint joints, trajectory/reference-axis crossings, or the perpendicular principal-axis joint. Each is individually judged legal; none hides text or breaks an arrow, contour, marker, or semantic relation.

## Failure accounting and handoff

- hard-failure count: 0
- all hard-failure IDs: `[]`
- advisory hard-failure promotions: 0
- disposition: `C_LOCAL_PASS_ONLY`
- next authority: mainline acceptance only
- central inventory/state mutation: none
- source-writer request: none
- TeX request: none

Seal identity and recordset hashes are written in the final `WRITE_STOPPED` marker. The manifest intentionally excludes itself and the marker, and it records each included file's resolved path, bytes, SHA256, exact UTC mtime, and Windows FILETIME in 100 ns units.

