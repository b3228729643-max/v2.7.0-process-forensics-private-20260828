# R216｜FIG-P640-01 SA2 R1 FAIL_TO_SA2 中央接受与R2静态授权

- HANDOFF_ID：`C-FIG-P640-01-SA2-GEOMETRY-DIRECT-BUILD-R1`
- sealed root：`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P640-01\sa2_geometry_direct_build_r1`
- source SHA：`FFAE906011BBAD21FD1AD53997693934828394C2AE516649CCCF8DA5938D9B89`
- PDF：1页、40,373 bytes、SHA `0ECC4B13E75A981AD23E7EBCA1CB2BAEBEF83D85EEE3A4518395C54AC296B87A`。

## 机械接受

- N=`40`，glyph=`160`（nonspace145），C=`780/780`，critical=`76`，clips=`40`，views=`9`，hard gates=`15`。
- manifest=`51`，ordinary=`53`；逐文件bytes/SHA/NTFS FILETIME差=`0`；ADS/cache/pyc=`0`。
- payload与manifest只读；唯一可写控制为C协议允许的`WRITE_STOPPED.json`；其严格最新`1,498,319` ticks。
- 唯一TeX调用invocation1/retry0/natural exit0；post TeX进程0。

## 决定性硬失败

- `PAIR_0779 / G08-G10`：`.99`竖直x刻度仍穿入空心endpoint marker下缘。
- 独立native300dpi masks共享`6px`；overlap bbox x=`2090..2091`、y=`759..761`。
- 主线实际打开native1x与8x overlay确认；manual `CRIT_075=FAIL`。这是真实几何碰撞，不受R168字体放宽影响。

## 路由与R2授权

- 接受`FAIL_TO_SA2`；不提交、不启fresh角色、不计local pass，不重用R1 PDF作为候选。
- 仅授权同一P640源的R2 static-only：把现有`ymin=-.04`进一步改为`ymin=-.06`；其他字节保持不变，尤其`.99`点、tick、标签、曲线、数学、caption与左图。
- 量化依据：当前marker/底轴数据差对应3.572pt，tick与marker侵入0.347pt；固定画幅下`-.06`预计把相对距离增加约1.331pt，形成约0.984pt（约4.1px@300dpi）原生净距。静态只作机制预测，必须新PDF重测。
- 未授权TeX；R2静态冻结后另申请唯一构建槽。P639仍排队，禁止第二源写入。

Inventory remains `32 SA1 / 55 SA2 / 0 SA3 / 12 A_LOCAL_PASS`; strict final remains `0/99`.

Accepted at: `2026-08-26T04:57:42+08:00`.
