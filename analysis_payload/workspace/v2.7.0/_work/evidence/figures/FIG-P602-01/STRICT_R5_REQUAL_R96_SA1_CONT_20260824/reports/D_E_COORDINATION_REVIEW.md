# R5 SA1 D/E source-size and coordination review

Canonical evidence directory: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\evidence\figures\FIG-P602-01\STRICT_R5_REQUAL_R96_SA1_CONT_20260824`.

## D — source size proof

The frozen figure source is `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C03\fig_v5_c03_mh_accept_reject.tex`, SHA-256 `18B88F4BC48A21D3FD1A246AC5B6909DEEB19900A3D0721C65F9A44369444084`.

The figure-level and every-node declaration is `\fontsize{9.6pt}{11.6pt}`.  The acceptance-ratio display intentionally raises its formula to `\fontsize{11.2pt}{13.6pt}`.  The 175-row `after_font_audit.csv` records `SOURCE_FONT_PASS=true` for every glyph; any extracted 6.695 pt natural mathematical script inherits a 9.6 pt base and is separately subject to its 15-px raw-script floor.  There is no graphics scale below 1.0 and no source base declaration below 9.5 pt.

**D result: PASS.**  This source-point-size conclusion is not a substitute for the stricter native-pixel C gate.

## E — visual coordination

The visual hierarchy is coherent in the direct final render and in grayscale: base nodes and edge labels share the 9.6 pt family, the ratio formula is intentionally larger, the decision diamond remains central, and accepted/rejected outcomes are symmetric around the branch point.  The serif CJK and STIX mathematical faces stay consistent inside their intended roles.  The six low-profile punctuation contexts were checked with same-codepoint/font/weight/color/effective-size calibration and all pass.

`element_level_ratio_audit.csv` and `same_class_ratio_audit.csv` are retained as diagnostics.  Their outline-height medians should not be interpreted as a generic typography pass/fail rule: they deliberately aggregate unlike outlines (for example CJK ideographs, italic letters, parentheses, fractions, and caption text), which have different raw ink heights even at the same declared size.  D/E was instead judged by source strata, semantic role, and the complete native visual overlay.  No accidental role-level font-scale drift was found.

**E result: PASS.**  The strict overall gate remains failed because section C reports mandatory final-PDF glyph floor and mask-ownership failures; D/E cannot waive those facts.
