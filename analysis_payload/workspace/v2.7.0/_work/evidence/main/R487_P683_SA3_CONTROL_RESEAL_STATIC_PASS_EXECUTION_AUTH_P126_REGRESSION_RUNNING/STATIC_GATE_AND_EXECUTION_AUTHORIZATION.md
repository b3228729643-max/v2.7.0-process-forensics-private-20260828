# Revision 487｜P683 SA3 control reseal static gate

## Frozen identities

- controller=`P683_SA3_CONTROL_RESEAL_V1_CONTROLLER.ps1`，23,517 bytes，SHA-256=`D516DA1B25B6BC6BB3F3878B0B3BE4841B89D0592A73C3551E129039436A831B`，ReadOnly，PowerShell AST errors0。
- auditor=`P683_SA3_CONTROL_RESEAL_V1_AUDITOR.ps1`，19,173 bytes，SHA-256=`7EBCC4727C8573660505F2B9E93F55E1B6957E00D2CF019E25872E86D691DEFB`，ReadOnly，PowerShell AST errors0。
- controller AST command sites：Move-Item1、New-Item2、Remove-Item0、process-management0、While/Do0、TeX0；auditor为Move/New/Remove/process/loop/TeX全0。

## Main independent static recomputation

- rejected source manifest实陂rows42=`FILE39+DIRECTORY2+ROOT1`，root relative path=`.`。
- 39 file canonical paths duplicate0，manifest↔actual material case-sensitive set diff0；2 directory canonical paths duplicate0，manifest↔actual subdir set diff0；old manifest/marker listed as material0。
- old manifest/marker SHA-256精确为`6552FAD53836A9D0E3A0368A98C868AD3BB8B4C2BC955C27F1D231D89920294E` / `435C310BEBB54CE13403133A7487D4769954F53D223F87049BA1C7684E1B66D9`。
- new root Leaf/Container/Any=false、Parent=true；root-external artifacts为empty；controller/auditor invocation0/0。

## Code-path acceptance

- controller在创建新root前硬验authorization token、source/new/artifacts absence、old control hashes与canonical sets；source before snapshot写在root外。
- 它仅复制39 manifest-bound files，对每个relative/resolved path、bytes、SHA-256、Creation/LastWrite FILETIME立即复算；新增identity/provenance后payload41，manifest/audit完成后premarker files43。
- hygiene门先完成；随后43 files与全部dirs/root先设ReadOnly且校验。marker在root外以UTF-8 no-BOM、13行one-key-per-line构建，FILETIME为`max(max-other+10,000,000 ticks, now+600,000,000 ticks)`，先设ReadOnly；controller唯一Move-Item将其移入root。
- move之后controller对new root只执行Get/enumerate/hash，所有snapshot/result只写root外；没有任何后续root content/attribute write site。
- separate auditor不创建/修改new root，独立复算source before/current、copy identity、provenance、manifest41、ordinary44、all-tree ReadOnly、marker13行绑定、strict-latest including files/dirs/root、at-or-after0、parse/ADS/cache-pyc/reparse0、postmarker snapshot0。

## Exact authorization

- 仅授controller token=`MAIN_R486_P683_SA3_CONTROL_RESEAL_V1_EXECUTE_ONCE_GRANTED`，invocation1/retry0/首错停。
- 仅在controller natural success/exit0后，允许冻结auditor invocation1/retry0/首错停。
- 禁修改脚本、第二调用、repair/reseal/replacement；禁PDF/render/visual/N/C/pair/manual/glyph/math/semantic/page重跑；禁TeX/source/Git/central/process/new UID/role。
- P683仍为SA3，这是control-only授权，未计C_LOCAL。
