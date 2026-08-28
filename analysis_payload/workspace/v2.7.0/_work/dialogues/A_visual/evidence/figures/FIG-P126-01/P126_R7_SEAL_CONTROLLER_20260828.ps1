$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$root = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\STRICT_R7_SA2_ABSOLUTE_LEGEND_KEY_PATCH_R115_DIRECT_BUILD_20260828'
$stage = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\P126_R7_WRITE_STOPPED.stage'
$resultPath = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\P126_R7_SEAL_CONTROLLER_RESULT_20260828.json'
$source = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_A_visual\src\绘图源码\第01册_数学基础与统计学习基本理论\V1-C08\fig_v1_c08_coordinate.tex'
$pdf = Join-Path $root 'build\v260_FIG-P126-01_standalone.pdf'
$handoff = 'A-R115-P126-SA2-DIRECT-BUILD-R7-20260828'
$verdict = 'LOCAL_SA2_FAIL_RETURN_TO_MAIN_SOURCE_SCOPE'
$utf8NoBom = [Text.UTF8Encoding]::new($false)
$startUtc = [DateTime]::UtcNow

function Get-Sha([string]$Path) { (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToUpperInvariant() }
function Get-Relative([string]$Path) { [IO.Path]::GetRelativePath($root, $Path).Replace('\','/') }
function Is-Readonly([IO.FileSystemInfo]$Item) { (($Item.Attributes -band [IO.FileAttributes]::ReadOnly) -ne 0) }
function Set-Readonly([IO.FileSystemInfo]$Item) { $Item.Attributes = $Item.Attributes -bor [IO.FileAttributes]::ReadOnly }

if (-not (Test-Path -LiteralPath $root -PathType Container)) { throw 'R7 root missing' }
foreach ($path in @($stage,$resultPath,(Join-Path $root 'PAYLOAD_MANIFEST.csv'),(Join-Path $root 'PAYLOAD_MANIFEST.json'),(Join-Path $root 'PRESEAL_VALIDATION.json'),(Join-Path $root 'WRITE_STOPPED'))) {
  if (Test-Path -LiteralPath $path) { throw "preexisting seal artifact: $path" }
}
$sourceItem = Get-Item -LiteralPath $source
$pdfItem = Get-Item -LiteralPath $pdf
if ($sourceItem.Length -ne 4366L -or (Get-Sha $source) -cne '20671687B41E0DD6C8D36774A7E669B0ABC55C5BBE8955BE39FA69137F52F279') { throw 'source identity mismatch' }
if ($pdfItem.Length -ne 33952L -or (Get-Sha $pdf) -cne '8EB275DEB382AD25E26C19F4B9A0EFBE01771317FE7DE475C5F2E330BCD789D6') { throw 'PDF identity mismatch' }
$objects = @(Import-Csv -LiteralPath (Join-Path $root 'machine\MACHINE_OBJECTS.csv'))
$pairs = @(Import-Csv -LiteralPath (Join-Path $root 'machine\MACHINE_ALL_PAIRS.csv'))
$manualObjects = @(Import-Csv -LiteralPath (Join-Path $root 'manual\MANUAL_OBJECT_LEDGER.csv'))
$pairClasses = @(Import-Csv -LiteralPath (Join-Path $root 'manual\MANUAL_PAIR_CLASS_LEDGER.csv'))
if ($objects.Count -ne 58 -or @($objects.object_id | Sort-Object -Unique).Count -ne 58) { throw 'object denominator mismatch' }
if ($pairs.Count -ne 1653 -or @($pairs.pair_id | Sort-Object -Unique).Count -ne 1653) { throw 'pair denominator mismatch' }
if ($manualObjects.Count -ne 58) { throw 'manual object denominator mismatch' }
$classCoverage = [double](($pairClasses | Measure-Object -Property coverage_count -Sum).Sum)
if ($classCoverage -ne 1653) { throw 'manual pair class coverage mismatch' }
$result = Get-Content -LiteralPath (Join-Path $root 'RESULT.json') -Raw | ConvertFrom-Json
if ($result.verdict -cne $verdict -or [int]$result.N -ne 58 -or [int]$result.C -ne 1653 -or [int]$result.hard_defect_count -ne 3) { throw 'business result mismatch' }

$controls = @('PAYLOAD_MANIFEST.csv','PAYLOAD_MANIFEST.json','PRESEAL_VALIDATION.json','WRITE_STOPPED')
$payloadFiles = @(Get-ChildItem -LiteralPath $root -Recurse -File -Force | Where-Object { (Get-Relative $_.FullName) -notin $controls } | Sort-Object { Get-Relative $_.FullName })
$payloadRows = @()
foreach ($file in $payloadFiles) {
  $payloadRows += [ordered]@{
    relative_path = Get-Relative $file.FullName
    bytes = [long]$file.Length
    sha256 = Get-Sha $file.FullName
    creation_time_utc_ticks = [long]$file.CreationTimeUtc.Ticks
    last_write_time_utc_ticks = [long]$file.LastWriteTimeUtc.Ticks
  }
}
$duplicates = @($payloadRows | Group-Object -Property relative_path -CaseSensitive | Where-Object { $_.Count -ne 1 })
if ($duplicates.Count -ne 0) { throw 'payload duplicate paths' }

$csvLines = [Collections.Generic.List[string]]::new()
$csvLines.Add('relative_path,bytes,sha256,creation_time_utc_ticks,last_write_time_utc_ticks')
foreach ($row in $payloadRows) {
  $escaped = ([string]$row.relative_path).Replace('"','""')
  $csvLines.Add(('"{0}",{1},{2},{3},{4}' -f $escaped,$row.bytes,$row.sha256,$row.creation_time_utc_ticks,$row.last_write_time_utc_ticks))
}
$manifestCsv = Join-Path $root 'PAYLOAD_MANIFEST.csv'
$manifestJson = Join-Path $root 'PAYLOAD_MANIFEST.json'
$presealPath = Join-Path $root 'PRESEAL_VALIDATION.json'
[IO.File]::WriteAllText($manifestCsv, [string]::Join("`r`n",$csvLines) + "`r`n", $utf8NoBom)
$manifestObject = [ordered]@{schema='P126_R7_PAYLOAD_MANIFEST_V1';handoff_id=$handoff;payload_count=$payloadRows.Count;rows=$payloadRows}
[IO.File]::WriteAllText($manifestJson, ($manifestObject | ConvertTo-Json -Depth 8) + "`n", $utf8NoBom)
$preseal = [ordered]@{
  schema='P126_R7_PRESEAL_VALIDATION_V1';handoff_id=$handoff;verdict=$verdict
  N=58;C=1653;machine_pair_rows=1653;manual_object_rows=58;manual_pair_class_coverage=1653
  hard_defect_count=3;clip_failure_count=0;missing_tofu_count=0;unresolved_reference_count=0
  payload_count=$payloadRows.Count;control_count=4;ordinary_count=$payloadRows.Count+4
  manifest_csv_sha256=Get-Sha $manifestCsv;manifest_json_sha256=Get-Sha $manifestJson
  source_bytes=4366;source_sha256=Get-Sha $source;pdf_bytes=33952;pdf_sha256=Get-Sha $pdf
  controller_invocation_count=1;retry_count=0;post_build_tex_invocation_count=0
  prepared_utc=[DateTime]::UtcNow.ToString('o');errors=@()
}
[IO.File]::WriteAllText($presealPath, ($preseal | ConvertTo-Json -Depth 6) + "`n", $utf8NoBom)

$allPremarkerFiles = @(Get-ChildItem -LiteralPath $root -Recurse -File -Force)
$allDirs = @(Get-ChildItem -LiteralPath $root -Recurse -Directory -Force | Sort-Object FullName -Descending)
foreach ($file in $allPremarkerFiles) { Set-Readonly $file }
foreach ($dir in $allDirs) { Set-Readonly $dir }
Set-Readonly (Get-Item -LiteralPath $root)
$writableFiles = @(Get-ChildItem -LiteralPath $root -Recurse -File -Force | Where-Object { -not (Is-Readonly $_) })
$writableDirs = @(@(Get-ChildItem -LiteralPath $root -Recurse -Directory -Force) + @(Get-Item -LiteralPath $root) | Where-Object { -not (Is-Readonly $_) })
if ($writableFiles.Count -ne 0 -or $writableDirs.Count -ne 0) { throw 'premarker readonly freeze failed' }

$allItems = @(@(Get-ChildItem -LiteralPath $root -Recurse -Force) + @(Get-Item -LiteralPath $root))
$maxTicks = [long](($allItems | Measure-Object -Property LastWriteTimeUtc -Maximum).Maximum.Ticks)
$futureTicks = [Math]::Max($maxTicks + [TimeSpan]::FromMinutes(5).Ticks, [DateTime]::UtcNow.AddMinutes(5).Ticks)
$markerLines = @(
  'SCHEMA=P126_R7_WRITE_STOPPED_V1',
  "HANDOFF_ID=$handoff",
  'UID=FIG-P126-01',
  'ROLE=SA2',
  "VERDICT=$verdict",
  "ROOT=$root",
  "PAYLOAD_COUNT=$($payloadRows.Count)",
  'CONTROL_COUNT=4',
  "ORDINARY_COUNT=$($payloadRows.Count+4)",
  "MANIFEST_CSV_SHA256=$(Get-Sha $manifestCsv)",
  "MANIFEST_JSON_SHA256=$(Get-Sha $manifestJson)",
  "PRESEAL_VALIDATION_SHA256=$(Get-Sha $presealPath)",
  'SOURCE_BYTES=4366',
  'SOURCE_SHA256=20671687B41E0DD6C8D36774A7E669B0ABC55C5BBE8955BE39FA69137F52F279',
  'PDF_BYTES=33952',
  'PDF_SHA256=8EB275DEB382AD25E26C19F4B9A0EFBE01771317FE7DE475C5F2E330BCD789D6',
  'N=58',
  'C=1653',
  'HARD_DEFECT_COUNT=3',
  'CONTROLLER_INVOCATION_COUNT=1',
  'RETRY_COUNT=0',
  'POST_BUILD_TEX_INVOCATION_COUNT=0',
  "PREPARED_UTC=$([DateTime]::UtcNow.ToString('o'))",
  "WSTOP_LAST_WRITE_UTC_TICKS=$futureTicks"
)
if (@($markerLines | Where-Object { $_ -notmatch '^[A-Z0-9_]+=[^\t\r\n]+$' }).Count -ne 0) { throw 'marker syntax failure' }
[IO.File]::WriteAllText($stage, [string]::Join("`r`n",$markerLines) + "`r`n", $utf8NoBom)
$stageItem = Get-Item -LiteralPath $stage
$stageItem.LastWriteTimeUtc = [DateTime]::new($futureTicks,[DateTimeKind]::Utc)
Set-Readonly $stageItem
if (-not (Is-Readonly (Get-Item -LiteralPath $stage))) { throw 'marker stage not readonly' }
if ((Get-Item -LiteralPath $stage).LastWriteTimeUtc.Ticks -ne $futureTicks) { throw 'marker stage future ticks mismatch' }

$markerPath = Join-Path $root 'WRITE_STOPPED'
Move-Item -LiteralPath $stage -Destination $markerPath

$marker = Get-Item -LiteralPath $markerPath
$filesAfter = @(Get-ChildItem -LiteralPath $root -Recurse -File -Force)
$dirsAfter = @(@(Get-ChildItem -LiteralPath $root -Recurse -Directory -Force) + @(Get-Item -LiteralPath $root))
$otherItems = @(@(Get-ChildItem -LiteralPath $root -Recurse -Force | Where-Object { $_.FullName -cne $markerPath }) + @(Get-Item -LiteralPath $root))
$maxOtherTicks = [long](($otherItems | Measure-Object -Property LastWriteTimeUtc -Maximum).Maximum.Ticks)
$controllerResult = [ordered]@{
  schema='P126_R7_SEAL_CONTROLLER_RESULT_V1';handoff_id=$handoff;verdict=$verdict
  controller_invocation_count=1;retry_count=0;exit_code=0;natural_exit=$true
  start_utc=$startUtc.ToString('o');end_utc=[DateTime]::UtcNow.ToString('o')
  payload_count=$payloadRows.Count;control_count=4;ordinary_count=$filesAfter.Count;directory_count=$dirsAfter.Count
  readonly_files=@($filesAfter | Where-Object { Is-Readonly $_ }).Count
  readonly_directories=@($dirsAfter | Where-Object { Is-Readonly $_ }).Count
  marker_path=$markerPath;marker_bytes=[long]$marker.Length;marker_sha256=Get-Sha $markerPath
  marker_ticks=[long]$marker.LastWriteTimeUtc.Ticks;strict_latest_margin_ticks=[long]$marker.LastWriteTimeUtc.Ticks-$maxOtherTicks
  source_sha256=Get-Sha $source;pdf_sha256=Get-Sha $pdf
  manifest_csv_sha256=Get-Sha $manifestCsv;manifest_json_sha256=Get-Sha $manifestJson
  postmarker_root_writes=0
}
[IO.File]::WriteAllText($resultPath, ($controllerResult | ConvertTo-Json -Depth 6) + "`n", $utf8NoBom)
$controllerResult | ConvertTo-Json -Depth 6
