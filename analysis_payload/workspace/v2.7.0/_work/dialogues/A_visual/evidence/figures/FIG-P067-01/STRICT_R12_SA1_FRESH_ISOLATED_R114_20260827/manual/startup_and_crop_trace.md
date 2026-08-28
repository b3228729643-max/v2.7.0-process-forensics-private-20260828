# Startup absence gate and pre-manual crop correction trace

## Startup absence gate

Before the evidence root was created, the exact path

`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P067-01\STRICT_R12_SA1_FRESH_ISOLATED_R114_20260827`

was checked independently as both a leaf and a container. Results were `FileExists=false` and `DirectoryExists=false`. This gate was reported to `/root` before any successful root creation. The first `New-Item` attempt used an unsupported `-LiteralPath` parameter and created nothing; the one successful creation occurred at `2026-08-27T21:10:29.9685197+08:00`.

## Pre-manual crop correction

1. Physical page 69 was independently located from the current caption text in the official R114 PDF.
2. The first mechanical crop used `[560,260,2040,930]` on the direct 300 dpi page render.
3. That first native view was actually opened. It cut into the left ordinate labels and therefore was rejected as incomplete evidence. No denominator or manual acceptance decision had yet been frozen.
4. The crop was widened to `[400,260,2040,930]`, producing the final `1640 x 670` native figure evidence.
5. The corrected native1x image was reopened and confirmed to contain both complete ordinate labels, both panels, all endpoints, and the full caption. Only then was the denominator frozen at `N=69`.

All final manual ledgers refer only to the corrected evidence. The superseded crop is not used as evidence and was not retained as a competing final file.
