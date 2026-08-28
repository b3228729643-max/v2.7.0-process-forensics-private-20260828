# P654 R7 local SA2 sealed package — 独立 root 机械验收

## 结论

`ROOT_REJECTED`

被审 sealed root：

`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P654-01\STRICT_R7_SA2_NARROW_R100_DIRECT_BUILD_20260825`

本次审计完整读取 current Goal、`STRICT-PIXEL-TYPOGRAPHY-PROTOCOL.md` 与 `STRICT_FIGURE_EVIDENCE_SCHEMA.md`；全程未修改、导入或执行 sealed root 内脚本，未创建或删除 sealed 文件，也未修改业务源、状态或 Git。唯一写入是本报告。

拒绝理由不是 PDF、mask、pair 或 manifest 的机器数值失败，而是人工裁决证据的生成机制违反硬门：`finalize_r7.py` 批量写入 `TRUE/PASS`、批量补齐人工行并写模板备注；166 个显式 ID map 只是统一 decision code 的键表，不含逐 ID 的对象/关系特异人工备注。critical pair 的所谓人工 decision 还被强制等同于机器分类，形成循环确认。任务已明确规定“发现 bulk 生成则 ROOT_REJECT”，故不能给出 `ROOT_ACCEPT_LOCAL_SA2_PASS_REQUEST_MAIN_INTEGRATION_AND_FRESH_SA1`。

## 致命缺口：人工裁决不是逐 ID 独立证据

### 1. finalizer 明确批量写人工布尔、PASS 与备注

sealed `finalize_r7.py` 的 `manual_phase()` 不是只消费并验证已完成的人工 ledger：

- lines 136–146：循环遍历 95 个 glyph，逐行写 `REVIEWER`，把 `ORIGINAL_MATCH`、`OVERLAY_COMPLETE`、`MASK_ONLY_PURE` 全部写成 `TRUE`，把 `DECISION` 写成 `PASS`，并对 95 行写入同一句 NOTE。
- lines 152–161：循环遍历 21 个 graphic，批量写三个 `TRUE`、`DECISION=PASS` 和同一句 NOTE。
- lines 167–182：循环遍历 50 个 critical pair，批量写四个 `OPENED_*=TRUE`、`MANUAL_DECISION`，NOTE 只在两种固定模板中二选一。
- lines 184–201：用循环/全局布尔批量生成 5 个 view 行和 3 个 semantic 行。
- lines 209–219：直接构造带硬编码 `PASS` 的 D/E ledger。
- lines 502–545：直接生成 `after_visual_acceptance.md`，其中字体、像素、D/E、视觉、语义、灰度、页面融合全部硬编码为 `true`，重叠/裁切/污染等硬编码为 `0`，并直接写 RESULT。

这与“finalizer 只能消费验证，不能批量写 True/PASS/0 或补行”的验收条件正面冲突。

### 2. 166 个显式 key 不是 166 份对象/关系特异人工判断

`manual_row_decisions.json` 的 key 集确实闭合为 `95 glyph + 21 graphic + 50 critical = 166`，无重复、无缺 ID；但 value 分布为：

- glyph：95/95 全为 `PASS_COMPLETE_PURE`；
- graphic：21/21 全为 `PASS_COMPLETE_PURE`；
- critical：39 个 `PASS_DESIGN_COMPOSITION`、11 个 `PASS_CLEARANCE`。

该 JSON 没有逐 ID NOTE、观察到的具体轮廓/缺笔/污染特征、具体关系对象或最近像素解释。`manual_decisions.json` 还包含 `glyph_scope_decision.default_decision = PASS` 以及 glyph/graphic/critical scope 级全局布尔。

最终 CSV 的 NOTE 重复统计为：

- `glyph_manual_review.csv`：95 行、仅 1 个 distinct NOTE，同一句重复 95 次；
- `graphic_manual_review.csv`：21 行、仅 1 个 distinct NOTE，同一句重复 21 次；
- `critical_pair_manual_review.csv`：50 行、仅 2 个 distinct NOTE，分别重复 39 次和 11 次。

这些 NOTE 不是对象/关系特异备注，属于固定模板。

### 3. critical 人工分类与机器分类循环一致

`finalize_r7.py` lines 169–171 先由 `MACHINE_ADJUDICATION` 计算唯一允许的 manual code，再要求人工 map 必须与这个机器期望完全相同；随后 lines 177–181 批量写入该 code 和模板 NOTE。因此 39 `DESIGN_COMPOSITION` + 11 `CLEAR` 的“人工结果”只是机器分类的复写，不能作为独立人工判决。

### 4. 49/49 终检只证明被生成 ledger 的内部一致性

`machine/terminal_crosscheck.json` 共有 49 checks，49 true、0 false，`hard_failures=[]`。但其中人工门只检查上述已被 finalizer 批量写成 `TRUE/PASS` 的 CSV 是否含 PASS、是否无 PENDING；它没有验证逐对象人工观察的独立生成过程。因此该 49/49 可保留为包内一致性事实，不能提升为可信人工验收或 root accept。

此外，`machine/terminal_crosscheck.json` 的 mtime 为 `2026-08-24T20:57:59.9934242Z`，而 sealed `finalize_r7.py` 的 mtime 为 `2026-08-24T21:02:27.1467932Z`；终检早于当前 sealed finalizer 源约 267 秒。包内没有 phase-time finalizer SHA，无法证明终检运行所用脚本与最终 sealed 脚本字节相同。这是额外的执行溯源缺口。

## 可保留的只读机械事实

以下复算均闭合，但不能弥补人工证据缺口。

### A. 源、Git 与构建身份

- 目标源 SHA256 独立复算为 `EA4A19FF940A177D4D754C4277896A2F38B75C1E6F252D8A374F418B84E31E6D`，3122 bytes。
- wrapper SHA256 独立复算为 `FE44F2E6005D884A6916A11C6EBCB89CF40BD523A64D8F8C6BC8124DBABC0CA1`，397 bytes。
- worktree `git status --short` 只有目标源一项修改；`git diff --numstat` 为 `1 1`；`git diff --check` exit 0。
- 唯一 diff 是 line 22 给 `\boldsymbol n` 增加局部 `\fontsize{10.7pt}{12.2pt}\selectfont`；未提交。
- controller 源只有一次 `Start-Process`，目标为 direct `lualatex.exe`，没有 latexmk 或 retry loop。start/result JSON 一致记录 parent PID `12540`、child PID `9932`、exit `0`、`natural_exit=true`、`invocation_count=1`、`latexmk_invoked=false`、`automatic_retry_count=0`，且三个 TeX cache 变量绑定一致。
- engine stdout 只出现 1 个 LuaHBTeX banner，末尾为 1 page / 43,385 bytes；stderr 为 0 bytes。
- `PRECHECK NONE`、`POSTCHECK NONE` 与 slot release 只出现在叙述性 Markdown；controller 没有 pre/post `Get-Process` 探针或结构化 slot-release 记录。因此这些历史全局进程状态无法由 sealed 包独立复算，不能与上面的单 controller/单 banner 事实混同。

### B. PDF 与 native render

- PDF：1 page，43,385 bytes，SHA256 `A7DBDECEA7B54C1649CD341112B7BB37FF379600CB6A61B54EDDBAF154E9E5D6`。
- 页面尺寸：`595.2760009765625 × 841.8900146484375 pt`，A4。
- render identity：full 200dpi `1654×2339`；full 300dpi `2481×3508`；figure crop 300dpi `1985×705`；standalone 300dpi `1985×624`；`POST_RENDER_RESIZE=false`。

### C. 对象、目标字形与 ownership

- `object_manifest.csv`：N=116，116 个唯一 ID，95 glyph（80 TEXT + 15 FORMULA）和 21 graphic/path（8 NODE_BORDER + 7 LINE_ARROW + 5 ARROWHEAD + 1 MATH_RULE）。
- 116 个 raw mask、116 个 pre mask 的非零面积逐项重算均与 manifest 一致；116 个 raw mask 尺寸逐项与其 raw bbox 一致。empty/missing/foreign/clip 的机器总和均为 0。
- `FRM_TRIAL_005`：source line 22；declared/effective `10.7pt`；PDF font `10.660019874572754pt`；U+1D45B / XITSMath-Bold；bbox `[488,379,510,401]`，即 `22×22px`；`H_INK=22px >= 22px`；raw/pre area `297/297px`；raw 与 pre mask 字节语义上同形；missing/foreign/clip/occluded/ownership-loss 均为 0。
- 目标 raw、pre、native1x、nearest8x 四个文件均存在并成功解码；目标 native8x 的 ORIGINAL / TARGET OVERLAY / MASK ONLY 三联可见轮廓完整且无邻物混入。ownership ledger 为 `PASS_NO_OCCLUSION`、later owner `NONE`。
- source font audit 6/6 machine PASS；pixel ledger 95/95 machine PASS；low-profile punctuation count 0。

### D. 全部无序 pair 与机器几何

- `C(116,2)=6670`；CSV 行数 6670，pair ID 唯一 6670，object unordered pair 唯一 6670，并与 object 顺序的 combinations 完全相等；未知对象引用 0。
- pair machine fail 0；final raw overlap 总和 0；非白名单 pre-occlusion contact 0；clearance fail 0。
- 分类最小净空：独立 text bbox 8px；own-node text-border 17px；text-line/arrow 27px；text-math-rule 71px；text-other-node-border 5px；formula-rule-own-border 118px。目标 `FRM_TRIAL_005` 对自己的 trial border 实测为 24px；17px 是全体 own-node 类别最小值。
- critical pair 共 50，机器分类 39 `DESIGN_COMPOSITION` + 11 `CLEAR`；50 个目录与 ledger ID 完全一致，每个 bundle 为 7 PNG + 1 JSON；pair JSON 与全 pair CSV、critical ledger 的 ID、对象、关系和 machine adjudication 交叉一致，0 mismatch。

### E. evidence 文件集

- glyph contact sheets：16 张，ledger 分布为前 15 张各 6 cell、末张 5 cell，共 95；95 个 `(sheet,cell)` 唯一，ID 集与 95 glyph 完全相等。
- graphic：21 个 ID 全部有 object-native 1x 与 nearest8x；21 张 graphic 8x contact sheet 存在；ledger ID 集与 21 graphic 完全相等。
- critical：50 个 native1x/nearest8x bundle 全部存在并闭合。
- views：`full_page_200dpi`、`figure_crop_300dpi`、`standalone_300dpi`、`grayscale_300dpi`、`after_text_measurement_overlay_300dpi` 共 5 个，路径存在、尺寸与 render identity 一致。
- ledger 结构层面无 pending、空字段或重复 ID；但这些形式条件不修复其内容由 finalizer 批量生成的问题。

### F. 封包、解析与停止写入

- ordinary files：1051。
- manifest payload：1048；`MANIFEST.json` 1048 行、`MANIFEST.csv` 1048 行、实际排除双 manifest 与 `WRITE_STOPPED` 后也是 1048。
- 以 relative path 为 key，逐项重算 path/file-set/bytes/mtime_ns/SHA256：0 差异；JSON 与 CSV manifest 逐项相等。
- JSON 62/62 全部实际解析；CSV 20/20 全部实际解析；PNG 856/856 全部实际完整 decode，错误 0。
- NTFS ADS 独立枚举为 0。
- payload 最晚 mtime 为 `PACKAGE_STATUS.json`：`2026-08-24T21:03:04.9649314Z`；`MANIFEST.csv` 为 `21:03:06.3253361Z`，`MANIFEST.json` 为 `21:03:06.3347454Z`；`WRITE_STOPPED` 为 `21:06:47.4709448Z`。marker 严格晚于全部 payload 和双 manifest；marker 后普通文件写入 0。
- `RESULT.txt`、`PACKAGE_STATUS.json`、terminal JSON、manifest、`SA2_REPORT.md` 与 `after_visual_acceptance.md` 都一致使用 `LOCAL_SA2_PATCH_VERIFIED_REQUEST_FRESH_SA1`。
- 包明确声明它不是 fresh isolated SA1、不是 SA3、不是 `STRICT_FINAL`，也不授权 final acceptance；没有把结果写成 `A_LOCAL_PASS`。

## 完整 gap list 与处置

1. **G1 / fatal**：finalizer 批量写 95 glyph + 21 graphic + 50 critical 的人工 `TRUE/PASS/OPENED` 和模板 NOTE，违反 finalizer 只消费验证的硬门。
2. **G2 / fatal**：人工 ID map 缺少逐 ID 特异 note；glyph/graphic 各只有一个模板，critical 只有两个模板。
3. **G3 / fatal**：critical manual code 被程序强制等同机器 adjudication，属于循环确认，不是独立人工裁决。
4. **G4 / provenance**：terminal 输出早于最终 sealed finalizer 源，且缺少 phase-time finalizer SHA，无法锁定实际执行代码身份。
5. **G5 / provenance**：PRECHECK/POSTCHECK/SLOT_RELEASE 只有叙述性声明，没有 sealed 机器探针记录；只能确认 controller 源的一次 direct invocation 和单 engine banner。

必须保留该 R7 包为 rejected diagnostic evidence，不得把现有 49/49、人工 CSV 或 local result 上推为 root accept、main integration、fresh SA1 或 SA3 依据。若要继续，应由真正逐 ID 的人工审阅重新产生对象/关系特异记录，并使用只读 finalizer 验证而非补写这些记录；随后重新封包并接受新的独立 root audit。
