# FIG-P602-01 fresh SA1 input

- OWNER_DIALOGUE: `DIALOGUE_C_VISUAL`
- HANDOFF_ID: `C-FIG-P602-01-R101-SA1-INITIAL`
- ROLE: `subagent1` (fresh, read-only, no TeX)
- MODEL: `gpt-5.6-sol`
- REASONING_EFFORT: `xhigh`
- WORKTREE: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_C_visual`
- BRANCH: `v2.7.0/dialogue-c-visual`
- BASELINE/HEAD: `eea4060c5229168e2b973bbaea81cf391e7a9dfd`
- FIGURE_ID: `B52 / 图 32.5`
- CANONICAL_UID: `FIG-P602-01`
- SOURCE_FILE: `src/绘图源码/第05册_采样方法主题模型与图排序/V5-C03/fig_v5_c03_mh_accept_reject.tex`
- READ_ONLY_CONTEXT: `src/讲义源码/第05册_采样方法主题模型与图排序/chapters/V5-C03.tex` around line 300
- INDEX_PHYSICAL_PAGE: `710` (v2.6 task index)
- R101_PDF_PAGE: `651` (book page 638; located by exact caption text)
- SCOPE_DENOMINATOR: `46`, not 99
- STATUS_BEFORE_REVIEW: `ASSIGNED`, not closed

## Official candidate identity

- Candidate: `R101`
- PDF: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r101_fullbook\main_full.pdf`
- Pages: `814`
- Page size: `A4`
- Bytes: `4,947,496`
- SHA-256: `0870FF226DC383875C4A1B6EABB06AAB942317DA294D90D2864B3030D46DF1A1`

## Current indexed issue and target plan

- Severity: `high`
- Indexed issue: page previously contained sub-6pt text (about 6.00pt), 11 characters below 8.5pt, an overlong caption, and a flow needing clearer single-direction reading.
- Target plan: separate proposal, ratio calculation, accept/reject, and old-state retention into a single-direction flow; keep only the core acceptance-rate formula; do not solve by globally shrinking the figure.
- Review focus: mathematical meaning and direction; source-effective font; native 300dpi ink height; all unordered semantic pairs; native 1x/8x overlap semantics; clipping and minimum clearance; grayscale; page integration; exact consistency with caption and adjacent text.

## Fresh rendered evidence (Poppler only; no TeX)

- `r101_pdfpage_651_200dpi.png`
- `r101_pdfpage_651_300dpi.png`
- `r101_figure_32_5_crop_300dpi.png`
- `r101_figure_32_5_grayscale_300dpi.png`

## Permissions

- ALLOWED_WRITE_SCOPE: none.
- FORBIDDEN_SCOPE: every source file, chapter text, shared macro/style/font, central state/inventory, A/B/C evidence mutation, and any TeX or build invocation.
- SA1 must not read any SA3 conclusion and must not reuse an earlier PASS/FAIL.
- Missing measurement/overlap evidence must be reported as evidence insufficiency and cannot be converted to PASS.
