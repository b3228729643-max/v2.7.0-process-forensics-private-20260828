# FIG-P609-01 R108/R168 read-only adjudication

## Identity and scope

- HANDOFF_ID: `C-FIG-P609-01-R108-SA2-R168-READONLY-ADJUDICATION-V1`
- Actual instance: `/root/sa2_fig_p609_r108_r168_readonly_v1`
- Model / effort / fork: `gpt-5.6-sol` / `xhigh` / `fork_turns=none`
- Route: `READONLY_R168_ADJUDICATION_FIRST -> P609_SA2_NO_SOURCE_CHANGE_READY_FOR_FRESH_SA1`
- Source changes: `0`; TeX/LuaLaTeX/latexmk/texlua calls: `0`; commits: `0`; central state/inventory writes: `0`.

The official R108 PDF and current sole C-worktree source match the assigned byte counts and SHA-256 identities. Independent caption/source localization places the target on physical page 661, where the visible printed page is 648 and the caption label is 图 32.9.

## Resolved whitelist paths

1. Official PDF: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r108_fullbook\main_full.pdf`
2. Sole figure source: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_C_visual\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C03\fig_v5_c03_autocorrelation_ess.tex`
3. Active Goal: `D:\Users\ASUS\.codex\attachments\99aa1e8a-0c07-4cb3-a04c-e66d4f1f29f3\goal-objective.md`
4. Strict protocol/schema resolved from the active Goal: internal section 9.2.1, lines 844-972, in that same Goal file; the Goal names required evidence schemas but does not directly reference a separate external strict-protocol file for this UID.
5. Minimum necessary chapter context: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_C_visual\src\讲义源码\第05册_采样方法主题模型与图排序\chapters\V5-C03.tex`, specifically the stationary covariance/ACF definitions, finite-sample variance and ESS derivation, and Figure 32.9 lead/readout at lines 535-608.

No old P609 evidence, SA root, report, handoff, state, inventory, task packet, routing log, chat conclusion, git-history conclusion, P656 material, other UID evidence, or central acceptance/report was read.

## Views actually opened

The manual review opened the complete page at 200 and 300 dpi; the PDF-extracted figure-plus-caption crop; the PDF-extracted standalone-style figure crop; the 300 dpi grayscale crop; the rendered-ink mask; the object/geometry overlay; four native-300-dpi risk ROIs; and the corresponding four nearest-neighbor 8x ROIs. The risk regions cover the weighted formula and natural scripts, ACF stems/window/boundary, caption glyphs, and connector-to-panel clearance.

## Mathematical and semantic recomputation

The visible ACF sequence is

`rho_hat_0:6 = (1, .86, .74, .64, .55, .47, .40)`.

It is positive and monotonically decaying over the displayed lags. The pale band begins after lag 0 and covers lags 1 through 6; the dashed boundary and ellipsis correctly separate the included preset window from unplotted and excluded later lags. The displayed finite-sample diagnostic is

`tau_hat_K,n = 1 + 2 sum_{k=1}^K (1-k/n) rho_hat_k`,

with `K=6<n`, followed by `N_hat_eff = n/tau_hat_K,n` and `tau_hat_K,n>0`. For the displayed values, `sum rho_hat_1:6=3.66` and `sum k*rho_hat_k=11.21`, hence `tau_hat_6,n=8.32-22.42/n`. Every integer `n>6` gives `tau_hat_6,n>1` (the minimum-domain case `n=7` gives about `5.117`), so the caption's direction—positive correlation increases the variance weight and decreases same-length ESS—is correct. The 7-by-7 Toeplitz matrix from the shown lags has minimum eigenvalue about `0.07736`, so the displayed finite sequence is not internally contradictory at the shown order.

The chapter context independently confirms `rho_k=gamma_k/gamma_0`, the `1-k/n` factor from the `2(n-k)` lag-pair count, the positive-denominator condition, and the distinction between a finite empirical diagnostic and a convergence proof. The formula notation, hats, bounds, fractions, subscripts, inequalities, caption, and post-figure readout all agree.

## Hard-gate adjudication under R168

General-visible source text is explicitly 9.6, 9.8, or 10.4 pt, with no text-bearing scaling; the caption is `normalsize` and appears as 10.909 pt spans in the final PDF. The only smaller PDF spans are natural TeX scripts derived from the 9.6 pt formula base, and they remain readable in native and nearest-8x ink views.

Actual rendered ink shows no missing/tofu/wrong codepoint, unreadable text or mathematics, real clipping, illegal text/object overlap, materially wrong geometry, semantic error, or visually conspicuous imbalance. The connector stops before the ESS border; text remains inside the rounded box; axis labels and truncation annotation do not collide with data; and grayscale preserves all required roles. Intended joins such as marker-on-stem, tick-on-axis, formula fraction bars, hats, and the connector's semantic relation are not illegal overlaps.

Pixel-height, glyph-area, ratio, and taxonomy/peer differences that do not cause a real defect remain R168 advisories only. None warrants a source request.

## Decision

`P609_SA2_NO_SOURCE_CHANGE_READY_FOR_FRESH_SA1`

This is a no-op adjudication: source modification count `0`, TeX count `0`, unresolved hard defects `0`. The next authorized action is a fresh SA1 review of the unchanged, identity-verified source/PDF pair.
