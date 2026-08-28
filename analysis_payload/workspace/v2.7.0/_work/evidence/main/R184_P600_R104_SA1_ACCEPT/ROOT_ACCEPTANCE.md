# FIG-P600-01 R104 fresh SA1 中央接受

- Revision：184
- 中央裁决：`ROOT_ACCEPT_SA1_PASS_TO_FRESH_ISOLATED_SA3`
- UID：`FIG-P600-01`
- SA1 identity：`C-FIG-P600-01-R104-SA1-FRESH-ISOLATED-V1`
- 官方候选：R104，物理页 651 / 印刷页 638 / 图 32.4
- 官方 PDF：817 页，4,967,222 bytes，SHA-256 `E5C871642FBDDBEC6508BE1B61BD911FE281CA5ACFBD16B0449B13357770A641`
- evidence root：`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P600-01\sa1_r104_fresh_isolated_v1`

## 中央独立复核

- 分母闭合：29 objects（11 text semantic parents + 18 visible graphics），完整 unordered pairs 406，critical 29，clip 29；glyph 197 另按逐字形账闭合。
- 机器硬门：illegal overlap 0、clip 0；最小 text-text clearance 8 px，text/formula-line-arrow 36.4833 px，text/formula-node-border 9 px。
- 语义：`a=pi(x)q(x,y)`、`b=pi(y)q(y,x)`；两向接受流均为 `min(a,b)`；两侧 alpha 参数、细致平衡推出平稳分布的充分性表述正确。
- 人工账：glyph 197、graphic 18、pair 406、semantic 12、source-font 8、peer-role 11、views 5、R168 advisory 12；空 ID/空 note/真实硬失败均为 0。R168 比例和轻微栅格差只作 advisory。
- 主线实际打开整页、figure crop、灰度图、文字测量 overlay、glyph contact 与两张代表性 pair card；双向提议流、截平接受流、公式、题注及正文修订一致，无缺字、错码、不可读、真实裁切、非法碰撞或明显肉眼失衡。

## 封存机械门

- 实际普通文件 1,356；manifest entries 1,354=`payload 1,351 + controls 3`，自排除项恰为 `MANIFEST.json` 与 `WRITE_STOPPED`。
- manifest/FS path、bytes、SHA-256、FILETIME mismatch 均 0；ADS/cache/pyc 均 0。
- 前置文件与 manifest 均只读；`WRITE_STOPPED` 按声明闭包模型保留控制写属性，时间严格最后，封后写 0。
- recordset SHA-256：`0BA2E8E7B3189DE2025B0D1156F6424302F0BAAC5A3EEE8F464C3EA7F0115144`
- manifest SHA-256：`BC4F328FA961B7F3D12D1F4EE15DCB8DEDFAAE6A03D71A9DFFD5D716AB009111`

## 路由

本轮只接受 SA1 PASS，不计 local pass。`FIG-P600-01` 从 SA1 转入 SA3；支线3须创建不同的、`fork_turns=none` 的 R104 fresh isolated SA3，绝对禁读本 SA1 evidence/report/result/handoff 及全部旧 P600 证据与结论。P637 的既有 fresh SA3 继续运行；支线3总并发保持恰两条，TeX 与业务源码写者保持禁用。
