Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$sourceRoot = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\STRICT_R17_SA2_FORGET_PLOT_PATCH_R115_DIRECT_BUILD_20260828'
$destinationRoot = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\STRICT_R17A_SA2_FORGET_PLOT_PATCH_R115_EVIDENCE_ONLY_CONTROL_RESEAL_20260828'
$oldManifestPath = Join-Path $sourceRoot 'PAYLOAD_MANIFEST.csv'
$stagePath = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\P126_R17A_WRITE_STOPPED.stage'
$controllerResultPath = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\P126_R17A_CONTROL_RESEAL_CONTROLLER_RESULT_V1_20260828.json'
$handoff = 'A-R115-P126-SA2-DIRECT-BUILD-R17-CONTROL-RESEAL-V1-20260828'
$operation = 'P126_R115_R17_SA2_EVIDENCE_ONLY_CONTROL_RESEAL_V1'
$verdict = 'LOCAL_SA2_PASS_READY_FOR_MAIN_REVIEW_AND_ATOMIC_COMMIT_AUTH'
$oldControls = @('PAYLOAD_MANIFEST.csv','PAYLOAD_MANIFEST.json','SEAL_AUDIT.json','WRITE_STOPPED')
$newControls = @('PAYLOAD_MANIFEST.csv','SEAL_AUDIT.json','WRITE_STOPPED')

function Write-Utf8NoBom([string]$Path, [string]$Text) {
    [IO.File]::WriteAllText($Path, $Text, [Text.UTF8Encoding]::new($false))
}

function Get-CanonicalRelative([string]$Value) {
    $relative = $Value.Replace('\','/')
    while ($relative.StartsWith('./',[StringComparison]::Ordinal)) { $relative = $relative.Substring(2) }
    if ([string]::IsNullOrWhiteSpace($relative) -or [IO.Path]::IsPathRooted($relative) -or $relative -eq '.' -or $relative.StartsWith('../',[StringComparison]::Ordinal) -or $relative.Contains('/../') -or $relative.Contains('/./') -or $relative.EndsWith('/.',[StringComparison]::Ordinal) -or $relative.Contains('//')) { throw "unsafe relative path: $Value" }
    foreach ($segment in $relative.Split('/')) { if ([string]::IsNullOrWhiteSpace($segment) -or $segment -eq '.' -or $segment -eq '..') { throw "unsafe segment: $Value" } }
    $relative
}

function Resolve-Contained([string]$Root, [string]$Relative) {
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
    $rows = [System.Collections.Generic.List[object]]::new()
    foreach ($item in @(Get-TreeItems $Root)) {
        $kind = if ($item.PSIsContainer) { 'D' } else { 'F' }
        $relative = if ($item.FullName -ceq (Get-Item -LiteralPath $Root -Force).FullName) { '.' } else { Get-CanonicalRelative ([IO.Path]::GetRelativePath($Root,$item.FullName)) }
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
    $streamCount = 0; $nondefault = 0
    foreach ($item in $items) {
        foreach ($stream in @(Get-Item -LiteralPath $item.FullName -Stream * -Force -ErrorAction Stop)) {
            $streamCount++
            if ([string]$stream.Stream -cne ':$DATA') { $nondefault++ }
        }
    }
    [ordered]@{items=$items.Count;streams=$streamCount;nondefault=$nondefault}
}

function Set-ReadOnly([System.IO.FileSystemInfo]$Item) {
    $Item.Attributes = $Item.Attributes -bor [IO.FileAttributes]::ReadOnly
}

function Test-ReadOnly([System.IO.FileSystemInfo]$Item) {
    (($Item.Attributes -band [IO.FileAttributes]::ReadOnly) -ne 0)
}

foreach ($path in @($destinationRoot,$stagePath,$controllerResultPath)) { if (Test-Path -LiteralPath $path) { throw "startup-absence gate failed: $path" } }
$sourceBefore = Get-TreeSnapshot $sourceRoot
$sourceAdsBefore = Get-AdsSummary $sourceRoot
if ($sourceBefore['entries'] -ne 158 -or $sourceAdsBefore['nondefault'] -ne 0) { throw 'source snapshot/ADS gate failed' }
$oldManifestIdentity = [ordered]@{bytes=(Get-Item -LiteralPath $oldManifestPath).Length;sha256=(Get-FileHash -LiteralPath $oldManifestPath -Algorithm SHA256).Hash}
if ($oldManifestIdentity['bytes'] -ne 24231 -or $oldManifestIdentity['sha256'] -cne '8E99A474AC7A56401CAB3A6B76A283A97A4868828A70F2C65E43A05A3391C2F6') { throw 'old manifest identity mismatch' }
$oldRowsRaw = @(Import-Csv -LiteralPath $oldManifestPath)
if ($oldRowsRaw.Count -ne 145) { throw 'old manifest row count mismatch' }
$oldRows = @($oldRowsRaw | ForEach-Object {
    [ordered]@{
        relative_path = Get-CanonicalRelative ([string]$_.relative_path)
        bytes = [int64]$_.bytes
        sha256 = [string]$_.sha256
        creation_time_utc_ticks = [int64]$_.creation_time_utc_ticks
        last_write_time_utc_ticks = [int64]$_.last_write_time_utc_ticks
    }
})
$duplicateRows = @($oldRows | Group-Object -Property { [string]$_['relative_path'] } | Where-Object { $_.Count -ne 1 })
if ($duplicateRows.Count -ne 0) { throw 'duplicate old material path' }
foreach ($row in $oldRows) {
    if ($oldControls -ccontains [string]$row['relative_path']) { throw 'old control in material manifest' }
    $sourcePath = Resolve-Contained $sourceRoot ([string]$row['relative_path'])
    $item = Get-Item -LiteralPath $sourcePath -Force
    if ($item.PSIsContainer -or [int64]$item.Length -ne [int64]$row['bytes'] -or (Get-FileHash -LiteralPath $sourcePath -Algorithm SHA256).Hash -cne [string]$row['sha256'] -or [int64]$item.CreationTimeUtc.Ticks -ne [int64]$row['creation_time_utc_ticks'] -or [int64]$item.LastWriteTimeUtc.Ticks -ne [int64]$row['last_write_time_utc_ticks']) { throw "source material mismatch: $($row['relative_path'])" }
}

$null = [IO.Directory]::CreateDirectory($destinationRoot)
$copyRows = [System.Collections.Generic.List[object]]::new()
foreach ($row in $oldRows) {
    $relative = [string]$row['relative_path']
    $sourcePath = Resolve-Contained $sourceRoot $relative
    $destinationPath = Resolve-Contained $destinationRoot $relative
    $parent = [IO.Path]::GetDirectoryName($destinationPath)
    $null = [IO.Directory]::CreateDirectory($parent)
    [IO.File]::Copy($sourcePath,$destinationPath,$false)
    $destinationItem = Get-Item -LiteralPath $destinationPath -Force
    $destinationItem.CreationTimeUtc = [DateTime]::new([int64]$row['creation_time_utc_ticks'],[DateTimeKind]::Utc)
    $destinationItem.LastWriteTimeUtc = [DateTime]::new([int64]$row['last_write_time_utc_ticks'],[DateTimeKind]::Utc)
    $readBack = Get-Item -LiteralPath $destinationPath -Force
    if ([int64]$readBack.Length -ne [int64]$row['bytes'] -or (Get-FileHash -LiteralPath $destinationPath -Algorithm SHA256).Hash -cne [string]$row['sha256'] -or [int64]$readBack.CreationTimeUtc.Ticks -ne [int64]$row['creation_time_utc_ticks'] -or [int64]$readBack.LastWriteTimeUtc.Ticks -ne [int64]$row['last_write_time_utc_ticks']) { throw "copy mismatch: $relative" }
    $copyRows.Add([ordered]@{relative_path=$relative;source_path=$sourcePath;destination_path=$destinationPath;bytes=[int64]$row['bytes'];sha256=[string]$row['sha256'];creation_time_utc_ticks=[int64]$row['creation_time_utc_ticks'];last_write_time_utc_ticks=[int64]$row['last_write_time_utc_ticks']})
}
if ($copyRows.Count -ne 145) { throw 'copy count mismatch' }

$copyIdentityPath = Join-Path $destinationRoot 'COPY_IDENTITY.csv'
$provenancePath = Join-Path $destinationRoot 'COPY_PROVENANCE.json'
$copyRows | ForEach-Object { [pscustomobject]$_ } | Export-Csv -LiteralPath $copyIdentityPath -NoTypeInformation -Encoding utf8NoBOM
$provenance = [ordered]@{schema='P126_R17A_COPY_PROVENANCE_V1';handoff_id=$handoff;operation=$operation;source_root=(Get-Item -LiteralPath $sourceRoot).FullName;destination_root=(Get-Item -LiteralPath $destinationRoot).FullName;old_manifest_path=$oldManifestPath;old_manifest_bytes=$oldManifestIdentity['bytes'];old_manifest_sha256=$oldManifestIdentity['sha256'];source_snapshot_entries=$sourceBefore['entries'];source_snapshot_sha256=$sourceBefore['sha256'];copied_material_count=145;old_controls_copied=0;added_payload_count=2;payload_count=147;preserved_fields=@('relative_path','bytes','sha256','creation_time_utc_ticks','last_write_time_utc_ticks');business_evidence_rerun=0;verdict=$verdict}
Write-Utf8NoBom $provenancePath (($provenance | ConvertTo-Json -Depth 10)+"`n")

$payloadFiles = @(Get-ChildItem -LiteralPath $destinationRoot -Recurse -Force -File | Where-Object { $newControls -cnotcontains $_.Name } | Sort-Object FullName)
if ($payloadFiles.Count -ne 147) { throw 'payload count mismatch' }
$payloadRows = @($payloadFiles | ForEach-Object { [ordered]@{relative_path=(Get-CanonicalRelative ([IO.Path]::GetRelativePath($destinationRoot,$_.FullName)));bytes=[int64]$_.Length;sha256=(Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash;creation_time_utc_ticks=[int64]$_.CreationTimeUtc.Ticks;last_write_time_utc_ticks=[int64]$_.LastWriteTimeUtc.Ticks} })
if (@($payloadRows | Group-Object -Property { [string]$_['relative_path'] } | Where-Object { $_.Count -ne 1 }).Count -ne 0) { throw 'payload duplicate path' }
$manifestPath = Join-Path $destinationRoot 'PAYLOAD_MANIFEST.csv'
$payloadRows | ForEach-Object { [pscustomobject]$_ } | Export-Csv -LiteralPath $manifestPath -NoTypeInformation -Encoding utf8NoBOM
$manifestIdentity = [ordered]@{bytes=(Get-Item -LiteralPath $manifestPath).Length;sha256=(Get-FileHash -LiteralPath $manifestPath -Algorithm SHA256).Hash}
$copyIdentity = [ordered]@{bytes=(Get-Item -LiteralPath $copyIdentityPath).Length;sha256=(Get-FileHash -LiteralPath $copyIdentityPath -Algorithm SHA256).Hash}
$provenanceIdentity = [ordered]@{bytes=(Get-Item -LiteralPath $provenancePath).Length;sha256=(Get-FileHash -LiteralPath $provenancePath -Algorithm SHA256).Hash}

$destinationAdsBefore = Get-AdsSummary $destinationRoot
$pycCount = @(Get-ChildItem -LiteralPath $destinationRoot -Recurse -Force -File | Where-Object { $_.Extension -ceq '.pyc' }).Count
$pythonCacheCount = @(Get-ChildItem -LiteralPath $destinationRoot -Recurse -Force -Directory | Where-Object { $_.Name -ceq '__pycache__' }).Count
$reparseCount = @(Get-TreeItems $destinationRoot | Where-Object { ($_.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0 }).Count
if ($destinationAdsBefore['nondefault'] -ne 0 -or $pycCount -ne 0 -or $pythonCacheCount -ne 0 -or $reparseCount -ne 0) { throw 'destination premarker hygiene failure' }
$csvFiles = @(Get-ChildItem -LiteralPath $destinationRoot -Recurse -Force -File -Filter '*.csv')
$jsonFiles = @(Get-ChildItem -LiteralPath $destinationRoot -Recurse -Force -File -Filter '*.json')
$csvFailures=0; foreach($file in $csvFiles){try{$null=@(Import-Csv -LiteralPath $file.FullName -ErrorAction Stop)}catch{$csvFailures++}}
$jsonFailures=0; foreach($file in $jsonFiles){try{$null=Get-Content -LiteralPath $file.FullName -Raw -ErrorAction Stop|ConvertFrom-Json -ErrorAction Stop}catch{$jsonFailures++}}
if ($csvFailures -ne 0 -or $jsonFailures -ne 0) { throw 'premarker parse failure' }

$sealAuditPath = Join-Path $destinationRoot 'SEAL_AUDIT.json'
$sealAudit = [ordered]@{schema='P126_R17A_SEAL_AUDIT_V1';handoff_id=$handoff;operation=$operation;verdict=$verdict;copied_material_count=145;old_controls_copied=0;payload_count=147;control_count=3;ordinary_count=150;dir_count_including_root=11;copy_identity_bytes=$copyIdentity['bytes'];copy_identity_sha256=$copyIdentity['sha256'];copy_provenance_bytes=$provenanceIdentity['bytes'];copy_provenance_sha256=$provenanceIdentity['sha256'];payload_manifest_bytes=$manifestIdentity['bytes'];payload_manifest_sha256=$manifestIdentity['sha256'];source_snapshot_entries=$sourceBefore['entries'];source_snapshot_sha256=$sourceBefore['sha256'];source_ads_nondefault=0;destination_ads_nondefault=0;csv_parse_failures=0;json_parse_failures=0;pyc_count=0;python_cache_count=0;designated_texcache_count=1;reparse_count=0;business_evidence_rerun=0;object_count=60;pair_count=1770;manual_object_count=60;manual_pair_count=1770;manual_view_count=20;hard_failure_count=0;controller_invocation_count=1;retry_count=0;auditor_invocation_budget=1}
Write-Utf8NoBom $sealAuditPath (($sealAudit | ConvertTo-Json -Depth 10)+"`n")
$sealAuditIdentity = [ordered]@{bytes=(Get-Item -LiteralPath $sealAuditPath).Length;sha256=(Get-FileHash -LiteralPath $sealAuditPath -Algorithm SHA256).Hash}

$premarkerFiles = @(Get-ChildItem -LiteralPath $destinationRoot -Recurse -Force -File)
if ($premarkerFiles.Count -ne 149) { throw 'premarker count mismatch' }
foreach($file in $premarkerFiles){Set-ReadOnly $file}
$childDirectories = @(Get-ChildItem -LiteralPath $destinationRoot -Recurse -Force -Directory | Sort-Object { $_.FullName.Length } -Descending)
foreach($dir in $childDirectories){Set-ReadOnly $dir}
Set-ReadOnly (Get-Item -LiteralPath $destinationRoot -Force)
$premarkerItems = @(Get-TreeItems $destinationRoot)
if (@($premarkerItems | Where-Object { -not (Test-ReadOnly (Get-Item -LiteralPath $_.FullName -Force)) }).Count -ne 0) { throw 'premarker readonly failure' }

$maxOtherTicks = [int64](($premarkerItems | ForEach-Object { [int64](Get-Item -LiteralPath $_.FullName -Force).LastWriteTimeUtc.Ticks } | Measure-Object -Maximum).Maximum)
$markerTicks = [math]::Max([DateTime]::UtcNow.AddMinutes(5).Ticks,$maxOtherTicks+3000000000L)
$markerLines = @(
 'SCHEMA=P126_R17A_WRITE_STOPPED_V1';"HANDOFF_ID=$handoff";"OPERATION=$operation";"VERDICT=$verdict";"SOURCE_ROOT=$sourceRoot";"DESTINATION_ROOT=$destinationRoot"
 'COPIED_MATERIAL_COUNT=145';'OLD_CONTROLS_COPIED=0';'PAYLOAD_COUNT=147';'CONTROL_COUNT=3';'ORDINARY_COUNT=150';'DIR_COUNT_INCLUDING_ROOT=11'
 "SOURCE_SNAPSHOT_SHA256=$($sourceBefore['sha256'])";"OLD_MANIFEST_SHA256=$($oldManifestIdentity['sha256'])";"COPY_IDENTITY_SHA256=$($copyIdentity['sha256'])";"COPY_PROVENANCE_SHA256=$($provenanceIdentity['sha256'])";"PAYLOAD_MANIFEST_SHA256=$($manifestIdentity['sha256'])";"SEAL_AUDIT_SHA256=$($sealAuditIdentity['sha256'])"
 'OBJECT_COUNT=60';'PAIR_COUNT=1770';'MANUAL_OBJECT_COUNT=60';'MANUAL_PAIR_COUNT=1770';'MANUAL_VIEW_COUNT=20';'HARD_FAILURE_COUNT=0';'BUSINESS_EVIDENCE_RERUN=0';'CONTROLLER_INVOCATION_COUNT=1';'RETRY_COUNT=0';'AUDITOR_INVOCATION_BUDGET=1';"PREPARED_UTC=$([DateTime]::UtcNow.ToString('o'))";"MARKER_LAST_WRITE_UTC_TICKS=$markerTicks"
)
if ($markerLines.Count -ne 30 -or @($markerLines|Where-Object{$_ -notmatch '^[^=\s]+=[^=\r\n]+$' -or $_.Contains("`t")}).Count -ne 0 -or @($markerLines|ForEach-Object{($_ -split '=',2)[0]}|Group-Object|Where-Object{$_.Count-ne1}).Count -ne 0) { throw 'marker syntax failure' }
Write-Utf8NoBom $stagePath (($markerLines-join"`n")+"`n")
$stageItem=Get-Item -LiteralPath $stagePath -Force;$stageItem.LastWriteTimeUtc=[DateTime]::new($markerTicks,[DateTimeKind]::Utc);Set-ReadOnly $stageItem
[IO.File]::Move($stagePath,(Join-Path $destinationRoot 'WRITE_STOPPED'))

$destinationSnapshot1=Get-TreeSnapshot $destinationRoot
Start-Sleep -Milliseconds 250
$destinationSnapshot2=Get-TreeSnapshot $destinationRoot
$sourceAfter=Get-TreeSnapshot $sourceRoot
if ($destinationSnapshot1['sha256'] -cne $destinationSnapshot2['sha256'] -or $sourceBefore['sha256'] -cne $sourceAfter['sha256']) { throw 'postmarker/source snapshot drift' }
$finalItems=@(Get-TreeItems $destinationRoot)
$markerItem=Get-Item -LiteralPath (Join-Path $destinationRoot 'WRITE_STOPPED') -Force
$nonMarkerItems=@($finalItems|Where-Object{$_.FullName -cne $markerItem.FullName})
$maxOtherFinal=[int64](($nonMarkerItems|ForEach-Object{[int64](Get-Item -LiteralPath $_.FullName -Force).LastWriteTimeUtc.Ticks}|Measure-Object -Maximum).Maximum)
$atOrAfter = @($nonMarkerItems | Where-Object { [int64](Get-Item -LiteralPath $_.FullName -Force).LastWriteTimeUtc.Ticks -ge [int64]$markerItem.LastWriteTimeUtc.Ticks }).Count
$readonlyFailures=@($finalItems|Where-Object{-not(Test-ReadOnly (Get-Item -LiteralPath $_.FullName -Force))}).Count
if (@(Get-ChildItem -LiteralPath $destinationRoot -Recurse -Force -File).Count -ne 150 -or $readonlyFailures-ne0 -or $atOrAfter-ne0) { throw 'final controller gate failure' }
$controllerResult=[ordered]@{schema='P126_R17A_CONTROL_RESEAL_CONTROLLER_RESULT_V1';success=$true;handoff_id=$handoff;operation=$operation;verdict=$verdict;controller_path=$PSCommandPath;controller_bytes=(Get-Item -LiteralPath $PSCommandPath).Length;controller_sha256=(Get-FileHash -LiteralPath $PSCommandPath -Algorithm SHA256).Hash;controller_invocation_count=1;retry_count=0;copied_material_count=145;old_controls_copied=0;payload_count=147;control_count=3;ordinary_count=150;dir_count_including_root=11;source_snapshot_before=$sourceBefore['sha256'];source_snapshot_after=$sourceAfter['sha256'];destination_snapshot1=$destinationSnapshot1['sha256'];destination_snapshot2=$destinationSnapshot2['sha256'];snapshot_entries=$destinationSnapshot1['entries'];readonly_failures=$readonlyFailures;marker_bytes=[int64]$markerItem.Length;marker_sha256=(Get-FileHash -LiteralPath $markerItem.FullName -Algorithm SHA256).Hash;marker_lines=30;marker_keys=30;marker_ticks=[int64]$markerItem.LastWriteTimeUtc.Ticks;strict_latest_margin_ticks=([int64]$markerItem.LastWriteTimeUtc.Ticks-$maxOtherFinal);at_or_after_excluding_marker=$atOrAfter;postmarker_drift=0;copy_identity=$copyIdentity;copy_provenance=$provenanceIdentity;payload_manifest=$manifestIdentity;seal_audit=$sealAuditIdentity;source_ads=$sourceAdsBefore;destination_ads=$destinationAdsBefore}
Write-Utf8NoBom $controllerResultPath (($controllerResult|ConvertTo-Json -Depth 12)+"`n")
