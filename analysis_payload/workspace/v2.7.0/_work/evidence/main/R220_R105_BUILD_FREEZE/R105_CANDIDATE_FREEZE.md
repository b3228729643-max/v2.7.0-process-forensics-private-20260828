# R105 官方候选冻结

- verdict: `PASS / OFFICIAL_CANDIDATE_FROZEN`
- source HEAD: `0f135f26203378213ab86aceb9fe1a6074311eeb`
- branch: `v2.7.0/integration`
- build invocation: 唯一 `build_v2.7.0.ps1 -Engine lualatex -OutputDir src\build\strict_current_r105_fullbook -NoPublish`
- wrapper result: `PASS`; 同一 latexmk 父链内三次自然 LuaLaTeX 收敛，无第二 invocation、retry 或中止
- terminal TeX processes: `NONE`

## PDF identity

- path: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r105_fullbook\main_full.pdf`
- pages: `817`
- bytes: `4,967,209`
- SHA-256: `F86E89047BA09FEA72FD8F79BF524A04DA367BFF3057806A879106A1032626A1`
- page size: `595.276 x 841.89 pt (A4)`; 817/817 rotation `0`
- PDF: `1.7`, unencrypted, suspects `no`
- log bytes: `258,877`

## Mechanical gates

- final log output: `Output written on main_full.pdf (817 pages, 4967209 bytes).`
- hard TeX errors, undefined control sequence, undefined references/citations, missing files/I/O, memory exhaustion, missing characters, multiply-defined labels, duplicate/unreferenced destinations, final rerun request, overfull and underfull boxes: `0`
- main index: `731 accepted / 0 rejected / 0 warnings`
- symbols index: `355 accepted / 0 rejected / 0 warnings`
- nonblocking warnings: 14 package/class warning headers; 3 PGF Lua survey fallbacks followed by TeX fallback; 1 luaotfload cache lookup/reload message; 2 imakeidx template reminders with final rerun gate `0`
- post-build main worktree: clean

## Incremental visual gates

- P608 / `fig:V5-C03-trace-running-mean`: printed page 648, physical page 661. Opened pages 660--662 and a 600 dpi target render. The first marker has visible white clearance from the y-axis and arrowhead; the last point has right-edge clearance. Both panels, ticks, labels and Figure 32.8 caption are complete and legible.
- P639 / `fig:V5-C04-bivariate-normal-conditionals`: printed page 676, physical page 689. Opened pages 688--690. The following Figure 33.7 introduction is now a single uninterrupted sentence ending `比较不同 |ρ| 下的混合速度。`; the old isolated fragment is absent. Figure 33.6/caption and surrounding text are intact.
- P640 / `fig:V5-C04-mixing-rho-comparison`: printed page 677, physical page 690. Opened pages 689--691 and a 600 dpi target render. The `.99` open marker and its vertical tick have visible white separation; both panels, legend, axes and Figure 33.7 caption are intact.
- Chapter transition: opened physical pages 701--704; Chapter 33 ends on physical 702 and Chapter 34 starts on physical 703 without abnormal blank space, clipping or overlap.

R105 supersedes R104 as the sole frozen official candidate. This freeze authorizes completely fresh read-only R105 role work for P608, P639 and P640, but does not itself migrate inventory roles, declare any new local pass, or declare whole-book final pass.
