# B-EXM-P08 fresh targeted SA1 (R2)

- assigned_scope: `37.4 exm:V5-C08-holdout` in the current `V5-C08.tex`, together with adjacent `prop:V5-C08-test-unbiased`; mathematical/content and local source-structure review only.
- completed: yes
- files_changed: `[]` (business source)
- report_path: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\B_content\evidence\B-EXM-P08_SA1_R2_TARGETED_FRESH.md`
- FINAL_DECISION: **FAIL**

## Decisions

1. **Conditional-unbiased premise — PASS.** The proposition conditions on `\mathcal D_{\mathrm{dev}}`, requires the evaluated predictor to be `\mathcal D_{\mathrm{dev}}`-measurable, requires the test units to remain conditionally iid from `P`, and assumes integrability. The proof correctly moves the conditional expectation through the finite average. The example correctly applies this premise separately to each candidate fixed after conditioning on the development data.
2. **Test-selected `\widehat K` and tie handling — PASS.** Lines 817–819 define `\widehat K` through test empirical-risk minimization over the 20 candidates and immediately state that the tie rule is fixed in advance. This is enough to make the selected index single-valued once that fixed rule is applied.
3. **Usual/nondegenerate dependence and explicit exceptions — PARTIAL/FAIL.** The solution itself correctly says the dependence occurs “usually” and explicitly preserves the two relevant measurability exceptions: conditionally almost-surely fixed `\widehat K`, or all possibly selected indices representing the same predictor. However, the example prompt and the adjacent proof retain categorical versions; see finding F1.
4. **Conditional inequality chain — PASS.** With `X_K=\widehat R_K` and `\mu_K=R(f_K)` conditional on `\mathcal D_{\mathrm{dev}}`, `E[\min_K X_K\mid\mathcal D_{\mathrm{dev}}]\le\min_K\mu_K\le E[\mu_{\widehat K}\mid\mathcal D_{\mathrm{dev}}]` is correct. The stated reasons—individual conditional unbiasedness and the selected risk taking one of the candidate-risk values—are valid.
5. **Both equality boundaries — FAIL.** The source only says vaguely that equality can occur in degenerate cases and then links that statement to two sufficient measurability exceptions. It does not state the separate exact boundary for either inequality; see finding F2.
6. **No-leak remedy — PASS.** Selecting the rank within development data, locking/refitting, and evaluating exactly once on an unopened test set is the correct remedy.
7. **Seven-stage and environment structure — PASS.** The solution contains exactly one each of `\SLReadTranslation`, `\SolGiven`, `\SLMethodTrigger`, `\SolPlan`, `\SolDerive`, `\SolCheck`, and `\SolAnswer`. The example label, solution heading, and `example`/`solution` begin/end pairs are balanced in the inspected object.
8. **No-new-overstatement check — FAIL.** The categorical claims identified in F1 overstate what follows once the same source acknowledges degenerate exceptions.

## Findings

### F1 — Categorical claims contradict the acknowledged degenerate exceptions (blocking)

- Location: `V5-C08.tex:503` and `V5-C08.tex:807`.
- The proof says that if test results participate in candidate selection, `\widehat f` no longer depends only on `\mathcal D_{\mathrm{dev}}` and the conditional-independence structure is broken. The example prompt likewise says selecting the minimum test error “will” break the proposition's condition. Both are unconditional claims.
- Yet lines 819 and 826 correctly acknowledge cases in which the test-based selector is conditionally almost surely fixed, or all possibly selected indices denote the same predictor. In those cases the evaluated predictor can remain `\mathcal D_{\mathrm{dev}}`-measurable, so test participation does not necessarily break the premise.
- Required correction: qualify the prompt and proof conclusion with “usually/in nondegenerate cases,” or state the exceptions at those categorical claims as well.

### F2 — The two equality boundaries are not separately and exactly stated (blocking)

- Location: `V5-C08.tex:825–826`.
- Conditional on `\mathcal D_{\mathrm{dev}}`, let `X_K=\widehat R_K`, `\mu_K=R(f_K)`, `M=\min_K X_K`, and `\mu_*=\min_K\mu_K`.
- The **left equality** `E[M\mid\mathcal D_{\mathrm{dev}}]=\mu_*` holds exactly when a population-risk minimizer is also an empirical test-loss minimizer almost surely (equivalently, for any fixed `K_*\in\arg\min_K\mu_K`, `X_{K_*}=M` almost surely, conditional on the development data).
- The **right equality** `\mu_*=E[\mu_{\widehat K}\mid\mathcal D_{\mathrm{dev}}]` holds exactly when `\widehat K` selects only population-risk minimizers almost surely, i.e. `P(\widehat K\in\arg\min_K\mu_K\mid\mathcal D_{\mathrm{dev}})=1`.
- The two measurability exceptions currently listed are sufficient examples that can make both inequalities equalities, but they are not the exact, separate equality characterizations. In particular, one inequality can be an equality while the other is strict.
- Required correction: state these two equality conditions separately, while retaining the warning that strict optimism is typical rather than universal.

## Unresolved

- F1 and F2 remain unresolved in the current source. No other content or structural issue was found within the assigned object.

## Validation

- Performed isolated, source-only inspection of `V5-C08.tex:479–504` and `V5-C08.tex:806–828`.
- Checked the conditional expectation argument, selector measurability, tie handling, both inequalities and their equality cases, leakage remedy, seven-stage uniqueness, label linkage, and environment balance.
- Did not read prior P08/P01–P07 evidence or state reports; did not run TeX, LuaLaTeX, latexmk, tests, Git staging/commit, or PDF validation.

## Next action

- Return to the source writer/root for a narrowly scoped correction of F1 and F2, then rerun a fresh targeted SA1 on the same proposition/example pair.
