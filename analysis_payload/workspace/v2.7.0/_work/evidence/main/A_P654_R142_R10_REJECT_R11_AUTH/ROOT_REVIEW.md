# P654 R10 root拒收与R11重封授权（Revision 142）

- 主线完整读取独立报告`P654_R10_ROOT_AUDIT.md`及`A-R141-P654-SA2-R10-ROOT-REJECT-20260825`三份handoff文件，接受裁决`ROOT_REJECT_R10`。
- 唯一决定性缺口：R10 payload manifest把mtime写成6位微秒，独立按NTFS 100ns ticks回读时935/1052不等、117相等，最大偏差600ns，12项大于0.5µs。Goal/protocol/schema未预定义量化容差，不能以bytes/SHA闭合替代mtime身份。
- 其余已通过事实只保留为可复用内容审计：source/wrapper/PDF绑定，N116/C6670、critical50、目标n H22/area297、R8 taxonomy 95→10组D/E0、人工192、视觉覆盖、parse/ADS/cache和封后0写。
- P654保持SA2；R10永久只读，不提交、不派fresh SA1/SA3、不计A_LOCAL_PASS。
- R11只授权evidence-only lossless reseal：R10的1052 payload须以path/bytes/SHA/NTFS ticks逐项同一迁移；新manifest用十进制字符串无损记录100ns ticks并由独立validator回读文件系统，path/bytes/SHA/ticks全部0差。新provenance/copy identity/validator等实际文件须纳入R11 payload；仅新两manifest与新WRITE_STOPPED自排除。
- R11不得改源或启TeX；封存后须由另一全新独立root执行R11 manifest/control全审计与差分反证，只能在基础payload同一被证明后复用R10已通过内容门。

结论：`ROOT_REJECT_R10_ACCEPTED__R11_EVIDENCE_ONLY_RESEAL_AUTHORIZED`。
