# FIG-P630-01｜候选串行 SA2 最小修复规格

状态：`QUEUED_AFTER_ROOT_ACCEPTED_FAIL_AND_CURRENT_SOURCE_WRITER_RELEASE`。root已接受SA1失败，但P608交权前仍不授权P630源码写入。

## 候选、白名单与候选失败

- 当前官方候选R98：813页、4,934,249 bytes、SHA-256 `52FA2EF0769553C8B6FD4B8D3CBA5BE671FA0F3190591A596FB8B6512C108A41`。
- 图33.1定位为物理页678／印刷页665；R97→R98仅物理页591变化，故该页与审查用R97逐页栅格相同。
- 唯一候选业务源：`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C04\fig_v5_c04_dependency_graph.tex`；当前SHA-256 `746163570B90750C1BE9731029C450B2F800D43296075FC22D71B9D9F72F2E43`。
- root已接受的SA1硬失败：`GLYPH-013` U+2212，3px＜22px；`GLYPH-022` U+22C5，5px＜22px；`GLYPH-025` U+2212，3px＜22px。三者都是语义数学operator，来自节点中两次`x_{-j}`与一次`\cdot`。

## 允许的最小修复方向

1. 若root最终接受上述失败，下一SA2优先用自然、语义等价的节点文案消除低轮廓数学符号依赖，例如把“给定`x_{-j}`的满条件 / `\pi_j(\cdot\mid x_{-j})`”改写为“给定其余坐标 / 第`j`个满条件`\pi_j`”或同等清楚的短语。最终措辞须准确表达Gibbs满条件，不得削弱数学含义。
2. 不得添加隐藏/透明字符、伪造参照、把符号加粗成突兀色块、整体缩放/拉伸，或用白底、halo、裁切、z-order遮问题。普通有效字号仍须≥9.5pt，节点宽高、箭头净空和整页版式必须协调。
3. 若保留U+2212或U+22C5，则必须在下一官方候选的原生300dpi中满足对应硬阈值及纯净mask，不能依赖四舍五入或视觉豁免。
4. 修改后必须从头重建当前协议：100% glyph、全部drawing/path、对象N与N choose2全pair、critical卡、裁切/遮挡、灰度、D/E和字体层级；每个glyph/graphic实际打开原生1×与至少8×。不得迁移旧P630 PASS字段。
5. 局部全门PASS只写`SA2_LOCAL_PASS_TO_ROOT_BUILD_NOT_FINAL`；root构建下一官方候选后，再走全新SA1、隔离SA3与root签发。封存顺序terminal→manifest→`WRITE_STOPPED`最后写，stop后0写入、0-byte=0、ADS=0、集合严格相等。
