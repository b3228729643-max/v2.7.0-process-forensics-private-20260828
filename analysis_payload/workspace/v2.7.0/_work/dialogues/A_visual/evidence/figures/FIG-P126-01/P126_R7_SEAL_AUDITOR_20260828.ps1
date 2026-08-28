$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$root = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\STRICT_R7_SA2_ABSOLUTE_LEGEND_KEY_PATCH_R115_DIRECT_BUILD_20260828'
$controllerResultPath = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\P126_R7_SEAL_CONTROLLER_RESULT_20260828.json'
$auditPath = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\P126_R7_POSTSEAL_AUDIT_20260828.json'
$reportPath = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\P126_R7_LOCAL_SA2_FAIL_REPORT_20260828.md'
$handoffPath = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\P126_R7_LOCAL_SA2_FAIL_HANDOFF_20260828.md'
$source = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_A_visual\src\绘图源码\第01册_数学基础与统计学习基本理论\V1-C08\fig_v1_c08_coordinate.tex'
$pdf = Join-Path $root 'build\v260_FIG-P126-01_standalone.pdf'
$utf8NoBom = [Text.UTF8Encoding]::new($false)

function Get-Sha([string]$Path) { (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToUpperInvariant() }
function Get-Relative([string]$Path) { [IO.Path]::GetRelativePath($root,$Path).Replace('\','/') }
function Is-Readonly([IO.FileSystemInfo]$Item) { (($Item.Attributes -band [IO.FileAttributes]::ReadOnly) -ne 0) }
function Get-Snapshot {
  $rows = [Collections.Generic.List[string]]::new()
  $items = @(@(Get-ChildItem -LiteralPath $root -Recurse -Force) + @(Get-Item -LiteralPath $root) | Sort-Object FullName)
  foreach ($item in $items) {
    $kind = if ($item.PSIsContainer) {'D'} else {'F'}
    $bytes = if ($item.PSIsContainer) {0L} else {[long]$item.Length}
    $sha = if ($item.PSIsContainer) {''} else {Get-Sha $item.FullName}
    $relative = if ($item.FullName -ceq $root) {'.'} else {Get-Relative $item.FullName}
    $rows.Add("$kind`t$relative`t$bytes`t$sha`t$($item.CreationTimeUtc.Ticks)`t$($item.LastWriteTimeUtc.Ticks)`t$([int]$item.Attributes)")
  }
  $text = [string]::Join("`n",$rows) + "`n"
  $bytes = $utf8NoBom.GetBytes($text)
  $sha256 = [Security.Cryptography.SHA256]::Create()
  return [ordered]@{count=$rows.Count;sha256=[Convert]::ToHexString($sha256.ComputeHash($bytes));rows=$rows}
}

foreach ($path in @($auditPath,$reportPath,$handoffPath)) { if (Test-Path -LiteralPath $path) { throw "external output preexists: $path" } }
$controllerResult = Get-Content -LiteralPath $controllerResultPath -Raw | ConvertFrom-Json
if ($controllerResult.exit_code -ne 0 -or $controllerResult.controller_invocation_count -ne 1 -or $controllerResult.retry_count -ne 0) { throw 'controller result mismatch' }
$markerPath = Join-Path $root 'WRITE_STOPPED'
$manifestCsv = Join-Path $root 'PAYLOAD_MANIFEST.csv'
$manifestJson = Join-Path $root 'PAYLOAD_MANIFEST.json'
$presealPath = Join-Path $root 'PRESEAL_VALIDATION.json'
$markerLines = @(Get-Content -LiteralPath $markerPath)
$badMarkerLines = @($markerLines | Where-Object { $_ -notmatch '^[A-Z0-9_]+=[^\t\r\n]+$' })
$markerKeys = @($markerLines | ForEach-Object { ($_ -split '=',2)[0] })
$duplicateMarkerKeys = @($markerKeys | Group-Object -CaseSensitive | Where-Object { $_.Count -ne 1 })
$markerMap = @{}
foreach ($line in $markerLines) { $parts=$line -split '=',2; $markerMap[$parts[0]]=$parts[1] }
$requiredKeys = @('SCHEMA','HANDOFF_ID','UID','ROLE','VERDICT','ROOT','PAYLOAD_COUNT','CONTROL_COUNT','ORDINARY_COUNT','MANIFEST_CSV_SHA256','MANIFEST_JSON_SHA256','PRESEAL_VALIDATION_SHA256','SOURCE_BYTES','SOURCE_SHA256','PDF_BYTES','PDF_SHA256','N','C','HARD_DEFECT_COUNT','CONTROLLER_INVOCATION_COUNT','RETRY_COUNT','POST_BUILD_TEX_INVOCATION_COUNT','PREPARED_UTC','WSTOP_LAST_WRITE_UTC_TICKS')
$missingKeys = @($requiredKeys | Where-Object { -not $markerMap.ContainsKey($_) })
if ($badMarkerLines.Count -ne 0 -or $duplicateMarkerKeys.Count -ne 0 -or $missingKeys.Count -ne 0 -or $markerLines.Count -ne $requiredKeys.Count) { throw 'marker syntax/key failure' }

$payloadRows = @(Import-Csv -LiteralPath $manifestCsv)
$manifestObject = Get-Content -LiteralPath $manifestJson -Raw | ConvertFrom-Json
$controls = @('PAYLOAD_MANIFEST.csv','PAYLOAD_MANIFEST.json','PRESEAL_VALIDATION.json','WRITE_STOPPED')
$actualPayload = @(Get-ChildItem -LiteralPath $root -Recurse -File -Force | Where-Object { (Get-Relative $_.FullName) -notin $controls } | Sort-Object { Get-Relative $_.FullName })
$rowDuplicates = @($payloadRows | Group-Object -Property relative_path -CaseSensitive | Where-Object { $_.Count -ne 1 })
$expectedSet = @($payloadRows.relative_path | Sort-Object -CaseSensitive)
$actualSet = @($actualPayload | ForEach-Object { Get-Relative $_.FullName } | Sort-Object -CaseSensitive)
$setDiff = @(Compare-Object -ReferenceObject $expectedSet -DifferenceObject $actualSet -CaseSensitive)
$identityErrors = [Collections.Generic.List[string]]::new()
foreach ($row in $payloadRows) {
  $path = Join-Path $root (($row.relative_path -replace '/','\'))
  if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { $identityErrors.Add("missing:$($row.relative_path)"); continue }
  $item = Get-Item -LiteralPath $path
  if ([long]$row.bytes -ne [long]$item.Length) { $identityErrors.Add("bytes:$($row.relative_path)") }
  if ([string]$row.sha256 -cne (Get-Sha $path)) { $identityErrors.Add("sha:$($row.relative_path)") }
  if ([long]$row.creation_time_utc_ticks -ne [long]$item.CreationTimeUtc.Ticks) { $identityErrors.Add("ctime:$($row.relative_path)") }
  if ([long]$row.last_write_time_utc_ticks -ne [long]$item.LastWriteTimeUtc.Ticks) { $identityErrors.Add("mtime:$($row.relative_path)") }
}
if ($manifestObject.payload_count -ne $payloadRows.Count -or @($manifestObject.rows).Count -ne $payloadRows.Count) { throw 'JSON manifest count mismatch' }

$allFiles = @(Get-ChildItem -LiteralPath $root -Recurse -File -Force)
$allDirs = @(@(Get-ChildItem -LiteralPath $root -Recurse -Directory -Force) + @(Get-Item -LiteralPath $root))
$writableFiles = @($allFiles | Where-Object { -not (Is-Readonly $_) })
$writableDirs = @($allDirs | Where-Object { -not (Is-Readonly $_) })
$marker = Get-Item -LiteralPath $markerPath
$otherItems = @(@(Get-ChildItem -LiteralPath $root -Recurse -Force | Where-Object { $_.FullName -cne $markerPath }) + @(Get-Item -LiteralPath $root))
$maxOtherTicks = [long](($otherItems | Measure-Object -Property LastWriteTimeUtc -Maximum).Maximum.Ticks)
$atOrAfter = @($otherItems | Where-Object { $_.LastWriteTimeUtc.Ticks -ge $marker.LastWriteTimeUtc.Ticks })
$extraStreams = [Collections.Generic.List[string]]::new()
foreach ($file in $allFiles) {
  foreach ($stream in @(Get-Item -LiteralPath $file.FullName -Stream * -ErrorAction SilentlyContinue)) {
    if ($stream.Stream -cne ':$DATA') { $extraStreams.Add("$($file.FullName):$($stream.Stream)") }
  }
}
$pyc = @(Get-ChildItem -LiteralPath $root -Recurse -File -Force | Where-Object { $_.Name -match '\.(pyc|pyo)$' })
$badCache = @(Get-ChildItem -LiteralPath $root -Recurse -Directory -Force | Where-Object { $_.Name -in @('__pycache__','.pytest_cache','.mypy_cache') })
$reparse = @(@(Get-ChildItem -LiteralPath $root -Recurse -Force) + @(Get-Item -LiteralPath $root) | Where-Object { ($_.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0 })
$csvFiles = @(Get-ChildItem -LiteralPath $root -Recurse -File -Filter '*.csv' -Force)
$jsonFiles = @(Get-ChildItem -LiteralPath $root -Recurse -File -Filter '*.json' -Force)
$parseErrors = [Collections.Generic.List[string]]::new()
foreach ($file in $csvFiles) { try { [void]@(Import-Csv -LiteralPath $file.FullName) } catch { $parseErrors.Add($file.FullName) } }
foreach ($file in $jsonFiles) { try { [void](Get-Content -LiteralPath $file.FullName -Raw | ConvertFrom-Json) } catch { $parseErrors.Add($file.FullName) } }
$snapshot1 = Get-Snapshot
Start-Sleep -Milliseconds 250
$snapshot2 = Get-Snapshot
$postmarkerDiff = @(Compare-Object -ReferenceObject @($snapshot1.rows) -DifferenceObject @($snapshot2.rows) -CaseSensitive)
$postmarkerStable = ($snapshot1.sha256 -ceq $snapshot2.sha256)
$errors = [Collections.Generic.List[string]]::new()
if ($rowDuplicates.Count -ne 0) {$errors.Add('manifest duplicates')}
if ($setDiff.Count -ne 0) {$errors.Add('manifest set mismatch')}
if ($identityErrors.Count -ne 0) {$errors.Add('manifest identity mismatch')}
if ($writableFiles.Count -ne 0 -or $writableDirs.Count -ne 0) {$errors.Add('readonly mismatch')}
if ($marker.LastWriteTimeUtc.Ticks -le $maxOtherTicks -or $atOrAfter.Count -ne 0) {$errors.Add('marker not strict latest')}
if (-not $postmarkerStable) {$errors.Add('postmarker snapshot drift')}
if ($extraStreams.Count -ne 0) {$errors.Add('ADS present')}
if ($pyc.Count -ne 0 -or $badCache.Count -ne 0 -or $reparse.Count -ne 0) {$errors.Add('hygiene failure')}
if ($parseErrors.Count -ne 0) {$errors.Add('parse failure')}
if ((Get-Sha $source) -cne '20671687B41E0DD6C8D36774A7E669B0ABC55C5BBE8955BE39FA69137F52F279' -or (Get-Sha $pdf) -cne '8EB275DEB382AD25E26C19F4B9A0EFBE01771317FE7DE475C5F2E330BCD789D6') {$errors.Add('source or PDF identity drift')}
if ($errors.Count -ne 0) { throw ('audit failed: ' + [string]::Join('; ',$errors)) }

$audit = [ordered]@{
  schema='P126_R7_POSTSEAL_AUDIT_V1';handoff_id='A-R115-P126-SA2-DIRECT-BUILD-R7-20260828'
  verdict='LOCAL_SA2_FAIL_RETURN_TO_MAIN_SOURCE_SCOPE';audit_invocation_count=1;retry_count=0;exit_code=0
  payload_count=$payloadRows.Count;control_count=4;ordinary_count=$allFiles.Count;directory_count=$allDirs.Count
  manifest_duplicate_count=$rowDuplicates.Count;manifest_set_diff_count=$setDiff.Count;manifest_identity_error_count=$identityErrors.Count
  readonly_files=@($allFiles | Where-Object { Is-Readonly $_ }).Count;readonly_directories=@($allDirs | Where-Object { Is-Readonly $_ }).Count
  marker_lines=$markerLines.Count;marker_unique_keys=@($markerKeys | Sort-Object -Unique).Count;marker_bad_lines=$badMarkerLines.Count
  marker_sha256=Get-Sha $markerPath;marker_ticks=[long]$marker.LastWriteTimeUtc.Ticks
  strict_latest_margin_ticks=[long]$marker.LastWriteTimeUtc.Ticks-$maxOtherTicks;at_or_after_excluding_marker=$atOrAfter.Count
  postmarker_snapshot1_sha256=$snapshot1.sha256;postmarker_snapshot2_sha256=$snapshot2.sha256;postmarker_content_attribute_diff_count=if($postmarkerStable){0}else{1}
  csv_parse_count=$csvFiles.Count;json_parse_count=$jsonFiles.Count;parse_error_count=$parseErrors.Count
  ads_count=$extraStreams.Count;pyc_count=$pyc.Count;bad_cache_count=$badCache.Count;reparse_count=$reparse.Count
  source_sha256=Get-Sha $source;pdf_sha256=Get-Sha $pdf;errors=@()
}
[IO.File]::WriteAllText($auditPath, ($audit | ConvertTo-Json -Depth 7) + "`n", $utf8NoBom)
$report = @"
# P126 R7 sealed local SA2 failure report

`A-R115-P126-SA2-DIRECT-BUILD-R7-20260828` is sealed as `LOCAL_SA2_FAIL_RETURN_TO_MAIN_SOURCE_SCOPE`.

- PDF: 33,952 bytes / SHA-256 `8EB275DEB382AD25E26C19F4B9A0EFBE01771317FE7DE475C5F2E330BCD789D6`.
- Fresh denominator: N58 = 25 glyph + 9 line + 4 rect + 20 curve; C1653 complete unordered pairs.
- Hard defects: x2 legend remains a continuous 73px run; numeral6 is crossed by the y-axis and a contour; numeral7 is occluded by a blue arrowhead and blue node.
- Regression: clip/tofu/missing/unresolved0; positive-definite quadratic, alternating exact coordinate minimization, strict objective decrease and caption semantics PASS.
- Seal: payload$($audit.payload_count), controls4, ordinary$($audit.ordinary_count), files/directories all ReadOnly, WSTOP unique strict-latest margin$($audit.strict_latest_margin_ticks) ticks, at-or-after0, postmarker0, parse/ADS/cache/reparse0.

No source edit, TeX, commit, fresh role or second UID occurred after build release. Main review and explicit narrow source scope are requested; no patch is self-authorized.
"@
$handoff = @"
HANDOFF_ID=A-R115-P126-SA2-DIRECT-BUILD-R7-20260828
UID=FIG-P126-01
ROLE=SA2
VERDICT=LOCAL_SA2_FAIL_RETURN_TO_MAIN_SOURCE_SCOPE
N=58
C=1653
HARD_DEFECT_COUNT=3
HARD_DEFECT_IDS=HARD-LEGEND-X2-CONTINUOUS;HARD-LABEL6-AXIS-CONTOUR-OVERLAP;HARD-LABEL7-MARKER-ARROW-OCCLUSION
SEALED_ROOT=$root
PAYLOAD_COUNT=$($audit.payload_count)
CONTROL_COUNT=4
ORDINARY_COUNT=$($audit.ordinary_count)
WSTOP_SHA256=$($audit.marker_sha256)
WSTOP_STRICT_LATEST_MARGIN_TICKS=$($audit.strict_latest_margin_ticks)
POSTMARKER_CONTENT_ATTRIBUTE_DIFF_COUNT=0
NEXT_ROUTE_REQUEST=MAIN_NARROW_SINGLE_SOURCE_SCOPE
SELF_ACCEPTED=false
"@
[IO.File]::WriteAllText($reportPath,$report,$utf8NoBom)
[IO.File]::WriteAllText($handoffPath,$handoff,$utf8NoBom)
(Get-Item -LiteralPath $auditPath).IsReadOnly=$true
(Get-Item -LiteralPath $reportPath).IsReadOnly=$true
(Get-Item -LiteralPath $handoffPath).IsReadOnly=$true
[ordered]@{audit=$audit;external_report=[ordered]@{path=$reportPath;bytes=(Get-Item $reportPath).Length;sha256=Get-Sha $reportPath};external_handoff=[ordered]@{path=$handoffPath;bytes=(Get-Item $handoffPath).Length;sha256=Get-Sha $handoffPath}} | ConvertTo-Json -Depth 8
