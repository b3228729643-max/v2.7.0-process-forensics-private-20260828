# B-EXM-P06 R1 build and visual evidence

Status: `ROOT_MECHANICAL_PASS_VISUAL_FAIL_AFTER_FRESH_SA3`

## Authorized build identity

- Workflow: one authorized `run_background_build.ps1 -Resume` invocation; no concurrent invocation, retry, or P07 work.
- Output root: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_B_content\build\dialogue_B_content\B-EXM-P06-R1-RESUME`
- Control root: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_B_content\build\dialogue_B_content\B-EXM-P06-R1-CONTROL`
- Started: `2026-08-25T06:11:23.1021138+08:00`
- Finished: `2026-08-25T06:26:22.0551417+08:00`
- Wrapper exit: `0`; child exit: `0`.
- Parent latexmk PID: `18868`; natural LuaLaTeX children: `11180`, `11368`.
- PDF: `main_full.pdf`, `817` pages, `4,954,624` bytes.
- Log: `main_full.log`, `249,757` bytes; terminal line is `Output written on main_full.pdf (817 pages, 4954624 bytes).`
- After natural completion, `latexmk/lualatex/luatex/luahbtex = NONE`; build lock released and independently accepted by main.

## Mechanical final

- PDF: A4 `595.276 x 841.89 pt`, PDF 1.7, rotation 0, unencrypted; all 817 page geometries agree.
- Hard `!` errors, LaTeX errors, fatal/emergency stops, missing I/O, memory exhaustion, undefined controls/references/citations, missing characters: all `0`.
- Overfull and underfull boxes: `0` / `0`.
- Duplicate labels/destinations: `0`.
- Main index: `731` accepted, `0` rejected, `0` warnings.
- Symbols index: `355` accepted, `0` rejected, `0` warnings.
- Mechanical decision: `PASS`.

## AUX anchors and physical pages

The book front-matter offset is 13 physical pages. The fresh R1 AUX anchors are:

| Example | Print page | Physical page | Complete solution pages |
|---|---:|---:|---|
| 25.1 | 479 | 492 | 492-493 |
| 26.2 | 499 | 512 | 512-513 |
| 27.1 | 521 | 534 | 534-535 |
| 28.1 | 545 | 558 | 558-559 |
| 30.1 | 592 | 605 | 605-606 |
| 30.2 | 597 | 610 | 610-611 |
| 31.1 | 621 | 634 | 634 |
| 31.2 | 628 | 641 | 641-642 |
| 32.1 | 650 | 663 | 663-664 |
| 32.2 | 655 | 668 | 668-669 |

## Visual review

- Rendered at 150 dpi with Poppler into `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\B_content\evidence\B-EXM-P06-R1_VISUAL`.
- Full affected/adjacent coverage: `491-494`, `511-514`, `533-536`, `557-559`, `604-607`, `609-612`, `633-635`, `640-642`, `662-665`, `667-670` (37 pages).
- Reviewed all 10 target openings and all continuation pages at original resolution, plus the ten range contact sheets.
- The initial root contact-sheet pass missed one blocking defect later found by fresh isolated SA3: physical page 557 ends with the isolated section title `28.6 例题、矩阵分解计算与练习`, while example 28.1 begins on page 558.
- The remaining pages show no clipping, overlap, broken box, abnormal vertical stretch, over-wide formula, missing stage, or adjacent-page regression.
- Seven-stage flow is visually legible on every target; continuation headers appear only where the solution naturally spans pages.
- Visual decision: `FAIL` because of the page-557 orphaned section title. The earlier root PASS message is withdrawn.

## Routing

- No second build is authorized. No commit or P07 work is permitted.
- Fresh isolated SA3 completed with `FINAL_DECISION=FAIL`; route `P06-VIS-001` to main for a narrowly scoped source decision.
