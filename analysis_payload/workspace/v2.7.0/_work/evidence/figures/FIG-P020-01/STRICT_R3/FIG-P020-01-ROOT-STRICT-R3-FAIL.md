# FIG-P020-01｜根线程严格证据失败（R3）

- RESULT: **FAIL**
- FAILURE_CLASS: `PIXEL_HEIGHT`
- NEXT_ROLE: `SA2`

正式连续版物理页 17 已由当前官方 813 页全书构建提取并以原生 300dpi 渲染。13/13 字号源级记录 PASS；13 个像素元素中 12 个 PASS，唯一失败为 `E02-RELATION-ARROW`：源码第 15 行的局部 `\to` 有效字号 13.4496pt，但实墨高度仅 21px，低于基础数学符号 22px 硬门。

其他可见文字最低有效字号 9.9626pt；四个节点标题为 10.4608pt，正文/注释/图注为 9.9626pt。CJK 实墨 35--40px，图注数字 26px，字号层级未见突兀。全书日志无 LaTeX 致命错误、`Float(s) lost`、未定义引用或 overfull；AUX 含 `fig:V1-C01-language-flow`（图 1.1、印刷页 4），图真实落在物理页 17。

本候选因 21px 数学箭头单项失败而总 FAIL，不生成 overlap 最终结论，不进入 SA1/SA3。白名单仅允许 SA2 微调该局部 `\to` 字号；不得修改节点、正文、路径、版式、caption/label 或公共文件。

