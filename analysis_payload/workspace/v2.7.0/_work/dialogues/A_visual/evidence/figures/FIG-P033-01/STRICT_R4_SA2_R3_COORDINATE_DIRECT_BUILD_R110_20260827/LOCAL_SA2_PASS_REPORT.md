# FIG-P033-01 R4 local SA2 report

## Verdict

`LOCAL_SA2_PASS_AWAIT_OFFICIAL_CANDIDATE_AND_FRESH_SA1`

This verdict is local to the single new standalone candidate. It is not `A_LOCAL_PASS`, does not authorize a commit, and does not start a fresh SA1 or SA3.

## Build identity

- HANDOFF_ID: `A-R110-P033-SA2-DIRECT-BUILD-R4-20260827`
- one PowerShell7 controller / one direct LuaLaTeX child PID 26468
- start `2026-08-26T20:43:29.7110206Z`; end `2026-08-26T20:45:31.6294124Z`; 121.918 s
- exit 0, natural exit, interrupted false, invocation 1, retry 0, latexmk 0
- PDF: 31,553 bytes; SHA-256 `CECFB8085EE0DB6327607879DE4600A45F4F8B312D4E1B2A9BAE9B675156153A`
- source before/after: 2,383 bytes; SHA-256 `D3C1D38ECB8468EC3294F7D18BD886316829F14690A516000189CE853A07BC05`
- wrapper before/after: 394 bytes; SHA-256 `6D5CAFA79EC5F2939FEE2A73A7360F1E5C3D88C522F2C6044905D4160B3C90F6`
- TeX-family processes after natural exit: 0

## Machine denominator and all pairs

The new PDF was independently parsed and rendered at native 300 dpi. The frozen denominator is 52 objects: 38 visible non-space glyphs and 14 drawing objects. The all-unordered-pair table has exactly 1,326 unique rows, equal to C(52,2). Clip failures, empty bboxes, U+FFFD/tofu, missing objects and pair-count mismatches are all zero.

The 123 bbox candidates are deliberately overinclusive: they include legitimate background ownership, formula-card containment, label masks, plane fill/borders, and shaft/head endpoint relations. They are preserved as machine candidates, not auto-written manual verdicts. Six final views and 16 semantic critical relation groups were actually opened and adjudicated after machine completion.

## Former R2886 regression

The old collision maps independently in the new standalone denominator to `G0001` (子) versus `D0003` (lower plane boundary). The PDF bboxes are disjoint by a conservative 9 px at 300 dpi. Direct row scanning of the unannotated native render over the glyph's x range detects the lower boundary at rows 902–915 and the glyph ink at rows 937–972, leaving 21 empty native rows and zero shared ink. The target 1x and nearest-neighbor 8x views visibly confirm the white separation.

The same scan detects the upper boundary at rows 840–853, leaving 83 empty rows to the glyph. Thus the moved label clears both plane boundaries. For official-page integration, the independently measured R110 label-to-caption gap was 85 empty rows before the 27.401575 px move; the conservative projected remaining gap is 57.598425 px. This must be confirmed on the next official full-book candidate but is not a current local blocker.

## Manual and semantic closure

- glyph ledger: 38/38 PASS, each row written after the contact sheet was opened
- drawing ledger: 14/14 PASS, with distinct semantic roles
- critical relation groups: 16/16 PASS
- opened views: full A4, native color crop, grayscale crop, glyph sheet, drawing sheet, target native1x/8x
- non-PASS manual rows 0; blank notes 0; script-generated manual fields 0
- projection semantics preserved: O→X, O→P, P→X; right-angle certificate, shortest-distance brace, Pythagorean norm identity, memberships and orthogonal-complement notation all remain correct
- R168 true hard defects (missing/tofu/wrong codepoint or math semantics, unreadable imbalance, real clipping, illegal overlap) 0

## Scope

The worktree still contains exactly the previously authorized P033 one-file 1+/1- source diff and an empty index. No commit, additional source edit, TeX retry, second PDF, second root, second UID, fresh role, or central-state write occurred.
