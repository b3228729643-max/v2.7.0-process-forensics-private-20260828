# R398 P067 integration and unique R114 full-book build lock

Time: `2026-08-27T20:44:24+08:00`.

## Integrated commit

- A commit: `df4f71ba3aef1d91b9c79fa787af3ff42b3ba763`; parent `3c371f2448c86686ef5fc198237a395f9c4668e1`.
- Subject: `fix(fig-p067): separate p4 label from CDF guides`.
- Exact name-only: `src/绘图源码/第01册_数学基础与统计学习基本理论/V1-C04/fig_v1_c04_cdf.tex`; numstat `1+/1-`.
- Exact change: `at (axis cs:4.08,.89) {$p_4$};` to `at (axis cs:4.08,.85) {$p_4$};`.
- Source: `4,014 bytes`, SHA-256 `11BF3681D069F6A38C479B3074F39F93E8EB6144FF155AC543508E3589A51144`.
- Main cherry-pick: new HEAD `4eb592fba94241feb44e03337f027bbbc83b51e2`, parent `3bc644256d833272a789a7685b91996f98fa3336`; main worktree/index clean.

## Unique build lock

- Build script: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\build_v2.7.0.ps1`; `6,379 bytes`; SHA-256 `4DE115D8D99855273DB0E12511ABB983A17750684071FDA36E3F3FC51482CD65`.
- Output root: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r114_fullbook`; pre-lock file/dir existence `false/false`.
- Pre-lock TeX-family process count `0`.

The sole authorized parent invocation is:

`build_v2.7.0.ps1 -Engine lualatex -OutputDir src\build\strict_current_r114_fullbook -NoPublish`

Exactly one PowerShell parent chain is allowed. No manual retry, `Resume`, second invocation, concurrent A/B/C TeX, source write, commit, process interruption, or fresh role. Natural internal latexmk convergence belongs to this one parent chain. On failure or platform interruption, preserve the output and return for adjudication without repair or restart. On natural completion, release the lock and freeze PDF/log/index/page/font/navigation identities before any fresh review.

Inventory remains `31 SA1 / 38 SA2 / 0 SA3 / 31 local pass`; strict final remains `0/99`. R113 remains non-final.
