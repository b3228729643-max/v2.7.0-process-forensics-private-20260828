# P654 R14C 静态预审

- 状态：`P654_R14C_STATIC_PREFLIGHT_READY_FOR_MAIN_REVIEW`
- 阶段：仅静态预审；未执行任何 R14C draft。
- P654 角色：SA2；未提交、未派 fresh SA1/SA3、未计 A_LOCAL_PASS。
- TeX：未启动。
- R14 失败执行根：永久只读；3/3 文件只读，未原地修补或重跑。
- R14C future sealed root：`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P654-01\STRICT_R14C_SA2_R10_EVIDENCE_ONLY_CONTROL_RESEAL_20260825`，当前不存在。
- 本静态目录：无 manifest、无 WRITE_STOPPED、无 seal。

## 唯一获准变化

相对已通过内容审查的 R14B 三份 draft：

1. prepare 中唯一 `Where-Object Count -ne1` 改为 `Where-Object { $_.Count -ne 1 }`。
2. validator 的 `Assert-Unique` 中唯一同类表达式作相同修改。
3. 仅同步 R14C future root、三份 draft 名称与未来脚本名称；其余 identity、CSV/JSON、source/target set、count/self-accounting 逻辑未扩改。
4. 三份脚本的唯一授权 token 统一为 `P654_R14C_COPY_SEAL_EXPLICITLY_GRANTED`，旧 R14 token 命中 0。
5. prepare provenance 与 validator preseal 的持久化 `round` 均为 `R14C`；三份授权拒绝文案均为 R14C。

逐字节获准变换复核：prepare PASS；validator PASS；seal PASS。

## 冻结身份

| 文件 | bytes | SHA-256 |
|---|---:|---|
| `R14C_prepare_draft.ps1` | 5581 | `69029D0736396CA19AD19E1FF5526A8ED426A48777C0288E0C8EC519C1FEB73B` |
| `R14C_validator_draft.ps1` | 10023 | `43784C57CE01AE83597B5F043923241AEFB8336C901D11A8BC93116C290B1D0E` |
| `R14C_seal_draft.ps1` | 7465 | `20A99AB090A0C14409B014DC2E30B4AAD6BFB2F9C35444B0B0D6585EA11EB803` |
| `R14C_COUNT_MODEL.json` | 3274 | `479975D02D5C6AFFCD47892419381A9369121DD8EA6276864761B46BC55F07F5` |

本报告的最终 bytes/SHA-256 在目录冻结后的外部回传中给出，避免自引用。

## 静态门

- PowerShell AST：3/3 scripts，错误 0。
- count model 对 draft 身份：3/3 一致，mismatch 0。
- 新授权 token：3/3；旧 R14 token：0。
- 持久化 round：R14C 2/2；旧 R14/R14B：0。
- 授权拒绝文案：R14C 3/3。
- future root：不存在。
- static controls：0。
- payload/control/ordinary：1059 / 3 / 1062。
- extension sums：1059 / 3 / 1062。
- JSON：71 + 2 = 73。
- CSV：23 + 1 = 24。
- 逐扩展 ordinary = payload + control：mismatch 0。
- R14 失败根非只读文件：0。

## Command-mode compact-operator lint

全文 lint 仅检查 `Where-Object` / `ForEach-Object` 命令参数位置中的 compact `-ne1/-eq1/-ne0/-eq0` 形态：

| 文件 | 命中 |
|---|---:|
| `R14C_prepare_draft.ps1` | 0 |
| `R14C_validator_draft.ps1` | 0 |
| `R14C_seal_draft.ps1` | 0 |
| 合计 | 0 |

## pwsh 7.6.4 无写入微测试

宿主：`D:\PowerShell7\pwsh.exe -NoProfile`。

duplicate 分支：

```powershell
$groups = @('a','a','b') | Group-Object | Where-Object { $_.Count -ne 1 }
@($groups).Count
```

输出：`1`（预期 1，PASS）。

unique 分支：

```powershell
$groups = @('a','b') | Group-Object | Where-Object { $_.Count -ne 1 }
@($groups).Count
```

输出：`0`（预期 0，PASS）。

两条微测试均未读写项目文件；未执行 prepare/validator/seal draft。

## 终态

`P654_R14C_STATIC_PREFLIGHT_READY_FOR_MAIN_REVIEW`
