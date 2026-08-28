# R348 — P067 R111 SA2 FAIL acceptance and narrow static source scope

Timestamp: `2026-08-27T14:16:24+08:00`

## Main decision

Main independently accepts `A-R111-P067-SA2-R168-READONLY-20260827` as `FAIL_TO_MAIN_SOURCE_SCOPE`. The single genuine hard defect is `REL006`: the lower PMF y-axis labels `0.35` and `0.3` visibly overprint. This is not an R168 source-size, taxonomy, or micropixel objection.

Accepted immutable root:

`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P067-01\STRICT_R1_SA2_R168_READONLY_R111_20260827`

## Independent acceptance basis

- Main actually opened the current native figure crop, atomic overlay, exact native-300-dpi tick ROI, and nearest-neighbour 8x tick ROI. The two labels cross visibly in color and remain ambiguous at 8x; the upper/lower strings cannot be read as two separate same-role ticks.
- Native label boxes penetrate vertically by 18 px. Their shared 51x18 px region contains 327 foreground pixels; nearest8x preserves a 408x144 px / 20,928 px collision. Mask contamination is zero.
- All other PMF/CDF facts pass: masses `0.15+0.30+0.35+0.20=1`; CDF levels `0.15/0.45/0.80/1.00`; monotonicity, right continuity, open/closed endpoints, panel meanings, caption, clipping, and page integration are coherent.
- Fresh denominator and pair closure independently recompute as N145=`95 glyph+50 foreground path` and C10440, with 145 unique IDs and 10,440 unique unordered nonself ordered keys. Manual ID ledger is 145/145 with no blank or missing row; critical ledger is 16/16 unique and nonblank, distributed as 14 PASS, one `ADVISORY_ONLY`, and one `FAIL_TRUE_COLLISION`.
- Root-external sealed manifest contains 42 unique rows and matches all 42 root files in path, bytes, SHA-256, creation/last-write NTFS ticks, and attributes; all 42 files and five directories including root are ReadOnly. `WRITE_STOPPED` is unique and strictly latest by about 555.905 million NTFS ticks with zero nonmarker item at or after it. JSON/CSV, ADS, cache/pyc, and reparse gates are clear.
- External report SHA-256 `3BB8C8034443871E44BE901D23EEE0CFB8E6F6C9CBF320F16D6FC1DBF3CFF4FF`, handoff SHA-256 `14E8F37A8FF37D247FDE25560558319B8D21B46B3F85B4F51847D0C2911D0A`, root-audit SHA-256 `A7B922E33AF03E79DD35EAFD846E1E11AB42D60F37E813DCCED6CF38D8FCB1ED`, and sealed-root manifest SHA-256 `97A73B259A84E0C348D58F6561306C921134547A175BD8EF05B74BBFAD53C6A1` match the immutable artifacts.

## Narrow static-only source authorization

A is authorized to edit exactly one file:

`src/绘图源码/第01册_数学基础与统计学习基本理论/V1-C04/fig_v1_c04_cdf.tex`

Baseline identity: 3,866 bytes / SHA-256 `03372740AB8015EFFB7BC6CFBBDC669A1E8FBF52246291491B1B0C506513B864`. The main worktree is clean at HEAD `b819e9f4810a2afc04d24a2f0b8bdaa2a3ccb079`; TeX-family process count is zero. Static evidence root `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P067-01\STRICT_R2_SA2_STATIC_TICK_LABEL_PATCH_R111_20260827` is file/dir absent at authorization.

Allowed change is limited to the lower PMF axis presentation of the adjacent `0.30` and `0.35` y-tick labels. Both values and both tick positions must remain visibly present and correctly associated. Preferred narrow mechanism is to suppress only one automatic label and reinsert the identical text at the same tick using a minimal explicit offset proven statically to create real native clearance; an equally narrow per-label placement mechanism is permitted. Do not remove either value, change the four PMF coordinates, CDF coordinates/levels, axes meanings, panel order, open/closed markers, caption/label/alt, font declarations, colors, strokes, or unrelated geometry. Do not use a global scale, resize, font reduction, or a broad panel-layout rewrite.

This authorization is `STATIC_ONLY_NOT_RENDERED_NOT_PASS`. A must produce an exact one-file diff, before/after identity, diff-check, source-level mechanism proof, predicted clearance and page-fit regression assessment, and an immutable static root/report/handoff. TeX/LuaLaTeX/latexmk, build, commit, fresh role, second UID, second source, and central state/inventory writes are forbidden. After Main accepts the static patch, A may request exactly one controlled standalone/direct build slot; it must not self-start it.

P660 fresh isolated SA1 continues independently and must not be interrupted or exposed to this P067 result.
