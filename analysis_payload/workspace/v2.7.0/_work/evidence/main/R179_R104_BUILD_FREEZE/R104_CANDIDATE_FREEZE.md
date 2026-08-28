# R104 官方候选冻结

- verdict: `PASS / OFFICIAL_CANDIDATE_FROZEN`
- source HEAD: `62ee7eec6447a1fa7c49cb54dfadcbc2a3b03ed0`
- branch: `v2.7.0/integration`
- build invocation: 唯一 `build_v2.7.0.ps1 -Engine lualatex -OutputDir src\build\strict_current_r104_fullbook -NoPublish`
- wrapper result: `PASS`; no concurrent invocation, retry, or interruption
- terminal TeX processes: `NONE`

## PDF identity

- path: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r104_fullbook\main_full.pdf`
- pages: `817`
- bytes: `4,967,222`
- SHA-256: `E5C871642FBDDBEC6508BE1B61BD911FE281CA5ACFBD16B0449B13357770A641`
- page size: `595.276 x 841.89 pt (A4)`; rotation `0`
- PDF: `1.7`, unencrypted, suspects `no`
- log bytes: `258,877`

## Mechanical gates

- final log output: `Output written on main_full.pdf (817 pages, 4967222 bytes).`
- hard TeX errors, undefined control sequence, undefined references/citations, missing files/I/O, memory exhaustion, missing characters, duplicate destinations/labels, final rerun request, overfull and underfull boxes: `0`
- main index: `731 accepted / 0 rejected / 0 warnings`
- symbols index: `355 accepted / 0 rejected / 0 warnings`
- post-build main worktree: clean

## Incremental visual gate

- AUX label `fig:V5-C03-mh-balance-flux` resolves to printed page 638, physical PDF page 651.
- Rendered and opened physical pages `650--652` at 150 dpi.
- Page 651 shows the paired proposal-flow and truncated accepted-flow figure completely. The revised sentence names the two visible layers accurately; caption, equations, arrows and adjacent proposition/section flow are intact.
- Crop, overlap, missing glyph, wrong codepoint, unreadability, gross imbalance, orphan heading and pagination regression: `0`.
- Early exploratory pages `637--639` were not used for the target verdict after AUX mapping correction.

R104 supersedes R103 as the sole frozen official candidate. This freeze authorizes fresh read-only role work but does not itself declare any figure local pass or whole-book final pass.
