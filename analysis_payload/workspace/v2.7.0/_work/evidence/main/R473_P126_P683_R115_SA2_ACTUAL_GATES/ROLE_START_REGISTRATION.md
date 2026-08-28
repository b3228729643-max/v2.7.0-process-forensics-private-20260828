# R473｜P126 / P683 R115 R168 只读 SA2 actual 与双门登记

时间：2026-08-28T06:52:41+08:00

## A / P126

- HANDOFF_ID：`A-R115-P126-SA2-R168-READONLY-20260828`
- actual：`/root/p126_r115_r168_sa2`
- model/effort/fork：`gpt-5.6-sol/xhigh/none`
- fixed root：`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\STRICT_R1_SA2_R168_READONLY_R115_20260828`
- Parent immediate pre-spawn：UID parent与root均Leaf/Container/Any=false。
- Child pre-artifact：UID parent与root均Leaf/Container/Any=false；随后仅同一实例创建fixed root一次。Main只读回看root为Container=true。

## C / P683

- HANDOFF_ID：`C-FIG-P683-01-R115-SA2-R168-READONLY-ADJUDICATION-V1`
- actual：`/root/sa2_fig_p683_r115_r168_readonly_v1`
- model/effort/fork：`gpt-5.6-sol/xhigh/none`
- fixed root：`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P683-01\sa2_r115_r168_readonly_adjudication_v1`
- Parent immediate pre-spawn：UID parent与root均Leaf/Container/Any=false。
- Child pre-artifact：UID parent与root均Leaf/Container/Any=false，gate时artifact/parent/root creation=0；仅同一实例获准各创建一次。

## Main 裁决

两条actual identity与R472授权逐项一致，parent/child双absence门闭合。P126/P683在权威inventory中本来均为SA2，故角色启动不改变`31 SA1 / 32 SA2 / 0 SA3 / 37 local pass`。Main分别发送ACK，仅这两个同一实例可按R472 exact-file-only白名单直跑一次sealed结果；禁restart、duplicate、replacement、old metrics/evidence、第三UID/role、TeX/build/source/Git/central/process management。此前local-pass全部材料继续永久冻结。
