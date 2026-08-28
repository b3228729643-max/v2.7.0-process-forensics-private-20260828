# FIG-P608-01｜下一唯一 SA2 最小修复任务规格

状态：`QUEUED_NOT_STARTED`。本文件只准备任务边界，不授权并发源码写入，也不构成修复或视觉验收。

## 固定候选与唯一白名单

- 当前官方候选：`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r98_fullbook\main_full.pdf`
- 候选身份：813页、4,934,249 bytes、SHA-256 `52FA2EF0769553C8B6FD4B8D3CBA5BE671FA0F3190591A596FB8B6512C108A41`。
- P608 定位：物理页659／印刷页646／图32.8。R97→R98唯一变化页为591，因此P608页面在两候选间逐页栅格相同。
- 唯一可改业务源：`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C03\fig_v5_c03_trace_running_mean.tex`
- 修复前源身份：2,837 bytes、SHA-256 `DA035C1920CB900E54D3658851C1D71D9C6446531EFF50BEE6E089B567835AE4`。
- SA2只能写该业务源和一个新建的唯一SA2证据目录；不得写正文、公共样式、其他图源、中央库存/状态或官方全书构建目录。任一时刻最多一个业务源码写者。

## 已由独立 SA1 与 root 共同确认的硬失败

- `G008` `=`：原生300dpi H_INK 12px＜22px。
- `G019` `=`：11px＜22px。
- `G027`、`G058`自然脚本`t`：各10px＜15px。
- `G063` `运`：混入上面板刻度对象`G005`的16个外来像素；这是跨面板碰撞的字形污染结果。
- `P2311`下方面板标题`T027`与上面板x轴`G001`：净空2px＜8px。
- `P2315`同一标题`T027`与上面板刻度`G005`：实际重叠16px、净空0。
- `P3071`上面板x轴`G001`与下方标题overbar数学规则`R002`：pre-z-order共享64px、final-visible净空0px＜8px，并有0.044765pt矢量穿透。

## 修复约束

1. 先从当前源和官方页独立复现失败；不得复制旧mask、手填旧PASS或把paint order当成净空。
2. 只做局部结构修复。优先测试增加两面板有效垂直净空、微调标题位置/锚点或在不破坏整页版心时适度调整面板几何；不得用白底、halo、opacity、裁切或z-order遮住冲突。
3. 两个矮`=`和两个脚本`t`须以语义保持的TeX/TikZ结构提高原生有效轮廓；允许适度调整字号或数学层级，但普通可见文字仍须≥9.5pt、脚本/关系符满足像素硬门，且不能显得突兀。禁止整图粗暴放大、拉伸、位图替换或把符号改成不同含义。
4. 图中五个目标参考线/运行均值标记关系仅能按`t=10/15/16/18/19`五项逐一源码锚定为`INTENTIONAL_DATA_RELATION`；不得扩成类别白名单。
5. 修改后必须从头重建当前schema证据：100% glyph；全部前景drawing/path；rawdict外的overbar等`GRAPHIC/MATH_RULE`；对象总数N与`N choose 2`全pair；遮挡反演；裁切；300dpi原生1×和至少8×nearest；灰度、色弱、线宽、字体层级及整页协调。自动统计只能辅助，所有字形、图形对象和失败/临界关系都要实际开图并逐行记录。
6. 任何硬失败、缺失对象/规则、空或污染mask、未打开证据、低于阈值、字号突兀、封存集合不闭合均写`SA2_LOCAL_FAIL_CONTINUE`。局部全门通过也只能写`SA2_LOCAL_PASS_TO_ROOT_BUILD_NOT_FINAL`，由root构建下一官方候选后再走全新SA1与隔离SA3。
7. 封存顺序必须是底表/图片→terminal JSON/MD→manifest→最后写`WRITE_STOPPED`；stop后零写入、0-byte=0、默认数据流外ADS=0、manifest与实际集合严格相等。
