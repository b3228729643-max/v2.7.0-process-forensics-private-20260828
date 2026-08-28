# FIG-P654-01 local SA2 主线验收与集成

- 主线验收时间：`2026-08-25T00:35:31+08:00`
- A 源提交：`e392bd8e5f37dfd49f071f7251c281d46bb68ffd`
- 主线集成提交：`81d7c7ad150a9306ae3599fe9c15f4c8bb125d9a`
- 唯一源码：`src/绘图源码/第05册_采样方法主题模型与图排序/V5-C05/fig_v5_c05_dependency_graph.tex`
- 源 SHA-256：`8041DAF98B04D763958DA9C83AF3472FA346D003F0FDCEF13A42FE1AA046B5F8`
- 路由：`LOCAL_SA2_PASS_AWAIT_FRESH_R100_SA1`

## 主线独立机械复核

- 提交父项、单文件范围、21 insertions / 23 deletions 与 `git diff --check` 均符合 handoff；主线集成后源 SHA 与封存值相同。
- P654 封存 manifest 938/938：相对路径唯一、无逃逸、missing=0、size mismatch=0、SHA mismatch=0；列示字节与声明均为 228,488,229。
- 实际普通文件 940，精确等于 manifest entries + manifest + `WRITE_STOPPED`；extra=0、ADS=0。
- `WRITE_STOPPED` 比 manifest 晚 8,521.4315 ms，严格为最后写入。
- N=116（95 glyphs + 21 paths），6,670/6,670 unordered pairs；terminal 53 checks / 0 failures。
- 本地整页、300 dpi crop、standalone、grayscale 与文字测量框由主线打开目检，未见裁切、非法碰撞或语义布局缺陷。

## 官方候选

- R100：814 页，4,943,206 bytes，SHA-256 `5B1E4B4C5D64A0CA49833F38ED28C4397392BF5E50503431F3170614DF63D171`。
- 官方物理页 702 的页面集成视觉 PASS；构建、索引、日志、A4、导航与字体门全部 PASS。
- 已向 Dialogue A 发出全新隔离 SA1 指令；在 fresh SA1 和随后必要的隔离 SA3 闭合前，不计 `A_LOCAL_PASS`。
