# FIG-P608-01 R7A 中央路由验收

- 结论：`ROOT_ACCEPT_R7A_FAIL_TO_SA2`。中央 inventory 仅执行 `SA1 -> SA2`；不得启动 SA3，不计 `A_LOCAL_PASS`。
- 官方输入：R101，814 页 A4、4,947,496 bytes、SHA-256 `0870FF226DC383875C4A1B6EABB06AAB942317DA294D90D2864B3030D46DF1A1`。本次不重复构建或重算其已冻结全书门。
- 正式 handoff：`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\handoff\A\A-R101-P608-SA1-FAIL-R7A-20260825`。
- A root 报告：`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\reports\P608_R7A_ROOT_AUDIT.md`；报告 SHA-256 `E8E2CF2B5CC7A6BE616EFC9E5FE228F06F3A9C8CCF4B705B683322B540675586`。
- 有效证据仅为全新 R7A；旧 R7 永久 `ROOT_REJECTED`、只读且不迁移人工结论。
- 分母闭合：`N=172`、`C=14,706`。人工账共 391 项，即 `172+102+64+13+35+4+1`；decision ID 唯一，空 note、exact/归一化重复、禁词与脚本生成/改写 manual 均为 0。
- 唯一硬失败：`HARD-LOWPROFILE-TXT-098`。target `H=28/area=56`；预冻结 exact-metadata peer 为 R101 物理页 187、seq 345，清除 rawdict 证实来自相邻 Latin C 的 11px 组件后，peer `H=28/area=61`；高度比 1.0，面积比 `56/61=0.9180327868852459 < 0.92`。阈值未放宽。
- 封存：manifest 1,917 项、22,291,728 bytes，SHA-256 `03A56E9146F089FC5DD17E800083EF48CE7D774D085871B5074419284E4CBCA4`；普通文件 1,920，parse/ADS/pyc 均 0，严格 seal 时序且封后 0 写。
- 本次无业务源提交、无 TeX、无官方候选更新。P608 进入唯一图源写者队列，须等待显式 SA2 授权。

记录时间：2026-08-25T05:41:00+08:00
