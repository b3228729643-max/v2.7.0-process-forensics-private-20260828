# P654 R17 main-line root audit

Decision: `ROOT_REJECT_R17_MANUAL_LEDGER_BULK_GENERATION__MACHINE_FAIL_ROUTE_ACCEPTED_TO_SA2_R3_STATIC`.

P654 remains `SA2`. This decision does not authorize a commit, TeX, fresh SA1/SA3, LOCAL PASS, or A_LOCAL_PASS.

## Independently accepted machine failure direction

- Handoff SHA-256 matches `4AD67A290338CB71BE5821C7E860176A252A7CAE1C74E34633A73092B22420CF`.
- Manifest CSV/JSON hashes match `93E0A4165E6608E75DAA6230E949FE722C52F50C23053C071B5278FAABA288F3` and `4FC7E4754C4F50C6C9286720DEC77C9B2F8460D11EE2B7F848D8646155CCD021`.
- Machine denominators are 93 glyphs, 21 graphics, 114 objects, 6,441 unordered pairs and 173 critical pairs.
- Target G0005 `n` is H=24px, frozen median=24px, ratio=1.0, PASS.
- G0040/G0059/G0064 are mathematical plus signs with H=26px / median=24px = 1.083333, above 1.08.
- G0065 literal `N` is H=27px / median=24px = 1.125, above 1.08.
- P06198/P06219 have 0 overlap but 0px native clearance to D0009, below the 3px gate.
- Source audit records 11.6pt, 10.0pt and 9.5pt in the same frozen formula role; max/min=1.221053 and span=2.1pt, failing 1.03 and 0.25pt.

These numeric facts are sufficient to keep P654 in SA2 and route a new static source correction. They are not a PASS claim.

## Decisive root rejection

The sealed package violates the existing prohibition on bulk/template/default/global manual adjudication:

- `build_r17_machine_evidence.py` loops over every glyph and writes `MANUAL_GLYPH_LEDGER.csv`, setting reviewer, original-match, overlay-complete, missing-stroke and decision fields from machine data and a generated note.
- The same script loops over every graphic and writes `MANUAL_GRAPHIC_LEDGER.csv` with generated reviewer/boolean/decision/note fields.
- The same script loops over all 6,441 pairs and writes `MANUAL_PAIR_LEDGER.csv` with generated decision and templated notes.
- `finalize_r17_manual_adjudication.py` again loops over all raw pairs and rewrites the full manual pair ledger and 173-row critical manual ledger from machine decisions, with only a small hard-coded exception map.

The presence of contact sheets or a statement that they were opened does not convert machine-generated per-ID human fields into genuine per-ID manual records. This is the same class of defect that caused earlier P608/P654 root rejections. Therefore the R17 sealed root and its local independent root verdict cannot be accepted as a protocol-compliant manual closure.

## Route

R17 remains immutable as historical machine FAIL evidence. No evidence-only reseal is required for this already-failing source state. A may prepare one new static-only source R3 proposal in the same P654 source file, covering all four glyph failures, both clearance failures and the source-role size gate while preserving literal `N`, genuine mathematical plus signs, target `n`, semantics, frozen taxonomy and thresholds. The next evidence round must keep machine generation separate from genuine per-ID manual adjudication; scripts may not generate or overwrite manual reviewer/boolean/decision/note fields.
