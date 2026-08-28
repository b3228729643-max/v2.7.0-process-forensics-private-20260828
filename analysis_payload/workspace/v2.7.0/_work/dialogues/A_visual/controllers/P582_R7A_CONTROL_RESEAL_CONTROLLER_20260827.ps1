param(
    [Parameter(Mandatory = $true)] [string] $SourceRoot,
    [Parameter(Mandatory = $true)] [string] $DestinationRoot,
    [Parameter(Mandatory = $true)] [string] $ExecutionGrant
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$ExpectedGrant = 'P582_R7A_ONE_CONTROL_RESEAL_AUTHORIZED'
$ExpectedSourceRoot = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P582-01\STRICT_R7_SA1_FRESH_ISOLATED_R110_20260827'
$ExpectedDestinationRoot = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P582-01\STRICT_R7A_SA1_R110_EVIDENCE_ONLY_CONTROL_RESEAL_20260827'
$OldControls = @('payload_manifest.json', 'payload_manifest.sha256', 'WRITE_STOPPED')
$NewControls = @('PAYLOAD_MANIFEST.json', 'SEAL_AUDIT.json', 'WRITE_STOPPED')
$Utf8NoBom = [System.Text.UTF8Encoding]::new($false)

function Assert-True {
    param([bool] $Condition, [string] $Message)
    if (-not $Condition) { throw $Message }
}

function Get-Sha256 {
    param([string] $Path)
    return (Get-FileHash -Algorithm SHA256 -LiteralPath $Path).Hash.ToUpperInvariant()
}

function Write-Utf8NoBom {
    param([string] $Path, [string] $Content)
    [System.IO.File]::WriteAllText($Path, $Content, $script:Utf8NoBom)
}

function Normalize-RelativePath {
    param([string] $RelativePath)
    return $RelativePath.Replace('\', '/').TrimStart('/')
}

function Resolve-ChildPath {
    param([string] $Root, [string] $RelativePath)
    $normalized = Normalize-RelativePath $RelativePath
    Assert-True (-not [System.IO.Path]::IsPathRooted($normalized)) "Rooted relative path rejected: $RelativePath"
    Assert-True (-not $normalized.Contains(':')) "Colon in relative path rejected: $RelativePath"
    $native = $normalized.Replace('/', [System.IO.Path]::DirectorySeparatorChar)
    $resolved = [System.IO.Path]::GetFullPath((Join-Path $Root $native))
    $rootPrefix = $Root.TrimEnd('\') + '\'
    Assert-True ($resolved.StartsWith($rootPrefix, [System.StringComparison]::OrdinalIgnoreCase)) "Path escapes root: $RelativePath"
    return $resolved
}

function Get-RelativePathNormalized {
    param([string] $Root, [string] $Path)
    return (Normalize-RelativePath ([System.IO.Path]::GetRelativePath($Root, $Path)))
}

function Set-ReadonlyAttribute {
    param([string] $Path)
    $attributes = [System.IO.File]::GetAttributes($Path)
    [System.IO.File]::SetAttributes($Path, ($attributes -bor [System.IO.FileAttributes]::ReadOnly))
}

function Get-NonDefaultAdsCount {
    param([string] $Root)
    $count = 0
    foreach ($file in Get-ChildItem -LiteralPath $Root -Recurse -File -Force) {
        $streams = @(Get-Item -LiteralPath $file.FullName -Stream * -ErrorAction Stop)
        $count += @($streams | Where-Object { $_.Stream -ne ':$DATA' }).Count
    }
    return $count
}

$source = [System.IO.Path]::GetFullPath($SourceRoot).TrimEnd('\')
$destination = [System.IO.Path]::GetFullPath($DestinationRoot).TrimEnd('\')
Assert-True ($ExecutionGrant -ceq $ExpectedGrant) 'Execution grant mismatch.'
Assert-True ($source -ceq $ExpectedSourceRoot) 'Resolved source root mismatch.'
Assert-True ($destination -ceq $ExpectedDestinationRoot) 'Resolved destination root mismatch.'
Assert-True (Test-Path -LiteralPath $source -PathType Container) 'Source root is missing.'
Assert-True (-not (Test-Path -LiteralPath $destination)) 'Destination root must not exist before the one-time invocation.'

$sourceManifestPath = Join-Path $source 'payload_manifest.json'
Assert-True (Test-Path -LiteralPath $sourceManifestPath -PathType Leaf) 'R7 payload manifest is missing.'
$sourceManifest = Get-Content -LiteralPath $sourceManifestPath -Raw -Encoding UTF8 | ConvertFrom-Json
Assert-True ([int]$sourceManifest.file_count -eq 140) 'R7 manifest declared count is not 140.'
Assert-True (@($sourceManifest.files).Count -eq 140) 'R7 manifest row count is not 140.'

$seen = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)
$sourceRows = [System.Collections.Generic.List[object]]::new()
foreach ($row in @($sourceManifest.files)) {
    $relative = Normalize-RelativePath ([string]$row.relative_path)
    Assert-True ($OldControls -notcontains $relative) "Old control appears in material manifest: $relative"
    Assert-True ($seen.Add($relative)) "Duplicate R7 manifest path: $relative"
    $sourcePath = Resolve-ChildPath $source $relative
    Assert-True (Test-Path -LiteralPath $sourcePath -PathType Leaf) "Missing source payload: $relative"
    $sourceItem = Get-Item -LiteralPath $sourcePath -Force
    $sourceSha = Get-Sha256 $sourcePath
    Assert-True ($sourceItem.Length -eq [int64]$row.size_bytes) "Source size mismatch: $relative"
    Assert-True ($sourceSha -ceq ([string]$row.sha256).ToUpperInvariant()) "Source SHA mismatch: $relative"
    $sourceRows.Add([pscustomobject]@{
        relative_path = $relative
        source_path = $sourcePath
        size_bytes = [int64]$sourceItem.Length
        sha256 = $sourceSha
        mtime_utc_ticks = $sourceItem.LastWriteTimeUtc.Ticks.ToString()
        mtime_utc_7digit = $sourceItem.LastWriteTimeUtc.ToString('yyyy-MM-ddTHH:mm:ss.fffffffZ', [System.Globalization.CultureInfo]::InvariantCulture)
    })
}
Assert-True ($sourceRows.Count -eq 140) 'Validated source material denominator is not 140.'

[System.IO.Directory]::CreateDirectory($destination) | Out-Null
$copyRows = [System.Collections.Generic.List[object]]::new()
$copyMismatch = 0
$materialIndex = 0
foreach ($row in ($sourceRows | Sort-Object relative_path)) {
    $materialIndex++
    $destinationPath = Resolve-ChildPath $destination $row.relative_path
    $destinationDirectory = [System.IO.Path]::GetDirectoryName($destinationPath)
    [System.IO.Directory]::CreateDirectory($destinationDirectory) | Out-Null
    [System.IO.File]::Copy($row.source_path, $destinationPath, $false)
    [System.IO.File]::SetLastWriteTimeUtc($destinationPath, [datetime]::new([int64]$row.mtime_utc_ticks, [System.DateTimeKind]::Utc))
    $destinationItem = Get-Item -LiteralPath $destinationPath -Force
    $destinationSha = Get-Sha256 $destinationPath
    $destinationTicks = $destinationItem.LastWriteTimeUtc.Ticks.ToString()
    if ($destinationItem.Length -ne $row.size_bytes -or $destinationSha -cne $row.sha256 -or $destinationTicks -cne $row.mtime_utc_ticks) {
        $copyMismatch++
    }
    $copyRows.Add([pscustomobject]@{
        material_index = $materialIndex
        source_relative_path = $row.relative_path
        destination_relative_path = $row.relative_path
        size_bytes = $row.size_bytes
        sha256 = $row.sha256
        source_mtime_utc_ticks = $row.mtime_utc_ticks
        destination_mtime_utc_ticks = $destinationTicks
        source_mtime_utc_7digit = $row.mtime_utc_7digit
        destination_mtime_utc_7digit = $destinationItem.LastWriteTimeUtc.ToString('yyyy-MM-ddTHH:mm:ss.fffffffZ', [System.Globalization.CultureInfo]::InvariantCulture)
    })
}
Assert-True ($copyMismatch -eq 0) 'Source-to-destination material copy identity mismatch.'
Assert-True ($copyRows.Count -eq 140) 'COPY_IDENTITY row denominator is not 140.'

$copyIdentityPath = Join-Path $destination 'COPY_IDENTITY.csv'
$copyRows | Export-Csv -LiteralPath $copyIdentityPath -NoTypeInformation -Encoding utf8NoBOM

$controllerItem = Get-Item -LiteralPath $PSCommandPath -Force
$provenance = [ordered]@{
    handoff_id = 'A-R110-P582-SA1-FRESH-ISOLATED-20260827'
    reseal_round = 'R7A_EVIDENCE_ONLY_CONTROL_RESEAL'
    figure_uid = 'FIG-P582-01'
    source_root = $source
    destination_root = $destination
    source_manifest_path = $sourceManifestPath
    source_manifest_sha256 = Get-Sha256 $sourceManifestPath
    material_payload_count = 140
    copy_identity_file = 'COPY_IDENTITY.csv'
    controller_path = [System.IO.Path]::GetFullPath($PSCommandPath)
    controller_bytes = [int64]$controllerItem.Length
    controller_sha256 = Get-Sha256 $PSCommandPath
    execution_grant = $ExecutionGrant
    created_at_utc = [datetime]::UtcNow.ToString('o')
}
Assert-True (-not $provenance.source_root.Contains('$')) 'Unresolved placeholder in source root.'
Assert-True (-not $provenance.destination_root.Contains('$')) 'Unresolved placeholder in destination root.'
$provenancePath = Join-Path $destination 'COPY_PROVENANCE.json'
Write-Utf8NoBom $provenancePath (($provenance | ConvertTo-Json -Depth 6) + "`n")

$payloadFiles = @(Get-ChildItem -LiteralPath $destination -Recurse -File -Force)
Assert-True ($payloadFiles.Count -eq 142) "Expected 142 payload files before controls; got $($payloadFiles.Count)."
$payloadRows = [System.Collections.Generic.List[object]]::new()
foreach ($file in ($payloadFiles | Sort-Object FullName)) {
    $relative = Get-RelativePathNormalized $destination $file.FullName
    Assert-True ($NewControls -notcontains $relative) "Control name appeared before manifest stage: $relative"
    $payloadRows.Add([pscustomobject]@{
        relative_path = $relative
        size_bytes = [int64]$file.Length
        sha256 = Get-Sha256 $file.FullName
        mtime_utc_ticks = $file.LastWriteTimeUtc.Ticks.ToString()
        mtime_utc_7digit = $file.LastWriteTimeUtc.ToString('yyyy-MM-ddTHH:mm:ss.fffffffZ', [System.Globalization.CultureInfo]::InvariantCulture)
    })
}
$payloadTotalBytes = [int64](($payloadRows | Measure-Object size_bytes -Sum).Sum)
$newManifest = [ordered]@{
    handoff_id = 'A-R110-P582-SA1-FRESH-ISOLATED-20260827'
    reseal_round = 'R7A_EVIDENCE_ONLY_CONTROL_RESEAL'
    figure_uid = 'FIG-P582-01'
    manifest_scope = '142 payload files; excludes PAYLOAD_MANIFEST.json, SEAL_AUDIT.json, WRITE_STOPPED'
    file_count = 142
    total_size_bytes = $payloadTotalBytes
    files = @($payloadRows | Sort-Object relative_path)
}
$newManifestPath = Join-Path $destination 'PAYLOAD_MANIFEST.json'
Write-Utf8NoBom $newManifestPath (($newManifest | ConvertTo-Json -Depth 8) + "`n")

$manifestReadback = Get-Content -LiteralPath $newManifestPath -Raw -Encoding UTF8 | ConvertFrom-Json
Assert-True ([int]$manifestReadback.file_count -eq 142) 'New manifest declared denominator is not 142.'
Assert-True (@($manifestReadback.files).Count -eq 142) 'New manifest row denominator is not 142.'
$manifestSeen = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)
$manifestIdentityMismatch = 0
foreach ($row in @($manifestReadback.files)) {
    $relative = Normalize-RelativePath ([string]$row.relative_path)
    Assert-True ($manifestSeen.Add($relative)) "Duplicate new manifest path: $relative"
    $path = Resolve-ChildPath $destination $relative
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { $manifestIdentityMismatch++; continue }
    $item = Get-Item -LiteralPath $path -Force
    if ($item.Length -ne [int64]$row.size_bytes -or (Get-Sha256 $path) -cne ([string]$row.sha256).ToUpperInvariant() -or $item.LastWriteTimeUtc.Ticks.ToString() -cne [string]$row.mtime_utc_ticks) {
        $manifestIdentityMismatch++
    }
}
Assert-True ($manifestIdentityMismatch -eq 0) 'New manifest payload identity mismatch.'
Assert-True ($manifestSeen.Count -eq 142) 'New manifest unique path denominator is not 142.'

$jsonParseFailures = 0
foreach ($file in Get-ChildItem -LiteralPath $destination -Recurse -File -Filter '*.json' -Force) {
    try { $null = Get-Content -LiteralPath $file.FullName -Raw -Encoding UTF8 | ConvertFrom-Json } catch { $jsonParseFailures++ }
}
$csvParseFailures = 0
foreach ($file in Get-ChildItem -LiteralPath $destination -Recurse -File -Filter '*.csv' -Force) {
    try { $null = @(Import-Csv -LiteralPath $file.FullName -Encoding UTF8) } catch { $csvParseFailures++ }
}
$pngParseFailures = 0
$pngCount = 0
foreach ($file in Get-ChildItem -LiteralPath $destination -Recurse -File -Filter '*.png' -Force) {
    $pngCount++
    $stream = [System.IO.File]::OpenRead($file.FullName)
    try {
        $signature = [byte[]]::new(8)
        $read = $stream.Read($signature, 0, 8)
        $expected = [byte[]](137,80,78,71,13,10,26,10)
        if ($read -ne 8 -or -not [System.Linq.Enumerable]::SequenceEqual[byte]($signature, $expected)) { $pngParseFailures++ }
    } finally { $stream.Dispose() }
}
$adsCount = Get-NonDefaultAdsCount $destination
$pycCount = @(Get-ChildItem -LiteralPath $destination -Recurse -File -Force | Where-Object { $_.Extension -ieq '.pyc' }).Count
$cacheDirectoryNames = @('__pycache__', '.pytest_cache', '.mypy_cache', 'cache', 'texcache')
$cacheCount = @(Get-ChildItem -LiteralPath $destination -Recurse -Directory -Force | Where-Object { $cacheDirectoryNames -contains $_.Name }).Count
$reparseCount = @(Get-ChildItem -LiteralPath $destination -Recurse -Force | Where-Object { ($_.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0 }).Count
Assert-True ($jsonParseFailures -eq 0) 'JSON parse failure before seal.'
Assert-True ($csvParseFailures -eq 0) 'CSV parse failure before seal.'
Assert-True ($pngParseFailures -eq 0) 'PNG parse failure before seal.'
Assert-True ($pngCount -eq 116) "PNG denominator changed; expected 116, got $pngCount."
Assert-True ($adsCount -eq 0) 'Non-default ADS found before seal.'
Assert-True ($pycCount -eq 0) 'PYC found before seal.'
Assert-True ($cacheCount -eq 0) 'Cache directory found before seal.'
Assert-True ($reparseCount -eq 0) 'Reparse point found before seal.'

$sealAudit = [ordered]@{
    result = 'PASS_IF_WRITE_STOPPED_IS_CREATED_LAST'
    handoff_id = 'A-R110-P582-SA1-FRESH-ISOLATED-20260827'
    reseal_round = 'R7A_EVIDENCE_ONLY_CONTROL_RESEAL'
    source_material_count = 140
    source_to_destination_path_bytes_sha_ticks_mismatch = $copyMismatch
    copy_identity_rows = $copyRows.Count
    declared_final_payload_count = 142
    declared_final_control_count = 3
    declared_final_ordinary_count = 145
    payload_manifest_rows = @($manifestReadback.files).Count
    payload_manifest_identity_mismatch = $manifestIdentityMismatch
    payload_manifest_sha256 = Get-Sha256 $newManifestPath
    json_parse_failures_before_self = $jsonParseFailures
    csv_parse_failures = $csvParseFailures
    png_count = $pngCount
    png_parse_failures = $pngParseFailures
    ads_nondefault_count = $adsCount
    pyc_count = $pycCount
    cache_directory_count = $cacheCount
    reparse_point_count = $reparseCount
    controller_requires_self_json_parse_after_write = $true
    controller_requires_144_of_144_pre_marker_files_readonly = $true
    controller_requires_all_directories_readonly_before_marker = $true
    created_at_utc = [datetime]::UtcNow.ToString('o')
}
$sealAuditPath = Join-Path $destination 'SEAL_AUDIT.json'
Write-Utf8NoBom $sealAuditPath (($sealAudit | ConvertTo-Json -Depth 6) + "`n")
$null = Get-Content -LiteralPath $sealAuditPath -Raw -Encoding UTF8 | ConvertFrom-Json

$preMarkerFiles = @(Get-ChildItem -LiteralPath $destination -Recurse -File -Force)
Assert-True ($preMarkerFiles.Count -eq 144) "Expected 144 files before WRITE_STOPPED; got $($preMarkerFiles.Count)."
foreach ($file in $preMarkerFiles) { Set-ReadonlyAttribute $file.FullName }
$allDirectories = @((Get-Item -LiteralPath $destination -Force)) + @(Get-ChildItem -LiteralPath $destination -Recurse -Directory -Force)
foreach ($directory in $allDirectories) { Set-ReadonlyAttribute $directory.FullName }

$preMarkerReadonlyFiles = @(Get-ChildItem -LiteralPath $destination -Recurse -File -Force | Where-Object { $_.IsReadOnly }).Count
$preMarkerReadonlyDirectories = @($allDirectories | Where-Object { ((Get-Item -LiteralPath $_.FullName -Force).Attributes -band [System.IO.FileAttributes]::ReadOnly) -ne 0 }).Count
Assert-True ($preMarkerReadonlyFiles -eq 144) "Pre-marker file read-only gate failed: $preMarkerReadonlyFiles/144."
Assert-True ($preMarkerReadonlyDirectories -eq $allDirectories.Count) "Pre-marker directory read-only gate failed: $preMarkerReadonlyDirectories/$($allDirectories.Count)."

$maxOtherTicks = (Get-ChildItem -LiteralPath $destination -Recurse -File -Force | Measure-Object LastWriteTimeUtc -Maximum).Maximum.Ticks
while ([datetime]::UtcNow.Ticks -le $maxOtherTicks) { Start-Sleep -Milliseconds 10 }
Start-Sleep -Milliseconds 50
$manifestSha = Get-Sha256 $newManifestPath
$auditSha = Get-Sha256 $sealAuditPath
$writeStoppedPath = Join-Path $destination 'WRITE_STOPPED'
$writeStoppedContent = @(
    'SEALED_AT_UTC=' + [datetime]::UtcNow.ToString('o')
    'HANDOFF_ID=A-R110-P582-SA1-FRESH-ISOLATED-20260827'
    'RESEAL_ROUND=R7A_EVIDENCE_ONLY_CONTROL_RESEAL'
    'FIGURE_UID=FIG-P582-01'
    'RESULT=CONTENT_PASS_CONTROL_RESEAL_PASS'
    'PAYLOAD_FILE_COUNT=142'
    'CONTROL_FILE_COUNT=3'
    'ORDINARY_FILE_COUNT=145'
    'PAYLOAD_MANIFEST_SHA256=' + $manifestSha
    'SEAL_AUDIT_SHA256=' + $auditSha
    'ROOT_CONTENT_WRITES_AFTER_THIS_FILE=0'
) -join "`n"
Write-Utf8NoBom $writeStoppedPath ($writeStoppedContent + "`n")
Set-ReadonlyAttribute $writeStoppedPath

$finalFiles = @(Get-ChildItem -LiteralPath $destination -Recurse -File -Force)
$finalDirectories = @((Get-Item -LiteralPath $destination -Force)) + @(Get-ChildItem -LiteralPath $destination -Recurse -Directory -Force)
$writeStoppedItem = Get-Item -LiteralPath $writeStoppedPath -Force
$otherFiles = @($finalFiles | Where-Object { $_.FullName -cne $writeStoppedPath })
$finalMaxOtherTicks = ($otherFiles | Measure-Object LastWriteTimeUtc -Maximum).Maximum.Ticks
$filesAtOrAfter = @($otherFiles | Where-Object { $_.LastWriteTimeUtc.Ticks -ge $writeStoppedItem.LastWriteTimeUtc.Ticks }).Count
$finalReadonlyFiles = @($finalFiles | Where-Object { $_.IsReadOnly }).Count
$finalReadonlyDirectories = @($finalDirectories | Where-Object { ((Get-Item -LiteralPath $_.FullName -Force).Attributes -band [System.IO.FileAttributes]::ReadOnly) -ne 0 }).Count
Assert-True ($finalFiles.Count -eq 145) "Final ordinary denominator is not 145: $($finalFiles.Count)."
Assert-True ($finalReadonlyFiles -eq 145) "Final file read-only gate failed: $finalReadonlyFiles/145."
Assert-True ($finalReadonlyDirectories -eq $finalDirectories.Count) 'Final directory read-only gate failed.'
Assert-True ($filesAtOrAfter -eq 0) 'WRITE_STOPPED is not uniquely strictly latest.'

[ordered]@{
    result = 'PASS'
    controller_invocation_count = 1
    source_material_count = 140
    source_to_destination_identity_mismatch = $copyMismatch
    payload_count = 142
    control_count = 3
    ordinary_count = 145
    readonly_files = $finalReadonlyFiles
    directory_count = $finalDirectories.Count
    readonly_directories = $finalReadonlyDirectories
    payload_manifest_sha256 = $manifestSha
    seal_audit_sha256 = $auditSha
    write_stopped_ticks = $writeStoppedItem.LastWriteTimeUtc.Ticks.ToString()
    max_other_ticks = $finalMaxOtherTicks.ToString()
    write_stopped_margin_ticks = ($writeStoppedItem.LastWriteTimeUtc.Ticks - $finalMaxOtherTicks).ToString()
    files_at_or_after_marker_excluding_marker = $filesAtOrAfter
    root_content_writes_after_marker = 0
} | ConvertTo-Json -Depth 5
