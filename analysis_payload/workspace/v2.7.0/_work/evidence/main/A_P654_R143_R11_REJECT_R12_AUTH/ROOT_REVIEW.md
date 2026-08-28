# P654 R11拒收与R12控制层重封授权（Revision 143）

- 主线完整读取`P654_R11_ROOT_AUDIT.md`与`A-R141-P654-SA2-R11-ROOT-REJECT-20260825`，接受`ROOT_REJECT_R11`。
- R11已成功证明ordinary1060=payload1057+3、manifest↔FS path/bytes/SHA/ticks 0差、R10→R11基础1052同一、新5文件入manifest、内容差分与seal卫生闭合。
- 唯一拒收原因在新增控制层：`R11_COPY_PROVENANCE.md`保留字面量`$src/$dst`；`json_excluding_write_stopped=69`与当前71个JSON排除自身后70不符，混淆payload与ordinary口径。
- R10/R11永久只读；P654保持SA2，不提交、不派fresh角色、不计A_LOCAL_PASS。
- R12直接从R10基础1052重建，不复制R11新增5文件。结构化provenance必须存resolved source/target且禁止任何未展开`$`占位符。WRITE_STOPPED分别声明payload JSON、manifest JSON control、self control、ordinary total、excluding-self，以及对应CSV口径，全部由实际枚举动态计算并独立回读。
- R12仍仅evidence-only，不改源、不启TeX。封存后须由另一全新root重点全审新增控制层和1052基础同一。

结论：`ROOT_REJECT_R11_ACCEPTED__R12_CONTROL_RESEAL_AUTHORIZED`。
