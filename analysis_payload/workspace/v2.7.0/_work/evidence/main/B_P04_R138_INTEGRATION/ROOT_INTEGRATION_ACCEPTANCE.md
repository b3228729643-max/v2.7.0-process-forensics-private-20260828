# B-EXM-P04 — mainline integration acceptance

- Timestamp: `2026-08-25T02:32:55+08:00`
- Mainline decision: `ACCEPT_B_LOCAL_PASS`
- Sealed handoff: `B-EXM-P04`
- B commit: `933fe1d00d9e0661d6a2dce6cc8e3d87b0ab649e`
- B parent: `475531944934b2c06e9183058829d5e42252a50f`
- Mainline integration commit: `05a5f6e21ac025fccb03f256731c6060d0a19043`

## Source and scope audit

- The atomic commit changes exactly seven authorized chapter files, with 85 insertions and 77 deletions.
- The ten objects are examples 13.1, 13.2, 14.1, 15.1, 16.1, 20.1, 20.2, 21.1, 21.2 and 22.1.
- Before cherry-pick, the current mainline versions of all seven files were byte-identical to the B commit parent versions; the integration was conflict-safe.
- No drawing source, shared macro/style, test, index, build entry or central state file is changed by the commit.
- `git diff --check` passes. After integration, the mainline content/layout suite runs 10 tests and reports `OK` with exit 0.
- The ten solution blocks contain the required seven stages in exact order, 70/70 in total. Labels and references are unchanged.

## Mathematical and terminology audit

- SA1 and isolated blind SA3 independently recomputed all ten examples and both report PASS with findings `NONE`.
- Mainline inspected the complete source diff. The numerical results, boundary checks, normalizations, path enumerations and unique-answer statements are internally consistent.
- Example 20.2 now defines the responsibility unambiguously as `P(Z=B\mid Y)`, while explicitly relating it to the first toss of coin A; the earlier “选择 A 的后验” ambiguity is removed.
- Example 22.1 retains the eight paths and scores in corresponding order, with unique optimum `(A,B,A)` and score 1.3.

## Build and visual audit

- Final build identity: `B-EXM-P04-R3-RESUME`; wrapper and child/latexmk exit 0/PASS.
- Mainline independently inspected the final PDF and log: 814 A4 pages, rotation 0, PDF 1.7, unencrypted, 4,947,493 bytes; the normal output line reports the same 814 pages and byte size.
- Searches find zero hard TeX, missing/I/O, memory-exhausted, overfull or underfull matches. Three pre-existing volume-5 PGF Lua fallback notices are non-fatal and outside P04 scope.
- The final visual denominator is 18/18 pages: 223, 227--228, 247--248, 262--263, 291--292, 382, 389--390, 406--407, 416--417 and 437--438.
- Mainline independently opened final pages 437 and 438. The R3 `\newline` produces natural spacing, preserves the eight-path/eight-score correspondence, and yields a complete continuation and method-transfer block without clipping or overlap.
- Isolated SA3 was read-only, did not read prior SA1/mechanical/state/handoff conclusions, and returned `FINAL_DECISION=PASS`, findings `NONE`.
- Terminal `latexmk/lualatex/luatex/luahbtex` process set is empty; R4 was not started and remains prohibited.

## Route

Accept and integrate B-P04 as `B_LOCAL_PASS`. This closes ten more example-solution objects locally but does not by itself declare the whole-book Goal complete. B must keep P05 source and TeX frozen until mainline freezes the joint R101 candidate and explicitly releases the next writer/build slot.
