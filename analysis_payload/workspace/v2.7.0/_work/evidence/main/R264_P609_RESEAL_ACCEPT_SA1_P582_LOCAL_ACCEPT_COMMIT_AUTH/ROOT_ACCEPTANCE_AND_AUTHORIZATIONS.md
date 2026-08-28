# Revision 264｜P609 重封接受与 fresh SA1 授权；P582 本地 SA2 接受与原子提交授权

时间：2026-08-26T21:45:18+08:00

## P609 evidence-only readonly reseal

- 正式接受 `C-FIG-P609-01-R108-SA2-R168-READONLY-RESEAL-V1`，保留业务路线 `P609_SA2_NO_SOURCE_CHANGE_READY_FOR_FRESH_SA1`。
- 原根保持零写；新根由唯一 PowerShell7 controller invocation 创建，material 29、copy identity/provenance 2、payload 31、controls 3、ordinary 34。
- 主线独立复核 `COPY_IDENTITY.csv` 29 行：source→destination relative path、bytes、SHA-256、NTFS ticks/FILETIME 差异均为 0；旧 controls 复制 0。
- 新 manifest 31 行，duplicate/missing/extra/bytes/SHA mismatch 均为 0；34/34 文件与 root 只读，ADS/cache/pyc/reparse 均为 0。
- `WRITE_STOPPED` 严格晚于其余文件 10,000,000 ticks，at-or-after/postmarker 写入为 0。
- 关键 SHA 与回传一致：manifest `EE220EF5C0AB482CAF098A921E37DFC9A774D1DDA1F20293E99F6C30B17D253C`；SEAL `F79793A29E03AB67341F53A6114108580971DC28262078DA1590EFC43BEAC3B2`；WSTOP `2F122EF2EE715176BDFC1B3C9A6E805290371854026D7952506F2C3F217B9559`。
- 原业务视觉在 Revision 263 已由主线打开代表性彩色、灰度、几何 overlay、轴/K=6、公式和箭头 8x，无反证；本轮是 identity-preserving control reseal，不重复业务审查。

### P609 fresh isolated SA1 authorization

- UID=`FIG-P609-01`；官方候选固定为 R108（physical 661 / printed 648 / Fig32.9），PDF SHA `C2EC93425486A57DE4C6670E16FC7DA729649A183230C28E8A0652467D3B5B78`。
- current main source SHA=`20687D1EE01AABA9B605591A61781CF688328026E0645AD51B6E02E921DC98A2`。
- 仅授权一个 completely fresh isolated SA1：`fork_turns=none`，优先 `gpt-5.6-sol/xhigh`，新 evidence root 必须在启动前不存在。
- 白名单仅 R108、current main P609 单源、active Goal、直接引用的 strict protocol/schema、确有必要的当前 V5-C03 正文。
- 绝对禁读原 P609 根、readonly reseal 根、全部旧 P609 evidence/role/root/report/handoff/state/inventory/chat/git-history conclusions 与其他 UID 结论。
- PDF/main/source 只读；TeX、源码写、commit、第二 UID、第二角色与中央 state/inventory 写入均为 0。
- 必须从零完成定位、对象分母、all unordered pairs、native1x/8x、语义复算、实际打开后逐项人工账与单次严格 WSTOP-last 封存。R168 微像素/轮廓差仅 advisory；真实缺字、错码、不可读、裁切、非法重叠、语义错误才是硬失败。
- PASS 只回 `SA1_PASS_READY_FOR_FRESH_ISOLATED_SA3`，不得自行启动 SA3 或计 local pass。actual HANDOFF_ID/instance/model-effort/root identity 需立即回传；actual identity 回传前中央仍计 SA2。

## P582 local SA2 acceptance

- 接受 `A-R108-P582-SA2-DIRECT-BUILD-20260826` 的 `LOCAL_SA2_PASS_AWAIT_OFFICIAL_CANDIDATE_AND_FRESH_SA1`。
- 唯一源码 before/after SHA=`C075D4A44A60B95848614543D1D2DBCCCB53F1F776FFDD79A3BF1FEAE3F6550C`→`4AB4E8D14252B20576F05BD1D5CB54BCB28F162B9E33EF439BD3ED6E01DBC65C`；精确一文件 12+/12-，仅 fontsize/leading，`git diff --check` PASS。
- 唯一 direct build exit 0；PDF 31,330 bytes、SHA `988E672096CC34E5A9B1634D84D150C644A0E07B049D81A92FACFE7276269F5B`；TeX 终态 NONE。
- 新 PDF 从零 N95/C4465、critical33；empty/clip/真实硬失败均为 0。主线实际打开彩色图、灰度图、`.380`/第二下降箭头 native1x 与 8x；terminal zero 与箭头清楚、无 shared ink，R168 下仅 advisory。
- 主线复核 sealed root：CSV/JSON 各239行，ordinary242，242/242只读；manifest hashes与报告一致；WSTOP 严格最后，margin 256,962 ticks，at-or-after 0。

### P582 atomic commit authorization

- A 仅获一次单文件原子提交授权；提交只能包含 `src/绘图源码/第05册_采样方法主题模型与图排序/V5-C02/fig_v5_c02_running_mean.tex`。
- commit 前必须保持精确 12+/12-、after SHA `4AB4E8D14252B20576F05BD1D5CB54BCB28F162B9E33EF439BD3ED6E01DBC65C`、`git diff --check` PASS；不得夹带 evidence/state/其他源。
- commit 后回传 commit、parent、branch、exact name-only/numstat、source SHA、worktree/index clean 与不可变 handoff。
- 禁第二 commit、TeX、fresh role、第二 UID；等待主线集成与新官方候选后再派 fresh SA1。

## Central accounting

- inventory 暂保持 `31 SA1 / 49 SA2 / 0 SA3 / 19 local pass`；严格最终仍为 `0/99`。
- P609 actual fresh SA1 identity 回传后才执行 `SA2→SA1`；P582 commit 集成不直接改变角色计数。

