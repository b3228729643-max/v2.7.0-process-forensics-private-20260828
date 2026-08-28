Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$root = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\STRICT_R17_SA2_FORGET_PLOT_PATCH_R115_DIRECT_BUILD_20260828'
$source = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_A_visual\src\绘图源码\第01册_数学基础与统计学习基本理论\V1-C08\fig_v1_c08_coordinate.tex'
$pdf = Join-Path $root 'build\v260_FIG-P126-01_standalone.pdf'
$controller = $PSCommandPath
$stage = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\P126_R17_WRITE_STOPPED.stage'
$resultPath = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\P126_R17_SEAL_CONTROLLER_RESULT_20260828.json'
$handoff = 'A-R115-P126-SA2-DIRECT-BUILD-R17-CONTROLLER-STATIC-20260828'
$operation = 'P126_R115_R17_NON_TEX_REVIEW_AND_SINGLE_SEAL'
$verdict = 'LOCAL_SA2_PASS_READY_FOR_MAIN_REVIEW_AND_ATOMIC_COMMIT_AUTH'
$controls = @('PAYLOAD_MANIFEST.csv','PAYLOAD_MANIFEST.json','SEAL_AUDIT.json','WRITE_STOPPED')

function Write-Utf8NoBom([string]$Path, [string]$Text) {
    [IO.File]::WriteAllText($Path, $Text, [Text.UTF8Encoding]::new($false))
}

function Get-FileIdentity([string]$Path) {
    $item = Get-Item -LiteralPath $Path -Force
    [ordered]@{
        path = $item.FullName
        bytes = [int64]$item.Length
        sha256 = (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash
        creation_time_utc_ticks = [int64]$item.CreationTimeUtc.Ticks
        last_write_time_utc_ticks = [int64]$item.LastWriteTimeUtc.Ticks
    }
}

function Get-CanonicalRelative([string]$Base, [string]$FullPath) {
    $relative = [IO.Path]::GetRelativePath($Base, $FullPath).Replace('\','/')
    if ([string]::IsNullOrWhiteSpace($relative) -or [IO.Path]::IsPathRooted($relative) -or $relative -eq '.' -or $relative.StartsWith('../',[StringComparison]::Ordinal) -or $relative.Contains('/../') -or $relative.Contains('/./')) {
        throw "unsafe relative path: $relative"
    }
    $relative
}

function Test-ReadOnly([System.IO.FileSystemInfo]$Item) {
    (($Item.Attributes -band [IO.FileAttributes]::ReadOnly) -ne 0)
}

function Set-ReadOnly([System.IO.FileSystemInfo]$Item) {
    $Item.Attributes = $Item.Attributes -bor [IO.FileAttributes]::ReadOnly
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
    $bytes = [Text.UTF8Encoding]::new($false).GetBytes($text)
    $sha = [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($bytes))
    [ordered]@{entries=$orderedRows.Count;sha256=$sha;rows=$orderedRows}
}

function Get-AdsSummary([string]$Base) {
    $items = @((Get-Item -LiteralPath $Base -Force)) + @(Get-ChildItem -LiteralPath $Base -Recurse -Force)
    $streams = 0
    $nondefault = 0
    foreach ($item in $items) {
        $found = @(Get-Item -LiteralPath $item.FullName -Stream * -Force -ErrorAction Stop)
        foreach ($stream in $found) {
            $streams++
            if ([string]$stream.Stream -cne ':$DATA') { $nondefault++ }
        }
    }
    [ordered]@{items=$items.Count;streams=$streams;nondefault=$nondefault}
}

if (-not (Test-Path -LiteralPath $root -PathType Container)) { throw 'R17 root missing' }
if (Test-Path -LiteralPath $stage) { throw 'marker stage must be absent' }
if (Test-Path -LiteralPath $resultPath) { throw 'controller result must be absent' }
foreach ($name in $controls) {
    if (Test-Path -LiteralPath (Join-Path $root $name)) { throw "control already exists: $name" }
}
$sourceIdentity = Get-FileIdentity $source
$pdfIdentity = Get-FileIdentity $pdf
if ($sourceIdentity['bytes'] -ne 4686 -or $sourceIdentity['sha256'] -cne '2887758F5CC94987BE750E1EC53B555FB88CE8F71B7260CABBE0A17DDF237405') { throw 'source identity mismatch' }
if ($pdfIdentity['bytes'] -ne 34138 -or $pdfIdentity['sha256'] -cne 'F336C6C8A47B17F18257F5BAFDE58817766D1BEE12C60931857B221C20002A73') { throw 'PDF identity mismatch' }

$payloadFiles = @(Get-ChildItem -LiteralPath $root -Recurse -Force -File | Where-Object { $controls -cnotcontains $_.Name } | Sort-Object FullName)
if ($payloadFiles.Count -ne 145) { throw "payload count mismatch: $($payloadFiles.Count)" }
$payloadRows = @($payloadFiles | ForEach-Object {
    [ordered]@{
        relative_path = Get-CanonicalRelative $root $_.FullName
        bytes = [int64]$_.Length
        sha256 = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash
        creation_time_utc_ticks = [int64]$_.CreationTimeUtc.Ticks
        last_write_time_utc_ticks = [int64]$_.LastWriteTimeUtc.Ticks
    }
})
$duplicatePayload = @($payloadRows | Group-Object -Property { [string]$_['relative_path'] } | Where-Object { $_.Count -ne 1 })
if ($duplicatePayload.Count -ne 0) { throw 'duplicate payload path' }

$manifestCsvPath = Join-Path $root 'PAYLOAD_MANIFEST.csv'
$manifestJsonPath = Join-Path $root 'PAYLOAD_MANIFEST.json'
$sealAuditPath = Join-Path $root 'SEAL_AUDIT.json'
$payloadRows | ForEach-Object { [pscustomobject]$_ } | Export-Csv -LiteralPath $manifestCsvPath -NoTypeInformation -Encoding utf8NoBOM
$manifestJson = [ordered]@{schema='P126_R17_PAYLOAD_MANIFEST_V1';handoff_id=$handoff;operation=$operation;payload_count=$payloadRows.Count;rows=$payloadRows}
Write-Utf8NoBom $manifestJsonPath (($manifestJson | ConvertTo-Json -Depth 12) + "`n")
$manifestCsvIdentity = Get-FileIdentity $manifestCsvPath
$manifestJsonIdentity = Get-FileIdentity $manifestJsonPath

$adsBefore = Get-AdsSummary $root
if ($adsBefore['nondefault'] -ne 0) { throw 'nondefault ADS found before seal' }
$pycCount = @(Get-ChildItem -LiteralPath $root -Recurse -Force -File | Where-Object { $_.Extension -ceq '.pyc' }).Count
$pythonCacheCount = @(Get-ChildItem -LiteralPath $root -Recurse -Force -Directory | Where-Object { $_.Name -ceq '__pycache__' }).Count
$reparseCount = @((Get-Item -LiteralPath $root -Force) + @(Get-ChildItem -LiteralPath $root -Recurse -Force) | Where-Object { ($_.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0 }).Count
if ($pycCount -ne 0 -or $pythonCacheCount -ne 0 -or $reparseCount -ne 0) { throw 'hygiene gate failed' }

$csvFiles = @(Get-ChildItem -LiteralPath $root -Recurse -Force -File -Filter '*.csv')
$jsonFiles = @(Get-ChildItem -LiteralPath $root -Recurse -Force -File -Filter '*.json')
$csvParseFailures = 0
foreach ($file in $csvFiles) { try { $null = @(Import-Csv -LiteralPath $file.FullName -ErrorAction Stop) } catch { $csvParseFailures++ } }
$jsonParseFailures = 0
foreach ($file in $jsonFiles) { try { $null = Get-Content -LiteralPath $file.FullName -Raw -ErrorAction Stop | ConvertFrom-Json -ErrorAction Stop } catch { $jsonParseFailures++ } }
if ($csvParseFailures -ne 0 -or $jsonParseFailures -ne 0) { throw 'premarker parse gate failed' }

$sealAudit = [ordered]@{
    schema = 'P126_R17_SEAL_AUDIT_V1'
    handoff_id = $handoff
    operation = $operation
    verdict = $verdict
    payload_count = 145
    control_count = 4
    final_ordinary_count = 149
    dir_count_including_root = @(Get-ChildItem -LiteralPath $root -Recurse -Force -Directory).Count + 1
    object_count = 60
    pair_count = 1770
    manual_object_count = 60
    manual_pair_count = 1770
    manual_view_count = 20
    glyph_codepoint_count = 25
    math_semantic_count = 14
    hard_failure_count = 0
    payload_manifest_csv_sha256 = $manifestCsvIdentity['sha256']
    payload_manifest_json_sha256 = $manifestJsonIdentity['sha256']
    source = $sourceIdentity
    pdf = $pdfIdentity
    ads_items = $adsBefore['items']
    ads_streams = $adsBefore['streams']
    ads_nondefault = 0
    csv_files = $csvFiles.Count
    csv_parse_failures = 0
    json_files_before_seal_audit = $jsonFiles.Count
    json_parse_failures = 0
    pyc_count = 0
    python_cache_count = 0
    designated_texcache_count = 1
    reparse_count = 0
    controller_invocation_count = 1
    retry_count = 0
    business_evidence_rerun = 0
}
Write-Utf8NoBom $sealAuditPath (($sealAudit | ConvertTo-Json -Depth 12) + "`n")
$sealAuditIdentity = Get-FileIdentity $sealAuditPath

$premarkerFiles = @(Get-ChildItem -LiteralPath $root -Recurse -Force -File)
if ($premarkerFiles.Count -ne 148) { throw "premarker file count mismatch: $($premarkerFiles.Count)" }
foreach ($file in $premarkerFiles) { Set-ReadOnly $file }
$directories = @(Get-ChildItem -LiteralPath $root -Recurse -Force -Directory | Sort-Object { $_.FullName.Length } -Descending)
foreach ($dir in $directories) { Set-ReadOnly $dir }
Set-ReadOnly (Get-Item -LiteralPath $root -Force)
$premarkerReadonlyFailures = @($premarkerFiles | Where-Object { -not (Test-ReadOnly (Get-Item -LiteralPath $_.FullName -Force)) }).Count
$dirReadonlyFailures = @((@(Get-ChildItem -LiteralPath $root -Recurse -Force -Directory) + @((Get-Item -LiteralPath $root -Force))) | Where-Object { -not (Test-ReadOnly (Get-Item -LiteralPath $_.FullName -Force)) }).Count
if ($premarkerReadonlyFailures -ne 0 -or $dirReadonlyFailures -ne 0) { throw 'premarker readonly gate failed' }

$allExisting = @($premarkerFiles) + @($directories) + @((Get-Item -LiteralPath $root -Force))
$maxOtherTicks = [int64](($allExisting | ForEach-Object { [int64](Get-Item -LiteralPath $_.FullName -Force).LastWriteTimeUtc.Ticks } | Measure-Object -Maximum).Maximum)
$futureFloor = [DateTime]::UtcNow.AddMinutes(5).Ticks
$markerTicks = [math]::Max($futureFloor, $maxOtherTicks + 3000000000L)
$preparedUtc = [DateTime]::UtcNow.ToString('o')
$markerLines = @(
    'SCHEMA=P126_R17_WRITE_STOPPED_V1'
    "HANDOFF_ID=$handoff"
    "OPERATION=$operation"
    "VERDICT=$verdict"
    "ROOT=$root"
    'PAYLOAD_COUNT=145'
    'CONTROL_COUNT=4'
    'ORDINARY_COUNT=149'
    "DIR_COUNT_INCLUDING_ROOT=$($directories.Count + 1)"
    "PDF_PATH=$pdf"
    'PDF_BYTES=34138'
    'PDF_SHA256=F336C6C8A47B17F18257F5BAFDE58817766D1BEE12C60931857B221C20002A73'
    "SOURCE_PATH=$source"
    'SOURCE_BYTES=4686'
    'SOURCE_SHA256=2887758F5CC94987BE750E1EC53B555FB88CE8F71B7260CABBE0A17DDF237405'
    'OBJECT_COUNT=60'
    'PAIR_COUNT=1770'
    'MANUAL_OBJECT_COUNT=60'
    'MANUAL_PAIR_COUNT=1770'
    'MANUAL_VIEW_COUNT=20'
    'HARD_FAILURE_COUNT=0'
    "PAYLOAD_MANIFEST_CSV_SHA256=$($manifestCsvIdentity['sha256'])"
    "PAYLOAD_MANIFEST_JSON_SHA256=$($manifestJsonIdentity['sha256'])"
    "SEAL_AUDIT_SHA256=$($sealAuditIdentity['sha256'])"
    'CONTROLLER_INVOCATION_COUNT=1'
    'RETRY_COUNT=0'
    'BUSINESS_EVIDENCE_RERUN=0'
    "PREPARED_UTC=$preparedUtc"
    "MARKER_LAST_WRITE_UTC_TICKS=$markerTicks"
)
if ($markerLines.Count -ne 29 -or @($markerLines | Where-Object { $_ -notmatch '^[^=\s]+=[^=\r\n]+$' }).Count -ne 0 -or @($markerLines | ForEach-Object { ($_ -split '=',2)[0] } | Group-Object | Where-Object { $_.Count -ne 1 }).Count -ne 0) { throw 'marker syntax gate failed' }
Write-Utf8NoBom $stage (($markerLines -join "`n") + "`n")
$stageItem = Get-Item -LiteralPath $stage -Force
$stageItem.LastWriteTimeUtc = [DateTime]::new($markerTicks,[DateTimeKind]::Utc)
Set-ReadOnly $stageItem
if (-not (Test-ReadOnly (Get-Item -LiteralPath $stage -Force))) { throw 'stage marker not readonly' }

$markerPath = Join-Path $root 'WRITE_STOPPED'
[IO.File]::Move($stage,$markerPath)

$snapshot1 = Get-TreeSnapshot $root
Start-Sleep -Milliseconds 250
$snapshot2 = Get-TreeSnapshot $root
if ($snapshot1['sha256'] -cne $snapshot2['sha256']) { throw 'postmarker snapshot drift' }
$markerIdentity = Get-FileIdentity $markerPath
$allFilesAfter = @(Get-ChildItem -LiteralPath $root -Recurse -Force -File)
$allDirsAfter = @(Get-ChildItem -LiteralPath $root -Recurse -Force -Directory) + @((Get-Item -LiteralPath $root -Force))
$fileReadonlyFailures = @($allFilesAfter | Where-Object { -not (Test-ReadOnly (Get-Item -LiteralPath $_.FullName -Force)) }).Count
$allDirReadonlyFailures = @($allDirsAfter | Where-Object { -not (Test-ReadOnly (Get-Item -LiteralPath $_.FullName -Force)) }).Count
$maxOtherAfter = [int64](((@($allFilesAfter | Where-Object { $_.FullName -cne $markerPath }) + $allDirsAfter) | ForEach-Object { [int64](Get-Item -LiteralPath $_.FullName -Force).LastWriteTimeUtc.Ticks } | Measure-Object -Maximum).Maximum)
$atOrAfter = @((@($allFilesAfter | Where-Object { $_.FullName -cne $markerPath }) + $allDirsAfter) | Where-Object { [int64](Get-Item -LiteralPath $_.FullName -Force).LastWriteTimeUtc.Ticks -ge [int64]$markerIdentity['last_write_time_utc_ticks'] }).Count
if ($allFilesAfter.Count -ne 149 -or $fileReadonlyFailures -ne 0 -or $allDirReadonlyFailures -ne 0 -or $atOrAfter -ne 0) { throw 'postmarker controller gate failed' }

$result = [ordered]@{
    schema='P126_R17_SEAL_CONTROLLER_RESULT_V1';success=$true;handoff_id=$handoff;operation=$operation;verdict=$verdict
    controller_path=$controller;controller_bytes=(Get-Item -LiteralPath $controller).Length;controller_sha256=(Get-FileHash -LiteralPath $controller -Algorithm SHA256).Hash
    controller_invocation_count=1;retry_count=0;payload_count=145;control_count=4;ordinary_count=149;dir_count_including_root=$allDirsAfter.Count
    file_readonly_failures=$fileReadonlyFailures;dir_readonly_failures=$allDirReadonlyFailures
    marker=$markerIdentity;marker_lines=29;marker_keys=29;strict_latest_margin_ticks=([int64]$markerIdentity['last_write_time_utc_ticks']-$maxOtherAfter);at_or_after_excluding_marker=$atOrAfter
    snapshot1_entries=$snapshot1['entries'];snapshot1_sha256=$snapshot1['sha256'];snapshot2_entries=$snapshot2['entries'];snapshot2_sha256=$snapshot2['sha256'];postmarker_drift=0
    source=$sourceIdentity;pdf=$pdfIdentity;manifest_csv=$manifestCsvIdentity;manifest_json=$manifestJsonIdentity;seal_audit=$sealAuditIdentity
}
Write-Utf8NoBom $resultPath (($result | ConvertTo-Json -Depth 12) + "`n")
