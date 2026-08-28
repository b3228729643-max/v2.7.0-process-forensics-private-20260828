# R01 current-input identity and isolation gate

- HANDOFF_ID: `C-FIG-P680-01-R114-SA2-R168-READONLY-ADJUDICATION-V1`
- UID: `FIG-P680-01`
- actual instance: `/root/sa2_fig_p680_r114_r168_readonly_v1`
- model / effort: `gpt-5.6-sol / xhigh`
- sealed root: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P680-01\sa2_r114_r168_readonly_adjudication_v1`

Before any root or artifact creation, the exact child root and exact UID parent were independently tested with `-LiteralPath`. Both returned `Leaf=False`, `Container=False`, and `Any=False`. The fixed child root was then created by the single exact operation `Path(exact_root).mkdir(parents=True, exist_ok=False)`; no alternate root or trial creation command was used.

Current allowlisted identities observed once at R01:

| kind | exact path | bytes | SHA-256 | match |
|---|---|---:|---|---|
| official R114 PDF | `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r114_fullbook\main_full.pdf` | 4,967,122 | `C3BB9B1C7FC9D7AF9178CD33F227F24899AA505FAB81840DB6E3AD8BD6CE78A6` | exact |
| current figure source | `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C06\fig_v5_c06_dependency_graph.tex` | 3,144 | `76474E18D9E735283274AF614DFAE606BA3683BDA2539168AC91920DDE6E22BA` | exact |
| exact chapter context | `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\讲义源码\第05册_采样方法主题模型与图排序\chapters\V5-C06.tex` | 120,809 | `7276DDB767246292D0924D1651D560975E0FE6D2ACE47CBAEC4EE45CEB4A0029` | exact |

The target was independently located inside the current R114 PDF by the current source/caption anchor `模型与后验不同`: physical PDF page 729, zero-based page index 728, printed page number 716, figure 35.1. No UID-number-to-page assumption was used.

R168 is controlling: historical numeric font/pixel/ratio thresholds are advisory and cannot alone hard-fail. Hard failure is limited here to a current-PDF missing/tofu/wrong codepoint, actual unreadability or severe imbalance, real clipping, illegal visible-ink overlap, or a mathematical/semantic/geometric error.

