# FIG-P020-01 — SA1 R111 role and write scope

- Role: independent historical-pass requalification reviewer (SA1).
- Runtime: spawned as `/root/p577_sa1_strict_r3_terra`, model `gpt-5.6-terra`, reasoning effort `max`; this record is the reviewer-side runtime attestation supplied by the root agent.
- Authority under review: official frozen R95 full-book PDF, physical page 17, rendered directly at 300 dpi.
- Figure identity: `FIG-P020-01`; source `src/绘图源码/第01册_数学基础与统计学习基本理论/V1-C01/fig_v1_c01_language_flow.tex`; chapter anchor `src/讲义源码/第01册_数学基础与统计学习基本理论/chapters/V1-C01.tex`.
- New evidence root (the sole writable output for this audit): `v2.7.0/_work/evidence/figures/FIG-P020-01/STRICT_FINAL/SA1_20260824_R111`.
- Read-only inputs: R95 PDF, figure source, chapter source, current Goal §9.2.1, and schema revision 111.
- Explicit exclusions: no business-source, LaTeX, public-style, build, inventory, central-state, or historical-P020-evidence writes; no historical P020 PASS/terminal conclusion was opened or inherited.
- Write whitelist: files and child directories below this evidence root only.

## Initial path and role gate

| Check | Result | Evidence |
|---|---:|---|
| new evidence root absent before creation | PASS | shell path check, 2026-08-24 |
| source exists | PASS | source path check |
| chapter exists | PASS | chapter path check |
| R95 PDF exists | PASS | frozen PDF path check |
| write scope restricted to this root | PASS | this attestation and subsequent terminal manifest |
| historical P020 results inherited | NO | independent rebuild required |
