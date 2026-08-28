# R89 官方全书页稳定性核验

- Build: `v2.7.0/_work/source/v2.7.0/build/strict_current_r89_fullbook/main_full.pdf`
- Result: PASS
- Pages: 813 (A4)
- Bytes: 4,933,622
- Hard log patterns: 0 matches for LaTeX/Package error, `Float(s) lost`, undefined control sequence/reference, emergency/fatal stop, rerun warning, and overfull h/vbox.

本次官方增量构建仅纳入 FIG-P020-01 的局部箭头字号 R4 改动。AUX 中 P020/P578/P632/P756 仍分别为图 1.1/31.5/33.2/37.8，印刷页 4/613/667/788；物理页分别为 17/626/680/801。

## 已严格关闭图的连续页稳定性

- P632：从 R89 官方全书物理页 680 原生渲染 300 dpi，与 `FIG-P632-01/STRICT_FINAL/fullbook_page_300dpi.png` 比较；尺寸均为 2481x3508，差异像素 0，最大通道差 0。
- P756：从 R89 官方全书物理页 801 原生渲染 300 dpi，与 `FIG-P756-01/STRICT_FINAL/full_page_300dpi.png` 比较；尺寸均为 2481x3508，差异像素 0，最大通道差 0。

因此 P020 的本次修改没有使 P632/P756 的严格连续页证据失效。此稳定性结论只覆盖这两个已关闭图，不代表其余图或全书发布验收完成。
