# P654 R11 root audit（独立 root auditor）

- 审计日期：2026-08-25（Asia/Shanghai）
- sealed root：`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P654-01\STRICT_R11_SA2_R10_EVIDENCE_ONLY_LOSSLESS_TICKS_RESEAL_20260825`
- 对照 R10 root：`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P654-01\STRICT_R10_SA2_TAXONOMY_R100_DIRECT_BUILD_20260825`
- 审计性质：只读；未执行或 import R11/R10 内任何脚本；未启动、重跑或中止 TeX/LuaLaTeX/latexmk；未修改 sealed root、业务源码、state 或 inventory；未读取旧 P654 R7/R7A 人工结论；未提交、未派 fresh 角色、未启 SA3。
- 最终结论：**REJECT**。R11 的 lossless-ticks reseal、1052 基础 payload 身份及 1057 manifest 均闭合，但两个 R11 控制声明不自洽，不能在“所有声明文件分母与解析”严格门下签发 ACCEPT。

## 1. 依据与方法

完整读取并按其严格门执行：

1. `D:\Users\ASUS\.codex\attachments\255038e7-59d5-4cf5-870f-463d35db7f09\goal-objective.md`；
2. `STRICT-PIXEL-TYPOGRAPHY-PROTOCOL.md`；
3. `STRICT_FIGURE_EVIDENCE_SCHEMA.md`。

允许的差分继承仅取自 `P654_R10_ROOT_AUDIT.md` 中已通过的内容门；R10 报告的最终 REJECT 原因是旧 manifest 的 `mtime_utc` 不能无损往返 NTFS ticks（1052 中仅 117 精确、935 不精确）。本次先独立证明 R10→R11 基础 1052 的 path/bytes/SHA-256/ticks 全零差，再对 R11 manifest/control 独立全量核验，并对内容证据作系统性代表项和极端项反证抽样。未重跑完整 N/C 生成流程。

审计器使用独立 PowerShell 只读枚举、`Get-FileHash -Algorithm SHA256`、`.LastWriteTimeUtc.Ticks.ToString(InvariantCulture)`、CSV/JSON 解析（JSON 日期强制保留字符串）、`System.Drawing` PNG 解码与 `pdfinfo` 只读检查。R11/R10 内脚本仅作静态阅读。

## 2. 文件集合、双 manifest 与 lossless ticks

| 项目 | 独立结果 |
|---|---:|
| ordinary files | 1060 |
| controls | 3（`PAYLOAD_MANIFEST.csv/json`、`WRITE_STOPPED.json`） |
| payload | 1057 |
| ordinary = payload + 3 | PASS |
| payload bytes | 117,672,630 |
| CSV manifest rows / duplicate paths | 1057 / 0 |
| JSON manifest rows / duplicate paths | 1057 / 0 |
| manifest vs current FS missing / extra | 0 / 0 |
| current FS bytes mismatches | 0 |
| current FS SHA-256 mismatches | 0 |
| current FS decimal-string ticks mismatches | 0 |
| invalid/non-decimal ticks | 0 |
| CSV `mtime_utc_7digit` mismatches | 0 |
| CSV↔JSON full ordered-field differences | 0 |

JSON 用 `ConvertFrom-Json -DateKind String` 解析，防止 PowerShell 自动把 7 位小数 UTC 字符串转换成 `DateTime` 后按本地文化重新格式化；未经该选项出现的日期字符串表象差异是审计命令类型转换伪差，已排除，不计作证据差异。

## 3. R10→R11 基础 1052 身份与新增五文件

R10 独立枚举基础 payload 为 1052 文件、116,974,049 bytes。`R11_BASE_COPY_IDENTITY.csv/json` 各 1052 行、无重复，source/destination relative path 全相等；逐文件对实际 R10 source 与 R11 destination 复算：missing source 0、missing destination 0、bytes 差 0、SHA-256 差 0、ticks 十进制字符串差 0。CSV↔JSON 全字段/顺序差 0。因此可以差分接受 R10 报告中已经通过的基础内容门。

R11 恰有以下 5 个新增 payload，全部进入 CSV/JSON manifest，且 manifest 与当前 FS 的 bytes/SHA/ticks 均精确一致：

| 文件 | bytes | SHA-256 | ticks |
|---|---:|---|---:|
| `R11_BASE_COPY_IDENTITY.csv` | 245189 | `71AEEDDAC26972E0D0B8D553000515D378DEDE6776A2A08F7E01BC3AB1F5F488` | 639232142198039188 |
| `R11_BASE_COPY_IDENTITY.json` | 447910 | `8BFAEEC43B39E0F5FED103DE90241EE43FFAADBBA38CBE1D8E281631166C975E` | 639232142197909155 |
| `R11_COPY_PROVENANCE.md` | 326 | `7E104508DE6373FC950E7AC10455BBAD0D1188ADC0F9A8365044A8EFF9503036` | 639232142198079187 |
| `R11_copy_seal.ps1` | 3155 | `87F961362C91CC42B8DF3F052645592CDF7A6CBC5BE87396CFD0848A264A9014` | 639232140606625120 |
| `R11_validator.ps1` | 2001 | `EED27FA5934B64CEFF18E26EB8DB5047A6DCC5FD5C9F78A47BFE576F13AD3909` | 639232142054399546 |

`R11_validator.ps1` 的实际 SHA-256 与 `WRITE_STOPPED.json` 声明一致。静态检查显示它自行递归枚举 payload、复算 bytes/SHA/ticks/7-digit UTC，并分别核 CSV/JSON；未 import/call seal 脚本。两个 R11 脚本以 basename 排除三个 control，理论上会误排同名嵌套文件，但当前 root 内不存在任何嵌套同名 control，因此对本候选的独立枚举结果无影响。上述脚本均未被本审计执行。

## 4. 声明分母、解析与卫生

独立分母如下：

- CSV：24 个，24/24 可解析；payload CSV 为 23 个。
- JSON：71 个，71/71 可解析；仅排除 `WRITE_STOPPED.json` 后为 70 个；payload JSON 为 69 个。
- PNG：856 个，856/856 可解码，271 种尺寸。
- PDF：1 个，1 页 A4（595.276 × 841.89 pt），未加密、无 JavaScript；实际 bytes 43,385，SHA-256 `86712CDD9610F2136976064317F333B73D4A2FF8E22D5FEF904C915DD2787260`。
- 非默认 ADS：0；`.pyc`：0；`__pycache__`、`.pytest_cache`、`.mypy_cache`、`.ruff_cache`：均 0；reparse file/dir：0。

声明文件逐一读取了 authority、ADS audit、consumer validation、lock、current-TeX-none、direct-invocation start/result、manual identity、prebuild identity、process reconciliation、R10 build freeze、R10 SA2 report、RESULT、scope certificates、static summary、taxonomy policy、typography group summary、R11 provenance、copy identity、dual manifest 与 `WRITE_STOPPED`。除第 8 节列出的两处外，已核分母/解析/身份与实际证据一致。

## 5. 内容分母与系统性反证抽样

### 5.1 全量结构分母

- 对象 N=116：95 glyph（80 TEXT + 15 FORMULA）与 21 graphic（8 node border + 7 line/arrow + 5 arrowhead + 1 math rule）；object ID、safe filename 无重复，索引连续；missing-stroke、foreign-pixel、clip failure 总数均 0。
- 全无序对象对 C=6670=`116×115/2`：期望集合 6670、实际唯一集合 6670，missing/extra/reversed/self/unknown 均 0；最终 raw intersection 非零 0；critical=50。
- `after_overlap_report` 为 6019 行、失败 0；其相对 6670 的 651 个省略项精确分解为 intended endpoint 15、math-rule composition 9、other-independent 180、same-parent 447，均仍存在于 canonical all-pairs 6670 账内。
- taxonomy element=95、group=10、summary count sum=95；对象集合与 glyph 95 全等。独立复算各组 median/ratio 与 D/E/pixel 门，差异/失败均 0；effective pt <9.5 为 0。

### 5.2 PDF、全视图与目标 n

检查 1 个 PDF 与全部 5 个视图：overlay、figure crop、full page 200%、grayscale、standalone。视图原生尺寸分别为 1985×705、1985×705、1654×2339、1985×705、1985×624。未观察到裁切、非法碰撞或灰度不可辨；overlay 可见 116 个对象标注。full-page evidence 是 standalone wrapper，页面下半留白不被误当作官方集成页。

目标 `FRM_TRIAL_005`（斜体 n）独立核对：height=22、area=297、raw/pre-visible=297、occlusion=0、threshold=22；1×/8×证据中笔画、拱肩与收笔完整且 mask 纯净。

### 5.3 glyph / graphic / critical / taxonomy 极端与代表项

打开 glyph sheets 1、2、6、11、12、15、16，覆盖目标 n、CJK 代表/最小项、Latin `a`/`m` 极端项、`+`、natural-script `0`（h=24）、uppercase `N` 单例（h=33）及 annotation；未发现证据与账不符。

打开 graphic 代表项：fraction math rule、LDA border、trial shaft、trial arrowhead；均显示几何对象完整且隔离纯净。

对 11 个关系类各取代表/极端 critical bundle 并检查 raw/pre/final 与解释：`PAIR_06580`、`PAIR_04345`、`PAIR_04538`、`PAIR_00102`、`PAIR_04478`、`PAIR_03281`、`PAIR_06331`、`PAIR_00893`、`PAIR_06668`、`PAIR_05245`、`PAIR_06344`。覆盖 arrow composition、formula-rule/own-border、independent text-text、intended endpoint、math-rule composition、other-independent、own-border/text、same-parent typography、arrowhead/text、text/math-rule、text/other-border。未反证出非法 final intersection。

taxonomy 十组独立核得：annotation/CJK 2（median 35）、formula/CJK 2（40）、formula binary-op 3（29）、formula lower 5（24）、formula upper 1（33）、natural script 3（min 24, median 26, ratio 0.9230769）、node CJK 69（34/35/36）、Latin cap/asc 3（27/28/29）、Latin x-height 6（21/22/22）、trial inline lower 1（22）。same-role source 四组与 hierarchy ratio 均在声明门内。

### 5.4 manual ledger 独立性/对象特异性

manual ledgers 合计 192 决策：glyph 95、graphic 21、critical 50、view 5、semantic 3、taxonomy 10、source-same-role 4、hierarchy 4。全部 PASS；decision ID 重复 0；空 note 0；原文/规范化 note 完全重复均 0；opened 等二值字段失败 0；glyph/graphic/critical 对象集合差均 0；view path missing 0；identity 中 current bytes/SHA/7-digit mtime 差 0。八账 mtime 各不相同。

反证抽样看到对象/关系特异 note，例如 n 的 stem/arch/curl、natural-script zero 的闭合椭圆、uppercase N 的三笔、Gamma `a` 的 counter 和 1-pixel pre-occlusion、`m` 双拱、CJK 稀疏笔画、plus 双杆；critical note 逐项描述实际 pair geometry/threshold。静态扫描 R11 `.py/.ps1` 未发现 manual ledger 生产器：R11 新脚本不引用 manual；R10 machine audit 明示“不生成”，consumer validator 只读核验，seal 脚本只读 identity。因此证据呈现独立且对象特异；但“真人亲手裁决”无法仅凭静态文件作密码学证明，本审计只确认没有自动生成反证。

## 6. WRITE_STOPPED 与封后写

- 声明 stop：`2026-08-25T00:24:07.3904218Z`，ticks 639232142473904218。
- 除 `WRITE_STOPPED.json` 外最新文件：`PAYLOAD_MANIFEST.json`，ticks 639232142285824349；早于声明 stop 188,079,869 ticks（18.8079869 s）。
- `WRITE_STOPPED.json` 自身 ticks 639232142753067000；晚于最新其他文件 467,242,651 ticks（46.7242651 s），且为唯一严格最新。
- 声明 stop 后其他文件数 0；在/晚于 `WRITE_STOPPED.json` 的其他文件数 0。
- 最终只读快照仍为 ordinary 1060 / payload 1057；未观察到 TeX 系进程。本审计没有据此声称历史上绝无外部进程，只确认审计未启动/干预 TeX，且封后文件事实为 0 写。

## 7. 已闭合的 control 哈希

| control | bytes | SHA-256 |
|---|---:|---|
| `PAYLOAD_MANIFEST.csv` | 189993 | `E48C8EF3A01984AB8AB4D32598D0B6952BD10BD1A5FECBC290DF6247393DFC1E` |
| `PAYLOAD_MANIFEST.json` | 341487 | `334D94959F39BCF8EACBCAA3C33280FF8B9D86A7E2095EBBBA82B297073A6742` |
| `WRITE_STOPPED.json` | 1440 | `6D9E96F9A5DE5A01222663FDEA7B4A625EACF33C8612175ADD29D18F65A2460D` |

## 8. 决定性差异

### D1 — provenance 路径为未展开占位符

`R11_COPY_PROVENANCE.md` 实际写的是：

```text
Source: $src
Target: $dst
```

而不是 R10 source 与 R11 target 的真实路径。静态阅读 `R11_copy_seal.ps1` 可定位原因：生成 here-string 时对变量使用了反引号转义，因而把 `$src`/`$dst` 原样落盘。虽然 1052 行 copy-identity 已让本审计能够从外部给定根独立闭合实际 source/destination，这仍是新增 provenance 控制文件本身的虚假/不完整声明。

### D2 — `WRITE_STOPPED` JSON 解析分母与字段语义不符

`WRITE_STOPPED.json` 声明：

```json
"json_excluding_write_stopped": 69
```

当前 FS 实际共有 71 个 JSON，仅排除 `WRITE_STOPPED.json` 后应为 70；69 是同时排除 `PAYLOAD_MANIFEST.json` 与 `WRITE_STOPPED.json` 后的 payload JSON 数。对照同一对象中 `csv: 24` 恰为包含 `PAYLOAD_MANIFEST.csv` 的全部 CSV 数，而非 payload CSV 23，故不存在一致的“parse 字段默认只数 payload”解释。文件全部 71/71 可解析，缺陷是声明分母/命名不自洽；`parse.all_pass=true` 不能消除此差异。

这两项均位于 R11 为修复 R10 后新引入的 control/provenance 层，而非继承内容层。任务明确要求“所有声明文件分母与解析”，严格 schema 又要求 bottom-level 与 terminal summary 一致，因此不能把它们降格为无关文字瑕疵。

## 9. 可复核事实/命令（只读）

以下为审计所用命令形态；不得替换为执行 R11/R10 内脚本：

```powershell
$files = Get-ChildItem -LiteralPath $root -Recurse -File
$payload = @($files | Where-Object { @('PAYLOAD_MANIFEST.csv','PAYLOAD_MANIFEST.json','WRITE_STOPPED.json') -notcontains $_.Name })
$files.Count; $payload.Count

Get-FileHash -LiteralPath $path -Algorithm SHA256
(Get-Item -LiteralPath $path).LastWriteTimeUtc.Ticks.ToString([Globalization.CultureInfo]::InvariantCulture)

@($files | Where-Object Extension -eq '.json').Count
@($files | Where-Object { $_.Extension -eq '.json' -and $_.Name -ne 'WRITE_STOPPED.json' }).Count
@($payload | Where-Object Extension -eq '.json').Count

Get-Content -LiteralPath $json -Raw -Encoding UTF8 | ConvertFrom-Json -DateKind String
Get-Content -LiteralPath $csv -Encoding UTF8 | ConvertFrom-Csv
Get-Item -LiteralPath $root -Stream *
```

关键全零差结论由当前 FS 独立复算得到，不依赖候选 validator 的自报 PASS。

## 10. 报告自身哈希约定

Canonical-self SHA-256：`5D1943F971AC5FC469781D658C936F8821D556E4FB7BA9EF9D0CFC21C2030ED4`

为避免“把最终文件散列写入文件自身会改变被散列字节”的递归矛盾，本字段采用可复核 canonical 定义：以最终 UTF-8 报告字节为输入，但先将上行反引号内恰好 64 位十六进制值替换成 64 个 ASCII `0`，再计算 SHA-256。最终文件的普通 SHA-256 在正式 handoff 中另行给出。

## 11. 结论与权限边界

R11 已成功证明 ordinary=payload+3、1057 manifest↔FS 的 path/bytes/SHA/ticks 全零差、基础 1052 R10→R11 lossless identity 全零差、新五文件纳入双 manifest、validator 身份与独立枚举逻辑成立、内容分母/视觉抽样未见反证、ADS/cache 为零且封后 0 写。可是 D1/D2 使 R11 的 provenance/terminal declaration 仍不自洽，严格 root audit 必须拒绝。

本 REJECT 不否定 R10 内容层已通过的门，也不授权提交、主线集成、官方候选、fresh SA1、A_LOCAL_PASS 或 SA3。

ROOT_REJECT_R11
