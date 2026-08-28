# FIG-P715-01 R107 R18 fresh isolated SA1 report

- HANDOFF_ID: `A-R107-P715-SA1-FRESH-ISOLATED-20260826`
- Route: `gpt-5.6-sol`, reasoning `xhigh`
- Evidence root: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P715-01\STRICT_R18_SA1_FRESH_ISOLATED_R107_20260826`
- Frozen PDF: 817 pages / 4,967,249 bytes / SHA256 `8811950621E2D64A3C2A8F0F7A52DD0FAC2BDB12018F3EA052C1F58C94EF8DF3`
- Frozen source SHA256: `900C3A8F72A7A6434101FEE9914019150D3D5F655A23FC5BF41EDB853C25EE87`
- Independent locator: physical page 765, printed page 752, Figure 36.2

从零重建的可见对象分母为 216 个文本字形加 43 个 drawing/path 对象，`N=259`，完整无序 pair 数 `C(N,2)=33,411`。最终机器硬失败 0：非法重叠候选 0、净距失败候选 0、空 mask 0、tofu/错码候选 0、裁切像素失败 0。16 个 critical pair 均有 native 1× 与 8× nearest 证据。

实际人工打开并检查了 source、full-page、figure crop、standalone、grayscale、text overlay、18 张 glyph sheets、4 张 graphic sheets 和 2 张 critical-pair sheets。人工 ledger 包含 glyph 216 行、graphic 43 行、critical pair 16 行、四视图 6 行、panel/role/script 9 行及 node-edge 几何 4 行，均无空项、pending 或硬失败。

图的四条有向边、`A`、`c=(1,2,1)`、列归一 `M`、`P=M^T`、行随机性质和概率更新公式均相互一致；两面板四边、节点、箭头、矩阵格、focus 框、灰度与整页融合均无真实裁切、非法重叠、不可读或明显严重失衡。R168 指定的微小字号/像素比例、`[0.92,1.08]`、taxonomy/peer 差、font metadata 和 1–2 px 栅格差仅作 advisory，未被单独用作 FAIL。

双 manifest 已校验：payload 363 个文件；`MANIFEST_FILES.json` SHA256 `1B34EE5EA8EB7143BC17C984EBC6EA656AAB002AE7BE525A08AC1806CD7CB385`，`MANIFEST_SHA256.csv` SHA256 `C60A3CF0A91266FA23E84C48DD05ACFDE45726C9F0DB3667375CAA17AD081232`。机器终检 PASS/0 failures；ADS/cache/pyc 均为 0。`WRITE_STOPPED` 是证据根最后创建的内容文件，SHA256 `908F9B45FE3888A0E256F8228215DBE8C39828BA2E44011AA0BCAD1957B2BD9C`；封存后根内 0 内容写，366/366 文件为只读。

Verdict: `PASS`

Callback: `SA1_PASS_READY_FOR_FRESH_ISOLATED_SA3`
