# Revision 454 — P109 R2A accepted and direct build authorized; P680 child gate passed

Time: 2026-08-28T04:18:39+08:00

## P109 R2A acceptance

Main accepts `A-R114-P109-SA2-STATIC-DOMAIN-LABEL-PATCH-CONTROL-RESEAL-V1-20260828`. The fixed sibling contains exactly five preserved static payload files and three controls, ordinary8, no subdirectories. Source-to-destination relative path, bytes, SHA, creation ticks, and last-write ticks have zero errors; old controls copied are zero. All eight files and root are ReadOnly. The marker has 12 physical valid unique `KEY=VALUE` lines and is strictly later than all other files and root by 2,999,845,527 .NET ticks; at-or-after excluding marker is zero. JSON parsing, ADS, cache/pyc, and reparse failures are zero. The rejected R2 root is unchanged.

The source remains 1,922 bytes/SHA-256 `887326D54E8DD97AA6D580EFA7CCD21FA371A94CACD36EB7029E80FC4D2D9355` with the single accepted 1+/1- static patch. It remains `STATIC_ONLY_NOT_RENDERED_NOT_PASS`.

## Unique controlled direct build authorization

Main observed latexmk/lualatex/luatex/luahbtex counts `0/0/0/0` and confirmed:

- engine `D:\texlive\2026\bin\windows\lualatex.exe`, 6,656 bytes, SHA-256 `CC944A1DB010B47FCF5CCB5D1B184CBA208FE7FEA9F18BEC414940E6FD3E24A6`;
- wrapper `v260_FIG-P109-01_standalone.tex`, 394 bytes, SHA-256 `F2594687F563AB4A11FC5D0E08F913BD53ADFEA9CF97498DB686E5C11E8B30C7`;
- patched source identity above;
- fixed R3 root `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P109-01\STRICT_R3_SA2_DOMAIN_LABEL_OPAQUE_PATCH_R114_DIRECT_BUILD_20260828` Leaf/Container/Any=false, Parent=true.

A may use one root-external PowerShell7 controller and exactly one direct LuaLaTeX child. In the same command immediately before the controller, all four TeX-family counts must still be zero; otherwise stop without invoking. Controller invocation1, child invocation1, retry0, latexmk0, version-probe0. Bind all TeX cache/config/home variables to the new root, preserve source/wrapper identities before and after, produce exactly one standalone PDF, and stop on the first error. No commit or fresh role is authorized. After a successful natural exit, release the slot and perform one non-TeX full evidence/manual/seal run on only the new PDF before requesting an atomic commit.

## P680 child gate

The same `/root/sa1_fig_p680_r114_fresh_isolated_v1` independently confirmed its exact root absent before artifacts, created it once, and matched all three exact current input identities. Its first full200 view showed that an old page assumption pointed to chapter 33 rather than the target; the child rejected that assumption before freezing any denominator or writing any manual ledger. It is now relocalizing only from the current caption within the exact allowlisted R114. No old P680/P670 evidence or directory search was used. The same instance continues once to a sealed result.

Inventory remains `32 SA1 / 33 SA2 / 0 SA3 / 35 local pass`; strict final remains `0/99`.
