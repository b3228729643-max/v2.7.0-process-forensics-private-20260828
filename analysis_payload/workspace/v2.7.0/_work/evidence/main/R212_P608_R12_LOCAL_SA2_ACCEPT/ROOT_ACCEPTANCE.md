# R212｜FIG-P608-01 R12 local SA2 PASS 中央接受

- 裁决：`LOCAL_SA2_PASS_AWAIT_OFFICIAL_CANDIDATE_AND_FRESH_SA1`
- 源补丁：唯一 P608 图源，`xmin=1,xmax=20` → `xmin=0.5,xmax=20.5`，1+/1-。
- source before/after SHA-256：`78C30F4A934F63E0EF1BBACF400A24F22477D38589F99503AE468F7024A35C05` / `49A683AEEC94AFD71AE33E95D4DF51BA3CC722F10B432B065FDBD2E45898635E`。
- 新单页 PDF：43,012 bytes，SHA-256 `A50EE094843FDA68A3E3CDCFA0F5DC1F4884B1FDA853A6B3BECEE7DB2758452A`。

R12 从新 PDF 闭合 N128=68 glyph+60 graphic、C8128/8128、critical12；empty mask、illegal overlap、clearance flag、clip、R168 hard readability 均 0。原失败 PAIR-06596/06650 共享像素均 0，净距分别 16.464px/12.928px；主线已打开 raw1x/overlay8x 确认首 marker 与 y-axis/y-arrowhead 原生分离。15 个 running means 与 `t20=2.0000` 保持正确；数据、标签、题注和双面板语义无变化。

机械封存：CSV/JSON manifest 各353，payload353/control3/ordinary356；manifest双方及FS的path/bytes/SHA/exact ticks差0；356/356只读，ADS/cache/pyc0，manual critical/view=14/17且时间失败0，WSTOP严格最新10,438,856 ticks，封后0写。

中央接受该本地SA2结果并授权唯一P608单文件原子提交；它仍不计A_LOCAL_PASS，不得从本地PDF启动fresh角色。提交集成主线并冻结下一官方候选后，才可派完全fresh isolated SA1。

