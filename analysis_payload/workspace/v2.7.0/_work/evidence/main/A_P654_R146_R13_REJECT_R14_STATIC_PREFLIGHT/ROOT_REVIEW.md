# P654 R13 主线复核与 R14 静态预封存授权

- 时间：2026-08-25T09:58:00+08:00
- 对象：`FIG-P654-01`
- 中央角色：保持 `SA2`
- R13 root 报告：`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\reports\P654_R13_ROOT_AUDIT.md`
- 报告 SHA-256：`F92555C0BED0039A55E99D50A30BA43EFE85F67D574D85A9CCA4B0E6824EF5E7`
- 主线裁决：接受 `ROOT_REJECT_R13`

## 硬缺口

R13 的文件总数均正确，但预验与 WSTOP 的三个扩展快照都漏计各自最终 JSON self：最终 payload/control/ordinary JSON 实际为 `71/2/73`，声明为 `70/1/72`。其他 R10 基础1052、R13 payload1059、双manifest、provenance、解析/ADS/cache/seal与内容层反证只作差分输入，不能覆盖声明错误。

## R14 当前仅授权静态预封存

本阶段禁止复制 R10 基础、禁止生成 manifest/WSTOP、禁止 seal。只允许在全新非sealed R14 preflight 目录写：

1. draft prepare/validator/seal 脚本；
2. `R14_COUNT_MODEL.json`；
3. `R14_STATIC_PREFLIGHT.md`。

主线复核这些文件前，不得执行 draft 脚本。

### 强制最终集合模型

- final payload：1059；扩展快照必须是 R13 fresh root 实测 payload 全集，其中 JSON=71、CSV=23。
- final controls：3，严格为 manifest CSV 1、manifest JSON 1、WSTOP JSON 1；扩展快照必须为 CSV=1、JSON=2。
- final ordinary：1062；逐扩展等于 payload+controls，其中 JSON=73、CSV=24。
- 三个快照各自的 values 求和必须分别等于1059、3、1062；每个扩展都必须满足 ordinary=payload+control。

### self 计数实现口径

- preseal validator 从“尚未写入预验报告”的 payload 枚举开始，必须显式将即将写入的预验报告作为 `JSON +1` 加入 projected final payload；不得只给总数加1而漏掉扩展。
- seal 在 WSTOP 写入前枚举已存在的 final payload 与两个 manifests，再显式将即将写入的 WSTOP 作为 control `JSON +1` 加入 projected final controls/ordinary；不得把只含两manifest的快照命名为 final control。
- WSTOP 中禁止使用 `actual_*` 描述尚未写入自身时的集合；改用 `declared_final_payload_extensions`、`declared_final_control_extensions`、`declared_final_ordinary_extensions`。fresh root 负责把声明与最终 FS actual 比较。
- draft 中必须有四类断言：总数求和、扩展值求和、逐扩展 ordinary=payload+control、JSON/CSV 明确值 `71/23 + 2/1 = 73/24`。

## 后续门

主线只读接受静态 preflight 后，才会另行授予 R14 copy/seal。R10/R11/R12/R13永久只读；P654不改源、不启TeX、Git/fresh角色，不提交、不计A_LOCAL_PASS。inventory保持`43/55/0/1`，严格最终0/99。
