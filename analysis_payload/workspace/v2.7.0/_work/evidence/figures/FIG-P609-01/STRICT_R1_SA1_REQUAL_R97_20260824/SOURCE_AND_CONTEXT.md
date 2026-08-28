# FIG-P609-01 identity and source/context audit

- UID: `FIG-P609-01`; official figure number: `32.9`.
- Candidate: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r97_fullbook\main_full.pdf`
- Candidate SHA256: `062AD81020CB19A5C6688A45C73E00965F5060E0960A69AF820D7DC154DEE814` (expected R97 SHA matched).
- Candidate length: 813 physical pages; independently located on physical page 659, printed page 646.
- Scope rectangle in official-page coordinates: `[70.0, 525.0, 510.0, 702.0]` pt; it excludes the Fig. 32.9 caption and surrounding prose from the object denominator.
- Source: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C03\fig_v5_c03_autocorrelation_ess.tex`
- Source SHA256: `20687D1EE01AABA9B605591A61781CF688328026E0645AD51B6E02E921DC98A2`.
- Direct neighboring text: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\讲义源码\第05册_采样方法主题模型与图排序\chapters\V5-C03.tex`, lines 569--614 inspected. It says Fig. 32.9 joins empirical ACF and finite-sample weighted ESS as a diagnostic; it explicitly limits the interpretation to the predeclared window and does not treat a finite trajectory as a convergence proof.

## Source-to-PDF semantic check

The current source shows `K=6`, ACF coordinates `(0,1),(1,.86),…,(6,.40)`, and the finite-weighted forms for `\widehat\tau_{K,n}` and `\widehat N_{\mathrm{eff}}`. The candidate's text, caption, and neighboring prose agree: positive retained ACF increases the variance-weight factor and reduces same-length effective sample size. The dashed cut at 6.5 separates the retained window from the explicit ellipsis, so it does not falsely imply unobserved lags are zero.

No old FIG-P609 evidence, prior PASS, central state, or sibling audit is an input to this package.
