# P654 R9 controller pre-launch failure

- Status: BUILD_FAIL_NO_CANDIDATE_PRE_TEX.
- Controller process: one invocation, natural exit code 1.
- Engine invocation: 0.
- latexmk invocation: 0.
- PDF count: 0.
- DIRECT_INVOCATION_START.json: absent because the path-identity check failed before Start-Process.
- DIRECT_INVOCATION_RESULT.json: absent for the same reason.
- Postcheck: latexmk, lualatex, luatex and luahbtex all NONE.
- Source and wrapper remained unchanged.

## Root cause

The controller was saved as UTF-8 without BOM and was invoked with Windows PowerShell 5 powershell.exe. That host decoded the Chinese path literals with the active ANSI/CP936 interpretation before the script's runtime console-encoding assignments could help. The wrapper path therefore became mojibake and the first Get-Item check failed.

The prior successful R7 record identifies D:\PowerShell7\pwsh.exe as its parent executable. A future retry can avoid this failure by using that PowerShell 7 host or a separately frozen BOM-safe controller, but this R9 grant forbids automatic retry and a second invocation. The current controller was not modified or rerun.
