# FIG-P020-01 — R6 R111 SA1 role and write scope

- Role: independent historical-pass requalification reviewer (SA1).
- Runtime attestation: root agent explicitly created this reviewer as `/root/p577_sa1_strict_r3_terra`, model `gpt-5.6-terra`, reasoning effort `max`.
- Authority under review: official frozen R95 full-book PDF, physical page 17, rendered directly at 300 dpi.
- Figure identity: `FIG-P020-01`; source `src/绘图源码/第01册_数学基础与统计学习基本理论/V1-C01/fig_v1_c01_language_flow.tex`; chapter anchor `src/讲义源码/第01册_数学基础与统计学习基本理论/chapters/V1-C01.tex`.
- Active new evidence root and sole write whitelist: `v2.7.0/_work/evidence/figures/FIG-P020-01/STRICT_R6_REQUAL_R111_SA1_20260824`.
- Read-only inputs: R95 PDF, figure source, chapter source, current Goal §9.2.1, and schema revision 111.
- Explicit exclusions: no business-source, LaTeX, public-style, build, inventory, central-state, or historical-P020-evidence writes; no historical P020 PASS/terminal conclusion was opened or inherited.

## Path gate

| Check | Result | Evidence |
|---|---:|---|
| R6 evidence root absent before creation | PASS | shell path check, 2026-08-24 |
| R6 root is not nested below historical `STRICT_FINAL` | PASS | direct sibling under `FIG-P020-01` |
| source exists | PASS | source path check |
| chapter exists | PASS | chapter path check |
| R95 PDF exists | PASS | frozen PDF path check |
| write scope restricted to this root | PASS | this attestation and terminal manifest |

The earlier `STRICT_FINAL/SA1_20260824_R111` staging directory is explicitly superseded and is not cited by this review.
