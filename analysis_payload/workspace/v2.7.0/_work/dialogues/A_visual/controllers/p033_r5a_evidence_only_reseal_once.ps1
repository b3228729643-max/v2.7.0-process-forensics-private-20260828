param(
    [Parameter(Mandatory = $true)][string]$SourceRoot,
    [Parameter(Mandatory = $true)][string]$DestinationRoot,
    [Parameter(Mandatory = $true)][string]$ExternalReportPath,
    [Parameter(Mandatory = $true)][string]$ExternalHandoffPath,
    [Parameter(Mandatory = $true)][string]$ExecutionGrant
)

$ErrorActionPreference = 'Stop'
$expectedGrant = 'P033_R5A_EVIDENCE_ONLY_CONTROL_RESEAL_GRANTED_R321'
if ($ExecutionGrant -ne $expectedGrant) { throw 'Execution grant mismatch' }

$source = [IO.Path]::GetFullPath($SourceRoot)
$destination = [IO.Path]::GetFullPath($DestinationRoot)
$externalReport = [IO.Path]::GetFullPath($ExternalReportPath)
$externalHandoff = [IO.Path]::GetFullPath($ExternalHandoffPath)
$expectedSource = [IO.Path]::GetFullPath('D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P033-01\STRICT_R5_SA1_FRESH_ISOLATED_R111_20260827')
$expectedDestination = [IO.Path]::GetFullPath('D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P033-01\STRICT_R5A_SA1_R111_EVIDENCE_ONLY_CONTROL_RESEAL_20260827')
$expectedReport = [IO.Path]::GetFullPath('D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\reports\FIG-P033-01_R111_R5_COORDINATOR_ROOT_REJECT_20260827.md')
$expectedHandoff = [IO.Path]::GetFullPath('D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\handoff\A_visual\FIG-P033-01_R111_R5_ROOT_REJECT_CONTROL_PLACEHOLDERS_20260827.json')

if ($source -ne $expectedSource) { throw 'Unexpected source root' }
if ($destination -ne $expectedDestination) { throw 'Unexpected destination root' }
if ($externalReport -ne $expectedReport) { throw 'Unexpected external report path' }
if ($externalHandoff -ne $expectedHandoff) { throw 'Unexpected external handoff path' }
if (-not (Test-Path -LiteralPath $source -PathType Container)) { throw 'Source root missing' }
if (Test-Path -LiteralPath $destination) { throw 'Destination root must not exist' }

$reportInfo = Get-Item -LiteralPath $externalReport -Force
$handoffInfo = Get-Item -LiteralPath $externalHandoff -Force
$reportHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $externalReport).Hash
$handoffHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $externalHandoff).Hash
if ($reportInfo.Length -ne 3149 -or $reportHash -ne '933BD513B0B09644CCCA93DD7C724F950AF12982782F7F08CA9D9550B2F0DB7F') { throw 'External report identity mismatch' }
if ($handoffInfo.Length -ne 1559 -or $handoffHash -ne '463F5C12584DF8E8338A0D4E24810E1F434DE855209FB1773C100123DADB5D04') { throw 'External handoff identity mismatch' }

function Get-RelativePath([string]$Root, [string]$Path) {
    return [IO.Path]::GetRelativePath($Root, $Path).Replace('\', '/')
}

function Get-FileIdentity([string]$Root, [IO.FileInfo]$File) {
    return [ordered]@{
        relative_path = Get-RelativePath $Root $File.FullName
        bytes = [int64]$File.Length
        sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $File.FullName).Hash
        mtime_utc_ticks = $File.LastWriteTimeUtc.Ticks.ToString()
    }
}

function Assert-NoTemplateTokens([string]$Path) {
    $text = [IO.File]::ReadAllText($Path)
    if ($text -match '\$[A-Za-z_][A-Za-z0-9_]*') { throw "Unresolved template token in $Path" }
    if ($text.Contains(([char]9).ToString() + 'rue')) { throw "Corrupted true token in $Path" }
}

$sourceManifest = Join-Path $source 'seal\MANIFEST_SHA256.csv'
$sourceRows = @(Import-Csv -LiteralPath $sourceManifest)
if ($sourceRows.Count -ne 43) { throw "Expected 43 source material rows, got $($sourceRows.Count)" }
if (@($sourceRows | Group-Object relative_path | Where-Object Count -ne 1).Count -ne 0) { throw 'Source manifest contains duplicate paths' }

$sourceMaterial = [System.Collections.Generic.List[object]]::new()
foreach ($row in $sourceRows) {
    $relative = $row.relative_path.Replace('/', [IO.Path]::DirectorySeparatorChar)
    $sourcePath = [IO.Path]::GetFullPath((Join-Path $source $relative))
    if (-not $sourcePath.StartsWith($source + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) { throw "Source path escaped root: $relative" }
    $sourceFile = Get-Item -LiteralPath $sourcePath -Force
    $identity = Get-FileIdentity $source $sourceFile
    if ($identity.bytes.ToString() -ne $row.bytes.ToString() -or $identity.sha256 -ne $row.sha256) { throw "Source manifest identity mismatch: $relative" }
    $sourceMaterial.Add([pscustomobject]@{ row = $row; file = $sourceFile; identity = $identity })
}

[IO.Directory]::CreateDirectory($destination) | Out-Null
$copyRows = [System.Collections.Generic.List[object]]::new()
foreach ($item in $sourceMaterial) {
    $relativeNative = $item.identity.relative_path.Replace('/', [IO.Path]::DirectorySeparatorChar)
    $targetPath = [IO.Path]::GetFullPath((Join-Path $destination $relativeNative))
    if (-not $targetPath.StartsWith($destination + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) { throw "Destination path escaped root: $relativeNative" }
    [IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($targetPath)) | Out-Null
    [IO.File]::Copy($item.file.FullName, $targetPath, $false)
    $targetFile = Get-Item -LiteralPath $targetPath -Force
    $targetFile.IsReadOnly = $false
    $targetFile.LastWriteTimeUtc = $item.file.LastWriteTimeUtc
    $targetFile = Get-Item -LiteralPath $targetPath -Force
    $targetIdentity = Get-FileIdentity $destination $targetFile
    foreach ($field in @('relative_path', 'bytes', 'sha256', 'mtime_utc_ticks')) {
        if ($item.identity[$field].ToString() -ne $targetIdentity[$field].ToString()) { throw "Copy identity mismatch for $($item.identity.relative_path), field $field" }
    }
    $copyRows.Add([pscustomobject][ordered]@{
        relative_path = $item.identity.relative_path
        bytes = $item.identity.bytes
        sha256 = $item.identity.sha256
        mtime_utc_ticks = $item.identity.mtime_utc_ticks
    })
}

$copyIdentityPath = Join-Path $destination 'COPY_IDENTITY.csv'
$copyProvenancePath = Join-Path $destination 'COPY_PROVENANCE.json'
$copyRows | Export-Csv -LiteralPath $copyIdentityPath -NoTypeInformation -Encoding utf8
$controllerPath = [IO.Path]::GetFullPath($PSCommandPath)
$provenance = [ordered]@{
    handoff_id = 'A-R111-P033-SA1-FRESH-ISOLATED-20260827'
    reseal_round = 'R5A'
    execution_grant = $ExecutionGrant
    source_root = $source
    destination_root = $destination
    source_manifest_path = [IO.Path]::GetFullPath($sourceManifest)
    source_manifest_sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $sourceManifest).Hash
    copied_material_count = 43
    old_control_files_copied = 0
    external_report_path = $externalReport
    external_report_bytes = [int64]$reportInfo.Length
    external_report_sha256 = $reportHash
    external_handoff_path = $externalHandoff
    external_handoff_bytes = [int64]$handoffInfo.Length
    external_handoff_sha256 = $handoffHash
    controller_path = $controllerPath
    controller_bytes = [int64](Get-Item -LiteralPath $controllerPath).Length
    controller_sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $controllerPath).Hash
    controller_invocation_count = 1
    retry_count = 0
    created_at_utc = [DateTime]::UtcNow.ToString('o')
}
$provenance | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $copyProvenancePath -Encoding utf8
Assert-NoTemplateTokens $copyProvenancePath

$manifestPath = Join-Path $destination 'PAYLOAD_MANIFEST.csv'
$sealAuditPath = Join-Path $destination 'SEAL_AUDIT.json'
$writeStoppedPath = Join-Path $destination 'WRITE_STOPPED.json'
$controls = @('PAYLOAD_MANIFEST.csv', 'SEAL_AUDIT.json', 'WRITE_STOPPED.json')
$payloadFiles = @(Get-ChildItem -LiteralPath $destination -Recurse -File -Force | Where-Object {
    (Get-RelativePath $destination $_.FullName) -notin $controls
} | Sort-Object FullName)
if ($payloadFiles.Count -ne 45) { throw "Expected 45 payload files, got $($payloadFiles.Count)" }
$payloadRows = @($payloadFiles | ForEach-Object { [pscustomobject](Get-FileIdentity $destination $_) })
$payloadRows | Export-Csv -LiteralPath $manifestPath -NoTypeInformation -Encoding utf8

$copyBack = @(Import-Csv -LiteralPath $copyIdentityPath)
if ($copyBack.Count -ne 43) { throw 'COPY_IDENTITY row count mismatch' }
$copyMap = @{}; foreach ($row in $copyBack) { if ($copyMap.ContainsKey($row.relative_path)) { throw 'COPY_IDENTITY duplicate path' }; $copyMap[$row.relative_path] = $row }
foreach ($item in $sourceMaterial) {
    $relative = $item.identity.relative_path
    if (-not $copyMap.ContainsKey($relative)) { throw "COPY_IDENTITY missing $relative" }
    foreach ($field in @('bytes', 'sha256', 'mtime_utc_ticks')) {
        if ($copyMap[$relative].$field.ToString() -ne $item.identity[$field].ToString()) { throw "COPY_IDENTITY mismatch $relative $field" }
    }
}

$manifestRows = @(Import-Csv -LiteralPath $manifestPath)
if ($manifestRows.Count -ne 45) { throw 'Payload manifest row count mismatch' }
if (@($manifestRows | Group-Object relative_path | Where-Object Count -ne 1).Count -ne 0) { throw 'Payload manifest duplicate path' }
$payloadMap = @{}; foreach ($file in $payloadFiles) { $payloadMap[(Get-RelativePath $destination $file.FullName)] = $file }
foreach ($row in $manifestRows) {
    if (-not $payloadMap.ContainsKey($row.relative_path)) { throw "Manifest extra path $($row.relative_path)" }
    $identity = Get-FileIdentity $destination $payloadMap[$row.relative_path]
    foreach ($field in @('bytes', 'sha256', 'mtime_utc_ticks')) {
        if ($row.$field.ToString() -ne $identity[$field].ToString()) { throw "Manifest mismatch $($row.relative_path) $field" }
    }
}

$parseFailures = 0
foreach ($file in $payloadFiles | Where-Object Extension -eq '.json') { try { Get-Content -LiteralPath $file.FullName -Raw | ConvertFrom-Json | Out-Null } catch { $parseFailures++ } }
foreach ($file in $payloadFiles | Where-Object Extension -eq '.csv') { try { $null = @(Import-Csv -LiteralPath $file.FullName) } catch { $parseFailures++ } }
try { $null = @(Import-Csv -LiteralPath $manifestPath) } catch { $parseFailures++ }
if ($parseFailures -ne 0) { throw "Parse failures: $parseFailures" }

$ads = @(Get-ChildItem -LiteralPath $destination -Recurse -File -Force | ForEach-Object { Get-Item -LiteralPath $_.FullName -Stream * -ErrorAction SilentlyContinue } | Where-Object Stream -ne ':$DATA')
$cachePyc = @(Get-ChildItem -LiteralPath $destination -Recurse -Force | Where-Object { $_.Name -match '^(texcache|__pycache__|\.cache)$' -or $_.Extension -eq '.pyc' })
$reparse = @(Get-ChildItem -LiteralPath $destination -Recurse -Force | Where-Object { $_.Attributes -band [IO.FileAttributes]::ReparsePoint })
if ($ads.Count -ne 0 -or $cachePyc.Count -ne 0 -or $reparse.Count -ne 0) { throw "Forbidden filesystem artifacts: ADS=$($ads.Count) cachePyc=$($cachePyc.Count) reparse=$($reparse.Count)" }

$sealAudit = [ordered]@{
    handoff_id = 'A-R111-P033-SA1-FRESH-ISOLATED-20260827'
    reseal_round = 'R5A'
    result = 'SA1_CONTENT_PASS_READY_FOR_FRESH_ISOLATED_SA3'
    source_root = $source
    destination_root = $destination
    external_report_path = $externalReport
    external_report_sha256 = $reportHash
    external_handoff_path = $externalHandoff
    external_handoff_sha256 = $handoffHash
    source_material_count = 43
    copied_material_count = 43
    old_controls_copied = 0
    new_copy_identity_payload_count = 1
    new_copy_provenance_payload_count = 1
    final_payload_count = 45
    manifest_control_count = 1
    seal_audit_control_count = 1
    write_stopped_control_count = 1
    final_control_count = 3
    final_ordinary_count = 48
    copy_identity_mismatch_count = 0
    manifest_filesystem_mismatch_count = 0
    parse_failure_count = 0
    ads_count = 0
    cache_pyc_count = 0
    reparse_count = 0
    controller_invocation_count = 1
    retry_count = 0
    declared_all_files_and_directories_readonly = $true
    declared_write_stopped_strictly_latest = $true
    declared_postmarker_write_count = 0
    created_at_utc = [DateTime]::UtcNow.ToString('o')
}
$sealAudit | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $sealAuditPath -Encoding utf8
Assert-NoTemplateTokens $sealAuditPath

$preMarkerFiles = @(Get-ChildItem -LiteralPath $destination -Recurse -File -Force)
if ($preMarkerFiles.Count -ne 47) { throw "Expected 47 premarker files, got $($preMarkerFiles.Count)" }
foreach ($file in $preMarkerFiles) { $file.IsReadOnly = $true }
$directories = @(Get-ChildItem -LiteralPath $destination -Recurse -Directory -Force | Sort-Object FullName -Descending)
foreach ($directory in $directories) { $directory.Attributes = $directory.Attributes -bor [IO.FileAttributes]::ReadOnly }
(Get-Item -LiteralPath $destination -Force).Attributes = (Get-Item -LiteralPath $destination -Force).Attributes -bor [IO.FileAttributes]::ReadOnly

$maxPreMarkerTicks = ($preMarkerFiles | Sort-Object LastWriteTimeUtc -Descending | Select-Object -First 1).LastWriteTimeUtc.Ticks
while ([DateTime]::UtcNow.Ticks -le $maxPreMarkerTicks) { Start-Sleep -Milliseconds 10 }

$writeStopped = [ordered]@{
    handoff_id = 'A-R111-P033-SA1-FRESH-ISOLATED-20260827'
    reseal_round = 'R5A'
    result = 'SA1_CONTENT_PASS_READY_FOR_FRESH_ISOLATED_SA3'
    source_root = $source
    destination_root = $destination
    external_report_path = $externalReport
    external_report_sha256 = $reportHash
    external_handoff_path = $externalHandoff
    external_handoff_sha256 = $handoffHash
    payload_manifest_path = [IO.Path]::GetFullPath($manifestPath)
    payload_manifest_sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $manifestPath).Hash
    seal_audit_path = [IO.Path]::GetFullPath($sealAuditPath)
    seal_audit_sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $sealAuditPath).Hash
    payload_file_count = 45
    control_file_count = 3
    ordinary_file_total = 48
    all_files_and_directories_readonly = $true
    write_stopped_strictly_latest = $true
    postmarker_write_count = 0
    controller_invocation_count = 1
    retry_count = 0
    created_at_utc = [DateTime]::UtcNow.ToString('o')
}
$writeStoppedJson = $writeStopped | ConvertTo-Json -Depth 6
if ($writeStoppedJson -match '\$[A-Za-z_][A-Za-z0-9_]*' -or $writeStoppedJson.Contains(([char]9).ToString() + 'rue')) { throw 'WRITE_STOPPED contains unresolved or corrupted control content' }
[IO.File]::WriteAllText($writeStoppedPath, $writeStoppedJson + [Environment]::NewLine, [Text.UTF8Encoding]::new($false))
(Get-Item -LiteralPath $writeStoppedPath -Force).IsReadOnly = $true

[pscustomobject]@{
    source_root = $source
    destination_root = $destination
    copied_material = 43
    payload = 45
    controls = 3
    ordinary = 48
    manifest_sha256 = $writeStopped.payload_manifest_sha256
    seal_audit_sha256 = $writeStopped.seal_audit_sha256
    write_stopped_sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $writeStoppedPath).Hash
    write_stopped_ticks = (Get-Item -LiteralPath $writeStoppedPath -Force).LastWriteTimeUtc.Ticks.ToString()
    max_pre_marker_ticks = $maxPreMarkerTicks.ToString()
    controller_invocation_count = 1
    retry_count = 0
    exit = 0
} | ConvertTo-Json -Depth 5
