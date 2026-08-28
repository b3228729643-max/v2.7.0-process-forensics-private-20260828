# R532 — P126 R13 STATIC acceptance and one direct-build authorization

## Main adjudication

- Accepted status: `STATIC_ONLY_NOT_RENDERED_NOT_PASS`.
- P126 remains `SA2`; preserved business defect remains `HARD-LEGEND-X2-CONTINUOUS` until a newly built PDF passes a full non-TeX review.
- P689 remains the already accepted same fresh SA3 instance and is not migrated in this revision.

## Source-scope verification

- Sole source: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_A_visual\src\绘图源码\第01册_数学基础与统计学习基本理论\V1-C08\fig_v1_c08_coordinate.tex`.
- Current identity: 4,626 bytes / SHA-256 `6CBAEBE50574E541A04B2FDCC74B432C49AF2590B579C6A85721EDF536912502`.
- Exact new block occurrence: 1; old block occurrence: 0.
- In-memory exact reverse replacement restores 4,373 bytes / SHA-256 `81EFC188FA5E4827CAAB034C1EA3F7F4AFE25375DEE4046CD46F3FF49B0789BD`.
- Git remains one modified target, index empty, aggregate numstat 33+/26-, `git diff --check` PASS.
- The incremental replacement consists only of the old two-line x2 `addlegendimage` and the adjacent uniquely named `p126 x2 disconnected legend` style plus its invocation.

## Handler and gap verification

- The handler contains four independent `\draw` commands over `[0,.06]`, `[.18,.24]`, `[.36,.42]`, and `[.54,.60]` cm.
- It contains no `only marks`, `mark=-`, or dash-pattern dependency.
- Nominal gaps are 0.12cm. Subtracting one full 1.05pt line width gives 0.0830967206cm / 9.814573px at 300dpi for every gap, above the required 0.05cm / 5.905512px.
- Installed primary source `D:\texlive\2026\texmf-dist\tex\generic\pgfplots\pgfplots.code.tex` is 486,348 bytes / SHA-256 `C4245419E40E5058320853728F6BB93521C153D89F1FBF185CE8793D067C1CA6`.
- Its lines 2007–2030 define the default continuous line legend; lines 5794–5796 store the `addlegendimage` plot spec; lines 5843–5848 activate current plot style before invoking legend image code; line 11488 applies the stored style. The custom absolute `/pgfplots/legend image code/.code` therefore replaces the default path at legend generation.

## R13 sealed-root acceptance

- Root: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\STRICT_R13_SA2_STATIC_DISCONNECTED_LEGEND_HANDLER_R115_20260828`.
- Files 13 = payload 10 + controls 3; subdirectories 0; files and root all ReadOnly.
- `PAYLOAD_MANIFEST.csv`: 10 rows / SHA-256 `4AB918ABC8C9BD8FB58995DFBFF2333550E0F6E4EE03470155E43B5125040DB0`; duplicate/set/path/bytes/SHA/Creation/LastWrite mismatch 0.
- `SEAL_AUDIT.json`: SHA-256 `6E62EB7234DC630A6621FCF5E8028F10005D2C6B78A7F8C8A17B39DFC8D41E9F`.
- `WRITE_STOPPED`: 699 bytes / SHA-256 `DA6E03A9D862163D01407BBCA3C5176922151F119C97492E1FD22D723472A49F`; 19 physical lines / 19 unique keys / bad 0 / duplicate 0 / BOM false; manifest, seal and count bindings exact.
- Marker strict-latest margin including root: 2,999,895,811 FILETIME ticks; at-or-after excluding marker 0.
- ADS / JSON parse / CSV parse / pyc / cache / reparse failures: 0 / 0 / 0 / 0 / 0 / 0.
- Main's first read-only audit expression used an unsupported `Measure-Object` hashtable property and stopped without any write. The corrected per-item FILETIME recomputation returned `OverallPass=true`.

## One controlled build authorization

- HANDOFF: `A-R115-P126-SA2-DIRECT-BUILD-R14-20260828`.
- Fixed fresh root: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\STRICT_R14_SA2_DISCONNECTED_LEGEND_HANDLER_R115_DIRECT_BUILD_20260828`.
- Main immediate gate: Leaf=false, Container=false, Any=false, Parent=true.
- Preflight process counts: latexmk/lualatex/luatex/luahbtex = 0/0/0/0.
- Authorized counts: one root-external controller invocation and one direct LuaLaTeX child invocation; retry/latexmk/version-probe/second invocation = 0/0/0/0.
- `TEXMFVAR`, `TEXMFCACHE`, `TEXMFCONFIG`, and `TEXMFHOME` must resolve to the same fresh R14 `texcache`.
- First error stops. Natural success must yield exactly one PDF and release the slot. Thereafter no TeX is allowed; A may perform only one full non-TeX review/manual/single-seal chain from that PDF, explicitly measuring the x2 legend as four occupied runs separated by at least three blank runs meeting the 300dpi gate, plus the frozen full regression.
- No source edit, commit, fresh role, second UID, or central-state write is authorized.
