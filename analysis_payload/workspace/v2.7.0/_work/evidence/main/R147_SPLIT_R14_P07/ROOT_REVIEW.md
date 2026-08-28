# Revision 147 主线裁决记录

时间：2026-08-25T10:58:11+08:00

## 图域拆分

- 用户明确要求新增`v2.7.0支线3`并把原支线1逐图工作对半分。
- C工作树/分支已从当前主线HEAD建立，权威scope为drawing-index B51--B99中排除FIG-P608-01、FIG-P654-01、FIG-P715-01后的46幅。
- A保留B01--B50与三幅例外；A已确认当前本地链与C域冲突UID为0。
- 本次只改执行所有权，不改变99图inventory角色或完成数。

## P654 R14

- 主线完整读取R14B五文件并验算未来总数、逐扩展关系、future script bytes/SHA和PowerShell AST后，只授一次PowerShell7 prepare→validator→seal。
- prepare第一次运行即在复制前exit1：`Where-Object Count -ne1`被PowerShell7解析为参数名。后续validator/seal均未执行，R10基础文件未复制。
- 主线检出R14B同类命令模式缺陷恰有两处；失败根永久只读。下一轮只允许R14C静态预检，必须修正两处谓词、更新身份，并增加不写future root的PowerShell7微测试和紧凑比较运算符lint。

## B-P07

- R1机械身份仍有效，但B的物理页719视觉FAIL优先于主线较窄预检。
- 主线delegated SA1-B渲染页序列遗漏719，因此其PASS不具接受效力。
- R2只授权V5-C05局部合并近重复自检段，并保留两个KN ID及全部条件/提交/停止语义；一个条件Resume槽已授。R2必须重绘718--721并检查新AUX全覆盖。

## 未改变项

- 主线HEAD：`eea4060c5229168e2b973bbaea81cf391e7a9dfd`，clean。
- 官方R101：814页A4、4,947,496 bytes、SHA-256 `0870FF226DC383875C4A1B6EABB06AAB942317DA294D90D2864B3030D46DF1A1`。
- inventory：43 SA1 / 55 SA2 / 0 SA3 / 1 A_LOCAL_PASS；严格最终0/99。
