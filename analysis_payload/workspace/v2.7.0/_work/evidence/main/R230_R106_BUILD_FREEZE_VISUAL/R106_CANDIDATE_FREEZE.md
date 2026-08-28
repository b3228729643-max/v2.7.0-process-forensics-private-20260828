# R106 官方候选冻结

- 状态：`OFFICIAL_CANDIDATE_FROZEN / BUILD_LOCK_RELEASED`
- 主线提交：`137342439ac0a7db6cb27bc99337da0d2ea2f902`
- 主线工作树：clean
- 构建：唯一 `build_v2.7.0.ps1 -Engine lualatex -OutputDir src\build\strict_current_r106_fullbook -NoPublish` 父链，自然收敛，exit 0，无并发、重试或中止
- 终态进程：`latexmk/lualatex/luatex/luahbtex = NONE`
- PDF：`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r106_fullbook\main_full.pdf`
- 身份：817 页，4,967,249 bytes，SHA-256 `0FA4A5A0B35D2566D71B5472B49E9B4A8A60CBAE76B3FA744B92783AFC6BC31A`
- 格式：A4 595.276×841.89 pt，rotation 0，PDF 1.7，未加密，Suspects=no
- 日志：258,877 bytes；硬 TeX 错误、undefined refs/citations、missing I/O、memory exhausted、missing characters、duplicate destinations、rerun、overfull、underfull 均为 0
- 索引：主索引 731 accepted / 0 rejected / 0 warnings；符号索引 355 accepted / 0 rejected / 0 warnings
- P640 定向视觉：物理页 690 整页与 300dpi 右图裁图均已打开；极限注记 `N_eff/N→0` 与金色曲线可见分离，右下 open marker 与 `.99` 刻度保留可见白隙，无裁切、融合或页面回归
- 视觉文件：`page_690.png`、`page_690_p640_crop_300dpi.png`
- P715 R168 只读复判：R105 物理页 765 的标题末字 `一` 为连续完整单横画，旧 6px 像素门仅 advisory；当前源无需修改或 TeX，下一步直接在 R106 上启动 fresh isolated SA1
- 冻结时间：2026-08-26T08:28:42+08:00

R106 自本记录起取代 R105，成为唯一官方候选。严格最终完成仍为 0/99；本记录不把 P640 或 P715 计为 A_LOCAL_PASS。
