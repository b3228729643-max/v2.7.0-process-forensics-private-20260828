$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$Root = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\STRICT_R11_SA2_STATIC_LABEL6_REPOSITION_R115_20260828'
$Result = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\P126_R11_STATIC_SEAL_AUDITOR_RESULT_20260828.json'
function H([string]$Path) { (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToUpperInvariant() }
function R([string]$Path) { [IO.Path]::GetRelativePath($Root, $Path).Replace('\', '/') }
function T([datetime]$Value) { $Value.ToUniversalTime().Ticks }
if (Test-Path -LiteralPath $Result) { throw 'RESULT_EXISTS' }
$files = @(Get-ChildItem -LiteralPath $Root -Recurse -Force -File)
$dirs = @((Get-Item -LiteralPath $Root -Force)) + @(Get-ChildItem -LiteralPath $Root -Recurse -Force -Directory)
if ($files.Count -ne 13) { throw 'ORDINARY_COUNT' }
$writableFiles = @($files | Where-Object { -not $_.IsReadOnly })
$writableDirs = @($dirs | Where-Object { ($_.Attributes -band [IO.FileAttributes]::ReadOnly) -eq 0 })
if ($writableFiles.Count -ne 0 -or $writableDirs.Count -ne 0) { throw 'READONLY_GATE' }
$rows = @(Import-Csv -LiteralPath (Join-Path $Root 'PAYLOAD_MANIFEST.csv'))
if ($rows.Count -ne 10) { throw 'MANIFEST_COUNT' }
$actual = @{}
foreach ($file in @($files | Where-Object { $_.Name -notin @('PAYLOAD_MANIFEST.csv', 'SEAL_AUDIT.json', 'WRITE_STOPPED') })) { $actual[(R $file.FullName)] = $file }
$errors = 0
foreach ($row in $rows) {
    if (-not $actual.ContainsKey($row.relative_path)) { $errors++; continue }
    $file = $actual[$row.relative_path]
    if ([int64]$row.bytes -ne $file.Length -or $row.sha256 -ne (H $file.FullName) -or [int64]$row.creation_time_utc_ticks -ne (T $file.CreationTimeUtc) -or [int64]$row.last_write_time_utc_ticks -ne (T $file.LastWriteTimeUtc)) { $errors++ }
}
if ($errors -ne 0) { throw 'IDENTITY_GATE' }
$marker = Get-Item -LiteralPath (Join-Path $Root 'WRITE_STOPPED') -Force
$lines = @([IO.File]::ReadAllLines($marker.FullName, [Text.UTF8Encoding]::new($false)))
$bad = @($lines | Where-Object { $_ -notmatch '^[A-Z0-9_]+=[^=\t\r\n]+$' })
$duplicates = @($lines | ForEach-Object { ($_ -split '=', 2)[0] } | Group-Object -CaseSensitive | Where-Object { $_.Count -ne 1 })
if ($lines.Count -ne 15 -or $bad.Count -ne 0 -or $duplicates.Count -ne 0) { throw 'MARKER_GATE' }
$atOrAfter = @($files + $dirs | Where-Object { $_.FullName -ne $marker.FullName -and $_.LastWriteTimeUtc.Ticks -ge $marker.LastWriteTimeUtc.Ticks })
if ($atOrAfter.Count -ne 0) { throw 'LATEST_GATE' }
$nonMarkerMax = ($files + $dirs | Where-Object { $_.FullName -ne $marker.FullName } | ForEach-Object { $_.LastWriteTimeUtc.Ticks } | Measure-Object -Maximum).Maximum
$csvFail = 0; foreach ($file in @($files | Where-Object Extension -eq '.csv')) { try { $null = @(Import-Csv -LiteralPath $file.FullName) } catch { $csvFail++ } }
$jsonFail = 0; foreach ($file in @($files | Where-Object Extension -eq '.json')) { try { $null = Get-Content -LiteralPath $file.FullName -Raw -Encoding utf8 | ConvertFrom-Json } catch { $jsonFail++ } }
$ads = 0; foreach ($file in $files) { $ads += @((Get-Item -LiteralPath $file.FullName -Stream * -ErrorAction SilentlyContinue) | Where-Object Stream -ne ':$DATA').Count }
$reparse = @($files + $dirs | Where-Object { ($_.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0 }).Count
if ($csvFail + $jsonFail + $ads + $reparse -ne 0) { throw 'HYGIENE_GATE' }
$output = [ordered]@{schema='P126_R11_STATIC_SEAL_AUDITOR_RESULT_V1';invocation_count=1;retry_count=0;exit=0;status='STATIC_ONLY_NOT_RENDERED_NOT_PASS';static_content_gate='PASS_READY_REQUEST_BUILD_SLOT';payload_count=10;control_count=3;ordinary_count=13;directories_including_root=$dirs.Count;readonly_files=$files.Count;readonly_directories=$dirs.Count;identity_errors=$errors;marker_sha256=H $marker.FullName;marker_lines=$lines.Count;marker_bad=$bad.Count;marker_duplicate=$duplicates.Count;strict_latest_margin_ticks=[int64]$marker.LastWriteTimeUtc.Ticks-[int64]$nonMarkerMax;at_or_after=0;csv_parse_fail=$csvFail;json_parse_fail=$jsonFail;ads=$ads;reparse=$reparse;postmarker_writes=0}
[IO.File]::WriteAllText($Result, (($output | ConvertTo-Json -Depth 5) + "`n"), [Text.UTF8Encoding]::new($false))
$output | ConvertTo-Json -Compress
