# P654 R12 Root Audit（独立 root 裁决）

- 审计日期：2026-08-25（Asia/Shanghai）
- assigned scope：`DIALOGUE_A_VISUAL / FIG-P654-01 / P654 / sealed R12 root`
- 被审根：`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P654-01\STRICT_R12_SA2_R10_EVIDENCE_ONLY_CONTROL_RESEAL_20260825`
- 基础根：`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P654-01\STRICT_R10_SA2_TAXONOMY_R100_DIRECT_BUILD_20260825`
- 裁决：`ROOT_REJECT_R12`

## 1. 结论

R12 的 R10 基础 1052 文件复制身份、双 manifest、解析性、只读封存和绝大多数新增控制层结构均可独立复核成立；在基础身份闭合后，内容层差分反证也没有发现像素、重叠、taxonomy、manual 账或 target `n` 的新反例。

但严格 schema 要求“声明文件必须与底层实际逐字段一致，不能由别的字段或人工解释补救”。本轮独立复核发现两处声明级硬不一致：

1. 实际 ordinary 为 `1062 = payload 1059 + controls 3`，而 `WRITE_STOPPED.json.ordinary_file_count` 声明为 `1059`。该值实际等于 payload，不是 ordinary。
2. `R12_PRESEAL_VALIDATION.json.ordinary_extension_denominator` 声明 `{json:71,csv:24,png:856,pdf:1}`，既不等于最终 ordinary `{json:73,csv:24,png:856,pdf:1}`，也不等于最终 payload `{json:71,csv:23,png:856,pdf:1}`；字段内部混用了两个口径。

因此 PASS 字样、其余正确分母、manifest 身份和封后只读状态均不能覆盖这两项底层不一致；正式裁决只能是 `ROOT_REJECT_R12`。

## 2. 独立性、依据与审计边界

本审计完整读取了当前 goal、严格像素/排印协议和严格 figure evidence schema；只把 R10/R11 root 报告用于基础身份闭合后的差分定位，没有读取旧 R7/R7A 人工结论。未执行或 import R10/R11/R12 任一脚本，未运行 TeX、LuaLaTeX 或 latexmk，未修改被审根、基础根、业务源、state、inventory 或 handoff。

审计通过只读文件枚举、字节数、SHA-256、NTFS UTC ticks、CSV/JSON 解析、PNG 解码、PDF 元数据/原始结构检查、脚本文本静态检查和代表性视觉反证完成。内容层采用“基础 1052 身份全闭合 + 独立分母 + 系统抽样反证”，没有重跑完整 N/C 工作流，也不把 standalone wrapper 当成官方集成页。

唯一写入是本外部报告。

## 3. 根目录口径与新增控制层

### 3.1 实际文件系统口径

| 口径 | 独立实测 |
|---|---:|
| ordinary files | 1062 |
| payload files | 1059 |
| root controls | 3 |
| directories below root | 71 |
| payload bytes | 117,481,301 |

根目录精确且仅有以下三个 controls，树内不存在同名嵌套副本：

- `PAYLOAD_MANIFEST.csv`
- `PAYLOAD_MANIFEST.json`
- `WRITE_STOPPED.json`

因此 R12 的 ordinary 关系为 `ordinary = payload + 3 = 1062`。

普通文件扩展名分布为：`aux=1, csv=24, fls=1, gz=24, idx=2, json=73, log=3, lua=21, luc=44, md=4, pdf=1, png=856, ps1=4, py=4`。

### 3.2 R11 新增五文件隔离

以下五个 R11 新增文件在 R12 整棵树中均为 0：

- `R11_BASE_COPY_IDENTITY.csv`
- `R11_BASE_COPY_IDENTITY.json`
- `R11_COPY_PROVENANCE.md`
- `R11_copy_seal.ps1`
- `R11_validator.ps1`

### 3.3 R12 相对 R10 的精确七个新增 payload 文件

R10 基础 payload 为 1052；R12 payload 与 R10 的集合差精确为下列七项，基础项缺失为 0。七项均进入 CSV/JSON 双 manifest。

| 新增文件 | bytes | SHA-256 | ticks |
|---|---:|---|---:|
| `R12_BASE_COPY_IDENTITY.csv` | 189228 | `0e039b589017d09243de4ade5d8c71d2bb4773974b35b064816aa403f293b33e` | 639232164803988049 |
| `R12_BASE_COPY_IDENTITY.json` | 309509 | `32a85163a927ed82022cd1f9440a044262850fb1a6343f27718cd64f0f88af4c` | 639232164803838012 |
| `R12_copy_prepare.ps1` | 3140 | `6b049b6dac1a3bf0384ef626ff55d3ec8458f18513a608f65114160f11a08103` | 639232164411423526 |
| `R12_COPY_PROVENANCE.json` | 468 | `a7ec28d61cf857403981292ae95fc2d3447083cf0aa35e6f3ee4bae091569962` | 639232164794359062 |
| `R12_PRESEAL_VALIDATION.json` | 775 | `d5ac516a49db2ae4b1f02c0b5c4e9fef21fdcb378379f523ccb276d38be2f729` | 639232165040007818 |
| `R12_preseal_validator.ps1` | 1882 | `f2efb7aed26ebd68ab3e9b5fca6659b55c390c9cf0270118d7f3b2d8c23da791` | 639232164972591842 |
| `R12_seal.ps1` | 2250 | `68633fb2dbfd8ad4b3c5cba1e44671ce30f340a363486cc70be21f7793f9b1be` | 639232164624030876 |

## 4. R10 → R12 基础 1052 身份闭合

独立重算结果：

- R10 基础相对路径 1052；R12 copy identity CSV 1052 行、JSON 1052 行；重复路径 0。
- CSV 与 JSON 在相对路径、bytes、SHA-256、ticks、7 位 UTC display 上差异 0。
- identity 对 R10 source 与 R12 destination：缺失 0、额外 0。
- source 对 destination：相对 path 差 0、bytes 差 0、SHA-256 差 0、`.LastWriteTimeUtc.Ticks.ToString(InvariantCulture)` 十进制字符串差 0、7 位 display 差 0。
- identity 对实际 destination：bytes 差 0、SHA-256 差 0、ticks 差 0、display 差 0。
- 所有 ticks 都是十进制字符串；JSON ticks 类型全部为 string；没有浮点、容差或科学计数法；所有 display 均为 7 位小数。

由此，R10 的 1052 文件内容与时间身份在 R12 中全闭合，可以在严格限定下差分接受 R10/R11 已通过的内容层，同时仍须由本审计独立做分母与反证抽样。

## 5. 双 manifest 与当前文件系统

两个 manifest 各 1059 行，重复路径 0；相对当前 payload：缺失 0、额外 0、bytes 差 0、SHA-256 差 0、ticks 差 0、7 位 display 差 0。CSV/JSON 按序逐字段差 0；非法十进制 ticks 0、JSON 非字符串 ticks 0、非法 7 位 display 0。

三个 control 的当前普通 SHA-256 为：

| control | bytes | SHA-256 | ticks |
|---|---:|---|---:|
| `PAYLOAD_MANIFEST.csv` | 190301 | `44F9244C0CEAAABC87B1861E45528E4B389BC52E77E8EC3B59A0CE00A9E5BE54` | 639232165048406592 |
| `PAYLOAD_MANIFEST.json` | 311366 | `072A5F55C43D3E3AB902205ADCC437CAEA9EE977377518AA25007E4CB44AAC73` | 639232165048156846 |
| `WRITE_STOPPED.json` | 725 | `7203F1BB54FB7C6BD681AAFF79EF9107C6F87C0AF0DF2748033DFBBA3E094190` | 639232165049004627 |

## 6. Provenance 与脚本职责静态复核

`R12_COPY_PROVENANCE.json` 的 `source_root` 与 `target_root` 分别精确等于经 full-path 解析的真实 R10/R12 绝对路径；`round=R12_EVIDENCE_ONLY_CONTROL_RESEAL`，`created_at=2026-08-25T01:01:19.3978075Z`。对 provenance 全部字符串值扫描，`$src`、`$dst` 或任何通用 `$` 占位符均为 0。

脚本文本静态职责如下：

- `R12_copy_prepare.ps1` 固定并核对 full-path source/target，要求 source 1052，逐文件核 bytes/SHA/ticks，写 copy identity/provenance，并回读 provenance 检查根路径及 `$`。
- `R12_preseal_validator.ps1` 只读 identity/provenance 和当前树，未调用或 import 其他 R10/R11/R12 脚本；生成的预验报告本身加入 payload。
- `R12_seal.ps1` 只读消费预验报告且要求其 `status=PASS`，再写双 manifest 与 `WRITE_STOPPED.json`；没有改写预验报告。
- 三脚本无 TeX 构建调用；没有手写字面量 `69/70/71`。

copy / validator / seal 的阶段职责和不互调结构成立；但静态可证的分母实现存在两项逻辑错误：seal 把 controls 排除后的 `$files.Count` 写入 `ordinary_file_count`；validator 的 `ordinary_extension_denominator` 对 JSON 与 CSV 加数方式不一致。脚本“动态计算”不等于字段语义正确。

## 7. 预验报告核对

`R12_PRESEAL_VALIDATION.json` 自身确实纳入最终 payload 和双 manifest；`current_payload_count=1058`、`expected_payload_after_report=1059` 与写入前后实际关系一致，最终 payload 实测为 1059。

但是字段 `ordinary_extension_denominator` 不成立：

| 扩展名 | 报告声明 | 最终 ordinary 实测 | 最终 payload 实测 |
|---|---:|---:|---:|
| json | 71 | 73 | 71 |
| csv | 24 | 24 | 23 |
| png | 856 | 856 | 856 |
| pdf | 1 | 1 | 1 |

JSON 数等于 payload，CSV 数等于 ordinary；字段内部没有统一可成立的 `ordinary` 或 `payload` 口径。这不是封存后自然增量的可解释偏差：最终新增 controls 中包含两个 JSON 和一个 CSV，最终 payload 仅新增预验报告一个 JSON。严格按字段名和 schema，此项为声明级 FAIL。

## 8. `WRITE_STOPPED.json` 逐命名字段裁决

| 字段 | 声明 | 独立实测 | 结果 |
|---|---:|---:|---|
| `payload_file_count` | 1059 | 1059 | PASS |
| `ordinary_file_count` | 1059 | 1062 | **FAIL** |
| `control_file_count` | 3 | 3 | PASS |
| `payload_json_count` | 71 | 71 | PASS |
| `manifest_json_control_count` | 1 | 1 | PASS |
| `write_stopped_json_control_count` | 1 | 1 | PASS |
| `ordinary_json_total` | 73 | 73 | PASS |
| `ordinary_json_excluding_write_stopped` | 72 | 72 | PASS |
| `payload_csv_count` | 23 | 23 | PASS |
| `manifest_csv_control_count` | 1 | 1 | PASS |
| `ordinary_csv_total` | 24 | 24 | PASS |
| `payload_png_count` | 856 | 856 | PASS |
| `payload_pdf_count` | 1 | 1 | PASS |
| `parse_denominators.json` | 73 | 73 | PASS |
| `parse_denominators.csv` | 24 | 24 | PASS |
| `parse_denominators.png` | 856 | 856 | PASS |
| `parse_denominators.pdf` | 1 | 1 | PASS |
| `ads_count` | 0 | 0 | PASS |
| `pyc_count` | 0 | 0 | PASS |

`source_to_destination_zero_diff=true` 与本审计重算一致；`validator_status=PASS` 与预验报告 status 字样一致。但 `ordinary_file_count` 是一个独立命名字段，不能用 `payload_file_count`、`control_file_count`、正确的 JSON/CSV 分母或 PASS 字样补救。实际公式为 `ordinary=payload+controls=1059+3=1062`，故该字段严格 FAIL。

## 9. 解析、封存与卫生状态

- JSON：73/73 全部可解析。
- CSV：24/24 全部可解析。
- PNG：856/856 全部成功解码，共 271 种尺寸。
- PDF：1/1 可解析；文件 43385 bytes，SHA-256 `86712CDD98EC92AF1A2D274D4E4E987E6AE8338064FD4A3339D2761737A87260`，PDF 1.7，1 页 A4（595.276 × 841.89 pt），未加密，未发现 JavaScript。
- ADS：扫描根及 1133 个后代项目，非默认数据流 0。
- `.pyc`：0；`__pycache__/.pytest_cache/.mypy_cache/.ruff_cache`：0；reparse items：0。
- 1062/1062 普通文件为只读，writable 0。
- `WRITE_STOPPED.json` 文件时间为 `2026-08-25T01:01:44.9004627Z`（ticks `639232165049004627`），严格唯一最新；其他文件在该时刻之后为 0，在其自身 `sealed_at=2026-08-25T01:01:44.8906639Z` 之后的非 WRITE_STOPPED 文件为 0。

封后 0 写、严格唯一最新、全文件只读均成立，但不修复声明字段错误。

## 10. 内容层差分反证与独立分母

在基础 1052 身份闭合后，本审计没有重跑完整 N/C；以下为独立分母与系统反证。

### 10.1 全局分母

- object manifest：116 行、116 个唯一对象、index 1..116；glyph 95（TEXT 80 + FORMULA 15），graphic 21（NODE_BORDER 8 + LINE_ARROW 7 + ARROWHEAD 5 + MATH_RULE 1）。raw/pre mask 缺失 0、空 ink 0、machine 非 PASS 0，missing/foreign/clip 合计均 0。
- after-pixel：95 行、95 个唯一 glyph，非 PASS 0；effective pt `<9.5` 为 0；H 低于阈值为 0。
- all-pairs：6670 行，等于 `116×115/2`；重复/反向/自配对/未知对象/缺预期对均 0；index 1..6670；final raw intersection 非零 0；非 PASS 0。
- critical：50 对、50 个目录、400 个文件（每对 8 文件），覆盖 11 个 relation class。
- after-overlap：6019 对；被排除 651 对由 intended endpoint 15、math-rule component 9、other-independent 180、same-parent 447 精确闭合；被排除项 final intersection 均 0、均 PASS。
- taxonomy：95 行、95 个唯一 glyph、10 组，组计数之和 95，failure 0。
- manual：八账分母 `95+21+50+5+3+10+4+4=192`，全局 decision id 唯一 192；空 note 0；规范化 note 完全重复组 0；glyph/graphic/critical 对象集精确闭合；`MANUAL_LEDGER_IDENTITY` 对八账 bytes/SHA/7 位 mtime 全差 0。

静态扫描只在 `consumer_validator.py` 的读取/验证清单中发现八个 manual 文件名，未发现生产或改写它们的脚本反例。该结论只说明“未发现自动生成反证”，不是对人工作者身份的密码学证明。

### 10.2 全视图与 target `n`

实际打开了五个全局视图：`full_page_200dpi`、`figure_crop_300dpi`、`standalone_300dpi`、`grayscale_300dpi`、`measurement_overlay_300dpi`。视图一致呈现左至右链、下部解释连线和虚线应用边；未观察到裁切、对象碰撞或灰度不可分。`full_page` 是 standalone wrapper，下部存在页内留白，不等同于官方集成页。

target `FRM_TRIAL_005` 为公式粗斜体 `n`：effective 10.7 pt、threshold 22、H=22、ink area=297、missing/foreign/clip=0。独立像素计数 raw/pre 两张 mask 均为 22×22，白色前景 297，bbox 高度 22，且 raw=pre；打开 contact sheet cell 后，竖干、拱部和末端弯曲均完整清楚。

### 10.3 taxonomy 极端/代表项

打开 glyph sheets 001、002、003、006、011、012、016，覆盖十组的代表或极端：target `n`；natural-script zero H=24、该组 median=26、ratio=0.9230769；upper `N` H=33；plus H=29；CJK 最小 34 与最大 36；Latin `m` H=21 与 `a` H=22；ascender `t` H=27 与 capital `G` H=29；annotation `应` H=35。未观察到 mask 污染、缺笔或错误对象替换。

另打开四个 graphic 代表：分数横线、LDA 边框、trial shaft、trial arrowhead；mask-only 边界清楚。

### 10.4 critical 十一类反证样本

| relation class | 样本 | 观察/数值 |
|---|---|---|
| arrow composition | `PAIR_06580` | final 0，pre 24，intended |
| formula rule / own border | `PAIR_04345` | clearance 118 |
| independent text-text | `PAIR_04538` | bbox gap 8，raw 27，required 4 |
| intended endpoint | `PAIR_00102` | final 0，pre 10，intended |
| math-rule component | `PAIR_04478` | raw 6 |
| other independent | `PAIR_03281` | node-border pair raw 30 |
| own-node text border | `PAIR_06331` | raw 17，required 5 |
| same-parent typography | `PAIR_00893` | final 0，pre 1 |
| text line/head | `PAIR_06668` | raw 27，required 3 |
| text math-rule | `PAIR_05245` | raw 71，required 3 |
| text other-border | `PAIR_06344` | raw 5，required 3 |

十一类各抽一项打开 bundle，未发现与 ledger/机器度量相冲突的视觉反例。manual notes 对象特异性也可见：target `n` 明确描述 stem/arch/curl，natural zero 描述 closed oval 并排除 alpha/fraction 污染，upper `N` 描述双竖和对角线，Gamma 的 `m/a` 分别描述双拱与闭合 counter；critical notes 对应各自 pair 几何，而非统一模板话术。

## 11. 硬缺口、可复核事实与边界

硬缺口只有达到裁决门槛所需的一项即可；本轮有两项：

- `WRITE_STOPPED.json.ordinary_file_count`：声明 1059，实际 1062。
- `R12_PRESEAL_VALIDATION.json.ordinary_extension_denominator`：JSON/CSV 混合 payload/ordinary 口径，不能与任何一个真实最终集合一致。

其余可复核事实——R10 基础 1052 零差、七个新增文件全部入 manifest、双 manifest 对当前 FS 零差、provenance 绝对路径真实、三阶段结构独立、全解析、ADS/cache/pyc 为 0、封后 0 写、严格唯一最新、全只读、内容层独立分母及反证未见新失败——均如实保留，但不能以多数通过覆盖声明级 FAIL。

本裁决不授权 A_LOCAL_PASS，不授权 SA3，不授权提交、主线集成、官方候选或 fresh SA1。若未来另行生成新的 sealed root，必须先使每个命名字段与其真实集合逐项一致，再由新的独立角色从头复核；不得原地修补本 R12。

## 12. 正式 verdict

`ROOT_REJECT_R12`
