# FIG-P608-01 R99 fresh SA1 失败主线接收

- 主线接收时间：`2026-08-25T00:35:31+08:00`
- 官方输入：R99，814 页，SHA-256 `E8D76EEF0D120C518FA94A8F339BF6777AD18AA6AF0BCC17DFB46DF6DFC49EC6`
- 接受包：`STRICT_R5A_SA1_FRESH_R99_METADATA_RESEAL_20260824`
- 路由：`FAIL_TO_SA2`

## 主线独立机械复核

- R5→R5A 复用 ledger 794/794：relative path 唯一、无逃逸，源/目标 missing=0、size mismatch=0、SHA mismatch=0、源目标字节不一致=0。
- R5A 实际普通文件 802；其中 794 项复用证据与 8 项 reseal/交接文件闭合；ADS=0。
- `WRITE_STOPPED` 严格晚于最后其他文件 1.7512011 秒。
- N=170（112 glyphs + 58 paths），14,365/14,365 unordered pairs，manual objects 170/170，critical pairs 13/13。

## 设计结论

- 唯一设计失败为 `GLYPH_0025` 与 `GLYPH_0056`：两枚 natural-script `t` 的原生 300 dpi 实墨高均为 10 px，小于 15 px 门。
- final illegal overlap/pair failure/clip 均为 0；D/E、标点校准、语义和所需视图均 PASS。
- 不启动 SA3，不计 `A_LOCAL_PASS`；中央 inventory 将 P608 从 SA1 转入 SA2，Dialogue A 已获得候选冻结后的唯一受控构建槽。
