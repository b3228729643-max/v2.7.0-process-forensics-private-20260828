# R212｜FIG-P640-01 R104 fresh isolated SA1 FAIL 中央接受

- HANDOFF_ID：`C-FIG-P640-01-R104-SA1-FRESH-ISOLATED-V1`
- 裁决：`ACCEPT_FAIL_TO_SA2`
- R104：物理页690、印刷页677、图33.7。
- 完整根：`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P640-01\sa1_r104_fresh_isolated_v1_completion_v2`
- 当前单源 SHA-256：`C684E4CF51D41C1C550D14077DEBB59D82AD0B423640F15EAC82BE1898C90D84`，C worktree clean。

fresh SA1 闭合40个实际语义对象（30 text+10 vector）、C780、263 glyph rows（242 non-space）；16/16 bbox相交pair逐项人工裁决。唯一真实硬失败为 `PAIR_0779`：右面板 `(.99,.010)` 空心 marker 与正x轴箭头/轴线共享55个native300dpi像素，mask contamination0、clip0。主线打开figure crop、native1x和nearest8x独立确认箭头穿入marker内环；该接触并非数据坐标所必需，属于R168仍保留的真实非法几何重叠。

数学与正文均通过：轮末ACF为`rho^(2k)`；ESS比例为`(1-rho^2)/(1+rho^2)`；`.99`点真实值0.0100499975；caption、线型、灰度和页面融合通过。字体微差仅advisory。

旧根因控制层未完成，原实例以全新completion根无损补齐：旧33载荷source→destination的bytes/SHA/exact FILETIME差0；最终manifest37/payload37/ordinary39，identity/extra差0，39/39只读，ADS/cache/pyc0，WSTOP严格最新690,827 ticks。

P640由SA1迁移至SA2，不启SA3、不计A_LOCAL_PASS。仅授权P640单源静态几何修复：保留真实点值与标签，通过扩展x轴终点、移除/移动正x箭头或等价最窄机制，使轴/箭头不穿入marker；未获构建槽不得TeX或提交。

