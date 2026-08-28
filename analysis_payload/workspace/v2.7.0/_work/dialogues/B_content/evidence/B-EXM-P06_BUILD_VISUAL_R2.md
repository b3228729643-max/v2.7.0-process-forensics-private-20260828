# B-EXM-P06 R2 build and visual evidence

Status: `ROOT_MECHANICAL_VISUAL_PASS`

## Build identity

- One authorized `run_background_build.ps1 -Resume` invocation; no concurrent invocation, retry, R3, or P07 work.
- Output: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_B_content\build\dialogue_B_content\B-EXM-P06-R2-RESUME`
- Control: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_B_content\build\dialogue_B_content\B-EXM-P06-R2-CONTROL`
- Started `2026-08-25T06:46:02.6061299+08:00`; finished `2026-08-25T07:00:30.1009761+08:00`.
- Wrapper/child exit: `0` / `0`.
- latexmk parent PID `14828`; natural LuaLaTeX children `7328`, `13180`.
- PDF: 816 pages, 4,953,900 bytes; log: 249,751 bytes.
- Log terminal identity: `Output written on main_full.pdf (816 pages, 4953900 bytes).`
- Terminal `latexmk/lualatex/luatex/luahbtex = NONE`; build lock released and independently confirmed by main.

## Mechanical final

- All 816 pages are A4 `595.276 x 841.89 pt`, rotation 0; PDF 1.7, unencrypted, suspects no.
- Hard errors, LaTeX/package errors, fatal/emergency stops, missing I/O, memory exhaustion, undefined controls/references/citations, missing characters, duplicate labels/destinations: all `0`.
- Overfull/underfull: `0` / `0`.
- Main index: 731 accepted, 0 rejected, 0 warnings.
- Symbols index: 355 accepted, 0 rejected, 0 warnings.
- Mechanical decision: `PASS`.

## Fresh AUX anchors

| Example | Print page | Physical page | Solution coverage |
|---|---:|---:|---|
| 25.1 | 479 | 492 | 492-493 |
| 26.2 | 499 | 512 | 512-513 |
| 27.1 | 521 | 534 | 534-535 |
| 28.1 | 544 | 557 | 557-558 |
| 30.1 | 591 | 604 | 604-605 |
| 30.2 | 596 | 609 | 609-610 |
| 31.1 | 620 | 633 | 633 |
| 31.2 | 627 | 640 | 640-641 |
| 32.1 | 649 | 662 | 662-663 |
| 32.2 | 654 | 667 | 667-668 |

## Visual final

- Poppler 150 dpi output: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\B_content\evidence\B-EXM-P06-R2_VISUAL`.
- Reviewed 38 pages across ranges `491-494`, `511-514`, `533-536`, `556-559`, `603-606`, `608-611`, `632-634`, `639-641`, `661-664`, `666-669`.
- Priority pages 556-559: page 556 ends with ordinary preceding content; page 557 contains the section title and the opening of example 28.1 together; page 558 completes the answer and reaches the chapter exercise banner; page 559 begins exercises naturally. The R1 orphaned section title is closed.
- The other nine target/adjacent ranges show no regression.
- No clipping, overlap, broken box, orphaned heading, abnormal stretch, formula overflow, missing stage, or discontinuity.
- Visual decision: `PASS`.

## Routing

- TeX remains disabled; no R3 is authorized or needed.
- Next gates are a completely fresh post-fix SA1, followed only after SA1 PASS by another fresh isolated SA3.
