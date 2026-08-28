# R507：P126 R6 静态验收、R7 唯一构建授权与 P689 SA2 启动门接受

时间：2026-08-28T11:55:51+08:00  
Main state：Revision 507  
inventory：`30 SA1 / 31 SA2 / 0 SA3 / 39 local pass`；严格最终`0/99`。

## P126 R6 独立接受

- Main接受R6业务状态仅为`STATIC_ONLY_NOT_RENDERED_NOT_PASS`，不把静态预期计作rendered PASS。
- 唯一增量为目标源line65把相对`legend image code/.code`改为绝对`/pgfplots/legend image code/.code`；其余现有aggregate diff冻结。
- live source：4,366 bytes，SHA-256 `20671687B41E0DD6C8D36774A7E669B0ABC55C5BBE8955BE39FA69137F52F279`。
- standalone wrapper：395 bytes，SHA-256 `706312FAED4A825F61E1517AFFFC852369845F9DAEA051B6E8FEB99335998124`。
- aggregate Git：仅P126目标源modified，index empty，numstat `32+/26-`，diff-check PASS。
- R6 sealed static root：payload8、controls3、ordinary11；manifest set/path/bytes/SHA/Creation+LastWrite mismatch0；11/11 files及root ReadOnly；WSTOP 21行/21键/bad0，含root strict-latest margin `2,999,748,484` ticks、at-or-after0、postmarker0。
- Main授权前即时门：R7 fixed root Leaf/Container/Any=false；source/wrapper身份精确；latexmk/lualatex/luatex/luahbtex=`0/0/0/0`。

## P126 唯一 R7 build slot

授权 HANDOFF_ID=`A-R115-P126-SA2-DIRECT-BUILD-R7-20260828`，fixed new root：

`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\STRICT_R7_SA2_ABSOLUTE_LEGEND_KEY_PATCH_R115_DIRECT_BUILD_20260828`

允许且仅允许：

1. 一个root-external PowerShell7 controller invocation和一个direct LuaLaTeX child invocation；retry0、latexmk0、version-probe0、second invocation0。
2. controller启动前再次确认TeX-family四项均0；若任一非0，首错停且不启动构建。
3. 使用R7内fresh dedicated `texcache`，`TEXMFVAR=TEXMFCACHE=TEXMFCONFIG=TEXMFHOME`必须解析为同一路径。
4. 记录source、wrapper、controller与engine的before/after bytes+SHA；等待child自然完成，禁止中断或进程管理。
5. 无论成功失败，先回`BUILD_SLOT_RELEASED`。exit非0或PDF不唯一时停止且不得重试。
6. 仅在exit0且唯一PDF时，从该PDF做一次非TeX全量N/C、真实post-observation manual、native1x+NN8x、彩色/灰度legend run、overlap/clip、数学语义、题注/page回归与single legal seal。

未授权：第二构建、repair/retry、latexmk、source新改动、commit/amend/push/merge/cherry-pick、fresh role、第二UID、central state写。

## P689 child gate 接受

- HANDOFF_ID=`C-FIG-P689-01-R115-SA2-R168-READONLY-ADJUDICATION-V1`；actual=`/root/sa2_fig_p689_r115_r168_readonly_v1`。
- Child在任何input读取、UID parent/root/artifact创建或其他task action前，独立确认UID parent与fixed root Leaf/Container/Any=false，UID-parent parent exists=true。
- Main接受该门；同一唯一实例现仅可创建UID parent与fixed root各一次，并在R506 exact-file-only、PDF/source/chapter只读、禁目录search/status-tool/TeX/source/Git/central/process/第二UID-role边界下连续返回一个sealed SA2结果。
- P689仍计现有SA2库存；无inventory数值变化。
