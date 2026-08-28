# Cleanup exception — calibration recompile output

Timestamp: 2026-08-24 Asia/Shanghai, during R5 SA1 punctuation-calibration
recompile.

## What happened

An attempted `lualatex` invocation passed `-output-directory=$out` literally
to the native executable, rather than expanding the PowerShell variable.  The
compiler consequently wrote four calibration leaves into the already-existing
literal directory below the frozen source worktree.  No business `.tex`, build
entry point, central status file, or prior evidence file was edited.

The four newly generated leaves were, before cleanup:

1. `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\讲义源码\合并总册\$out\low_profile_calibration.aux`
2. `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\讲义源码\合并总册\$out\low_profile_calibration.idx`
3. `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\讲义源码\合并总册\$out\low_profile_calibration.log`
4. `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\讲义源码\合并总册\$out\low_profile_calibration.pdf`

The live compiler transcript established the PDF output as one page / 29,296
bytes.  The pre-delete listing established the `.aux` as 230 bytes and `.idx`
as 0 bytes.  The pre-delete log byte count and individual SHA-256 values were
**not captured before deletion**.  They are intentionally recorded as unknown,
not reconstructed or inferred after the fact.

## Why the scope was attributable to this R5 run

All four leaf names exactly match the R5-only input
`low_profile_calibration.tex`; their modification time was the just-completed
calibration compiler invocation (13:07 local time).  The surrounding directory
also contained pre-existing unrelated `current_page.*`,
`current_standalone.*`, and `symbols.*` files.  Those files were excluded from
the target set.

## Actual cleanup invocation and verification

Before deletion, all four explicit leaf paths above were tested with
`Test-Path -LiteralPath`.  The actual PowerShell invocation used a prevalidated
array containing exactly those four literal resolved paths:

```powershell
Remove-Item -LiteralPath $targets -Force
```

No recursion and no wildcard were used.  This did not meet the preferred
pre-delete hash-capture order, which is the reason for this exception record.
After deletion, each of the four paths was rechecked with
`Test-Path -LiteralPath` and was absent.  The surviving directory file list was
verified as only:

```text
current_page.aux
current_page.fdb_latexmk
current_page.fls
current_page.idx
current_page.ilg
current_page.ind
current_page.log
current_page.pdf
current_standalone.aux
current_standalone.fdb_latexmk
current_standalone.fls
current_standalone.idx
current_standalone.ilg
current_standalone.ind
current_standalone.log
current_standalone.pdf
symbols.idx
symbols.ilg
symbols.ind
```

## Impact on verdict

This is a process exception for an evidence-only calibration compiler cleanup.
It is separate from the R5 figure result: all formal R5 measurements and final
artifacts are being generated exclusively inside
`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\evidence\figures\FIG-P602-01\STRICT_R5_REQUAL_R96_SA1_CONT_20260824`.
