# B-EXM-P06 R2 fresh isolated SA3

## Role isolation

- Role: a new isolated, read-only SA3 final reviewer for the frozen P06 R2 source and build.
- Read `codex-lean-execution/SKILL.md`, `TASK_PACKET_B.md`, the current seven chapter sources/diff, R2 CONTROL/PDF/log, and the specified individual R2 page images.
- Did not read any P06 SA1 report, any prior P06 SA3 conclusion, `B-EXM-P06_SCOPE_STATIC.md`, `B-EXM-P06_BUILD_VISUAL_R1/R2.md`, CURRENT_STATE, or root/main conclusions.
- Did not create or modify files, run TeX, commit, or enter P07. `files_changed=[]`.

## Independent mathematics audit

1. 25.1: initial squared-distance rows are `(0,4),(4,0),(5,1),(29,25),(25,29)`. The assignment is `G1={x1,x5}`, `G2={x2,x3,x4}`, with centers `(5/2,2)^T` and `(2,0)^T`; reassignment is unchanged and `J=53/2=26.5`. PASS.
2. 26.2: `A^T A=diag(9,1)`, singular values are `3,1`, the full/compact dimensions are correct, and the best rank-one residual has sole nonzero singular value `1`, so both spectral and Frobenius errors are `1`. PASS.
3. 27.1: the characteristic polynomial is `lambda^2-7lambda+6`, eigenvalues are `6,1`, the first axis is `(2,1)^T/sqrt(5)`, contribution ratio `6/7`, projection `(12/5,6/5)^T`, reconstruction `(17/5,11/5)^T`, and the residual is orthogonal to the axis. PASS.
4. 28.1: `W^(1)=diag(3/2,3/2)` and `H^(1)=[[4/3,2/3],[2/3,4/3]]`; their product equals `X`, the loss falls from `1` to `0`, and zero support is preserved. PASS.
5. 30.1: `rho1=(0,1)`, `rho2=(1,0)`, the stationary distribution is `(1/2,1/2)`, detailed balance holds, and the original chain has period two. The lazy kernel has every entry `1/2` and reaches stationarity in one step from every initial distribution. PASS.
6. 30.2: rows sum to one, `rho1=(0.7,0.3)`, `rho2=(0.55,0.45)`, stationarity is `(0.4,0.6)`, both directional flows are `3/25`, and irreducibility plus positive self-loops gives convergence. PASS.
7. 31.1: weights are `100/101` and `100`, contributions are `0` and `10000`, `I=1`, second moment `10000`, and variance `9999`. Four zero-state draws have probability `0.9999^4=0.9996000599960001`; the estimate is then zero while empirical ESS is four. PASS.
8. 31.2: values are `0.16,0.64,0.01,0.49`, mean `13/40=0.325`, error `-1/120`, squared-deviation sum `0.2529`, unbiased variance `0.0843`, and standard error about `0.1451723`; the raw second-moment check agrees. PASS.
9. 32.1: every positive forward proposal has zero reverse probability, so all acceptances vanish and `K=I3`. The target is stationary but the chain is fully reducible and does not generally converge to it. PASS.
10. 32.2: `alpha12=1/3` and `alpha21=alpha23=alpha32=1`; `K=[[5/6,1/6,0],[1/4,1/2,1/4],[0,1/2,1/2]]`. Rows sum to one, `pi K=pi`, both bidirectional edge flows are `1/12`, the kernel is irreducible and aperiodic, and the fixed inputs give `x1=2,x2=3`. PASS.

Result: mathematics `10/10 PASS`; no content finding.

## Source structure and scope

- HEAD: `73049af2eac24af285a29b627ad98c085bc7d699`.
- The worktree diff contains exactly the authorized seven chapter files: V4-C02, V4-C03, V4-C04, V4-C05, V5-C01, V5-C02, and V5-C03.
- Cumulative diff: `61 insertions / 55 deletions`; no staged change; `git diff --check` PASS.
- All ten labels are globally unique. Each target has one matching `\SLExampleSolutionHeading`, one balanced `solution` environment, and one occurrence of each of the seven stages in the required order. Total: `70/70`.
- All target references resolve uniquely in the successful final build.
- The sole R2 delta beyond the ten solution rewrites is moving the existing `\Needspace{6\baselineskip}` in V4-C05 from after to immediately before `\SLDirectSection{例题、矩阵分解计算与练习}{sec:V4-C05-S06}`. Its parameter, the section title, mathematics, and labels are unchanged.
- No drawing source, shared macro/style, index, build entry, state, test, or other forbidden domain was touched.

Result: source structure and write scope PASS.

## R2 build identity and mechanical gates

- CONTROL: `B-EXM-P06-R2-CONTROL`.
- Output: `B-EXM-P06-R2-RESUME`.
- Started: `2026-08-25T06:46:02.6061299+08:00`.
- Finished: `2026-08-25T07:00:30.1009761+08:00`.
- Exit: `0`.
- PDF: `816` A4 pages (`595.276 x 841.89 pt`), `4,953,900` bytes.
- Log: `249,751` bytes.
- Hard errors, undefined controls, undefined references/citations, duplicate labels, final rerun requests, overfull, and underfull: all `0`.
- Main index: `731 accepted`, `0 rejected`, `0 warnings`; symbols index: `355 accepted`, `0 rejected`, `0 warnings`.
- Three log strings mentioning `slpivtarget is undefined` belong to a pgfplots Lua-expression probe followed by the documented TeX-backend fallback; they are not undefined controls/references and did not impair the successful output.

Result: build identity and mechanical gates PASS.

## Independent visual review

The reviewer individually reopened p556, p557, p558, and p559, plus representative target/adjacent pages p491-492, p511-512, p533-534, p603-604, p608-609, p632-633, p639-640, p661-663, and p666-668. Text anchors independently located the ten targets at physical pages 492, 512, 534, 557, 604, 609, 633, 640, 662, and 667.

- p557 contains section 28.6 and the opening of example 28.1 on the same page.
- p556-559 have no orphan heading, clipping, overlap, broken box, or abnormal stretch.
- The other target and adjacent pages have no visual regression.

Result: visual review PASS.

## Findings and decision

- `FINDINGS=[]`
- `FINAL_DECISION=PASS`
- `LOCAL_STATUS=B_LOCAL_PASS`
- `files_changed=[]`
- `unresolved=[]`

