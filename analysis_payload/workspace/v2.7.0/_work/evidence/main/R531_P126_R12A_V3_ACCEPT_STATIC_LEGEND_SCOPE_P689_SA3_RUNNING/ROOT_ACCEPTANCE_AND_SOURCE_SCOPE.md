# R531 P126 R12A 接受与静态源范围

- 时间：2026-08-28T15:33:10+08:00
- inventory：`30 SA1 / 30 SA2 / 1 SA3 / 39 local pass`；严格最终0/99；B 66/66。

## R12A 控制根接受

Main独立只读复核PASS：root142 files/10 dirs含root、106,207,360 bytes，全树ReadOnly；COPY_IDENTITY137与PAYLOAD_MANIFEST139的canonical path/bytes/SHA/Creation+LastWrite mismatch0。Source snapshot=`D0230EE5E13AAD8D27C88564D884BCD44EB208AD1357CBB007DBC468C93686B0`，destination snapshot=`A1008438161718E2B458763E3A46B87C66C6819933C808AE0224936BF92B5D6E`，分别与controller/auditor全部记录一致。

Source full-tree ADS0；sealed destination full-tree ADS0。JSON10/CSV10 parse0，pyc/cache/reparse0。Marker1,588 bytes/SHA=`70DE2147270309739E11195C46489D3F1C3EE043986BE944972F2FA561195455`，28 lines/28 keys/bad/dup/BOM0、bindings0、strict-latest含rootmargin5,999,909,799 ticks、at-or-after0，stage absent。

Controller result2,881 bytes/SHA=`1A95DC239A9D4ED8389FE8E80067BAAB32C7C8822D333F3E16681A00FCBEA5EC`虽为root-external writable file，但Main绑定其当前身份并禁止修改；sealed root本身完整，故不拒收。Auditor result3,136 bytes/SHA=`C95FB6FC41C15356267CF84A91DB41BAFE2E8EE7C013AB5ADC92C371C6DAF50F`、ReadOnly。

Preserved verdict `LOCAL_SA2_FAIL_RETURN_TO_MAIN_SOURCE_SCOPE`正式接受；唯一hard=`HARD-LEGEND-X2-CONTINUOUS`。

## 唯一静态源授权

目标源current4,373 bytes/SHA=`81EFC188FA5E4827CAAB034C1EA3F7F4AFE25375DEE4046CD46F3FF49B0789BD`。只允许修改current lines67--68的x2 legend image declaration，结构必要时可紧邻增加一个唯一figure-local pgfplots style。

新handler须直接画至少三段互不相连的SLTeal水平subpaths；至少三个internal gaps各≥0.05cm（300dpi为5.906px）。不得再依赖default line legend 0--0.6cm path、`only marks`或仅把dash pattern加在该default path上。Installed pgfplots primary source/documentation须证明custom handler在legend image generation时实际生效。

Contours、q0--q7、arrows、markers、label nodes/backgrounds、axes/ranges/names、x1 legend、legend text/placement/font、quadratic/math、caption/label/alt、figure width、shared macros、其他源与build entry全部冻结。仅回STATIC_ONLY sealed evidence；不授TeX/build/commit/role。

P689同一fresh SA3继续，未接受sealed结果前不迁移inventory。
