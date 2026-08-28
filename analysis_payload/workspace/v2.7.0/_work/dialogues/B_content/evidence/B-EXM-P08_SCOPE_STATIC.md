# B-EXM-P08｜source/static freeze

## Identity and authority

- `OWNER_DIALOGUE=DIALOGUE_B_CONTENT`
- `HANDOFF_ID=B-EXM-P08`
- B branch HEAD/parent at freeze: `57ffe7f630770a2fecf75f2a277b886e916f3246` / `bc713ff1505a84b8fd72f2a56a6386bc4dd84a50`.
- Main has integrated P07 as `3767c9d2b256e9be956bcb2922cc380ea34fe932`; that main-only integration commit was not written back to B.
- Main message `MAIN_R102_BUILD_LOCK_ACTIVE` remains controlling: B ran no TeX and may only request a later build slot.

## Exact P08 objects and source scope

The authoritative remaining example inventory contains exactly five objects:

1. 36.3 `exm:V5-C07-damped-four`;
2. 36.4 `exm:V5-C07-power-three`;
3. 37.1 `exm:V5-C08-two-candidate-selection`;
4. 37.3 `exm:V5-C08-lsa-shape`;
5. 37.4 `exm:V5-C08-holdout`.

Business-source diff is exactly two files, `78 insertions / 75 deletions`:

- `src/讲义源码/第05册_采样方法主题模型与图排序/chapters/V5-C07.tex`: `37+/32-`; only the 36.3 and 36.4 solution bodies.
- `src/讲义源码/第05册_采样方法主题模型与图排序/chapters/V5-C08.tex`: `41+/43-`; the 37.1, 37.3 and 37.4 solution bodies, plus the adjacent proposition-proof final sentence and the 37.4 question sentence needed to make the same nondegenerate/degenerate measurability boundary mathematically consistent.

No drawing source, shared macro/style/font/color, index, navigation, build entry, test, label, figure/table source, main authority state, or P01--P07 sealed source/evidence was changed. Nothing is staged and no commit exists for P08.

## Independent pre-edit audit

Fresh read-only `gpt-5.6-sol/xhigh` pre-audit independently recomputed all five objects. Main numerical answers were correct, but the old source had only `22/35` stage macros. It also found:

- 36.3 skipped component elimination and uniqueness;
- 36.4 retained an iteration approximation without iteration count or stopping certificate;
- 37.4 used an unconditional expectation statement and omitted degenerate equality boundaries.

The sole source writer was routed as `gpt-5.6-terra/high`; it changed only the exact source scope above. Root and all QA roles remained source-read-only while that writer was active.

## Final mathematics/content result

1. **36.3 PASS.** Component elimination gives `r_B=r_D=19/148`, `r_A=15/148`, `r_C=95/148`; the vector is positive, normalized, has zero fixed-point residual, and `||0.8S||_1<1` makes `I-0.8S` invertible. Final rank: `C > B=D > A`.
2. **36.4 PASS.** The first two iterates are `(1/3,23/120,19/40)^T` and `(363/800,23/120,851/2400)^T`; the exact fixed point is `(686,380,703)^T/1769`. The uncertified decimal iterate was removed. Max normalization `(686/703,380/703,1)^T` has sum `1769/703` and L1-normalizes to the exact probability vector.
3. **37.1 PASS.** Eligibility vectors are `a_A=(1,1)` and `a_B=(1,0)`, so only A is comparable; its mean validation loss/cost are `0.44` and `8.5` minutes. A is refit on all development data and the locked test value `0.47` is reported once without feedback.
4. **37.3 PASS.** Shapes are `U_2:6x2`, `Sigma_2:2x2`, `V_2:4x2`, `H:2x4`; reconstruction is `6x4`. `V_2^T V_2=I_2` and `HH^T=Sigma_2^2` do not imply pairwise orthogonality of the four document columns.
5. **37.4 PASS after targeted R3 closure.** For each fixed development-measurable candidate, the test risk is conditionally unbiased. Test-based rank selection usually destroys that measurability, with explicit exceptions when the selected index is conditionally almost surely fixed or all selectable indices denote the same predictor. The final source gives the correct conditional inequality chain and the exact, separate equality conditions for both inequalities, then restores the no-leak development-select / lock-refit / one-test protocol.

## SA1 history and final status

- `B-EXM-P08_SA1_POSTEDIT_FRESH.md`: historical `FAIL`, four objects PASS, one low 37.4 measurability-boundary finding.
- `B-EXM-P08_SA1_R2_TARGETED_FRESH.md`: historical targeted `FAIL`, identifying categorical adjacent wording and two separate equality conditions.
- `B-EXM-P08_SA1_R3_TARGETED_FRESH.md`: fresh isolated targeted `FINAL_DECISION=PASS`, zero findings; proposition proof, question, solution, both equality boundaries, seven stages and environments all PASS.

The failed reports are preserved as repair history and are not reused as final PASS evidence. Final root result is `5/5 mathematics/content PASS` and `35/35 ordered stage macros PASS`.

## Final static gates

```text
git diff --check
PASS

python -m unittest src.tests.test_style_term_solution_contracts src.tests.test_layout_source_contracts
Ran 9 tests in 0.305s
OK

powershell -File D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\B_content\tools\check_p08_static.ps1 -Worktree <B_WORKTREE>
P08_STATIC=PASS
TARGET_SOLUTIONS=5
STAGE_MACROS=35/35
TARGET_LABELS_AND_HEADINGS=5/5
TARGET_NESTED_RUNNING_EXAMPLE=0
ENVIRONMENT_STACKS=BALANCED
HANDWRITTEN_CHECK_ANSWER_HEADINGS=0
TARGET_DISPLAY_MATH=BALANCED
UNCERTIFIED_36_4_APPROX=0
HOLDOUT_CONDITIONAL_BOUNDARY=PASS
HOLDOUT_EQUALITY_BOUNDARIES=PASS
```

- `git diff --name-only`: exactly the two authorized chapter files.
- `git diff --numstat`: V5-C07 `37/32`; V5-C08 `41/43`; total `78/75`.
- `git diff --cached --name-only`: empty.
- The five target labels/headings each occur exactly once; `solution` and `SLRunningExample` stacks are balanced in both changed files.

## Resource state and routing

- B started no `latexmk`, `lualatex`, `luatex`, or `luahbtex` process.
- At the final read-only process check, main's declared R102 lock was active and the host showed `latexmk PID 2448` and `lualatex PID 14920` (both started around `12:22`); B did not terminate or inspect them beyond the permitted process listing.
- `TEX_FOR_B=DISABLED`; no PDF/visual/build claim is made for P08.
- `B_P08_SOURCE_STATIC_READY_REQUEST_BUILD_SLOT` is the only allowed next routing. P08 source and this evidence are frozen pending a future explicit main grant.
- No P08 commit and no later batch has started.

## Unresolved

- Content/static findings: `NONE`.
- External wait only: main R102 build lock must be explicitly released and a B-P08 build slot explicitly granted before any TeX invocation.
