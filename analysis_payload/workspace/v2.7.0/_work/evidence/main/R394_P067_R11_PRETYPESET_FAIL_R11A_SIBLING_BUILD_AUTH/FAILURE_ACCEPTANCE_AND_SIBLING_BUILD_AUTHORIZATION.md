# R394：P067 R11 pre-typeset失败接受与R11A sibling build授权

- 时间：2026-08-27T19:55:54+08:00。
- P067保持SA2，source static patch未提交且身份仍4014 bytes/SHA-256=`11BF3681D069F6A38C479B3074F39F93E8EB6144FF155AC543508E3589A51144`。

## R11失败接受

- HANDOFF=`A-R113-P067-SA2-DIRECT-BUILD-R11-20260827`；controller invocation1、natural exit1。
- typeset invocation0、retry0、latexmk invocation0、version probe0、child/PDF0。
- 首错为controller line64 `Split-Path -LiteralPath $wrapper -Parent`在PowerShell7产生parameter-set错误；位置在`Start-Process`之前，故不把本次计为LuaLaTeX typeset。
- failed R11 root仅root/build/texcache三目录、ordinary0/PDF0；该root永久冻结，不得reuse、补写、retimestamp、删除或作为candidate/evidence。
- external `BUILD_FAILURE.json` 1675 bytes/SHA=`45CE24DBF083CFE2B04AAA934EDC2351C7E71D0B641D51FF8FC47350C58B8AF6`；handoff1772 bytes/SHA=`C90057C00B68EDBDC542C6BD9B68DE3A86284726A9F58ADECD4A01C859E5878D`。冻结controller6154 bytes/SHA=`D9AD484721F3E86B5258FE99EDA4035B978113965AA7AA4D94F1F7AE244232CA`。
- source与wrapper388 bytes/SHA=`ADDF75D1C82DAB9AB4D5A76E6B241DA1CEB7AED9C2E536106ECFD7710B2D14BF`未变。曾见外部latexmk1，未查询归属/管理/中止，随后自然归零；本轮新preflight TeX0。

## R11A唯一sibling授权

- 新root（授权时file=false/dir=false）：`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P067-01\STRICT_R11A_SA2_P4_COORDINATE_DIRECT_BUILD_R113_20260827`。
- 新controller必须在root创建/实际调用前完成：PowerShell7 AST parse0；使用`[IO.Path]::GetDirectoryName($wrapper)`取得working directory；在同一pwsh7 host对精确wrapper路径微测返回真实parent；旧失败controller保持不改。
- 除R11A HANDOFF/root/output路径与上述working-directory修正外，不得改变build参数或扩展权限。实际调用前再次确认TeX-family count0；若非0则HOLD，不消费调用。
- 允许恰一次root-external controller invocation和其内部恰一次direct LuaLaTeX typeset child；retry0、latexmk0、version-probe0、new texcache。记录controller/child PID、准确start/end、natural exit、唯一PDF、source/wrapper/controller before/after身份。
- 禁fullbook、第二R11A调用、失败后自动第三槽、并发TeX、源写、第二源、commit、fresh role、第二UID、central state写。成功或失败先自然释放并回终态TeX；成功后才可非TeX复核。

- inventory保持`31 SA1 / 38 SA2 / 0 SA3 / 31 local pass`。
