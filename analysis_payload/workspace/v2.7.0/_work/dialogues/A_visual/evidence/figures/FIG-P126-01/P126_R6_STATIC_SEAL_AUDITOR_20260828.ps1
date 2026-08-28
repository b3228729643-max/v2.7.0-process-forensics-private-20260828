Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$Root = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\STRICT_R6_SA2_STATIC_ABSOLUTE_LEGEND_KEY_PATCH_R115_20260828'
$Manifest = Join-Path $Root 'PAYLOAD_MANIFEST.csv'
$Audit = Join-Path $Root 'SEAL_AUDIT.json'
$Marker = Join-Path $Root 'WRITE_STOPPED'
$ControllerResult = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\P126_R6_STATIC_SEAL_CONTROLLER_RESULT_20260828.json'
$Result = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\P126_R6_STATIC_SEAL_AUDITOR_RESULT_20260828.json'
$Utf8 = [Text.UTF8Encoding]::new($false)

function Sha([string]$Path) { return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToUpperInvariant() }
function IsRO([string]$Path) { return (([IO.File]::GetAttributes($Path) -band [IO.FileAttributes]::ReadOnly) -ne 0) }
function Rel([string]$Path) { return [IO.Path]::GetRelativePath($Root, $Path).Replace('\', '/') }
function Snapshot {
    $snapshotRows = [Collections.Generic.List[string]]::new()
    $snapshotFiles = @(Get-ChildItem -LiteralPath $Root -File -Recurse | Sort-Object FullName)
    foreach ($file in $snapshotFiles) {
        $snapshotRows.Add("F`t$(Rel $file.FullName)`t$($file.Length)`t$(Sha $file.FullName)`t$($file.CreationTimeUtc.Ticks)`t$($file.LastWriteTimeUtc.Ticks)`t$([int][IO.File]::GetAttributes($file.FullName))")
    }
    $snapshotDirs = @((Get-Item -LiteralPath $Root)) + @(Get-ChildItem -LiteralPath $Root -Directory -Recurse | Sort-Object FullName)
    foreach ($dir in $snapshotDirs) {
        $relative = if ($dir.FullName -eq $Root) { '.' } else { Rel $dir.FullName }
        $snapshotRows.Add("D`t$relative`t$($dir.CreationTimeUtc.Ticks)`t$($dir.LastWriteTimeUtc.Ticks)`t$([int][IO.File]::GetAttributes($dir.FullName))")
    }
    $snapshotText = (@($snapshotRows | Sort-Object -CaseSensitive) -join "`n") + "`n"
    return [ordered]@{ files = $snapshotFiles.Count; dirs = $snapshotDirs.Count; sha256 = [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($Utf8.GetBytes($snapshotText))) }
}

if (Test-Path -LiteralPath $Result) { throw 'result exists' }
$controller = Get-Content -LiteralPath $ControllerResult -Raw | ConvertFrom-Json
if ($controller.exit -ne 0 -or -not $controller.natural) { throw 'controller failed' }
$files = @(Get-ChildItem -LiteralPath $Root -File -Recurse)
$dirs = @((Get-Item -LiteralPath $Root)) + @(Get-ChildItem -LiteralPath $Root -Directory -Recurse)
$payload = @($files | Where-Object { $_.FullName -notin @($Manifest, $Audit, $Marker) })
$rows = @(Import-Csv -LiteralPath $Manifest)
$map = @{}
foreach ($row in $rows) { $map[[string]$row.relative_path] = $row }
$actual = @{}
foreach ($file in $payload) { $actual[(Rel $file.FullName)] = $file }
$setdiff = @(Compare-Object @($map.Keys | Sort-Object -CaseSensitive) @($actual.Keys | Sort-Object -CaseSensitive) -CaseSensitive).Count
$mismatch = 0
foreach ($key in $map.Keys) {
    if (-not $actual.ContainsKey($key)) { $mismatch++; continue }
    $row = $map[$key]; $file = $actual[$key]
    if ([long]$row.bytes -ne $file.Length -or [string]$row.sha256 -ne (Sha $file.FullName) -or [long]$row.creation_time_utc_ticks -ne $file.CreationTimeUtc.Ticks -or [long]$row.last_write_time_utc_ticks -ne $file.LastWriteTimeUtc.Ticks) { $mismatch++ }
}
$fileRO = @($files | Where-Object { -not (IsRO $_.FullName) }).Count
$dirRO = @($dirs | Where-Object { -not (IsRO $_.FullName) }).Count
$markerText = [IO.File]::ReadAllText($Marker, $Utf8)
$markerLines = @($markerText -split "`r?`n" | Where-Object { $_ -ne '' })
$markerBad = @($markerLines | Where-Object { $_ -notmatch '^[^=\s]+=[^\r\n]+$' -or $_ -match "`t|PLACEHOLDER" }).Count
$markerKeys = @{}
foreach ($line in $markerLines) { $pair = $line.Split('=', 2); if ($markerKeys.ContainsKey($pair[0])) { throw 'duplicate key' }; $markerKeys[$pair[0]] = $pair[1] }
$markerTicks = (Get-Item -LiteralPath $Marker).LastWriteTimeUtc.Ticks
$others = @($files | Where-Object FullName -ne $Marker) + @($dirs)
$maxTicks = 0L
foreach ($item in $others) { if ($item.LastWriteTimeUtc.Ticks -gt $maxTicks) { $maxTicks = $item.LastWriteTimeUtc.Ticks } }
$atOrAfter = @($others | Where-Object { $_.LastWriteTimeUtc.Ticks -ge $markerTicks }).Count
$snapshot = Snapshot
$postMismatch = @($controller.snapshot1, $controller.snapshot2 | Where-Object { $_ -ne $snapshot.sha256 }).Count
$jsonFail = 0
foreach ($file in @($files | Where-Object Extension -eq '.json')) { try { $null = Get-Content -LiteralPath $file.FullName -Raw | ConvertFrom-Json } catch { $jsonFail++ } }
$csvFail = 0
foreach ($file in @($files | Where-Object Extension -eq '.csv')) { try { $null = @(Import-Csv -LiteralPath $file.FullName) } catch { $csvFail++ } }
$resultObject = [ordered]@{
    schema = 'P126_R6_STATIC_SEAL_AUDITOR_RESULT_V1'; payload = $payload.Count; controls = 3; ordinary = $files.Count; dirs = $dirs.Count
    manifest_rows = $rows.Count; set_diff = $setdiff; identity_mismatch = $mismatch; file_readonly_fail = $fileRO; dir_readonly_fail = $dirRO
    marker_lines = $markerLines.Count; marker_keys = $markerKeys.Count; marker_bad = $markerBad; strict_margin_ticks = $markerTicks - $maxTicks
    at_or_after_excluding_marker = $atOrAfter; postmarker_mismatch = $postMismatch; json_parse_fail = $jsonFail; csv_parse_fail = $csvFail; snapshot_sha256 = $snapshot.sha256
    pass = ($payload.Count -eq 8 -and $files.Count -eq 11 -and $rows.Count -eq 8 -and $setdiff -eq 0 -and $mismatch -eq 0 -and $fileRO -eq 0 -and $dirRO -eq 0 -and $markerLines.Count -eq 21 -and $markerKeys.Count -eq 21 -and $markerBad -eq 0 -and $markerTicks -gt $maxTicks -and $atOrAfter -eq 0 -and $postMismatch -eq 0 -and $jsonFail -eq 0 -and $csvFail -eq 0)
}
if (-not $resultObject.pass) { throw ($resultObject | ConvertTo-Json -Compress) }
[IO.File]::WriteAllText($Result, (($resultObject | ConvertTo-Json -Depth 5) + "`n"), $Utf8)
[IO.File]::SetAttributes($Result, ([IO.File]::GetAttributes($Result) -bor [IO.FileAttributes]::ReadOnly))
$resultObject | ConvertTo-Json -Depth 5
