$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$Controller = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\P126_R11_STATIC_SEAL_CONTROLLER_20260828.ps1'
$Auditor = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\P126_R11_STATIC_SEAL_AUDITOR_20260828.ps1'
$KnownReadOnlyRoot = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\STRICT_R10_SA2_STATIC_TWO_HARD_PATCH_R115_20260828'
function Test-Marker([string[]]$Lines) {
    $bad = @($Lines | Where-Object { $_ -notmatch '^[A-Z0-9_]+=[^=\t\r\n]+$' })
    $keys = @($Lines | ForEach-Object { ($_ -split '=', 2)[0] })
    $duplicates = @($keys | Group-Object -CaseSensitive | Where-Object { $_.Count -ne 1 })
    [pscustomobject]@{ Bad = $bad.Count; Duplicate = $duplicates.Count }
}
$fileGate = @(@(Get-Item -LiteralPath $Controller, $Auditor -Force) | Where-Object { -not $_.IsReadOnly })
$dirGate = @(@(Get-Item -LiteralPath $KnownReadOnlyRoot -Force) | Where-Object { ($_.Attributes -band [IO.FileAttributes]::ReadOnly) -eq 0 })
$valid = Test-Marker @('A=1', 'B=two')
$invalid = Test-Marker @('A=1', 'A=2', 'BAD', "TAB`tX=1")
if ($fileGate.Count -ne 0 -or $dirGate.Count -ne 0) { throw 'REAL_RO_GATE_MICROTEST' }
if ($valid.Bad -ne 0 -or $valid.Duplicate -ne 0) { throw 'VALID_MARKER_MICROTEST' }
if ($invalid.Bad -lt 2 -or $invalid.Duplicate -ne 1) { throw 'INVALID_MARKER_MICROTEST' }
[pscustomobject]@{
    strict_mode = 'Latest'
    file_ro_gate_writable = $fileGate.Count
    dir_ro_gate_writable = $dirGate.Count
    valid_marker_bad = $valid.Bad
    valid_marker_duplicate = $valid.Duplicate
    invalid_marker_bad = $invalid.Bad
    invalid_marker_duplicate = $invalid.Duplicate
    empty_array_count = @().Count
    verdict = 'PASS'
} | ConvertTo-Json -Compress
