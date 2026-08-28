# FIG-P126-01 R15 static `forget plot` patch

- HANDOFF: `A-R115-P126-SA2-STATIC-FORGET-PLOT-PATCH-20260828`
- STATUS: `STATIC_ONLY_NOT_RENDERED_NOT_PASS`
- Sole source: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_A_visual\src\绘图源码\第01册_数学基础与统计学习基本理论\V1-C08\fig_v1_c08_coordinate.tex`
- Authorized before: 4,626 bytes / SHA-256 `6CBAEBE50574E541A04B2FDCC74B432C49AF2590B579C6A85721EDF536912502`.
- Current after: 4,686 bytes / SHA-256 `2887758F5CC94987BE750E1EC53B555FB88CE8F71B7260CABBE0A17DDF237405`.
- In-memory removal of the five exact `,forget plot` additions reconstructs the authorized before bytes and hash exactly.

## Exact incremental scope

Exactly five existing option lists changed, each by one `forget plot` token:

1. line 20, outer gray contour;
2. line 22, second gray contour;
3. line 24, third gray contour;
4. line 26, inner gray contour;
5. line 56, square-marker plot.

The incremental diff is exactly `5+/5-`. All five plots retain their existing options, data, coordinates, and rendering semantics; only legend-list participation changes. Every other token—including both manual `\addlegendimage` commands, the disconnected x2 handler, legend entries/style, q0–q7, contours, arrows, markers, labels/backgrounds, axes, fonts, math, caption, label, alt text, shared macros, and build entry—is unchanged.

## Installed pgfplots causality

- `pgfplots.code.tex` lines 4249–4250 define `forget plot` as the `pgfplots@curplot@isirrelevant` switch.
- `pgfplotscoordprocessing.code.tex` lines 5121–5132 apply plot options before testing that switch.
- Its lines 3716–3720 remember a normal plot spec only in the non-irrelevant branch.
- `pgfplots.code.tex` lines 5794–5796 append each manual legend image spec.
- Its lines 5721–5739 and 5760–5768 consume remembered plot specs in list order when pairing legend entries and images.

The current source has five ordinary plots and all five now contain `forget plot` exactly once. Therefore their specs are excluded from the legend list. The two unchanged manual images become the only remembered legend specs and pair, in order, with the two unchanged entries. This explains the R14 failure and statically closes the intended mechanism, but it does not prove the rendered x2 gaps; a new PDF is still required.

## Git boundary

- Worktree name-only: exactly the P126 source.
- Index: empty.
- Aggregate diff: one file, `38+/31-` (the five-token increment sits on top of the previously authorized P126 aggregate patch).
- `git diff --check`: PASS.

No TeX/build, commit, fresh role, second UID/source, or central state write was performed.
