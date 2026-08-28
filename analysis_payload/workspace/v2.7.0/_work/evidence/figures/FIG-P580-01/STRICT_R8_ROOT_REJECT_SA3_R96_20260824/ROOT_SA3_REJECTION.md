# FIG-P580-01 root rejection of R7 SA3

## Verdict

`REJECT_SA3_PASS__FAIL_TO_SA2_NOT_CLOSED`

The R7 SA3 package is sealed and its candidate identity is correct, but its `PASS_TO_ROOT` conclusion is not acceptable under the authoritative strict evidence schema. This rejection does not assert a new visual defect in the business source; it asserts multiple hard evidence failures that prevent the isolated SA3 gate from closing.

## Package identity and terminal integrity

- Candidate PDF SHA-256: `8EED8765A4856C4C197262DEA06E283790FBA8DA906C70C26FC7BD56F6F7E5E8`; source SHA-256: `F0ECC9B28361A2AE73AF085A4958AD09F8F94575D789B8F776C55631FD45E161`.
- Package: `STRICT_R7_SA3_BLIND_R96_20260824`, 1,170 files, including 1,131 PNG and 9 CSV files; zero empty files, zero ADS, and zero files newer than `WRITE_STOPPED`.
- `WRITE_STOPPED` is the last write. These terminal-order facts pass, but they cannot repair the evidence failures below.

## Hard evidence failures

### 1. Visible-glyph denominator is incomplete and one mask is not unique

- The fixed PDF contains 235 non-whitespace PDF glyph records in the defined figure/caption scope. The independent SA1 ledger records 235. R7 SA3 records only 234.
- The omitted record is combining glyph `U+0338` at PDF bbox `[263.38486, 270.76367, 263.38486, 280.92554]`, used with `U+226A` in the displayed composite relation.
- Root opened R7 SA3 `G0090` Original, Target-overlay, Mask-only and 8×-nearest evidence. Although that row is labelled only `U+226A` (`≪`), its selected mask visibly contains both the relation sign and the `U+0338` diagonal overlay. Therefore the required one-to-one `CHAR ↔ contour ↔ bbox ↔ raw mask` mapping is not closed and `MASK ONLY` is not unique to the claimed glyph.
- This directly violates the schema requirement that every visible glyph be represented and that each raw mask contain only that glyph's final visible ink.

### 2. Required per-glyph human ledger was replaced by a bulk PASS write

- `glyph_contact_table.csv` has only `glyph_id`, `element_id`, nearest-object clearance and contact status. It lacks the required per-row reviewer/sheet/cell/original-match/overlay-complete/mask-only-pure/missing-stroke-px/foreign-pixel-px/decision/note fields.
- `06_scripts/sa3_blind_visual_audit.py`, function `record_manual()`, loops over every glyph and assigns the same `PASS_MANUAL` values to `manual_1x` and `manual_8x`; it likewise bulk-closes all manually required pairs.
- The authoritative schema expressly prohibits converting all glyphs to PASS with one global/bulk boolean operation. A narrative statement that all atlases were viewed cannot substitute for the mandatory per-glyph reviewer ledger.

### 3. Foreground-object and pair universes are not reconciled

- Accepted SA1 evidence uses 260 foreground objects (235 glyph objects plus 25 graphic primitives) and exhausts 33,670 unordered pairs: TT 27,495 + TG 5,875 + GG 300.
- R7 SA3 aggregates the same content into 45 objects (30 text parents plus 15 graphic parents) and reports only 990 pairs: TT 435 + TG 450 + GG 105.
- No complete lossless mapping reconciles the omitted glyph-level/composite relations or the ten aggregated graphic primitives. The reduction also changes the named-contact universe from the independently checked source-level primitive contacts. Thus the SA3 pair denominator cannot establish complete unordered-pair coverage.

### 4. Evidence population is not cryptographically enumerated

- `MANIFEST.md` says that 1,168 files existed before the manifest, but it hashes only six selected core artifacts. There is no file-by-file `MANIFEST.sha256` or equivalent JSON enumeration for the 1,168 preterminal files.
- This is an additional integrity shortfall; it is not the sole basis of rejection.

## Routing

Per the authoritative closure rule, an SA3 hard evidence failure returns the figure to SA2, followed by a new SA1 and a new isolated SA3. Root made no business-source edit and did not modify the sealed R7 package. `FIG-P580-01` remains open and the strict total remains `0/99`.
