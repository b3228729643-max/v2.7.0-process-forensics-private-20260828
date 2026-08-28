# B-EXM-P07 R1 主线只读预检

- CONTROL：`2026-08-25T08:06:52.5632567+08:00`至`2026-08-25T08:30:27.4731890+08:00`，exit 0；唯一latexmk父PID10940，三个自然内部LuaLaTeX遍次；终态TeX四类进程NONE。
- PDF：818页、4,959,761 bytes、A4、rotation0、PDF1.7、未加密；log 249,763 bytes。
- 日志预检：TeX hard error、undefined、rerun、duplicate destination、over/underfull hbox/vbox、missing character均0。双索引731/355 accepted，0 rejected，0 warnings。
- AUX定位的目标物理页：682、717、721--722、752--754、778--779。主线用Poppler 120dpi查看物理页681--683、716--723、751--755、777--780共20页；目标解答及续页未见裁切、重叠、断框、孤立标题、异常拉伸、公式越界或不可接受分页。
- 物理页719有两条相近“读前自检：闭式更新与后验预测”及较大段间距。对比未含P07改动的官方R101物理页717，确认两条文案已原样存在；P07精确diff只改10个target solution body。因此它不是P07写域回归，不阻断P07局部批次，但须保留为后续全书文案/版式对象，最终发布前不得遗漏。
- 本文件是主线预检，不替代B正式BUILD_SLOT_RELEASED、完整机械/视觉报告、post-build fresh角色或最终handoff。

当前结论：`PRECHECK_PASS_WITH_PREEXISTING_GLOBAL_COPY_NOTE`。
