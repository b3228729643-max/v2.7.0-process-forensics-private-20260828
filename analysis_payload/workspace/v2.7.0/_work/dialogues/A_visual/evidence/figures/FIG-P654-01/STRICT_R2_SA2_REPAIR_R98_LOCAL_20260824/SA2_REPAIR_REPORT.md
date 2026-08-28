# FIG-P654-01 strict local SA2 repair report

## Identity and boundary

- Handoff: `A-R130-P654-SA2-REPAIR-V2-20260824`; reviewer: `Codex gpt-5.6-sol SA2 A-R130-P654-SA2-REPAIR-V2-20260824`.
- Final source normalized SHA-256: `8041DAF98B04D763958DA9C83AF3472FA346D003F0FDCEF13A42FE1AA046B5F8`; base HEAD `e933f09e757d406954edd09f8ce0a326248c7da9`; only the P654 source is unstaged (`21+/23-`). Git commit is explicitly deferred to root after `WRITE_STOPPED`.
- Frozen official R98 reference: 813 pages, 4,934,249 bytes, SHA-256 `52FA2EF0769553C8B6FD4B8D3CBA5BE671FA0F3190591A596FB8B6512C108A41`; target physical page 702 / printed 689; R98 source SHA `01EA85F46A9567D7ED6CF88C92346F9BE317FAFDDCF1F7791C07B2A3ED3858EB`.
- The local SA2 wrapper is not an official full-book candidate; its printed label is 685.

## Final source repair

- Base text is 10.1pt; formula text is 11.6pt; source formula/base ratio `1.148514851485` passes the `<=1.18` gate.
- Posterior/predictive wording was compacted without changing the alpha+n or posterior-predictive semantics.
- Nodes and lower branches were re-spaced; posterior and downstream geometry moved 0.15cm right to remove the genuine families-to-posterior arrowhead/border collision without a false whitelist.
- No public macro, font, chapter, index, build entry, central state, mainline source, Dialogue B, or FINAL_ROOT was changed.

## Complete evidence closure

- 95 visible glyphs + 21 PDF graphic/path objects (including one rawdict-external math rule) = N=116.
- `C(116,2)=6,670` unordered pairs rebuilt in full; unassigned text=0, coverage residual/excess=0, empty masks=0.
- Glyph threshold failures=0; low-profile targets/pending references=0; D failures=0; E failures=0; source ratio and font harmony PASS.
- All 95 glyphs and 21 graphic objects opened at native 1x and nearest 8x; foreign/missing pixels are 0 for every object.
- 17 actual-contact critical pairs opened at native 1x/8x; 19 exact pair-specific contact definitions; illegal final overlap=0; clearance failures=0.
- Final foreground crop margins L/T/R/B `10/10/37/11px`; clip=0. Compiled page/standalone geometry is identical modulo placement translation.

## Crop correction distinction

The candidate page PDF was complete. A prior analysis crop, not the PDF, clipped the left foreground and failed its pad (`0/3/29/4px`). That trial remains read-only under `trials/crop_clipped_r3`. The expanded final crop has `10/10/37/11px` margins and was used to regenerate the entire N=116/C(N,2)=6,670 evidence set.

## Verdict

`LOCAL_SA2_PASS_AWAIT_OFFICIAL_CANDIDATE_AND_FRESH_SA1`. Root must review/commit the sole source diff, build a new official full-book candidate, and commission a fresh isolated SA1. This report does not claim `A_LOCAL_PASS` or a final-book PASS.
## Terminal and seal-stage closure

- Terminal check: PASS (53 checks, 660 referenced PNGs mechanically opened, 0 failures).
- Final seal order: terminal check -> this finalized report and manifest -> `WRITE_STOPPED` absolute last.
- Route remains `LOCAL_SA2_PASS_AWAIT_OFFICIAL_CANDIDATE_AND_FRESH_SA1`; official candidate construction and fresh isolated SA1 remain external work.
