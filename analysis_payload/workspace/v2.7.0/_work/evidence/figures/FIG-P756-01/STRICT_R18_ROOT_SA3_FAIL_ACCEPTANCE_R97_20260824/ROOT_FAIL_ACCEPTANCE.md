# FIG-P756-01｜隔离 SA3 失败的 root 验收

- Root decision：**接受 `FAIL_TO_SA2` 路由**。
- 本结论仅确认图37.8当前仍有硬失败；不构成图形PASS，也不增加严格最终完成数。
- SA3审查候选：官方R97，813页，SHA-256 `062AD81020CB19A5C6688A45C73E00965F5060E0960A69AF820D7DC154DEE814`；物理页801／印刷页788。
- 当前连续候选R98仅物理页591相对R97变化，物理页801逐页栅格相同；故本硬失败同样适用于R98。
- 图源SHA-256：`00213AE30379E4337830B1C4957BE4CB7B1E99BE88144E2D7D262998E1B6CAAA`。

## Root 独立复算

- 对象账：113个唯一对象 = 55 TEXT + 58 GRAPHIC。
- 全pair账：6,328 = `C(113,2)`；pair ID与无序对象键均6,328个唯一值，自配对0、未知对象0；TT 1,485、TG 3,190、GG 1,653。
- pair终态：4,236普通PASS、33逐项意图接触、2,050非竞争不透明背景、9同一语义文字父对象；硬pair失败0。pair通过不能抵消字形硬失败。
- rawdict 380行 = 378个可见glyph + 2个不可见空格；可见glyph仅`GLY0215`失败。glyph人工台账380行，失败1；graphic人工台账58行、非PASS 0；critical人工台账129行，五种原生1×/mask/overlay/8×打开字段缺失0。
- 字体对象55行全PASS，最小有效字号9.6pt；drawing path 39行；clip 93行、失败0；低轮廓校准20行、失败1。

## 决定性硬失败与实际开图

`GLY0215`为U+FF1A全角冒号，目标原生300dpi `H_INK/area = 10/34`。两个完全同codepoint、字体、有效字号、RGB且排除目标页的官方参照`CAL02_01`与`CAL02_02`均为`10/37`。因此：

- 高度比：`10/10 = 1.0`；
- 面积比：`34/37 = 0.918918918918… < 0.92`。

Root实际打开`glyph_contact_sheet_11`、目标的original/overlay/mask-only/8×四卡、两个参照各自的original/overlay/mask-only/8×四卡。目标与参照mask均纯净、完整；目标两个点的整数面积确实小于参照。该门禁止四舍五入、视觉例外或由其他通过项抵消，故接受`FAIL_TO_SA2`。

Root另打开官方300dpi全页、彩色图体裁片与灰度裁片；整体无可见重叠、裁切或突兀字号。这些通过项不治愈0.918918…的硬门失败。

## 封存完整性

- `evidence_manifest.json`声明/实有载荷均2,905项，总字节25,583,457；root逐项重算missing 0、bytes mismatch 0、SHA-256 mismatch 0。
- 实际文件2,908 = 2,905载荷 + `evidence_manifest.json` + `MANIFEST.sha256` + `WRITE_STOPPED.md`；额外集合精确为这三项。
- `evidence_manifest.json` root重算SHA-256为`543b8cd19c2efe0d8f45aacb0dc4dcb25f3e60019fc1543264f38998ea8fff8b`，与`MANIFEST.sha256`一致。
- 零字节0；非默认ADS 0；ADS枚举错误0；stop后写入0；`WRITE_STOPPED.md`是最后写入。

## 路由

FIG-P756-01从隔离SA3正式转入唯一串行SA2队列。下一SA2只可做最小、语义不变且字体协调的局部修复；局部通过后仍须root构建新的官方候选，再走全新SA1、全新隔离SA3与root签发。
