# FIG-P634-01 caption effective-font chain

1. `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\讲义源码\第05册_采样方法主题模型与图排序\main.tex` line 3 selects `ctexbook` at `11pt`.
2. `D:\texlive\2026\texmf-dist\tex\latex\base\size11.clo` lines 58--60 expand `\small` to `\@setfontsize\small\@xpt\@xiipt`: declared caption base is 10.0 pt (12 pt leading).
3. `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\讲义源码\common\statlearnbook.sty` line 305 applies `\captionsetup{font={small,stretch=1.12},...}`; stretch changes leading, not the 10.0 pt glyph size. Lines 244--245 load caption/subcaption.
4. `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C04\fig_v5_c04_coordinate_sweep.tex` line 60 only sets width `.94\linewidth`; line 61 emits the caption and does not override its font or apply scale.
5. Therefore FIG-P634-01 caption declared_pt=10.0, graphics_scale=1.000, effective_pt=10.0. Caption math base is 10.0 pt; `statlearnbook.sty` line 295 declares the 10pt math ladder as 10/9/9, so its legal scripts are 9.0 pt and are checked at raw H_ink >=15 px.
6. Final-PDF span sizes are retained only as an output cross-check in raw_char_measurements.csv, not used as the declared/effective source-font proof.
