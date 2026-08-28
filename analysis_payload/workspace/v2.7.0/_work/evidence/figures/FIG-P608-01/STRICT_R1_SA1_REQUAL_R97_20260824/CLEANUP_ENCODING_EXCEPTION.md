# Cleanup transport exception (no deletion occurred)

During the `2026-08-24 16:00` Asia/Shanghai minute, the first planned execution of
`CLEANUP_EXECUTED_EXACT.ps1` stopped before deletion. Windows PowerShell 5.1
decoded the BOM-less UTF-8 Chinese workspace path as an ANSI code page, so the
first exact command resolved to a nonexistent path and returned `PathNotFound`.

The attempted command was exactly:

```powershell
& 'C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe' -NoProfile -ExecutionPolicy Bypass -File 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\evidence\figures\FIG-P608-01\STRICT_R1_SA1_REQUAL_R97_20260824\CLEANUP_EXECUTED_EXACT.ps1'
```

No `Remove-Item` target was removed: the first command failed before it could
act and `$ErrorActionPreference = 'Stop'` terminated the session. The exact
target list and pre-delete hashes remain valid. The script generator is changed
only to write the same literal commands as UTF-8 with BOM, then the planned
post-delete existence/hash/reference checks are rerun.
