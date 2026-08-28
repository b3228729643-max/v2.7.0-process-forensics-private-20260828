Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$sourceRoot = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\STRICT_R17_SA2_FORGET_PLOT_PATCH_R115_DIRECT_BUILD_20260828'
$destinationRoot = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\STRICT_R17A_SA2_FORGET_PLOT_PATCH_R115_EVIDENCE_ONLY_CONTROL_RESEAL_20260828'
$oldManifestPath = Join-Path $sourceRoot 'PAYLOAD_MANIFEST.csv'
$stagePath = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\P126_R17A_WRITE_STOPPED.stage'
$controllerPath = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\P126_R17A_CONTROL_RESEAL_CONTROLLER_V1_20260828.ps1'
$controllerResultPath = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\P126_R17A_CONTROL_RESEAL_CONTROLLER_RESULT_V1_20260828.json'
$auditorResultPath = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\P126_R17A_CONTROL_RESEAL_AUDITOR_RESULT_V1_20260828.json'
$reportPath = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\P126_R17A_CONTROL_RESEAL_REPORT_V1_20260828.md'
$handoffPath = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\P126_R17A_CONTROL_RESEAL_HANDOFF_V1_20260828.md'
$handoff = 'A-R115-P126-SA2-DIRECT-BUILD-R17-CONTROL-RESEAL-V1-20260828'
$operation = 'P126_R115_R17_SA2_EVIDENCE_ONLY_CONTROL_RESEAL_V1'
$verdict = 'LOCAL_SA2_PASS_READY_FOR_MAIN_REVIEW_AND_ATOMIC_COMMIT_AUTH'
$expectedControllerBytes = 18655L
$expectedControllerSha = '96520D7AFC5056B3B7C1D3C5E6C4F7F9CDA11E9AEA6B4B974B6B65318A2F15D7'
$expectedOldManifestBytes = 24231L
$expectedOldManifestSha = '8E99A474AC7A56401CAB3A6B76A283A97A4868828A70F2C65E43A05A3391C2F6'
$oldControls = @('PAYLOAD_MANIFEST.csv','PAYLOAD_MANIFEST.json','SEAL_AUDIT.json','WRITE_STOPPED')
$newControls = @('PAYLOAD_MANIFEST.csv','SEAL_AUDIT.json','WRITE_STOPPED')

function Write-Utf8NoBom([string]$Path,[string]$Text) {
    [IO.File]::WriteAllText($Path,$Text,[Text.UTF8Encoding]::new($false))
}

function Get-CanonicalRelative([string]$Value) {
    $relative = $Value.Replace('\','/')
    while ($relative.StartsWith('./',[StringComparison]::Ordinal)) { $relative = $relative.Substring(2) }
    if ([string]::IsNullOrWhiteSpace($relative) -or [IO.Path]::IsPathRooted($relative) -or $relative -eq '.' -or $relative.StartsWith('../',[StringComparison]::Ordinal) -or $relative.Contains('/../') -or $relative.Contains('/./') -or $relative.EndsWith('/.',[StringComparison]::Ordinal) -or $relative.Contains('//')) { throw "unsafe relative path: $Value" }
    foreach ($segment in $relative.Split('/')) { if ([string]::IsNullOrWhiteSpace($segment) -or $segment -eq '.' -or $segment -eq '..') { throw "unsafe segment: $Value" } }
    $relative
}

function Resolve-Contained([string]$Root,[string]$Relative) {
    $rootFull = [IO.Path]::GetFullPath($Root).TrimEnd('\')
    $candidate = [IO.Path]::GetFullPath((Join-Path $rootFull $Relative.Replace('/','\')))
    if (-not $candidate.StartsWith($rootFull + '\',[StringComparison]::OrdinalIgnoreCase)) { throw "path escape: $Relative" }
    $candidate
}

function Get-TreeItems([string]$Root) {
    $rootItems = @((Get-Item -LiteralPath $Root -Force))
    $childItems = @(Get-ChildItem -LiteralPath $Root -Recurse -Force)
    $allItems = @($rootItems)
    $allItems += @($childItems)
    @($allItems)
}

function Get-TreeSnapshot([string]$Root) {
    $rootFull = (Get-Item -LiteralPath $Root -Force).FullName
    $rows = [System.Collections.Generic.List[object]]::new()
    foreach ($item in @(Get-TreeItems $Root)) {
        $kind = if ($item.PSIsContainer) { 'D' } else { 'F' }
        $relative = if ($item.FullName -ceq $rootFull) { '.' } else { Get-CanonicalRelative ([IO.Path]::GetRelativePath($Root,$item.FullName)) }
        $bytes = if ($item.PSIsContainer) { 0L } else { [int64]$item.Length }
        $sha = if ($item.PSIsContainer) { '' } else { (Get-FileHash -LiteralPath $item.FullName -Algorithm SHA256).Hash }
        $rows.Add([ordered]@{kind=$kind;relative_path=$relative;bytes=$bytes;sha256=$sha;creation_time_utc_ticks=[int64]$item.CreationTimeUtc.Ticks;last_write_time_utc_ticks=[int64]$item.LastWriteTimeUtc.Ticks;attributes=[int]$item.Attributes})
    }
    $orderedRows = @($rows | Sort-Object -Property @{Expression={$_['kind']}},@{Expression={$_['relative_path']}})
    $text = ($orderedRows | ForEach-Object { "{0}`t{1}`t{2}`t{3}`t{4}`t{5}`t{6}" -f $_['kind'],$_['relative_path'],$_['bytes'],$_['sha256'],$_['creation_time_utc_ticks'],$_['last_write_time_utc_ticks'],$_['attributes'] }) -join "`n"
    $text += "`n"
    $sha = [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData([Text.UTF8Encoding]::new($false).GetBytes($text)))
    [ordered]@{entries=$orderedRows.Count;sha256=$sha;rows=$orderedRows}
}

function Get-AdsSummary([string]$Root) {
    $items = @(Get-TreeItems $Root)
    $streams = 0; $nondefault = 0
    foreach ($item in $items) {
        foreach ($stream in @(Get-Item -LiteralPath $item.FullName -Stream * -Force -ErrorAction Stop)) {
            $streams++
            if ([string]$stream.Stream -cne ':$DATA') { $nondefault++ }
        }
    }
    [ordered]@{items=$items.Count;streams=$streams;nondefault=$nondefault}
}

function Get-Identity([string]$Path) {
    $item = Get-Item -LiteralPath $Path -Force
    [ordered]@{path=$item.FullName;bytes=[int64]$item.Length;sha256=(Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash;readonly=(($item.Attributes -band [IO.FileAttributes]::ReadOnly) -ne 0)}
}

function Test-ReadOnly([System.IO.FileSystemInfo]$Item) {
    (($Item.Attributes -band [IO.FileAttributes]::ReadOnly) -ne 0)
}

function New-OrdinalMap([object[]]$Rows,[string]$Label) {
    $map = [System.Collections.Generic.Dictionary[string,object]]::new([StringComparer]::Ordinal)
    foreach ($row in @($Rows)) {
        $key = Get-CanonicalRelative ([string]$row.relative_path)
        if ($map.ContainsKey($key)) { throw "$Label duplicate path: $key" }
        $map.Add($key,$row)
    }
    return ,$map
}

function Assert-Equal([object]$Actual,[object]$Expected,[string]$Label) {
    if ([string]$Actual -cne [string]$Expected) { throw "$Label mismatch: actual=$Actual expected=$Expected" }
}

foreach ($path in @($stagePath,$auditorResultPath,$reportPath,$handoffPath)) { if (Test-Path -LiteralPath $path) { throw "auditor startup-absence gate failed: $path" } }
if (-not (Test-Path -LiteralPath $destinationRoot -PathType Container)) { throw 'sealed destination missing' }
$controllerIdentity = Get-Identity $controllerPath
if ($controllerIdentity['bytes'] -ne $expectedControllerBytes -or $controllerIdentity['sha256'] -cne $expectedControllerSha -or -not $controllerIdentity['readonly']) { throw 'controller identity mismatch' }
$controllerResultIdentity = Get-Identity $controllerResultPath
$controllerResult = Get-Content -LiteralPath $controllerResultPath -Raw -ErrorAction Stop | ConvertFrom-Json -ErrorAction Stop
Assert-Equal $controllerResult.schema 'P126_R17A_CONTROL_RESEAL_CONTROLLER_RESULT_V1' 'controller result schema'
Assert-Equal $controllerResult.success 'True' 'controller success'
Assert-Equal $controllerResult.handoff_id $handoff 'controller handoff'
Assert-Equal $controllerResult.operation $operation 'controller operation'
Assert-Equal $controllerResult.verdict $verdict 'controller verdict'
Assert-Equal $controllerResult.controller_path $controllerPath 'controller path'
Assert-Equal $controllerResult.controller_bytes $expectedControllerBytes 'controller bytes'
Assert-Equal $controllerResult.controller_sha256 $expectedControllerSha 'controller sha'
Assert-Equal $controllerResult.controller_invocation_count 1 'controller invocation'
Assert-Equal $controllerResult.retry_count 0 'controller retry'
foreach ($pair in @(@('copied_material_count',145),@('old_controls_copied',0),@('payload_count',147),@('control_count',3),@('ordinary_count',150),@('dir_count_including_root',11),@('marker_lines',30),@('marker_keys',30),@('readonly_failures',0),@('at_or_after_excluding_marker',0),@('postmarker_drift',0))) { Assert-Equal $controllerResult.($pair[0]) $pair[1] "controller $($pair[0])" }

$sourceBefore = Get-TreeSnapshot $sourceRoot
$sourceAds = Get-AdsSummary $sourceRoot
if ($sourceBefore['entries'] -ne 158 -or $sourceAds['items'] -ne 158 -or $sourceAds['streams'] -ne 147 -or $sourceAds['nondefault'] -ne 0) { throw 'source tree/ADS mismatch' }
Assert-Equal $controllerResult.source_snapshot_before $sourceBefore['sha256'] 'controller source before'
Assert-Equal $controllerResult.source_snapshot_after $sourceBefore['sha256'] 'controller source after'
$oldManifestIdentity = Get-Identity $oldManifestPath
if ($oldManifestIdentity['bytes'] -ne $expectedOldManifestBytes -or $oldManifestIdentity['sha256'] -cne $expectedOldManifestSha) { throw 'old manifest identity mismatch' }
$oldRows = @(Import-Csv -LiteralPath $oldManifestPath -ErrorAction Stop)
$copyPath = Join-Path $destinationRoot 'COPY_IDENTITY.csv'
$provenancePath = Join-Path $destinationRoot 'COPY_PROVENANCE.json'
$manifestPath = Join-Path $destinationRoot 'PAYLOAD_MANIFEST.csv'
$sealAuditPath = Join-Path $destinationRoot 'SEAL_AUDIT.json'
$markerPath = Join-Path $destinationRoot 'WRITE_STOPPED'
$copyRows = @(Import-Csv -LiteralPath $copyPath -ErrorAction Stop)
if ($oldRows.Count -ne 145 -or $copyRows.Count -ne 145) { throw 'old/copy row count mismatch' }
$oldMap = New-OrdinalMap $oldRows 'old manifest'
$copyMap = New-OrdinalMap $copyRows 'copy identity'
if ($oldMap.Count -ne $copyMap.Count) { throw 'old/copy set count mismatch' }
$fieldNames = @('bytes','sha256','creation_time_utc_ticks','last_write_time_utc_ticks')
foreach ($relative in $oldMap.Keys) {
    if (-not $copyMap.ContainsKey($relative)) { throw "copy missing path: $relative" }
    $oldRow = $oldMap[$relative]; $copyRow = $copyMap[$relative]
    foreach ($field in $fieldNames) { Assert-Equal $copyRow.$field $oldRow.$field "copy field $relative/$field" }
    $sourcePath = Resolve-Contained $sourceRoot $relative
    $destinationPath = Resolve-Contained $destinationRoot $relative
    Assert-Equal $copyRow.source_path $sourcePath "copy source path $relative"
    Assert-Equal $copyRow.destination_path $destinationPath "copy destination path $relative"
    foreach ($binding in @(@($sourcePath,$oldRow),@($destinationPath,$copyRow))) {
        $item = Get-Item -LiteralPath $binding[0] -Force
        if ($item.PSIsContainer) { throw "material is directory: $relative" }
        Assert-Equal $item.Length $binding[1].bytes "material bytes $relative"
        Assert-Equal (Get-FileHash -LiteralPath $binding[0] -Algorithm SHA256).Hash $binding[1].sha256 "material sha $relative"
        Assert-Equal $item.CreationTimeUtc.Ticks $binding[1].creation_time_utc_ticks "material creation $relative"
        Assert-Equal $item.LastWriteTimeUtc.Ticks $binding[1].last_write_time_utc_ticks "material lastwrite $relative"
    }
}
if (Test-Path -LiteralPath (Join-Path $destinationRoot 'PAYLOAD_MANIFEST.json')) { throw 'old PAYLOAD_MANIFEST.json copied' }

$provenance = Get-Content -LiteralPath $provenancePath -Raw -ErrorAction Stop | ConvertFrom-Json -ErrorAction Stop
foreach ($pair in @(@('schema','P126_R17A_COPY_PROVENANCE_V1'),@('handoff_id',$handoff),@('operation',$operation),@('source_root',$sourceRoot),@('destination_root',$destinationRoot),@('old_manifest_path',$oldManifestPath),@('old_manifest_bytes',$expectedOldManifestBytes),@('old_manifest_sha256',$expectedOldManifestSha),@('source_snapshot_entries',158),@('source_snapshot_sha256',$sourceBefore['sha256']),@('copied_material_count',145),@('old_controls_copied',0),@('added_payload_count',2),@('payload_count',147),@('business_evidence_rerun',0),@('verdict',$verdict))) { Assert-Equal $provenance.($pair[0]) $pair[1] "provenance $($pair[0])" }
Assert-Equal (@($provenance.preserved_fields) -join ',') 'relative_path,bytes,sha256,creation_time_utc_ticks,last_write_time_utc_ticks' 'provenance preserved fields'

$payloadRows = @(Import-Csv -LiteralPath $manifestPath -ErrorAction Stop)
$payloadMap = New-OrdinalMap $payloadRows 'payload manifest'
$actualPayloadRows = @(Get-ChildItem -LiteralPath $destinationRoot -Recurse -Force -File | ForEach-Object {
    $relative = Get-CanonicalRelative ([IO.Path]::GetRelativePath($destinationRoot,$_.FullName))
    if ($newControls -cnotcontains $relative) { [pscustomobject]@{relative_path=$relative;bytes=[int64]$_.Length;sha256=(Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash;creation_time_utc_ticks=[int64]$_.CreationTimeUtc.Ticks;last_write_time_utc_ticks=[int64]$_.LastWriteTimeUtc.Ticks} }
})
$actualPayloadMap = New-OrdinalMap $actualPayloadRows 'actual payload'
if ($payloadMap.Count -ne 147 -or $actualPayloadMap.Count -ne 147) { throw 'payload count mismatch' }
foreach ($relative in $payloadMap.Keys) {
    if (-not $actualPayloadMap.ContainsKey($relative)) { throw "actual payload missing: $relative" }
    foreach ($field in $fieldNames) { Assert-Equal $actualPayloadMap[$relative].$field $payloadMap[$relative].$field "payload field $relative/$field" }
}

$copyIdentity = Get-Identity $copyPath
$provenanceIdentity = Get-Identity $provenancePath
$manifestIdentity = Get-Identity $manifestPath
$sealAuditIdentity = Get-Identity $sealAuditPath
if ($manifestIdentity['sha256'] -ceq $expectedOldManifestSha) { throw 'new payload manifest is indistinguishable from rejected old control' }
$sealAudit = Get-Content -LiteralPath $sealAuditPath -Raw -ErrorAction Stop | ConvertFrom-Json -ErrorAction Stop
foreach ($pair in @(@('schema','P126_R17A_SEAL_AUDIT_V1'),@('handoff_id',$handoff),@('operation',$operation),@('verdict',$verdict),@('copied_material_count',145),@('old_controls_copied',0),@('payload_count',147),@('control_count',3),@('ordinary_count',150),@('dir_count_including_root',11),@('copy_identity_bytes',$copyIdentity['bytes']),@('copy_identity_sha256',$copyIdentity['sha256']),@('copy_provenance_bytes',$provenanceIdentity['bytes']),@('copy_provenance_sha256',$provenanceIdentity['sha256']),@('payload_manifest_bytes',$manifestIdentity['bytes']),@('payload_manifest_sha256',$manifestIdentity['sha256']),@('source_snapshot_entries',158),@('source_snapshot_sha256',$sourceBefore['sha256']),@('source_ads_nondefault',0),@('destination_ads_nondefault',0),@('csv_parse_failures',0),@('json_parse_failures',0),@('pyc_count',0),@('python_cache_count',0),@('designated_texcache_count',1),@('reparse_count',0),@('business_evidence_rerun',0),@('object_count',60),@('pair_count',1770),@('manual_object_count',60),@('manual_pair_count',1770),@('manual_view_count',20),@('hard_failure_count',0),@('controller_invocation_count',1),@('retry_count',0),@('auditor_invocation_budget',1))) { Assert-Equal $sealAudit.($pair[0]) $pair[1] "seal audit $($pair[0])" }

$markerBytes = [IO.File]::ReadAllBytes($markerPath)
if ($markerBytes.Length -ge 3 -and $markerBytes[0] -eq 0xEF -and $markerBytes[1] -eq 0xBB -and $markerBytes[2] -eq 0xBF) { throw 'marker BOM present' }
$markerText = [Text.UTF8Encoding]::new($false,$true).GetString($markerBytes)
if (-not $markerText.EndsWith("`n",[StringComparison]::Ordinal) -or $markerText.Contains("`r") -or $markerText.Contains("`t")) { throw 'marker line encoding failure' }
$markerLines = @($markerText.TrimEnd("`n").Split("`n"))
$markerMap = [System.Collections.Generic.Dictionary[string,string]]::new([StringComparer]::Ordinal)
foreach ($line in $markerLines) {
    if ($line -notmatch '^[^=\s]+=[^=\r\n]+$') { throw "bad marker line: $line" }
    $parts = $line -split '=',2
    if ($markerMap.ContainsKey($parts[0])) { throw "duplicate marker key: $($parts[0])" }
    $markerMap.Add($parts[0],$parts[1])
}
$expectedMarker = [ordered]@{
    SCHEMA='P126_R17A_WRITE_STOPPED_V1';HANDOFF_ID=$handoff;OPERATION=$operation;VERDICT=$verdict;SOURCE_ROOT=$sourceRoot;DESTINATION_ROOT=$destinationRoot
    COPIED_MATERIAL_COUNT='145';OLD_CONTROLS_COPIED='0';PAYLOAD_COUNT='147';CONTROL_COUNT='3';ORDINARY_COUNT='150';DIR_COUNT_INCLUDING_ROOT='11'
    SOURCE_SNAPSHOT_SHA256=$sourceBefore['sha256'];OLD_MANIFEST_SHA256=$expectedOldManifestSha;COPY_IDENTITY_SHA256=$copyIdentity['sha256'];COPY_PROVENANCE_SHA256=$provenanceIdentity['sha256'];PAYLOAD_MANIFEST_SHA256=$manifestIdentity['sha256'];SEAL_AUDIT_SHA256=$sealAuditIdentity['sha256']
    OBJECT_COUNT='60';PAIR_COUNT='1770';MANUAL_OBJECT_COUNT='60';MANUAL_PAIR_COUNT='1770';MANUAL_VIEW_COUNT='20';HARD_FAILURE_COUNT='0';BUSINESS_EVIDENCE_RERUN='0';CONTROLLER_INVOCATION_COUNT='1';RETRY_COUNT='0';AUDITOR_INVOCATION_BUDGET='1'
}
if ($markerLines.Count -ne 30 -or $markerMap.Count -ne 30 -or $expectedMarker.Count -ne 28) { throw 'marker count mismatch' }
foreach ($key in $expectedMarker.Keys) { if (-not $markerMap.ContainsKey($key)) { throw "marker missing key: $key" }; Assert-Equal $markerMap[$key] $expectedMarker[$key] "marker $key" }
foreach ($key in $markerMap.Keys) { if (-not $expectedMarker.Contains($key) -and $key -cnotin @('PREPARED_UTC','MARKER_LAST_WRITE_UTC_TICKS')) { throw "unexpected marker key: $key" } }
$prepared = [DateTime]::Parse($markerMap['PREPARED_UTC'],[Globalization.CultureInfo]::InvariantCulture,[Globalization.DateTimeStyles]::RoundtripKind)
if ($prepared.Kind -eq [DateTimeKind]::Unspecified) { throw 'marker prepared UTC lacks zone' }
$markerItem = Get-Item -LiteralPath $markerPath -Force
Assert-Equal $markerMap['MARKER_LAST_WRITE_UTC_TICKS'] $markerItem.LastWriteTimeUtc.Ticks 'marker ticks binding'

$finalFiles = @(Get-ChildItem -LiteralPath $destinationRoot -Recurse -Force -File)
$finalDirectories = @((Get-Item -LiteralPath $destinationRoot -Force))
$finalDirectories += @(Get-ChildItem -LiteralPath $destinationRoot -Recurse -Force -Directory)
if ($finalFiles.Count -ne 150 -or $finalDirectories.Count -ne 11) { throw 'final file/directory count mismatch' }
$allFinalItems = @($finalFiles); $allFinalItems += @($finalDirectories)
$readonlyFailures = @($allFinalItems | Where-Object { -not (Test-ReadOnly (Get-Item -LiteralPath $_.FullName -Force)) })
if ($readonlyFailures.Count -ne 0) { throw 'final readonly failure' }
$nonMarkerItems = @($allFinalItems | Where-Object { $_.FullName -cne $markerItem.FullName })
$atOrAfter = @($nonMarkerItems | Where-Object { [int64](Get-Item -LiteralPath $_.FullName -Force).LastWriteTimeUtc.Ticks -ge [int64]$markerItem.LastWriteTimeUtc.Ticks })
$maxOtherTicks = [int64](($nonMarkerItems | ForEach-Object { [int64](Get-Item -LiteralPath $_.FullName -Force).LastWriteTimeUtc.Ticks } | Measure-Object -Maximum).Maximum)
if ($atOrAfter.Count -ne 0 -or [int64]$markerItem.LastWriteTimeUtc.Ticks -le $maxOtherTicks) { throw 'marker strict-latest failure' }

$csvFiles = @(Get-ChildItem -LiteralPath $destinationRoot -Recurse -Force -File -Filter '*.csv')
$jsonFiles = @(Get-ChildItem -LiteralPath $destinationRoot -Recurse -Force -File -Filter '*.json')
$csvFailures = 0; foreach ($file in $csvFiles) { try { $null = @(Import-Csv -LiteralPath $file.FullName -ErrorAction Stop) } catch { $csvFailures++ } }
$jsonFailures = 0; foreach ($file in $jsonFiles) { try { $null = Get-Content -LiteralPath $file.FullName -Raw -ErrorAction Stop | ConvertFrom-Json -ErrorAction Stop } catch { $jsonFailures++ } }
$destinationAds = Get-AdsSummary $destinationRoot
$pycCount = @(Get-ChildItem -LiteralPath $destinationRoot -Recurse -Force -File | Where-Object { $_.Extension -ceq '.pyc' }).Count
$pythonCacheCount = @(Get-ChildItem -LiteralPath $destinationRoot -Recurse -Force -Directory | Where-Object { $_.Name -ceq '__pycache__' }).Count
$designatedTexcacheCount = @(Get-ChildItem -LiteralPath $destinationRoot -Recurse -Force -Directory | Where-Object { $_.Name -ceq 'texcache' }).Count
$reparseCount = @(Get-TreeItems $destinationRoot | Where-Object { ($_.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0 }).Count
if ($csvFailures -ne 0 -or $jsonFailures -ne 0 -or $destinationAds['items'] -ne 161 -or $destinationAds['streams'] -ne 150 -or $destinationAds['nondefault'] -ne 0 -or $pycCount -ne 0 -or $pythonCacheCount -ne 0 -or $designatedTexcacheCount -ne 1 -or $reparseCount -ne 0 -or (Test-Path -LiteralPath $stagePath)) { throw 'parse/hygiene/stage gate failure' }

$destinationSnapshot1 = Get-TreeSnapshot $destinationRoot
Start-Sleep -Milliseconds 250
$destinationSnapshot2 = Get-TreeSnapshot $destinationRoot
$sourceAfter = Get-TreeSnapshot $sourceRoot
if ($destinationSnapshot1['sha256'] -cne $destinationSnapshot2['sha256'] -or $sourceBefore['sha256'] -cne $sourceAfter['sha256']) { throw 'postmarker/source drift' }
Assert-Equal $controllerResult.destination_snapshot1 $destinationSnapshot1['sha256'] 'controller destination snapshot1'
Assert-Equal $controllerResult.destination_snapshot2 $destinationSnapshot1['sha256'] 'controller destination snapshot2'
Assert-Equal $controllerResult.snapshot_entries $destinationSnapshot1['entries'] 'controller destination entries'
Assert-Equal $controllerResult.marker_bytes $markerItem.Length 'controller marker bytes'
Assert-Equal $controllerResult.marker_sha256 (Get-FileHash -LiteralPath $markerPath -Algorithm SHA256).Hash 'controller marker sha'
Assert-Equal $controllerResult.marker_ticks $markerItem.LastWriteTimeUtc.Ticks 'controller marker ticks'
Assert-Equal $controllerResult.strict_latest_margin_ticks ([int64]$markerItem.LastWriteTimeUtc.Ticks-$maxOtherTicks) 'controller marker margin'

$auditorResult = [ordered]@{schema='P126_R17A_CONTROL_RESEAL_AUDITOR_RESULT_V1';success=$true;handoff_id=$handoff;operation=$operation;verdict=$verdict;auditor_path=$PSCommandPath;auditor_bytes=(Get-Item -LiteralPath $PSCommandPath).Length;auditor_sha256=(Get-FileHash -LiteralPath $PSCommandPath -Algorithm SHA256).Hash;auditor_invocation_count=1;retry_count=0;controller_result=$controllerResultIdentity;copy_count=145;payload_count=147;control_count=3;ordinary_count=150;dir_count_including_root=11;old_copy_identity_mismatch=0;manifest_identity_mismatch=0;readonly_failures=0;marker_lines=$markerLines.Count;marker_keys=$markerMap.Count;marker_bytes=[int64]$markerItem.Length;marker_sha256=(Get-FileHash -LiteralPath $markerPath -Algorithm SHA256).Hash;marker_ticks=[int64]$markerItem.LastWriteTimeUtc.Ticks;strict_latest_margin_ticks=([int64]$markerItem.LastWriteTimeUtc.Ticks-$maxOtherTicks);at_or_after_excluding_marker=0;source_snapshot_before=$sourceBefore['sha256'];source_snapshot_after=$sourceAfter['sha256'];destination_snapshot1=$destinationSnapshot1['sha256'];destination_snapshot2=$destinationSnapshot2['sha256'];postmarker_drift=0;source_ads=$sourceAds;destination_ads=$destinationAds;csv_count=$csvFiles.Count;csv_parse_failures=$csvFailures;json_count=$jsonFiles.Count;json_parse_failures=$jsonFailures;pyc_count=$pycCount;python_cache_count=$pythonCacheCount;designated_texcache_count=$designatedTexcacheCount;reparse_count=$reparseCount;business_evidence_rerun=0}
Write-Utf8NoBom $auditorResultPath (($auditorResult | ConvertTo-Json -Depth 12)+"`n")
$report = @(
    '# P126 R17A evidence-only control reseal audit';'';"HANDOFF_ID=$handoff";"OPERATION=$operation";"VERDICT=$verdict";'BUSINESS_EVIDENCE_RERUN=0';''
    '- copy=145, payload=147, controls=3, ordinary=150, dirs including root=11';'- old controls copied=0; five-field source-to-destination mismatch=0';'- all files/directories/root ReadOnly; WSTOP unique and strictly latest including root';'- at-or-after excluding marker=0; postmarker content/attribute drift=0; source-root drift=0';'- CSV/JSON parse failures=0; ADS/cache/pyc/reparse failures=0';''
    'This operation reseals preserved R17 material only. It does not rerun or readjudicate visual, object, pair, glyph, mathematical, semantic, or page evidence.'
) -join "`n"
Write-Utf8NoBom $reportPath ($report+"`n")
$handoffText = @('# P126 R17A sealed handoff';'';"HANDOFF_ID=$handoff";"OPERATION=$operation";"VERDICT=$verdict";'REQUEST=MAIN_REVIEW_OF_EVIDENCE_ONLY_CONTROL_RESEAL';'AUDITOR_INVOCATION_COUNT=1';'RETRY_COUNT=0';'BUSINESS_EVIDENCE_RERUN=0') -join "`n"
Write-Utf8NoBom $handoffPath ($handoffText+"`n")
foreach ($path in @($auditorResultPath,$reportPath,$handoffPath)) { $item=Get-Item -LiteralPath $path -Force; $item.Attributes=$item.Attributes -bor [IO.FileAttributes]::ReadOnly }
