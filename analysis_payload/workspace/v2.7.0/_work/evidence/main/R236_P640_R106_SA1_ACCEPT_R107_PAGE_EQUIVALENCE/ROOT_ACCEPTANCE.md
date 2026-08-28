# Revision 236｜FIG-P640-01 replacement SA1 接受与 R107 页面等价迁移

Timestamp: `2026-08-26T14:05:02+08:00`

## 中央裁决

- 接受正确型号 replacement 角色 `/root/sa1_fig_p640_r106_fresh_isolated_replacement_v2` 的 `CANDIDATE_PASS_PENDING_MAIN_ACCEPTANCE` 为合法 fresh isolated SA1 `PASS`。
- 角色身份为 `gpt-5.6-sol / xhigh / fork_turns=none`；identity SHA-256=`177769D7B11A0F22F87F85190D4D1C29E15CEBC45F7131358A924889935263D0`。
- 旧的 `gpt-5.4/xhigh` SA1 根继续永久拒收，不参与本次接受。
- P640 中央角色由 `SA2` 迁至 `SA1`；不计 `A_LOCAL_PASS`，必须再由不同实例完成一个全新隔离 SA3。

## replacement SA1 内容与机械验收

- sealed root：`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P640-01\sa1_r106_fresh_isolated_replacement_v2`。
- R106 目标唯一映射：物理页690、印刷页677、图33.7；图源 SHA-256=`A1CB852A7B433D3B3FB39EB4F4E0310FD1F76631F01F366AF9D4B1B1B2FF434B`。
- 分母 `N=45`（32 text + 13 graphic），全部无序对 `990/990`，critical `37/37`，逐字形 `242/242`，drawing primitive `20/20`；空前景/空 glyph mask=0。
- 人工账387行：242 glyph + 45 object + 37 critical + 32 font + 10 peer/role + 6 view + 15 hard gate。ID、分母和 reviewer 全部闭合；空 note、重复 note、模板/default note、非 PASS 均为0。
- R168 真实业务硬失败=0；非法重叠=0、裁切=0、未决=0。最小总文字净空6px、独立文字—文字15px、文字—图形8px；28项旧微阈值只作 advisory。
- ordinary files=875，目录8，总字节17,342,134；`MANIFEST.csv` 873项=`PAYLOAD 859 + CONTROL 14`，路径/bytes/SHA256 mismatch=0。
- manifest SHA-256=`DEDFBE7238B132120470F792D27AF4D1A7CE5028BD5A33E9F711FB67BA8B1E96`；`WRITE_STOPPED` SHA-256=`9F4A5AB073A7C9027819B1A3B463FAA0559BDF97D537D55B8BCD04E0DCA112B9`。
- `WRITE_STOPPED` 是唯一最新文件，领先次新manifest 46,892.2375ms；封后写入0。ADS、cache/pyc、reparse、hidden/system均0。

## R106 → R107 页面等价证据

- 当前唯一官方候选为R107：817页、4,967,249 bytes、SHA-256=`8811950621E2D64A3C2A8F0F7A52DD0FAC2BDB12018F3EA052C1F58C94EF8DF3`。
- R106与R107物理页690均以Poppler 300dpi独立渲染；两个PNG均为706,947 bytes，SHA-256均为 `8106A6D480683C05957D11A4939EF91503877584CFB85A4ACD3BEE06590EB61E96`，逐字节完全相同。
- 两页提取文本也完全相同；主线打开R107 p690，确认图33.7曲线、`.99` marker、极限注释、题注及页面融合正常。
- 因目标页最终可见输出逐字节相同，R106 replacement SA1结论可迁移到R107，不重复制造一轮等价SA1。下一角色必须直接使用R107并从零执行 fresh isolated SA3。

## 后续授权边界

- 授权支线3启动一个不同实例、不同HANDOFF_ID、全新根的P640 R107 fresh isolated SA3；模型/推理必须显式为 `gpt-5.6-sol/xhigh`，`fork_turns=none`。
- 白名单仅R107官方PDF、主线当前P640单源、active Goal、strict protocol/schema及必要当前V5-C04正文。
- 绝对禁读当前replacement SA1根、旧错误型号根、全部旧P640 evidence/role/root/handoff/state/inventory/chat/git history。
- PDF/main/source只读；TeX、源码写、提交、第二UID与第二角色均禁用。PASS只回主线等待中央 `A_LOCAL_PASS` 接受。

## 中央计数

- inventory：`34 SA1 / 51 SA2 / 0 SA3 / 14 A_LOCAL_PASS`。
- 严格最终完成仍为 `0/99`。
