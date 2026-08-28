# FIG-P637-01 R103 fresh isolated SA3｜中央接受

- 中央裁决：`ACCEPT / C_LOCAL_PASS`
- UID / role identity：`FIG-P637-01 / C-FIG-P637-01-R103-SA3-FRESH-ISOLATED-V1`
- 绑定候选：R103，物理687页、印刷674页、图33.4；PDF为817页、4,967,184 bytes、SHA-256 `9379A489E0C2A57A7DA670C98029BB27B3F1A385BF8E4C3BD14FE9B606AA0F23`。
- sealed evidence：`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P637-01\sa3_r103_fresh_isolated_v1`

## 一次性中央机械复核

- 普通文件648，严格等于manifest entries 646 + `MANIFEST.json` + `WRITE_STOPPED`；missing/extra均0。
- 对646项逐文件复算relative path、bytes、SHA-256与NTFS FILETIME 100ns，四类差异均0；manifest自身SHA与marker声明一致。
- 648/648只读；非默认ADS=0；除marker外晚于或等于marker的文件=0。marker FILETIME=`134321376260259923`。
- 九类人工账均闭合：glyph131、critical42、clip152、graphic23、view6、text-parent16、peer-role12、semantic24、hard-gate12；各表行数=预期、ID全唯一、空note0、重复note0、错误reviewer0、非通过decision0。
- machine/manual边界清楚；未发现脚本批量生成或覆盖人工裁决字段的证据。

## 分母差异裁决

- 已接受SA1以16个semantic text parent + 21个graphic计N37，并另行完整审查131个glyph；本SA3直接把131个glyph与21个graphic都纳入foreground pair分母，得到N152、C(152,2)=11,476。
- 这是同一可见元素从父文本粒度到逐glyph粒度的保守细分，不是漏项或候选漂移。更大SA3分母覆盖全部glyph、graphic、pair、clip与42个critical pair，未产生硬失败，因此接受该分母差异。

## 中央视觉与语义复核

主线实际打开并检查整页、300dpi彩色裁图、灰度裁图、对象/文字测量overlay、glyph contact与critical-pair contact。状态0--6、六次水平/竖直交替更新、`x_1/x_2`、倾斜长轴/短轴、三层等高线、说明框、题注及相邻正文一致；灰度仍可读。未见tofu、错字形、实际不可读、明显字号失衡、裁切、文字碰撞或非法对象重叠。42个交叉均为坐标轴、等高线、轨迹、箭头或主轴的合法结构交点。

## 角色迁移

`FIG-P637-01` 从SA3迁入共享第5个`A_LOCAL_PASS`桶；这不是全书最终PASS，严格完成计数仍为0/99。中央分布更新为`39 SA1 / 53 SA2 / 2 SA3 / 5 A_LOCAL_PASS`。
