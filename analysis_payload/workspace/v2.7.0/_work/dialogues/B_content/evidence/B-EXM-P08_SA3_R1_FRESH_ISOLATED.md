# B-EXM-P08 SA3 R1 fresh isolated audit

- `HANDOFF_ID`: `B-EXM-P08`
- `ROLE`: fresh isolated read-only SA3
- `MODEL_ROUTING`: `gpt-5.6-sol/xhigh`
- `WORKTREE`: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_B_content`
- `R1_OUTPUT`: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_B_content\build\dialogue_B_content\B-EXM-P08-R1-RESUME`
- `R1_CONTROL`: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_B_content\build\dialogue_B_content\B-EXM-P08-R1-CONTROL`
- `VISUAL_DIR`: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\B_content\evidence\B-EXM-P08-SA3-R1-VISUAL`
- `REPORT_PATH`: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\B_content\evidence\B-EXM-P08_SA3_R1_FRESH_ISOLATED.md`
- `FINAL_DECISION`: **PASS**

## 1. Isolation and write declaration

This audit was derived independently from the permitted current source, the goal/task packet, the current public solution-stage/heading definitions, the R1 OUTPUT/CONTROL artifacts, and a newly rendered 12-page visual set. No P08 SA1 report or conclusion, prior/current SA3 report, preaudit/root/build-visual evidence, main R158/R102 precheck or acceptance, P01--P07 evidence/handoff, state/inventory/risk/handoff evidence, or chat conclusion was read.

No TeX engine, LuaLaTeX, latexmk, luatex, or luahbtex command was run. No business source was modified. The only writes were the requested PNG directory and this report.

## 2. Independent mathematics/content recomputation: 5/5 PASS

### 2.1 Example 36.3, `exm:V5-C07-damped-four` — PASS

Source: `V5-C07.tex:845--884`. The supplied matrix is nonnegative and column-stochastic. With (d=4/5) and (v=\boldsymbol1/4), every teleport component is (1/20). Expanding

\[
\boldsymbol r=\frac45S\boldsymbol r+\frac1{20}\boldsymbol1
\]

gives the four displayed equations in the source. Subtracting the (B,D) equations gives

\[
r_B-r_D=\frac25(r_D-r_B),
\]

hence (r_B=r_D). Substitution yields

\[
\frac{37}{75}r_B=\frac{19}{300},\qquad
(r_A,r_B,r_C,r_D)=\frac1{148}(15,19,95,19).
\]

Independent exact arithmetic gave zero residual in all four fixed-point equations, four strictly positive entries, and total mass (148/148=1). Since (\|0.8S\|_1=0.8<1), (I-0.8S) is invertible (Neumann series), so the fixed point is unique; the positive teleport term makes it strictly positive. The ranking (C\succ B=D\succ A) is correct.

### 2.2 Example 36.4, `exm:V5-C07-power-three` — PASS

Source: `V5-C07.tex:887--930`. The matrix is nonnegative and column-stochastic. Starting from (\boldsymbol1/3), independent exact iteration gives

\[
\boldsymbol r^{(1)}=(1/3,23/120,19/40)^{\mathsf T},\qquad
\boldsymbol r^{(2)}=(363/800,23/120,851/2400)^{\mathsf T},
\]

and both sums are (1). Solving the fixed-point equations gives

\[
\boldsymbol r=\frac1{1769}(686,380,703)^{\mathsf T}.
\]

Exact substitution gave zero residual in all three equations, positive entries, and mass (1). Uniqueness follows again from (\|0.85S\|_1=0.85<1). Maximum-component normalization gives (\boldsymbol z=(686/703,380/703,1)^{\mathsf T}) with sum (1769/703), so dividing by that sum recovers the probability vector exactly. The ranking (3\succ1\succ2) and the scale-versus-probability distinction are correct.

### 2.3 Example 37.1, `exm:V5-C08-two-candidate-selection` — PASS

Source: `V5-C08.tex:397--420`. The predeclared eligibility rule requires both folds to succeed. Thus

\[
a_A=(1,1),\quad a_B=(1,0),\quad \mathcal B_{\rm ok}=\{A\}.
\]

Candidate B has no legal two-fold aggregate and cannot compete using only its successful fold. Candidate A has

\[
\overline L_A=(0.42+0.46)/2=0.44,\qquad
\overline C_A=(8+9)/2=8.5\text{ minutes}.
\]

The selection, full-development-data refit, and single locked-test report (L_{\rm test}=0.47) are correctly separated; the test result is explicitly barred from feeding back to candidate choice, hyperparameters, or preprocessing.

### 2.4 Example 37.3, `exm:V5-C08-lsa-shape` — PASS

Source: `V5-C08.tex:767--804`. For (X\in\mathbb R^{6\times4}), (K=2), the thin truncated factors have dimensions

\[
U_2:6\times2,\quad \Sigma_2:2\times2,\quad V_2:4\times2,
\quad H=\Sigma_2V_2^{\mathsf T}:2\times4.
\]

Both multiplication chains recover (6\times4). The correct orthogonality is (V_2^{\mathsf T}V_2=I_2), not (V_2V_2^{\mathsf T}=I_4). For document columns (h_j,h_\ell),

\[
h_j^{\mathsf T}h_\ell=e_j^{\mathsf T}V_2\Sigma_2^2V_2^{\mathsf T}e_\ell
\]

is generally nonzero. Meanwhile (HH^{\mathsf T}=\Sigma_2^2), so the two rows of (H) are orthogonal (with row norms given by singular values). The row-versus-document-column distinction is correct.

### 2.5 Example 37.4, `exm:V5-C08-holdout`, with adjacent proposition/proof — PASS

Sources: proposition/proof `V5-C08.tex:479--504`; question/solution `V5-C08.tex:806--832`.

The proposition has the necessary conditions: (\widehat f) is (\mathcal D_{\rm dev})-measurable; conditional on development data the test units remain iid from the target distribution; the loss is integrable. Finite-sum conditional expectation then gives the stated conditional unbiasedness.

For fixed candidates (f_1,\ldots,f_{20}), test-based

\[
\widehat K\in\arg\min_K\widehat R_K
\]

normally makes (f_{\widehat K}) depend on (\mathcal D_{\rm test}), so it is no longer a candidate fixed by development data. The stated degeneracies are valid: conditional on (\mathcal D_{\rm dev}), the selected index may be almost surely fixed; or every conditionally possible selected index may represent the same predictor.

The inequality chain is exact:

\[
\mathbb E[\min_K\widehat R_K\mid\mathcal D_{\rm dev}]
\le \min_KR(f_K)
\le \mathbb E[R(f_{\widehat K})\mid\mathcal D_{\rm dev}].
\]

For the left inequality, (Y=\min_K\widehat R_K\le\widehat R_{K_\star}) for any conditionally fixed population-risk minimizer (K_\star), and conditional unbiasedness supplies the expectation. Equality holds exactly when such a (K_\star\) attains the empirical minimum conditionally almost surely. For the right inequality, (R(f_{\widehat K})\ge\min_KR(f_K)) pointwise; equality holds exactly when (\widehat K\) belongs to the population-risk argmin conditionally almost surely. These are both exact equality cases, so the source correctly says the optimism is typical/general rather than an exception-free strict inequality. The prescribed nonleaking remedy—choose rank within development data, lock/refit, test once—is correct.

## 3. Source structure, labels, references, and environment gates — PASS

The current public macros define the seven required stages as `SLReadTranslation`, `SolGiven`, `SLMethodTrigger`, `SolPlan`, `SolDerive`, `SolCheck`, and `SolAnswer`; `SLExampleSolutionHeading` prints the same-number heading through `\ref` and keeps it with its opening block.

Each of the five target solutions contains each stage exactly once and in that exact order:

| Object | Label count | Heading count | Ordered stages |
|---|---:|---:|---:|
| `exm:V5-C07-damped-four` | 1 | 1 | 7/7 |
| `exm:V5-C07-power-three` | 1 | 1 | 7/7 |
| `exm:V5-C08-two-candidate-selection` | 1 | 1 | 7/7 |
| `exm:V5-C08-lsa-shape` | 1 | 1 | 7/7 |
| `exm:V5-C08-holdout` | 1 | 1 | 7/7 |
| **Total** | **5/5** | **5/5** | **35/35** |

No extra `SolBoundary`/type-specific solution stage occurs inside any of the five target blocks. Whole-file balance checks:

| File | `solution` begin/end | `SLRunningExample` begin/end | `\[` / `\]` | all environment stack mismatches/unclosed |
|---|---:|---:|---:|---:|
| `V5-C07.tex` | 4/4 | 1/1 | 49/49 | 0/0 |
| `V5-C08.tex` | 4/4 | 0/0 | 50/50 | 0/0 |

New AUX identities are unique and resolved:

| Label | AUX number | Logical PDF page | Title |
|---|---:|---:|---|
| `exm:V5-C07-damped-four` | 36.3 | 766 | 四结点阻尼 PageRank |
| `exm:V5-C07-power-three` | 36.4 | 767 | 三结点幂法与概率归一化 |
| `exm:V5-C08-two-candidate-selection` | 37.1 | 781 | 两候选、两折的完整选择轮次 |
| `prop:V5-C08-test-unbiased` | 37.3 | 784 | 独立测试均值对已锁定模型条件无偏 |
| `exm:V5-C08-lsa-shape` | 37.3 | 790 | LSA因子维数纠错 |
| `exm:V5-C08-holdout` | 37.4 | 790 | 锁定测试的条件无偏 |

The R1 log has zero undefined references, undefined citations, changed-label rerun notices, and multiply-defined-label notices.

## 4. Exact business write domain — PASS

Independent `git -c core.quotepath=false status --short`, `diff --name-status`, and `diff --numstat` agree on exactly two modified business files and no other worktree paths:

| File | Status | Added | Deleted |
|---|---:|---:|---:|
| `src/讲义源码/第05册_采样方法主题模型与图排序/chapters/V5-C07.tex` | M | 37 | 32 |
| `src/讲义源码/第05册_采样方法主题模型与图排序/chapters/V5-C08.tex` | M | 41 | 43 |

## 5. R1 CONTROL/PDF/AUX/log/index mechanical identity — PASS

- CONTROL: `exit_code.txt = 0`; started `2026-08-25T12:48:00.5146338+08:00`; finished `2026-08-25T12:58:07.7048225+08:00`.
- CONTROL stdout records two LuaLaTeX passes, both producing `main_full.pdf (817 pages, 4962906 bytes)`, followed by `Latexmk: All targets ... are up-to-date` and JSON `"result": "PASS"`.
- The actual R1 PDF is 4,962,906 bytes with last-write time `2026-08-25 12:58:02`; `pdfinfo` independently reports 817 pages, A4 `595.276 x 841.89 pts`, rotation 0, PDF 1.7, unencrypted. The Windows Poppler build printed `File size: 0 bytes` on this Unicode path, so byte identity was taken from both the filesystem and CONTROL stdout, which agree exactly.
- AUX contains the unique resolved identities listed above. AUX/IDX were written before the final PDF/log and before CONTROL completion, consistent with the two-pass build sequence.
- Hard log gates: 0 TeX fatal lines, 0 `LaTeX Error`, 0 undefined controls, 0 emergency/fatal stop, 0 no-pages output, 0 undefined references/citations, 0 changed-label notices, 0 multiply-defined labels, 0 missing characters, 0 overfull/underfull hbox/vbox, 0 duplicate-destination warnings, and 0 rerunfilecheck warnings.
- Main index identity: `main_full.idx` has 731 index entries; `main_full.ilg` says 731 accepted, 0 rejected, 719 output lines, 0 warnings; `main_full.ind` is nonempty (637 item lines counted).
- Symbol index identity: `symbols.idx` has 355 entries; `symbols.ilg` says 355 accepted, 0 rejected, 572 output lines, 0 warnings; `symbols.ind` is nonempty (353 item lines counted).
- Non-hard messages were retained rather than hidden: CONTROL stderr contains only Perl locale fallback plus successful makeindex summaries; the final log has six PDF-string token-removal warnings outside the audited P08 objects and two imakeidx reminder messages even though latexmk completed its index passes and declared all targets current. They do not alter P08 content, references, page rendering, or the hard-gate result.

## 6. Independent 300 dpi visual audit — 12/12 PASS

All PNGs were newly rendered from the R1 PDF with system Poppler `pdftoppm` at 300 dpi, then every image was opened at readable/original detail. Checks included target and adjacent content, formulas/tables, page transitions, running headers, footers/logical page numbers, clipping, overlaps, broken frames, missing glyphs, isolated headings, abnormal vertical stretch/gaps, and visible regression.

| Physical page | Logical page | Inspected content | Result |
|---:|---:|---|---|
| 778 | 765 | example 36.1 continuation; transition into 36.2 and opening solution stages | PASS |
| 779 | 766 | 36.2 completion; example 36.3 question, heading, and main derivation | PASS |
| 780 | 767 | 36.3 check/conclusion; example 36.4 question, heading, iterations and fixed point | PASS |
| 781 | 768 | 36.4 normalization/check/conclusion; chapter-exercise transition | PASS |
| 793 | 780 | adjacent loss derivations/proposition 37.1 proof and page transition | PASS |
| 794 | 781 | adjacent proposition 37.2; example 37.1 question and opening solution stages | PASS |
| 795 | 782 | example 37.1 completion; adjacent explanatory blocks and numerical example | PASS |
| 796 | 783 | section 37.3 opening; two protocol diagram; adjacent proposition self-check boundary | PASS |
| 802 | 789 | section 37.5 opening; adjacent example 37.2 solution and displayed formulas | PASS |
| 803 | 790 | example 37.3 full solution; example 37.4 question boundary | PASS |
| 804 | 791 | example 37.4 complete solution, inequality chain and equality cases; following figure lead-in | PASS |
| 805 | 792 | full-course synthesis figure, caption/read-check, chapter-exercise transition | PASS |

No clipped glyph or formula, text/figure overlap, broken/split frame artifact, missing glyph, orphaned target answer heading, footer/header/page-number defect, abnormal stretch, or unprofessional gap was found on any of the 12 pages. Natural breakable-solution continuations are clearly marked `解答（续）` and preserve content continuity.

## 7. Findings by severity/file/page/remedy

| Severity | File/artifact | Page | Finding | Remedy |
|---|---|---:|---|---|
| P0/P1/P2/P3 | Target source and 12 rendered pages | all audited | No mathematical, structural, reference, environment, write-domain, mechanical, or visual defect found. | None. |
| INFO | `B-EXM-P08-R1-CONTROL/stderr.log` | N/A | Perl locale fallback; build and both indexers completed successfully. | None for P08. |
| INFO | `B-EXM-P08-R1-RESUME/main_full.log` | outside P08 objects / N/A | Six pre-existing PDF-string token-removal warnings and two imakeidx reminders; no hard-gate consequence, index outputs current and internally consistent. | None for P08; only a future global metadata cleanup if desired. |
| INFO | `pdfinfo` on Unicode path | N/A | Poppler printed `File size: 0 bytes`; actual filesystem size and both LuaLaTeX stdout records agree at 4,962,906 bytes. | None; use filesystem length for Windows Unicode-path byte identity. |

## 8. Return contract

- `assigned_scope`: independent fresh isolated SA3 review of five P08 objects, exact 35-stage/label/ref/environment/write-domain gates, R1 identity/hard gates, and 12-page fresh visual audit.
- `completed`: yes; math 5/5, structure/write/ref/env complete, R1 mechanical identity complete, visual 12/12.
- `files_changed`: `[]` for business source. Audit-only outputs are this report and 12 PNG files in `VISUAL_DIR`.
- `decisions`: all required gates pass; `FINAL_DECISION=PASS`.
- `unresolved`: `NONE`.
- `validation`: exact rational fixed-point/iteration recomputation; conditional-expectation/equality-case derivation; source parser/counts; AUX/log/index/CONTROL/PDF inspection; read-only git verification; fresh 300 dpi 12-page visual review.
- `next_action`: parent coordinator may consume this independent SA3 evidence for P08 acceptance. No P09, handoff, commit, staging, source change, or TeX action was performed.
- `report_path`: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\B_content\evidence\B-EXM-P08_SA3_R1_FRESH_ISOLATED.md`.
- `visual_dir`: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\B_content\evidence\B-EXM-P08-SA3-R1-VISUAL`.
- `FINAL_DECISION`: **PASS**.

