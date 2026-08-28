$ErrorActionPreference = 'Stop'
$Root = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P665-01\sa2_r113_r168_readonly_adjudication_v1'
$Parent = Split-Path -Parent $Root
$Manifest = Join-Path $Root 'SEALED_MANIFEST.csv'
$Marker = Join-Path $Root 'FINAL_MARKER.txt'
$Stage = Join-Path $Parent '__FIG-P665-01_R113_R168_SA2_FINAL_MARKER_STAGE.txt'
$HandoffId = 'C-FIG-P665-01-R113-SA2-R168-READONLY-ADJUDICATION-V1'
$Uid = 'FIG-P665-01'
$Verdict = 'SA2_NO_SOURCE_CHANGE_READY_FOR_FRESH_SA1'

if (Test-Path -LiteralPath $Manifest) { throw 'Manifest already exists; refusing duplicate seal.' }
if (Test-Path -LiteralPath $Marker) { throw 'Final marker already exists; refusing duplicate seal.' }
if (Test-Path -LiteralPath $Stage) { throw 'External marker stage already exists.' }

$AuditPath = Join-Path $Root 'machine\preseal_audit.json'
$Audit = Get-Content -LiteralPath $AuditPath -Raw | ConvertFrom-Json
foreach ($Field in 'csv_parse_errors','json_parse_errors','empty_manual_cells','pair_id_set_differences','pair_object_set_differences','replacement_character_count','placeholder_hits','additional_ads_count','cache_pyc_count','reparse_point_count') {
    if ([int]$Audit.$Field -ne 0) { throw "Premarker audit field $Field is nonzero." }
}
if ([int]$Audit.object_manual_rows -ne 16 -or [int]$Audit.pair_manual_rows -ne 120 -or [int]$Audit.pair_manual_unique_ids -ne 120 -or [int]$Audit.text_glyph_manual_rows -ne 14) {
    throw 'Premarker denominator counts are incomplete.'
}

function Get-Sha256([string]$Path) {
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToUpperInvariant()
}
function Csv-Escape([string]$Value) {
    return '"' + $Value.Replace('"','""') + '"'
}

$PayloadFiles = @(Get-ChildItem -LiteralPath $Root -Recurse -File | Sort-Object FullName)
$Lines = [Collections.Generic.List[string]]::new()
$Lines.Add('relative_path,bytes,sha256,creation_filetime_utc_ticks,last_write_filetime_utc_ticks')
foreach ($File in $PayloadFiles) {
    $Relative = $File.FullName.Substring($Root.Length + 1).Replace('\','/')
    $CreationTicks = [IO.File]::GetCreationTimeUtc($File.FullName).ToFileTimeUtc()
    $LastWriteTicks = [IO.File]::GetLastWriteTimeUtc($File.FullName).ToFileTimeUtc()
    $Lines.Add((Csv-Escape $Relative) + ',' + $File.Length + ',' + (Get-Sha256 $File.FullName) + ',' + $CreationTicks + ',' + $LastWriteTicks)
}
[IO.File]::WriteAllText($Manifest, ($Lines -join "`r`n"), [Text.UTF8Encoding]::new($false))
$ManifestRows = $PayloadFiles.Count
$ManifestSha256 = Get-Sha256 $Manifest

$AllPremarkerFiles = @(Get-ChildItem -LiteralPath $Root -Recurse -File)
$AllDirectories = @((Get-Item -LiteralPath $Root)) + @(Get-ChildItem -LiteralPath $Root -Recurse -Directory)
foreach ($File in $AllPremarkerFiles) {
    [IO.File]::SetAttributes($File.FullName, ([IO.File]::GetAttributes($File.FullName) -bor [IO.FileAttributes]::ReadOnly))
}
foreach ($Directory in ($AllDirectories | Sort-Object { $_.FullName.Length } -Descending)) {
    [IO.File]::SetAttributes($Directory.FullName, ([IO.File]::GetAttributes($Directory.FullName) -bor [IO.FileAttributes]::ReadOnly))
}

$MarkerLines = @(
    'HANDOFF_ID=' + $HandoffId
    'UID=' + $Uid
    'SEALED_ROOT=' + $Root
    'MANIFEST_ROWS=' + $ManifestRows
    'MANIFEST_SHA256=' + $ManifestSha256
    'VERDICT=' + $Verdict
)
foreach ($Line in $MarkerLines) {
    if ($Line.Contains("`t") -or $Line -notmatch '^[A-Z][A-Z0-9_]*=[^=\r\n]+$' -or $Line -match 'TODO|TBD|PLACEHOLDER|UNKNOWN') {
        throw 'Malformed marker line.'
    }
}
[IO.File]::WriteAllText($Stage, ($MarkerLines -join "`r`n"), [Text.UTF8Encoding]::new($false))
$MaxRootWrite = ($AllPremarkerFiles | ForEach-Object { [IO.File]::GetLastWriteTimeUtc($_.FullName) } | Sort-Object -Descending | Select-Object -First 1)
$MarkerBase = @([DateTime]::UtcNow, $MaxRootWrite) | Sort-Object -Descending | Select-Object -First 1
$MarkerTime = $MarkerBase.AddSeconds(2)
[IO.File]::SetCreationTimeUtc($Stage, $MarkerTime)
[IO.File]::SetLastWriteTimeUtc($Stage, $MarkerTime)
[IO.File]::SetAttributes($Stage, ([IO.File]::GetAttributes($Stage) -bor [IO.FileAttributes]::ReadOnly))
[IO.File]::Move($Stage, $Marker)

[ordered]@{
    HANDOFF_ID = $HandoffId
    UID = $Uid
    SEALED_ROOT = $Root
    MANIFEST_ROWS = $ManifestRows
    MANIFEST_SHA256 = $ManifestSha256
    VERDICT = $Verdict
    MARKER_LAST_WRITE_FILETIME_UTC_TICKS = [IO.File]::GetLastWriteTimeUtc($Marker).ToFileTimeUtc()
} | ConvertTo-Json
