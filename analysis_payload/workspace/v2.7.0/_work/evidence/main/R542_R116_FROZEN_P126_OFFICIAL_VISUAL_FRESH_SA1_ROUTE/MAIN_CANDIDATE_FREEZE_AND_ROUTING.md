# R542 — R116 candidate freeze and P126 fresh-SA1 route

## Main decision

- `R116_ACCEPTED_AS_SOLE_OFFICIAL_CURRENT_CANDIDATE`
- `P126_OFFICIAL_VISUAL_SCREEN_PASS_READY_FOR_COMPLETELY_FRESH_ISOLATED_SA1`
- R115 remains immutable historical evidence and is no longer the current candidate.
- P689 remains an accepted local pass and permanently frozen.

## Integration and build identity

- Main branch: `v2.7.0/integration`.
- Main HEAD: `f1874b2a4f1ffe823968d417019cfdc2c5641888`.
- Parent: `bd6efc7eaef9fc8fff82919e89934b60c2e2cbcf`.
- Subject: `fix(fig-p126): correct coordinate descent geometry and legend`.
- Commit boundary: exactly `src/绘图源码/第01册_数学基础与统计学习基本理论/V1-C08/fig_v1_c08_coordinate.tex`, `38+/31-`.
- Integrated source: 4,686 bytes, SHA-256 `2887758F5CC94987BE750E1EC53B555FB88CE8F71B7260CABBE0A17DDF237405`.
- Main worktree and index are clean; `git diff --check` passes.
- Main consumed exactly one authorized parent call:
  `build_v2.7.0.ps1 -Engine lualatex -OutputDir src\build\strict_current_r116_fullbook -NoPublish`.
- The build ended naturally with exit 0. Latexmk completed three LuaLaTeX passes and the two required makeindex rules. No retry, Resume, second parent call, manual engine call, package install, or source mutation occurred. The TeX lock was released and terminal TeX-family process counts were zero.

## Frozen R116 identity and whole-book audit

- PDF: `src/build/strict_current_r116_fullbook/main_full.pdf`.
- PDF: 4,967,281 bytes, SHA-256 `19F3D0413AD8C72B4D855B2C23246F10DD7ACECF2FD1E984AEE9F25E1051D3DC`.
- Log: 260,299 bytes, SHA-256 `38455041239C12F5671595EF38DDEBC808BBB8DF11A6CD05BFBCA3EDEA93DE9D`.
- TOC: 118,583 bytes, SHA-256 `EA5F09079A670A22A63FF08CDD061A3106E3999994963A9FBBD61CEC1C7E560D`.
- Main index: 23,734 bytes, SHA-256 `B32C889C28CAE7E4D6D7BB209D544715497AC7567C55435B9EF8B9851E7AB472`.
- Symbol index: 25,820 bytes, SHA-256 `E62CD6894BACCB383FAB12A058B9F83C91BE89AE6687104CF8D89E19CB7BC49A`.
- Page gate: 817/817 pages are `595.276 × 841.89 pt`, rotation 0; PDF 1.7, unencrypted, no JavaScript.
- Navigation gate: 273 bookmarks (`8/38/227` by levels 1/2/3), all chapters 1–37, all volumes 1–5, required symbol/topic indexes, 7,421 named destinations, 4,961 valid internal links on 816 non-cover pages, and no invalid bookmark or link.
- Font gate: 17/17 records embedded, subset, and Unicode-enabled.
- Final log gate: fatal/error, undefined reference/citation/control sequence, rerun, over/underfull box, missing glyph, duplicate destination, and missing font counts are all zero.
- Index gate: main `731 accepted / 0 rejected / 0 warnings`; symbols `355 accepted / 0 rejected / 0 warnings`.
- Independent audit result: `PASS`; `candidate_audit.json` is 4,829 bytes/SHA-256 `55EBB36C7B70102F015B3398FAA18BBF6EFE20140CE96142F647FEF5EAF6500D`.

## P126 official-page screen

- Current caption independently locates P126 at R116 physical page 137 / printed page 124 / Figure 8.1.
- Main rendered R115 and R116 physical page 137 at 300 dpi and actually opened the R116 full page, native figure/caption, grayscale figure/caption, label/path native and NN8× ROI, and legend native and NN8× ROI.
- Page text sequence is unchanged: 691/691 characters matched. For 560 downstream characters below 285 pt, horizontal coordinates are exact and the maximum vertical reflow is 0.599 pt; page integration remains clean.
- The corrected figure visibly uses rotated positive-definite quadratic contours and an alternating horizontal/vertical coordinate-descent path approaching the unique optimum.
- Legend pixel gate at native 300 dpi: `更新 x1` is one occupied 75 px run; `更新 x2` is four occupied 11 px runs with internal blank runs `11/10/10 px`. The distinction remains clear in grayscale.
- Labels 6 and 7, q-point markers, arrows, axes, contours, optimum marker, formula labels, caption, and neighboring page material are readable without a visible hard collision or clip in the opened native and NN8× views.
- Pixel report: `p126_r116_legend_measurement.json` is 785 bytes/SHA-256 `F75EA3D03C52A939EB53E9959DD460F1E5102D9146C51DC1FFC43790E714DC97`, result `PASS`.
- Text/page integration report: `p126_r115_r116_text_geometry.json` is 1,171 bytes/SHA-256 `C9F07B7028D15784EB86603357309336499B689A96DA83BC0FEC5C3CAC7E57FE`, result `PASS_PAGE_INTEGRATION`.
- This Main screen is a candidate-freeze gate, not a substitute for the required fresh role denominator, all-pairs manual ledger, semantic checks, or role-local seal.

## Fresh P126 SA1 authorization

Main authorizes exactly one completely fresh isolated SA1 and no other role:

- HANDOFF: `A-R116-P126-SA1-FRESH-ISOLATED-20260828`.
- Requested actual: `/root/p126_r116_fresh_sa1`.
- Model/effort: `gpt-5.6-sol/xhigh`.
- `fork_turns=none`.
- Fixed startup-absent root: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\STRICT_R18_SA1_FRESH_ISOLATED_R116_20260828`.
- Exact R116 PDF: 4,967,281 bytes/SHA-256 `19F3D0413AD8C72B4D855B2C23246F10DD7ACECF2FD1E984AEE9F25E1051D3DC`.
- Exact current P126 source: 4,686 bytes/SHA-256 `2887758F5CC94987BE750E1EC53B555FB88CE8F71B7260CABBE0A17DDF237405`.
- Exact current V1-C08 chapter: 59,218 bytes/SHA-256 `3C60FABCACA8BFC390323033F3CF6539CA5497EBF5A09641B8C4B78E81A0816C`.
- Parent must prove the fixed root absent immediately before spawn. The child must independently prove the same exact LiteralPath gate before reading any input or creating any root/artifact. Only after both gates may the same sole instance create the fixed root once and run to one sealed PASS/FAIL.
- The fresh prompt may contain only the exact R116 PDF/current source/current V1-C08 chapter plus current Goal-direct protocol resources. It must not expose any old P126 page, denominator, pair count, pixel metric, visual verdict, evidence path, SA2 result, or this Main visual-screen result.
- No restart, duplicate, replacement, second UID/role, TeX/build, source/Git/central write, process management, or directory-level fallback/search is authorized.
- Inventory remains `30 SA1 / 30 SA2 / 0 SA3 / 40 local pass` until the requested actual identity and both startup gates are returned and accepted by Main. At that point P126 may transition `SA2→SA1`.

## Boundary

No new source edit, commit, build, role, inventory migration, release publication, remote push, destructive Git action, or mutation of frozen P689/P126 evidence was performed after the R116 freeze. Strict final remains `0/99`; B remains `66/66`.
