# FIG-P634-01 候选无源码变更说明

DECISION: `SOURCE_HOLD_FOR_ROOT_METHODOLOGY_REVIEW`  
SOURCE_FILE: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C04\fig_v5_c04_coordinate_sweep.tex`

## 源码 before/after diff

```text
before: current R93-backed source
after:  current R93-backed source
diff hunks: 0
lines added: 0
lines deleted: 0
lines modified: 0
```

本 SA2 没有对该图源执行写入或补丁。没有修改相邻 `V5-C04.tex`、公共样式、正文、合并入口、wrapper、build 或中央状态。

## 为什么没有为了“显示工作”而改图

1. 当前基准字号为 9.6 pt，标题 10.6 pt，轮内状态卡 10.0 pt，图例 9.8 pt，题注 10.0 pt；源级硬门和同角色源比例已满足。
2. 编号顺序、新旧值边界、`x^[j]` 与 `x^[d]=x^(t)` 语义准确，且与相邻正文一致。
3. R93 全对象实测为 overlap 0、clip 0、独立文字净空 31 px、文字—图形净空 13 px、边缘 16 px；不存在需要移动对象才能修复的几何故障。
4. 剩余 23 项均为短横、等号、逗号、省略号的自身墨迹高度。孤立纵向拉伸会产生约 2–15 倍畸形，破坏视觉层级；本轮明确禁止这样处理。
5. root 尚未裁决这些横向/低矮字形的统一 `H_ink` 口径。在裁决前改写标签或公式存在语义、全书一致性和角色比例风险。

## 不是 `NO_CHANGE_REQUIRED`

该说明只证明“本 SA2 没有提交源码候选差异”，不等于最终无需修改。正式状态仍是 `PARTIAL_METHODOLOGY_REVIEW`；root 裁决后才能决定保留现源或重新授权结构性最小修复。

## 证据变更

专属证据目录新增/更新了诊断脚本、原生视图、131 对象台账、23 项失败清单、58 套运算符三件套、比例/净空/边缘报告以及正式 SA2 报告。这些文件不改变生产源码或构建产物。
