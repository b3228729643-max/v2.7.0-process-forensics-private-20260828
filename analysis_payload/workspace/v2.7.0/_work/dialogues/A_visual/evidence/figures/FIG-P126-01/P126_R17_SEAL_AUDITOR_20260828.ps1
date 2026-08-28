Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$root = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\STRICT_R17_SA2_FORGET_PLOT_PATCH_R115_DIRECT_BUILD_20260828'
$source = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_A_visual\src\绘图源码\第01册_数学基础与统计学习基本理论\V1-C08\fig_v1_c08_coordinate.tex'
$pdf = Join-Path $root 'build\v260_FIG-P126-01_standalone.pdf'
$controllerResultPath = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\P126_R17_SEAL_CONTROLLER_RESULT_20260828.json'
$auditorResultPath = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\P126_R17_SEAL_AUDITOR_RESULT_20260828.json'
$reportPath = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\P126_R17_LOCAL_SA2_REPORT_20260828.md'
$handoffPath = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\P126_R17_LOCAL_SA2_HANDOFF_20260828.md'
$expectedHandoff = 'A-R115-P126-SA2-DIRECT-BUILD-R17-CONTROLLER-STATIC-20260828'
$expectedOperation = 'P126_R115_R17_NON_TEX_REVIEW_AND_SINGLE_SEAL'
$expectedVerdict = 'LOCAL_SA2_PASS_READY_FOR_MAIN_REVIEW_AND_ATOMIC_COMMIT_AUTH'
$controls = @('PAYLOAD_MANIFEST.csv','PAYLOAD_MANIFEST.json','SEAL_AUDIT.json','WRITE_STOPPED')

function Write-Utf8NoBom([string]$Path, [string]$Text) {
    [IO.File]::WriteAllText($Path, $Text, [Text.UTF8Encoding]::new($false))
}

function Get-CanonicalRelative([string]$Base, [string]$FullPath) {
    $relative = [IO.Path]::GetRelativePath($Base, $FullPath).Replace('\','/')
    if ([string]::IsNullOrWhiteSpace($relative) -or [IO.Path]::IsPathRooted($relative) -or $relative -eq '.' -or $relative.StartsWith('../',[StringComparison]::Ordinal) -or $relative.Contains('/../') -or $relative.Contains('/./')) { throw "unsafe relative path: $relative" }
    $relative
}

function Test-ReadOnly([System.IO.FileSystemInfo]$Item) {
    (($Item.Attributes -band [IO.FileAttributes]::ReadOnly) -ne 0)
}

function Get-TreeSnapshot([string]$Base) {
    $rows = [System.Collections.Generic.List[object]]::new()
    $rootItem = Get-Item -LiteralPath $Base -Force
    $rows.Add([ordered]@{kind='D';relative_path='.';bytes=0;sha256='';creation_time_utc_ticks=[int64]$rootItem.CreationTimeUtc.Ticks;last_write_time_utc_ticks=[int64]$rootItem.LastWriteTimeUtc.Ticks;attributes=[int]$rootItem.Attributes})
    foreach ($dir in @(Get-ChildItem -LiteralPath $Base -Recurse -Force -Directory | Sort-Object FullName)) {
        $rows.Add([ordered]@{kind='D';relative_path=(Get-CanonicalRelative $Base $dir.FullName);bytes=0;sha256='';creation_time_utc_ticks=[int64]$dir.CreationTimeUtc.Ticks;last_write_time_utc_ticks=[int64]$dir.LastWriteTimeUtc.Ticks;attributes=[int]$dir.Attributes})
    }
    foreach ($file in @(Get-ChildItem -LiteralPath $Base -Recurse -Force -File | Sort-Object FullName)) {
        $rows.Add([ordered]@{kind='F';relative_path=(Get-CanonicalRelative $Base $file.FullName);bytes=[int64]$file.Length;sha256=(Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash;creation_time_utc_ticks=[int64]$file.CreationTimeUtc.Ticks;last_write_time_utc_ticks=[int64]$file.LastWriteTimeUtc.Ticks;attributes=[int]$file.Attributes})
    }
    $orderedRows = @($rows | Sort-Object -Property @{Expression={$_['kind']}},@{Expression={$_['relative_path']}})
    $text = ($orderedRows | ForEach-Object { "{0}`t{1}`t{2}`t{3}`t{4}`t{5}`t{6}" -f $_['kind'],$_['relative_path'],$_['bytes'],$_['sha256'],$_['creation_time_utc_ticks'],$_['last_write_time_utc_ticks'],$_['attributes'] }) -join "`n"
    $text += "`n"
    $sha = [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData([Text.UTF8Encoding]::new($false).GetBytes($text)))
    [ordered]@{entries=$orderedRows.Count;sha256=$sha;rows=$orderedRows}
}

function Get-AdsSummary([string]$Base) {
    $items = @((Get-Item -LiteralPath $Base -Force)) + @(Get-ChildItem -LiteralPath $Base -Recurse -Force)
    $streams = 0; $nondefault = 0
    foreach ($item in $items) {
        foreach ($stream in @(Get-Item -LiteralPath $item.FullName -Stream * -Force -ErrorAction Stop)) {
            $streams++
            if ([string]$stream.Stream -cne ':$DATA') { $nondefault++ }
        }
    }
    [ordered]@{items=$items.Count;streams=$streams;nondefault=$nondefault}
}

foreach ($path in @($auditorResultPath,$reportPath,$handoffPath)) { if (Test-Path -LiteralPath $path) { throw "external output already exists: $path" } }
$controllerResult = Get-Content -LiteralPath $controllerResultPath -Raw | ConvertFrom-Json
if (-not $controllerResult.success -or $controllerResult.handoff_id -cne $expectedHandoff -or $controllerResult.operation -cne $expectedOperation -or $controllerResult.verdict -cne $expectedVerdict -or $controllerResult.controller_invocation_count -ne 1 -or $controllerResult.retry_count -ne 0) { throw 'controller result binding failed' }

$allFiles = @(Get-ChildItem -LiteralPath $root -Recurse -Force -File)
$allDirs = @(Get-ChildItem -LiteralPath $root -Recurse -Force -Directory) + @((Get-Item -LiteralPath $root -Force))
if ($allFiles.Count -ne 149 -or $allDirs.Count -ne 11) { throw 'final count mismatch' }
$fileReadonlyFailures = @($allFiles | Where-Object { -not (Test-ReadOnly (Get-Item -LiteralPath $_.FullName -Force)) }).Count
$dirReadonlyFailures = @($allDirs | Where-Object { -not (Test-ReadOnly (Get-Item -LiteralPath $_.FullName -Force)) }).Count
if ($fileReadonlyFailures -ne 0 -or $dirReadonlyFailures -ne 0) { throw 'readonly audit failed' }

$manifestCsvPath = Join-Path $root 'PAYLOAD_MANIFEST.csv'
$manifestJsonPath = Join-Path $root 'PAYLOAD_MANIFEST.json'
$sealAuditPath = Join-Path $root 'SEAL_AUDIT.json'
$markerPath = Join-Path $root 'WRITE_STOPPED'
$csvRows = @(Import-Csv -LiteralPath $manifestCsvPath)
$jsonManifest = Get-Content -LiteralPath $manifestJsonPath -Raw | ConvertFrom-Json
$jsonRows = @($jsonManifest.rows)
$sealAudit = Get-Content -LiteralPath $sealAuditPath -Raw | ConvertFrom-Json
if ($csvRows.Count -ne 145 -or $jsonRows.Count -ne 145 -or $jsonManifest.payload_count -ne 145) { throw 'manifest row count mismatch' }
$payloadFiles = @(Get-ChildItem -LiteralPath $root -Recurse -Force -File | Where-Object { $controls -cnotcontains $_.Name } | Sort-Object FullName)
if ($payloadFiles.Count -ne 145) { throw 'actual payload count mismatch' }
$actual = @{}
foreach ($file in $payloadFiles) {
    $relative = Get-CanonicalRelative $root $file.FullName
    $actual[$relative] = [ordered]@{bytes=[int64]$file.Length;sha256=(Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash;creation_time_utc_ticks=[int64]$file.CreationTimeUtc.Ticks;last_write_time_utc_ticks=[int64]$file.LastWriteTimeUtc.Ticks}
}
$manifestMismatch = 0
$seen = @{}
foreach ($row in $csvRows) {
    $relative = [string]$row.relative_path
    if ($seen.ContainsKey($relative) -or -not $actual.ContainsKey($relative)) { $manifestMismatch++; continue }
    $seen[$relative] = $true
    $item = $actual[$relative]
    if ([int64]$row.bytes -ne $item['bytes'] -or [string]$row.sha256 -cne $item['sha256'] -or [int64]$row.creation_time_utc_ticks -ne $item['creation_time_utc_ticks'] -or [int64]$row.last_write_time_utc_ticks -ne $item['last_write_time_utc_ticks']) { $manifestMismatch++ }
}
if ($seen.Count -ne 145) { $manifestMismatch++ }
$jsonMismatch = 0
for ($index=0; $index -lt 145; $index++) {
    $left = $csvRows[$index]; $right = $jsonRows[$index]
    if ([string]$left.relative_path -cne [string]$right.relative_path -or [int64]$left.bytes -ne [int64]$right.bytes -or [string]$left.sha256 -cne [string]$right.sha256 -or [int64]$left.creation_time_utc_ticks -ne [int64]$right.creation_time_utc_ticks -or [int64]$left.last_write_time_utc_ticks -ne [int64]$right.last_write_time_utc_ticks) { $jsonMismatch++ }
}
if ($manifestMismatch -ne 0 -or $jsonMismatch -ne 0) { throw 'manifest identity mismatch' }

$markerItem = Get-Item -LiteralPath $markerPath -Force
$markerBytes = [IO.File]::ReadAllBytes($markerPath)
$bom = $markerBytes.Length -ge 3 -and $markerBytes[0] -eq 0xEF -and $markerBytes[1] -eq 0xBB -and $markerBytes[2] -eq 0xBF
$markerText = [Text.UTF8Encoding]::new($false,$true).GetString($markerBytes)
$markerLines = @($markerText -split "`n" | Where-Object { $_.Length -gt 0 } | ForEach-Object { $_.TrimEnd("`r") })
$badLines = @($markerLines | Where-Object { $_ -notmatch '^[^=\s]+=[^=\r\n]+$' -or $_.Contains("`t") -or $_ -match '\$\{?[^} ]+\}?' }).Count
$markerMap = @{}
foreach ($line in $markerLines) { $parts=$line -split '=',2; if ($markerMap.ContainsKey($parts[0])) { throw 'duplicate marker key' }; $markerMap[$parts[0]]=$parts[1] }
$requiredKeys = @('SCHEMA','HANDOFF_ID','OPERATION','VERDICT','ROOT','PAYLOAD_COUNT','CONTROL_COUNT','ORDINARY_COUNT','DIR_COUNT_INCLUDING_ROOT','PDF_PATH','PDF_BYTES','PDF_SHA256','SOURCE_PATH','SOURCE_BYTES','SOURCE_SHA256','OBJECT_COUNT','PAIR_COUNT','MANUAL_OBJECT_COUNT','MANUAL_PAIR_COUNT','MANUAL_VIEW_COUNT','HARD_FAILURE_COUNT','PAYLOAD_MANIFEST_CSV_SHA256','PAYLOAD_MANIFEST_JSON_SHA256','SEAL_AUDIT_SHA256','CONTROLLER_INVOCATION_COUNT','RETRY_COUNT','BUSINESS_EVIDENCE_RERUN','PREPARED_UTC','MARKER_LAST_WRITE_UTC_TICKS')
$keyDiff = @(Compare-Object -ReferenceObject ($requiredKeys | Sort-Object) -DifferenceObject ($markerMap.Keys | Sort-Object)).Count
if ($markerLines.Count -ne 29 -or $markerMap.Count -ne 29 -or $badLines -ne 0 -or $keyDiff -ne 0 -or $bom) { throw 'marker syntax/key audit failed' }
if ($markerMap['HANDOFF_ID'] -cne $expectedHandoff -or $markerMap['OPERATION'] -cne $expectedOperation -or $markerMap['VERDICT'] -cne $expectedVerdict -or [int]$markerMap['PAYLOAD_COUNT'] -ne 145 -or [int]$markerMap['ORDINARY_COUNT'] -ne 149 -or [int]$markerMap['OBJECT_COUNT'] -ne 60 -or [int]$markerMap['PAIR_COUNT'] -ne 1770 -or [int]$markerMap['HARD_FAILURE_COUNT'] -ne 0) { throw 'marker binding audit failed' }
if ($markerMap['PAYLOAD_MANIFEST_CSV_SHA256'] -cne (Get-FileHash -LiteralPath $manifestCsvPath -Algorithm SHA256).Hash -or $markerMap['PAYLOAD_MANIFEST_JSON_SHA256'] -cne (Get-FileHash -LiteralPath $manifestJsonPath -Algorithm SHA256).Hash -or $markerMap['SEAL_AUDIT_SHA256'] -cne (Get-FileHash -LiteralPath $sealAuditPath -Algorithm SHA256).Hash) { throw 'marker control hash binding failed' }
if ([int64]$markerMap['MARKER_LAST_WRITE_UTC_TICKS'] -ne [int64]$markerItem.LastWriteTimeUtc.Ticks) { throw 'marker tick binding failed' }

$nonMarkerItems = @($allFiles | Where-Object { $_.FullName -cne $markerPath }) + $allDirs
$maxOtherTicks = [int64](($nonMarkerItems | ForEach-Object { [int64](Get-Item -LiteralPath $_.FullName -Force).LastWriteTimeUtc.Ticks } | Measure-Object -Maximum).Maximum)
$atOrAfter = @($nonMarkerItems | Where-Object { [int64](Get-Item -LiteralPath $_.FullName -Force).LastWriteTimeUtc.Ticks -ge [int64]$markerItem.LastWriteTimeUtc.Ticks }).Count
$margin = [int64]$markerItem.LastWriteTimeUtc.Ticks - $maxOtherTicks
if ($margin -le 0 -or $atOrAfter -ne 0) { throw 'marker strict-latest audit failed' }

$snapshotA = Get-TreeSnapshot $root
Start-Sleep -Milliseconds 250
$snapshotB = Get-TreeSnapshot $root
if ($snapshotA['sha256'] -cne $snapshotB['sha256'] -or $snapshotA['sha256'] -cne [string]$controllerResult.snapshot2_sha256) { throw 'postmarker snapshot audit failed' }
$ads = Get-AdsSummary $root
$csvFiles = @(Get-ChildItem -LiteralPath $root -Recurse -Force -File -Filter '*.csv')
$jsonFiles = @(Get-ChildItem -LiteralPath $root -Recurse -Force -File -Filter '*.json')
$csvFailures=0; foreach($file in $csvFiles){try{$null=@(Import-Csv -LiteralPath $file.FullName -ErrorAction Stop)}catch{$csvFailures++}}
$jsonFailures=0; foreach($file in $jsonFiles){try{$null=Get-Content -LiteralPath $file.FullName -Raw -ErrorAction Stop|ConvertFrom-Json -ErrorAction Stop}catch{$jsonFailures++}}
$pycCount=@(Get-ChildItem -LiteralPath $root -Recurse -Force -File|Where-Object{$_.Extension -ceq '.pyc'}).Count
$pythonCacheCount=@(Get-ChildItem -LiteralPath $root -Recurse -Force -Directory|Where-Object{$_.Name -ceq '__pycache__'}).Count
$reparseCount=@((Get-Item -LiteralPath $root -Force)+@(Get-ChildItem -LiteralPath $root -Recurse -Force)|Where-Object{($_.Attributes -band [IO.FileAttributes]::ReparsePoint)-ne 0}).Count
$stageAbsent = -not (Test-Path -LiteralPath 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\P126_R17_WRITE_STOPPED.stage')
if ($ads['nondefault'] -ne 0 -or $csvFailures -ne 0 -or $jsonFailures -ne 0 -or $pycCount -ne 0 -or $pythonCacheCount -ne 0 -or $reparseCount -ne 0 -or -not $stageAbsent) { throw 'parse/hygiene audit failed' }
if ((Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash -cne '2887758F5CC94987BE750E1EC53B555FB88CE8F71B7260CABBE0A17DDF237405' -or (Get-FileHash -LiteralPath $pdf -Algorithm SHA256).Hash -cne 'F336C6C8A47B17F18257F5BAFDE58817766D1BEE12C60931857B221C20002A73') { throw 'source/PDF changed' }

$auditResult = [ordered]@{
    schema='P126_R17_SEAL_AUDITOR_RESULT_V1';success=$true;handoff_id=$expectedHandoff;operation=$expectedOperation;verdict=$expectedVerdict
    payload_count=145;control_count=4;ordinary_count=149;dir_count_including_root=11;manifest_mismatch=$manifestMismatch;json_manifest_mismatch=$jsonMismatch
    file_readonly_failures=$fileReadonlyFailures;dir_readonly_failures=$dirReadonlyFailures
    marker_bytes=[int64]$markerItem.Length;marker_sha256=(Get-FileHash -LiteralPath $markerPath -Algorithm SHA256).Hash;marker_lines=$markerLines.Count;marker_keys=$markerMap.Count;marker_bad_lines=$badLines;marker_key_diff=$keyDiff;marker_bom=$bom
    marker_ticks=[int64]$markerItem.LastWriteTimeUtc.Ticks;strict_latest_margin_ticks=$margin;at_or_after_excluding_marker=$atOrAfter
    snapshot_entries=$snapshotA['entries'];snapshot_sha256=$snapshotA['sha256'];postmarker_content_attribute_drift=0
    ads_items=$ads['items'];ads_streams=$ads['streams'];ads_nondefault=$ads['nondefault'];csv_files=$csvFiles.Count;csv_parse_failures=$csvFailures;json_files=$jsonFiles.Count;json_parse_failures=$jsonFailures;pyc_count=$pycCount;python_cache_count=$pythonCacheCount;designated_texcache_count=1;reparse_count=$reparseCount;stage_absent=$stageAbsent
    object_count=60;pair_count=1770;manual_object_count=60;manual_pair_count=1770;manual_view_count=20;glyph_codepoint_count=25;math_semantic_count=14;hard_failure_count=0
    pdf_bytes=34138;pdf_sha256='F336C6C8A47B17F18257F5BAFDE58817766D1BEE12C60931857B221C20002A73';source_bytes=4686;source_sha256='2887758F5CC94987BE750E1EC53B555FB88CE8F71B7260CABBE0A17DDF237405'
}
Write-Utf8NoBom $auditorResultPath (($auditResult | ConvertTo-Json -Depth 12)+"`n")
$report = @"
# P126 R17 sealed local SA2 report

Verdict: $expectedVerdict.

Unique PDF: 34,138 bytes, SHA256 `F336C6C8A47B17F18257F5BAFDE58817766D1BEE12C60931857B221C20002A73`. Fresh non-TeX review closed N60/C1770, manual objects60/pairs1770/views20, glyph-codepoints25, math-semantic-page14, hard failures0. The x1 legend is one blue 75px run; x2 is four teal 11px runs with 11/10/10px internal blanks, and the distinction remains clear in grayscale. Label 6/7 critical clearances and all full-figure regressions pass.

Seal audit: payload145, controls4, ordinary149, directories including root11; all files/directories ReadOnly; manifest identity mismatches0; marker 29 lines/29 keys, strict-latest including root margin $margin ticks, at-or-after0; postmarker content/attribute drift0; ADS/CSV/JSON/pyc/python-cache/reparse failures0.

P126 remains SA2 pending Main review. No commit or new role is performed.
"@
Write-Utf8NoBom $reportPath $report
$handoff = @"
# Immutable P126 R17 local-SA2 handoff

Token: $expectedVerdict.

Root: $root

PDF SHA256: `F336C6C8A47B17F18257F5BAFDE58817766D1BEE12C60931857B221C20002A73`. N60/C1770; manual60/1770/views20; hard0. x2 legend occupied runs 11/11/11/11px with internal blanks 11/10/10px. Sealed root ordinary149/directories11, all ReadOnly, WSTOP strict latest, postmarker0.

Request: Main independent review and, only if accepted, separate atomic-commit authorization.
"@
Write-Utf8NoBom $handoffPath $handoff
foreach($path in @($auditorResultPath,$reportPath,$handoffPath)){ $item=Get-Item -LiteralPath $path -Force; $item.Attributes=$item.Attributes -bor [IO.FileAttributes]::ReadOnly }
