# Revision 237｜FIG-P715-01 R107 fresh SA1 接受与 fresh SA3 授权

Timestamp: `2026-08-26T15:03:35+08:00`

## 中央裁决

- 接受 `A-R107-P715-SA1-FRESH-ISOLATED-20260826` 为合法 fresh isolated SA1 `PASS`。
- 角色身份：instance=`/root/p715_r107_fresh_sa1`，model/effort=`gpt-5.6-sol/xhigh`，`fork_turns=none`。
- 当前仅迁移到 `SA1_PASS_READY_FOR_FRESH_ISOLATED_SA3`；不计 `A_LOCAL_PASS`，不代表全书或最终 PASS。

## 身份与分母

- sealed root：`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P715-01\STRICT_R18_SA1_FRESH_ISOLATED_R107_20260826`。
- R107 PDF：817页、4,967,249 bytes、SHA-256=`8811950621E2D64A3C2A8F0F7A52DD0FAC2BDB12018F3EA052C1F58C94EF8DF3`；物理页765、印刷页752、图36.2。
- 当前图源：4,057 bytes、SHA-256=`900C3A8F72A7A6434101FEE9914019150D3D5F655A23FC5BF41EDB853C25EE87`。
- 分母 `N=259`（216 glyph + 43 foreground drawing/path），全部无序对 `33,411/33,411`，critical `16/16`；empty mask、tofu/decode、clip、非法overlap candidate、clearance failure均0。

## 独立内容与人工账验收

- 人工账：glyph216/216、graphic43/43、critical pair16/16、four-view6/6、panel-role9/9、node-edge connection4/4，全部PASS且空note0。
- glyph/graphic/critical notes逐项绑定具体字形、矩阵位置、路径或关系，唯一数分别216/43/16；抽检未见模板/default/bulk note。
- 实际覆盖18张glyph contact、4张graphic contact、2张critical sheet及四类主视图；无缺笔、邻字/边框污染、裁切、不可读或严重层级失衡。
- 三个瞬态机器候选由相邻同色bbox重复认领产生；重生成mask后逐字`foreign_pixel_px=0`，最终pair ledger不含这些候选，不是PDF可见碰撞。
- 四条有向边、A、出度(1,2,1)、列归一M、`P=M^T`、行/列随机关系、两种状态更新、高亮单元均与源和正文一致。
- R168真实硬门通过；9.4645pt提取舍入、脚本/标点和微像素比例只作advisory，未用作FAIL。

## 封存验收

- ordinary files=366：payload363 + 2 manifests + WSTOP；全部366/366只读，目录9。
- JSON manifest 363 payload；CSV 364行，额外包含JSON manifest并排除自身与WSTOP。所有目标path/bytes/SHA实算差0，无重复/不安全路径。
- JSON manifest SHA-256=`1B34EE5EA8EB7143BC17C984EBC6EA656AAB002AE7BE525A08AC1806CD7CB385`；CSV manifest SHA-256=`C60A3CF0A91266FA23E84C48DD05ACFDE45726C9F0DB3667375CAA17AD081232`；WSTOP中记录一致。
- ADS、cache目录、pyc/pyo、reparse point均0。
- `WRITE_STOPPED` SHA-256=`908F9B45FE3888A0E256F8228215DBE8C39828BA2E44011AA0BCAD1957B2BD9C`，严格唯一最新；封后根内内容写入0。

## fresh SA3 授权边界

- 授权支线1立即启动一个不同实例、不同HANDOFF_ID、全新不存在证据根的P715 R107 fresh isolated SA3。
- 必须显式 `gpt-5.6-sol/xhigh`、`fork_turns=none`。
- 白名单仅R107官方PDF、主线当前P715单源、active Goal、strict protocol/schema及必要当前V5-C07正文。
- 绝对禁读本R18 SA1根/report/handoff/result，以及全部旧P715 evidence/role/root/handoff/state/inventory/chat/git history。
- PDF/main/source只读；禁TeX、源码写、提交、第二UID与第二角色。PASS只回主线等待中央 `A_LOCAL_PASS` 接受。

## 中央计数

- P715在收到SA3 actual identity前仍计SA1；inventory保持 `34 SA1 / 51 SA2 / 0 SA3 / 14 A_LOCAL_PASS`。
- 严格最终完成仍为 `0/99`。
