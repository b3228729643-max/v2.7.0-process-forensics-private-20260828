# R327 — P657 R111 SA2 只读重封接受与 fresh SA1 授权

## 主线裁决

主线独立接受 `C-FIG-P657-01-R111-SA2-R168-READONLY-RESEAL-V1` 的 evidence-only readonly control reseal。既有业务裁决保持：`SA2_NO_SOURCE_CHANGE_READY_FOR_FRESH_SA1`。原未冻结根永久保持原样；新重封根永久冻结。

新根：
`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P657-01\sa2_r111_r168_readonly_adjudication_reseal_v1`

## 独立机械复算

- 旧 `MANIFEST.json` declared/rows=`487/487`；`COPY_IDENTITY.csv` rows=`487`。
- 旧manifest↔旧FS、旧FS↔新FS的relative path/bytes/SHA-256/NTFS mtime ticks mismatch均为0；旧controls复制0。
- 新payload declared/manifest rows/FS=`489/489/489`；missing/extra/duplicate/path/bytes/SHA/ticks mismatch均为0。
- 新ordinary files=`492`，directories including root=`10`；read-only files=`492/492`，read-only dirs=`10/10`，root ReadOnly=true。
- JSON/CSV parse failures、ADS、cache/pyc、reparse均0。
- `WRITE_STOPPED` ticks=`639233989871623808`，max-other ticks=`639233989861623841`，严格最后margin=`9,999,967` ticks；at-or-after excluding marker=0，postmarker root content/attribute writes=0。
- controls中未解析 `$...` 占位符0，TAB+`rue`残留0；关键control SHA与回传一致。
- 旧MANIFEST SHA=`3112495365D202A410972D758A37D39F1E7A88C63BDAA10F43621B8A70F48700`；旧WSTOP SHA=`E8B46E8C95771E486834CCBEA5FE09DBEB3BF67FA19CAC630701DA2F024CCD55`，未改变。
- 独立根外audit SHA=`57AF11397CDD28B1F37EDB2A7D815599FAC488F6E5F3E5FF1958F57154879634`且`success=true`；终态TeX进程0。

## 业务承接

R324已独立接受内容方向：R111 physical706/printed693/Fig34.3；N210=186 glyph+24 foreground drawing，C21945，critical36；manual glyph186/drawing24/critical36/views8/semantics16/hard gates12；17个nonzero raw contacts共1378px均为合法arrow-own-node或shaft-own-head连接；真实missing/tofu/错码/不可读/明显失衡/clip/illegal overlap/语义几何hard defect均0。此次重封未重跑或改变业务证据。

## 唯一下一角色授权

授权C启动恰一个 completely fresh isolated R111 SA1：

- UID：`FIG-P657-01`
- HANDOFF_ID：`C-FIG-P657-01-R111-SA1-FRESH-ISOLATED-V1`
- model/effort/fork：`gpt-5.6-sol / xhigh / fork_turns=none`
- 新根：`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P657-01\sa1_r111_fresh_isolated_v1`
- 派发前门：该根file/dir均不存在；R111=`4,967,076 bytes / DAB10625...012D6`；source=`2,927 bytes / B2B3A874...E31D2`；main HEAD=`b819e9f...b079`且clean；TeX0。
- 白名单仅R111/current P657 source/root GOAL/direct strict protocol-schema/必要当前V5-C05正文。
- 绝对禁读本SA2/reseal及全部旧P657/其他UID/main acceptance/state/inventory/chat/Git-history结论；禁止agent/thread/task状态或identity查询。
- PDF/main/source只读；TeX/latexmk/source write/Git/central/第二UID/第二角色/process management=0。
- 同一实例从零直跑一次sealed PASS/FAIL；PASS只请求另一个fresh isolated SA3，不自行启动。

fresh SA1 actual identity返回前，inventory保持`32 SA1 / 41 SA2 / 0 SA3 / 26 local pass`。
