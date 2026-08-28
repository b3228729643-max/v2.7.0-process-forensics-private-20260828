# R549｜P126 R19A V1 静态拒收与 P690 同实例恢复

- 时间：`2026-08-28T20:00:37+08:00`
- 官方候选：R116，817页，4,967,281 bytes，SHA-256=`19F3D0413AD8C72B4D855B2C23246F10DD7ACECF2FD1E984AEE9F25E1051D3DC`。
- inventory：`30 SA1 / 30 SA2 / 0 SA3 / 40 local pass`；严格最终`0/99`；B累计`66/66`。

## P126 R19A V1

Main逐文件全文审查controller13,824/SHA-256 `64D79132776EAF1CC0E2BD6D58B13708C954F9FDCDCE003FDEB9C2F668DA5A9A`与auditor11,865/SHA-256 `19E5EE42D2B37B7C4144E4A7060F936050632DD102D38A965E770E2F6A113F66`。两脚本ReadOnly、AST0；fixed destination、V1 stage/controller-result/auditor-result均absent；invocation0/0。

V1的复制顺序、premarker ReadOnly、root-external future marker与sole-final move正确，但auditor只验证28-key marker的少数字段，未验证BOM、每行恰一个`=`、ordered exact key、roots/counts/source/reverse/invocation/postwrites/encoded FILETIME；provenance、seal audit与controller result仅查子集；manifest未用ordinal exact maps证明duplicate/missing/extra。因此V1永久STATIC REJECT且不得编辑或调用。

仅授权新HANDOFF=`A-R116-P126-SA2-STATIC-TEXT-CURVE-COLLISION-PATCH-CONTROL-RESEAL-V2-20260828`、OPERATION=`P126_R116_R19_STATIC_EVIDENCE_ONLY_CONTROL_RESEAL_V2`的V2 STATIC CORRECTION。Destination仍保持startup-absent；V2必须补齐完整逐键/逐字段、ordinal set、old before=after-copy=final=current与controller/auditor destination four-snapshot门。本轮仍不授权执行或build。

## P690

Main root-external只读进度核对发现accepted fixed root创建近30分钟仍0 files，遂要求同一canonical instance做非破坏性status check。Child状态为`pending_init`，不是正常工具调用中；first error/blocker=`NONE`。上次只读PDF提取被incoming steer中断，target/state写0。Parent只对同一 `/root/sa2_fig_p690_r116_r168_readonly_v1` 发送follow-up，未restart、duplicate、replace、新建root/UID/role。

同一child现已恢复；R116 PDF、current P690 source与exact chapter bytes/SHA命中，已读current caption/label与semantic context，正独立定位physical page。下一自然checkpoint必须回localization与fresh denominator/all-pairs，然后继续唯一sealed SA2链。
