# Revision 274 — P582 fresh SA3 FAIL 接受与单坐标修复范围

时间：2026-08-27T00:05:16+08:00  
官方候选：R109，physical632 / printed619 / Fig31.7。

## Root acceptance

- 正式接受 `A-R109-P582-SA3-FRESH-ISOLATED-20260826` 的 `FAIL_TO_SA2`。
- 最终N156=139 glyph+17 foreground paths，C=12,090；语义重算全PASS。
- 唯一真实硬失败：P05555 / T042蓝色down-arrow与T062 `.380`末位0在native300dpi shared14px、clearance0。P04848/P05554仅advisory。
- 主线已实际打开P05555 native1x、nearest8x及contact sheet，确认箭头尖端侵入数字0；撤回Revision270中沿用SA1的“可见白隙”方向，以fresh SA3和主线当前原生复核为准。
- sealed root=563 payload+5 controls=568；568/568文件只读，manifest/hash/size/mtime、ADS/cache/pyc/reparse/postmarker/manual time均PASS，WSTOP严格最后+11,583,531 ticks。report/handoff SHA与回报一致且只读。

## Authorized source scope

唯一允许修改：

`src/绘图源码/第05册_采样方法主题模型与图排序/V5-C02/fig_v5_c02_running_mean.tex`

精确一行坐标：

```tex
at (axis cs:3.58,.49) {$\downarrow$ 再下降};
```

改为：

```tex
at (axis cs:3.58,.53) {$\downarrow$ 再下降};
```

即保持x、文本、字号、颜色、公式与全部其他源码不变，仅把整条“↓ 再下降”标注上移0.04轴单位。预期原生垂直位移约数十像素，足以消除14px交叠并保留与顶部公式/边界的安全余量。

## Gates

- static-only阶段：精确1文件1+/1-；`git diff --check`；确认其余diff=0；验证标注、`.380`、曲线、数据、题注、字号与全局样式token均未变。
- static冻结后回 `P582_SOURCE_COORDINATE_PATCH_READY_REQUEST_BUILD_SLOT`；未获显式构建槽不得TeX。
- 新PDF必须从零复核P05555、邻近`.380`/箭头/“再下降”、全图对象与pair、灰度/页面融合；不得迁移R4人工结论。
- 不授权字体变化、数值/曲线/公式变化、其他坐标、共享样式、第二源、提交或第二UID。

## Inventory

P582 `SA3→SA2`；P630保持SA1。当前 `32 SA1 / 47 SA2 / 0 SA3 / 20 local pass`，严格最终0/99。
