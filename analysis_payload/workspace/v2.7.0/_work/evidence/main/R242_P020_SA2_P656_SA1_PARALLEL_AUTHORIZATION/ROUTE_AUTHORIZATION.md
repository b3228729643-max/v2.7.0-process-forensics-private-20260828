# Revision 242 路由授权

时间：2026-08-26T16:03:02+08:00

## 固定身份

- 主线HEAD：`9fad2af933911092f4a494d66fd607cdb94264cc`，派发前clean。
- 唯一官方候选：R107，817页，4,967,249 bytes，SHA-256 `8811950621E2D64A3C2A8F0F7A52DD0FAC2BDB12018F3EA052C1F58C94EF8DF3`。
- 派发前`latexmk/lualatex/luatex/luahbtex=NONE`；本授权不授予TeX槽。
- inventory保持`32 SA1 / 51 SA2 / 0 SA3 / 16 A_LOCAL_PASS`；严格最终`0/99`。

## A / FIG-P020-01

- 角色：SA2；A为当前全局唯一业务图源写者。
- 唯一源：`src/绘图源码/第01册_数学基础与统计学习基本理论/V1-C01/fig_v1_c01_language_flow.tex`。
- A工作树HEAD：`7a0c4f45c8be66cc53c5a73d0d01685b2559ea43`；源SHA-256 `FF006894E35D1D3E79F1C1D85D212B79735F3D11937B17F23A49D68DC97547CE`。
- 先按R168只读复判真实硬缺陷。旧schema的单横画CJK像素高度差只记ADVISORY；若无真实硬缺陷，必须NO_SOURCE_CHANGE并请求fresh SA1。若有真实硬缺陷，仅可改单一源、static冻结后申请构建槽。
- 禁止TeX、提交、第二图源、中央state/inventory写入与自行启动fresh角色。

## C / FIG-P656-01

- 角色：R107 fresh isolated SA1；C全程只读。
- 源：`src/绘图源码/第05册_采样方法主题模型与图排序/V5-C05/fig_v5_c05_multinomial_counts.tex`。
- C工作树HEAD：`3ab2b570b43fd7e4fc21252803e7fc435b0ed59a`；源SHA-256 `BC954A32F6FC8811F9557AD9A3147795CB6CB467DEAEF6195A3A0B1D9E855852`。
- 仅允许恰一条全新`gpt-5.6-sol/xhigh/fork_turns=none`实例；禁读全部旧P656证据/角色/状态/聊天/Git历史。
- 完整对象、全部unordered pair、native300dpi/1x/8x、灰度/整页/局部、语义与逐ID真实人工账不缩减；R168下微小字体/轮廓像素差仅ADVISORY。
- 禁止TeX、源码写、提交、第二UID/第二角色与中央state/inventory写入。

两条任务已通过顶层任务消息实际派发；待各自actual identity或sealed结果回传后，主线分别验收并迁移角色。
