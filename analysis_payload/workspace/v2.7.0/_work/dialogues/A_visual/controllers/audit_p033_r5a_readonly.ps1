param(
    [Parameter(Mandatory = $true)][string]$SourceRoot,
    [Parameter(Mandatory = $true)][string]$DestinationRoot
)

$ErrorActionPreference = 'Stop'
$source = [IO.Path]::GetFullPath($SourceRoot)
$destination = [IO.Path]::GetFullPath($DestinationRoot)
$expectedSource = [IO.Path]::GetFullPath('D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P033-01\STRICT_R5_SA1_FRESH_ISOLATED_R111_20260827')
$expectedDestination = [IO.Path]::GetFullPath('D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P033-01\STRICT_R5A_SA1_R111_EVIDENCE_ONLY_CONTROL_RESEAL_20260827')
if ($source -ne $expectedSource -or $destination -ne $expectedDestination) { throw 'Unexpected root identity' }

function Get-RelativePath([string]$Root, [string]$Path) { return [IO.Path]::GetRelativePath($Root, $Path).Replace('\', '/') }
function Get-Identity([string]$Root, [IO.FileInfo]$File) {
    return [ordered]@{
        relative_path = Get-RelativePath $Root $File.FullName
        bytes = [int64]$File.Length
        sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $File.FullName).Hash
        mtime_utc_ticks = $File.LastWriteTimeUtc.Ticks.ToString()
    }
}

$sourceManifest = @(Import-Csv -LiteralPath (Join-Path $source 'seal\MANIFEST_SHA256.csv'))
$copyIdentity = @(Import-Csv -LiteralPath (Join-Path $destination 'COPY_IDENTITY.csv'))
$manifest = @(Import-Csv -LiteralPath (Join-Path $destination 'PAYLOAD_MANIFEST.csv'))
$provenance = Get-Content -LiteralPath (Join-Path $destination 'COPY_PROVENANCE.json') -Raw | ConvertFrom-Json
$sealAudit = Get-Content -LiteralPath (Join-Path $destination 'SEAL_AUDIT.json') -Raw | ConvertFrom-Json
$writeStopped = Get-Content -LiteralPath (Join-Path $destination 'WRITE_STOPPED.json') -Raw | ConvertFrom-Json
$controls = @('PAYLOAD_MANIFEST.csv', 'SEAL_AUDIT.json', 'WRITE_STOPPED.json')
$files = @(Get-ChildItem -LiteralPath $destination -Recurse -File -Force)
$payloadFiles = @($files | Where-Object { (Get-RelativePath $destination $_.FullName) -notin $controls })
$directories = @((Get-Item -LiteralPath $destination -Force)) + @(Get-ChildItem -LiteralPath $destination -Recurse -Directory -Force)

$sourceMap = @{}; foreach ($row in $sourceManifest) { if ($sourceMap.ContainsKey($row.relative_path)) { throw 'Duplicate source manifest path' }; $sourceMap[$row.relative_path] = $row }
$copyMap = @{}; foreach ($row in $copyIdentity) { if ($copyMap.ContainsKey($row.relative_path)) { throw 'Duplicate copy identity path' }; $copyMap[$row.relative_path] = $row }
$payloadMap = @{}; foreach ($file in $payloadFiles) { $relative = Get-RelativePath $destination $file.FullName; if ($payloadMap.ContainsKey($relative)) { throw 'Duplicate payload filesystem path' }; $payloadMap[$relative] = $file }
$manifestMap = @{}; foreach ($row in $manifest) { if ($manifestMap.ContainsKey($row.relative_path)) { throw 'Duplicate payload manifest path' }; $manifestMap[$row.relative_path] = $row }

$copyMismatch = 0
foreach ($relative in $sourceMap.Keys) {
    $sourcePath = Join-Path $source ($relative.Replace('/', [IO.Path]::DirectorySeparatorChar))
    $destinationPath = Join-Path $destination ($relative.Replace('/', [IO.Path]::DirectorySeparatorChar))
    if (-not (Test-Path -LiteralPath $sourcePath -PathType Leaf) -or -not (Test-Path -LiteralPath $destinationPath -PathType Leaf) -or -not $copyMap.ContainsKey($relative)) { $copyMismatch++; continue }
    $sourceIdentity = Get-Identity $source (Get-Item -LiteralPath $sourcePath -Force)
    $destinationIdentity = Get-Identity $destination (Get-Item -LiteralPath $destinationPath -Force)
    foreach ($field in @('relative_path', 'bytes', 'sha256', 'mtime_utc_ticks')) {
        if ($sourceIdentity[$field].ToString() -ne $destinationIdentity[$field].ToString() -or $sourceIdentity[$field].ToString() -ne $copyMap[$relative].$field.ToString()) { $copyMismatch++ }
    }
}
$copySetDiff = @(Compare-Object @($sourceMap.Keys | Sort-Object) @($copyMap.Keys | Sort-Object)).Count

$manifestMismatch = 0
foreach ($relative in $manifestMap.Keys) {
    if (-not $payloadMap.ContainsKey($relative)) { $manifestMismatch++; continue }
    $identity = Get-Identity $destination $payloadMap[$relative]
    foreach ($field in @('relative_path', 'bytes', 'sha256', 'mtime_utc_ticks')) {
        if ($identity[$field].ToString() -ne $manifestMap[$relative].$field.ToString()) { $manifestMismatch++ }
    }
}
$manifestSetDiff = @(Compare-Object @($manifestMap.Keys | Sort-Object) @($payloadMap.Keys | Sort-Object)).Count

$parseFailures = 0
foreach ($file in $files | Where-Object Extension -eq '.json') { try { Get-Content -LiteralPath $file.FullName -Raw | ConvertFrom-Json | Out-Null } catch { $parseFailures++ } }
foreach ($file in $files | Where-Object Extension -eq '.csv') { try { $null = @(Import-Csv -LiteralPath $file.FullName) } catch { $parseFailures++ } }
$ads = @(Get-ChildItem -LiteralPath $destination -Recurse -File -Force | ForEach-Object { Get-Item -LiteralPath $_.FullName -Stream * -ErrorAction SilentlyContinue } | Where-Object Stream -ne ':$DATA')
$cachePyc = @(Get-ChildItem -LiteralPath $destination -Recurse -Force | Where-Object { $_.Name -match '^(texcache|__pycache__|\.cache)$' -or $_.Extension -eq '.pyc' })
$reparse = @(Get-ChildItem -LiteralPath $destination -Recurse -Force | Where-Object { $_.Attributes -band [IO.FileAttributes]::ReparsePoint })

$writeStoppedPath = Join-Path $destination 'WRITE_STOPPED.json'
$markerInfo = Get-Item -LiteralPath $writeStoppedPath -Force
$otherFiles = @($files | Where-Object FullName -ne $markerInfo.FullName)
$maxOther = @($otherFiles | Sort-Object LastWriteTimeUtc -Descending)[0]
$placeholderFiles = @('COPY_PROVENANCE.json', 'SEAL_AUDIT.json', 'WRITE_STOPPED.json')
$placeholderCount = 0
$corruptTrueCount = 0
foreach ($relative in $placeholderFiles) {
    $text = Get-Content -LiteralPath (Join-Path $destination $relative) -Raw
    $placeholderCount += [regex]::Matches($text, '\$[A-Za-z_][A-Za-z0-9_]*').Count
    $corruptTrueCount += [regex]::Matches($text, ([char]9).ToString() + 'rue').Count
}

$expectedReport = [IO.Path]::GetFullPath('D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\reports\FIG-P033-01_R111_R5_COORDINATOR_ROOT_REJECT_20260827.md')
$expectedHandoff = [IO.Path]::GetFullPath('D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\handoff\A_visual\FIG-P033-01_R111_R5_ROOT_REJECT_CONTROL_PLACEHOLDERS_20260827.json')
$expectedReportHash = '933BD513B0B09644CCCA93DD7C724F950AF12982782F7F08CA9D9550B2F0DB7F'
$expectedHandoffHash = '463F5C12584DF8E8338A0D4E24810E1F434DE855209FB1773C100123DADB5D04'
$resolvedIdentityFailures = 0
foreach ($obj in @($provenance, $sealAudit, $writeStopped)) {
    if ([IO.Path]::GetFullPath($obj.source_root) -ne $source) { $resolvedIdentityFailures++ }
    if ([IO.Path]::GetFullPath($obj.destination_root) -ne $destination) { $resolvedIdentityFailures++ }
    if ([IO.Path]::GetFullPath($obj.external_report_path) -ne $expectedReport -or $obj.external_report_sha256 -ne $expectedReportHash) { $resolvedIdentityFailures++ }
    if ([IO.Path]::GetFullPath($obj.external_handoff_path) -ne $expectedHandoff -or $obj.external_handoff_sha256 -ne $expectedHandoffHash) { $resolvedIdentityFailures++ }
}
$booleanFailures = 0
foreach ($value in @($sealAudit.declared_all_files_and_directories_readonly, $sealAudit.declared_write_stopped_strictly_latest, $writeStopped.all_files_and_directories_readonly, $writeStopped.write_stopped_strictly_latest)) { if ($value -isnot [bool] -or -not $value) { $booleanFailures++ } }

$result = [ordered]@{
    source_material_rows = $sourceManifest.Count
    copy_identity_rows = $copyIdentity.Count
    copied_material_set_diff = $copySetDiff
    copied_material_identity_mismatch = $copyMismatch
    payload_manifest_rows = $manifest.Count
    payload_files = $payloadFiles.Count
    payload_manifest_set_diff = $manifestSetDiff
    payload_manifest_identity_mismatch = $manifestMismatch
    controls = $files.Count - $payloadFiles.Count
    ordinary = $files.Count
    readonly_files = $files.Count - @($files | Where-Object { -not $_.IsReadOnly }).Count
    total_files = $files.Count
    readonly_directories = $directories.Count - @($directories | Where-Object { -not ($_.Attributes -band [IO.FileAttributes]::ReadOnly) }).Count
    total_directories = $directories.Count
    parse_failures = $parseFailures
    ads_count = $ads.Count
    cache_pyc_count = $cachePyc.Count
    reparse_count = $reparse.Count
    placeholder_count = $placeholderCount
    corrupted_true_count = $corruptTrueCount
    resolved_identity_failures = $resolvedIdentityFailures
    boolean_failures = $booleanFailures
    write_stopped_ticks = $markerInfo.LastWriteTimeUtc.Ticks.ToString()
    max_other_ticks = $maxOther.LastWriteTimeUtc.Ticks.ToString()
    write_stopped_margin_ticks = ($markerInfo.LastWriteTimeUtc.Ticks - $maxOther.LastWriteTimeUtc.Ticks).ToString()
    files_at_or_after_marker_excluding_marker = @($otherFiles | Where-Object { $_.LastWriteTimeUtc.Ticks -ge $markerInfo.LastWriteTimeUtc.Ticks }).Count
    controller_invocation_count = [int]$writeStopped.controller_invocation_count
    retry_count = [int]$writeStopped.retry_count
    payload_manifest_sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $destination 'PAYLOAD_MANIFEST.csv')).Hash
    seal_audit_sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $destination 'SEAL_AUDIT.json')).Hash
    write_stopped_sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $writeStoppedPath).Hash
}

$hardFailureSum = $result.copied_material_set_diff + $result.copied_material_identity_mismatch + $result.payload_manifest_set_diff + $result.payload_manifest_identity_mismatch + $result.parse_failures + $result.ads_count + $result.cache_pyc_count + $result.reparse_count + $result.placeholder_count + $result.corrupted_true_count + $result.resolved_identity_failures + $result.boolean_failures + $result.files_at_or_after_marker_excluding_marker
if ($result.source_material_rows -ne 43 -or $result.copy_identity_rows -ne 43 -or $result.payload_manifest_rows -ne 45 -or $result.payload_files -ne 45 -or $result.controls -ne 3 -or $result.ordinary -ne 48 -or $result.readonly_files -ne $result.total_files -or $result.readonly_directories -ne $result.total_directories -or [int64]$result.write_stopped_margin_ticks -le 0 -or $result.controller_invocation_count -ne 1 -or $result.retry_count -ne 0 -or $hardFailureSum -ne 0) {
    throw ('Readonly audit failed: ' + ($result | ConvertTo-Json -Compress))
}

$result | ConvertTo-Json -Depth 5
