param(
    [Parameter(Mandatory = $true)] [string] $SourceRoot,
    [Parameter(Mandatory = $true)] [string] $SealedRoot,
    [Parameter(Mandatory = $true)] [string] $OutputPath
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$Utf8NoBom = [System.Text.UTF8Encoding]::new($false)
$ExpectedSourceRoot = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P582-01\STRICT_R7_SA1_FRESH_ISOLATED_R110_20260827'
$ExpectedSealedRoot = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P582-01\STRICT_R7A_SA1_R110_EVIDENCE_ONLY_CONTROL_RESEAL_20260827'
$Controls = @('PAYLOAD_MANIFEST.json', 'SEAL_AUDIT.json', 'WRITE_STOPPED')
$Errors = [System.Collections.Generic.List[string]]::new()

function Add-CheckError {
    param([bool] $Condition, [string] $Message)
    if (-not $Condition) { $script:Errors.Add($Message) }
}

function Get-Sha256 {
    param([string] $Path)
    return (Get-FileHash -Algorithm SHA256 -LiteralPath $Path).Hash.ToUpperInvariant()
}

function Normalize-RelativePath {
    param([string] $RelativePath)
    return $RelativePath.Replace('\', '/').TrimStart('/')
}

function Get-RelativePathNormalized {
    param([string] $Root, [string] $Path)
    return (Normalize-RelativePath ([System.IO.Path]::GetRelativePath($Root, $Path)))
}

function Resolve-ChildPath {
    param([string] $Root, [string] $RelativePath)
    $normalized = Normalize-RelativePath $RelativePath
    if ([System.IO.Path]::IsPathRooted($normalized) -or $normalized.Contains(':')) { throw "Unsafe relative path: $RelativePath" }
    $resolved = [System.IO.Path]::GetFullPath((Join-Path $Root ($normalized.Replace('/', [System.IO.Path]::DirectorySeparatorChar))))
    $prefix = $Root.TrimEnd('\') + '\'
    if (-not $resolved.StartsWith($prefix, [System.StringComparison]::OrdinalIgnoreCase)) { throw "Path escapes root: $RelativePath" }
    return $resolved
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
$root = [System.IO.Path]::GetFullPath($SealedRoot).TrimEnd('\')
$output = [System.IO.Path]::GetFullPath($OutputPath)
Add-CheckError ($source -ceq $ExpectedSourceRoot) 'Resolved source root mismatch.'
Add-CheckError ($root -ceq $ExpectedSealedRoot) 'Resolved sealed root mismatch.'
Add-CheckError (-not $output.StartsWith($root + '\', [System.StringComparison]::OrdinalIgnoreCase)) 'External audit output must be outside sealed root.'
Add-CheckError (Test-Path -LiteralPath $source -PathType Container) 'Source root missing.'
Add-CheckError (Test-Path -LiteralPath $root -PathType Container) 'Sealed root missing.'

$manifestPath = Join-Path $root 'PAYLOAD_MANIFEST.json'
$auditPath = Join-Path $root 'SEAL_AUDIT.json'
$writeStoppedPath = Join-Path $root 'WRITE_STOPPED'
Add-CheckError (Test-Path -LiteralPath $manifestPath -PathType Leaf) 'PAYLOAD_MANIFEST.json missing.'
Add-CheckError (Test-Path -LiteralPath $auditPath -PathType Leaf) 'SEAL_AUDIT.json missing.'
Add-CheckError (Test-Path -LiteralPath $writeStoppedPath -PathType Leaf) 'WRITE_STOPPED missing.'

$manifest = Get-Content -LiteralPath $manifestPath -Raw -Encoding UTF8 | ConvertFrom-Json
$sealAudit = Get-Content -LiteralPath $auditPath -Raw -Encoding UTF8 | ConvertFrom-Json
$provenancePath = Join-Path $root 'COPY_PROVENANCE.json'
$provenance = Get-Content -LiteralPath $provenancePath -Raw -Encoding UTF8 | ConvertFrom-Json
$copyIdentityPath = Join-Path $root 'COPY_IDENTITY.csv'
$copyIdentity = @(Import-Csv -LiteralPath $copyIdentityPath -Encoding UTF8)

Add-CheckError ([int]$manifest.file_count -eq 142) 'Manifest declared payload count is not 142.'
Add-CheckError (@($manifest.files).Count -eq 142) 'Manifest row count is not 142.'
Add-CheckError ($copyIdentity.Count -eq 140) 'COPY_IDENTITY row count is not 140.'
Add-CheckError ([string]$provenance.source_root -ceq $source) 'Provenance source root mismatch.'
Add-CheckError ([string]$provenance.destination_root -ceq $root) 'Provenance destination root mismatch.'
Add-CheckError (-not ([string]$provenance.source_root).Contains('$')) 'Provenance source root contains unresolved placeholder.'
Add-CheckError (-not ([string]$provenance.destination_root).Contains('$')) 'Provenance destination root contains unresolved placeholder.'

$allFiles = @(Get-ChildItem -LiteralPath $root -Recurse -File -Force)
$allDirectories = @((Get-Item -LiteralPath $root -Force)) + @(Get-ChildItem -LiteralPath $root -Recurse -Directory -Force)
$actualPayload = @($allFiles | Where-Object { $Controls -notcontains (Get-RelativePathNormalized $root $_.FullName) })
Add-CheckError ($allFiles.Count -eq 145) "Ordinary count is not 145: $($allFiles.Count)."
Add-CheckError ($actualPayload.Count -eq 142) "Actual payload count is not 142: $($actualPayload.Count)."

$manifestMap = [System.Collections.Generic.Dictionary[string,object]]::new([System.StringComparer]::OrdinalIgnoreCase)
$duplicatePaths = 0
$manifestIdentityMismatch = 0
foreach ($row in @($manifest.files)) {
    $relative = Normalize-RelativePath ([string]$row.relative_path)
    if ($manifestMap.ContainsKey($relative)) { $duplicatePaths++; continue }
    $manifestMap.Add($relative, $row)
    $path = Resolve-ChildPath $root $relative
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { $manifestIdentityMismatch++; continue }
    $item = Get-Item -LiteralPath $path -Force
    if ($item.Length -ne [int64]$row.size_bytes -or (Get-Sha256 $path) -cne ([string]$row.sha256).ToUpperInvariant() -or $item.LastWriteTimeUtc.Ticks.ToString() -cne [string]$row.mtime_utc_ticks) {
        $manifestIdentityMismatch++
    }
}
$extraPayload = 0
foreach ($file in $actualPayload) {
    $relative = Get-RelativePathNormalized $root $file.FullName
    if (-not $manifestMap.ContainsKey($relative)) { $extraPayload++ }
}
Add-CheckError ($duplicatePaths -eq 0) 'Duplicate manifest path found.'
Add-CheckError ($manifestIdentityMismatch -eq 0) 'Manifest-to-filesystem identity mismatch found.'
Add-CheckError ($extraPayload -eq 0) 'Extra payload file found.'
Add-CheckError ($manifestMap.Count -eq 142) 'Unique manifest path count is not 142.'

$copyDuplicate = 0
$copyMismatch = 0
$copySeen = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)
foreach ($row in $copyIdentity) {
    $sourceRelative = Normalize-RelativePath ([string]$row.source_relative_path)
    $destinationRelative = Normalize-RelativePath ([string]$row.destination_relative_path)
    if (-not $copySeen.Add($sourceRelative)) { $copyDuplicate++ }
    if ($sourceRelative -cne $destinationRelative) { $copyMismatch++; continue }
    $sourcePath = Resolve-ChildPath $source $sourceRelative
    $destinationPath = Resolve-ChildPath $root $destinationRelative
    if (-not (Test-Path -LiteralPath $sourcePath -PathType Leaf) -or -not (Test-Path -LiteralPath $destinationPath -PathType Leaf)) { $copyMismatch++; continue }
    $sourceItem = Get-Item -LiteralPath $sourcePath -Force
    $destinationItem = Get-Item -LiteralPath $destinationPath -Force
    $sourceSha = Get-Sha256 $sourcePath
    $destinationSha = Get-Sha256 $destinationPath
    if ($sourceItem.Length -ne [int64]$row.size_bytes -or $destinationItem.Length -ne [int64]$row.size_bytes -or $sourceSha -cne ([string]$row.sha256).ToUpperInvariant() -or $destinationSha -cne ([string]$row.sha256).ToUpperInvariant() -or $sourceItem.LastWriteTimeUtc.Ticks.ToString() -cne [string]$row.source_mtime_utc_ticks -or $destinationItem.LastWriteTimeUtc.Ticks.ToString() -cne [string]$row.destination_mtime_utc_ticks -or [string]$row.source_mtime_utc_ticks -cne [string]$row.destination_mtime_utc_ticks) {
        $copyMismatch++
    }
}
Add-CheckError ($copyDuplicate -eq 0) 'Duplicate COPY_IDENTITY source path found.'
Add-CheckError ($copySeen.Count -eq 140) 'Unique COPY_IDENTITY denominator is not 140.'
Add-CheckError ($copyMismatch -eq 0) 'Source-to-destination copy identity mismatch found.'

$jsonParseFailures = 0
foreach ($file in Get-ChildItem -LiteralPath $root -Recurse -File -Filter '*.json' -Force) {
    try { $null = Get-Content -LiteralPath $file.FullName -Raw -Encoding UTF8 | ConvertFrom-Json } catch { $jsonParseFailures++ }
}
$csvParseFailures = 0
foreach ($file in Get-ChildItem -LiteralPath $root -Recurse -File -Filter '*.csv' -Force) {
    try { $null = @(Import-Csv -LiteralPath $file.FullName -Encoding UTF8) } catch { $csvParseFailures++ }
}
$pngCount = 0
$pngParseFailures = 0
foreach ($file in Get-ChildItem -LiteralPath $root -Recurse -File -Filter '*.png' -Force) {
    $pngCount++
    $stream = [System.IO.File]::OpenRead($file.FullName)
    try {
        $signature = [byte[]]::new(8)
        $read = $stream.Read($signature, 0, 8)
        $expected = [byte[]](137,80,78,71,13,10,26,10)
        if ($read -ne 8 -or -not [System.Linq.Enumerable]::SequenceEqual[byte]($signature, $expected)) { $pngParseFailures++ }
    } finally { $stream.Dispose() }
}

$readonlyFiles = @($allFiles | Where-Object { $_.IsReadOnly }).Count
$readonlyDirectories = @($allDirectories | Where-Object { ((Get-Item -LiteralPath $_.FullName -Force).Attributes -band [System.IO.FileAttributes]::ReadOnly) -ne 0 }).Count
$adsCount = Get-NonDefaultAdsCount $root
$pycCount = @($allFiles | Where-Object { $_.Extension -ieq '.pyc' }).Count
$cacheDirectoryNames = @('__pycache__', '.pytest_cache', '.mypy_cache', 'cache', 'texcache')
$cacheCount = @(Get-ChildItem -LiteralPath $root -Recurse -Directory -Force | Where-Object { $cacheDirectoryNames -contains $_.Name }).Count
$reparseCount = @(Get-ChildItem -LiteralPath $root -Recurse -Force | Where-Object { ($_.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0 }).Count

$writeStoppedFiles = @($allFiles | Where-Object { (Get-RelativePathNormalized $root $_.FullName) -ceq 'WRITE_STOPPED' })
$filesAtOrAfter = -1
$writeStoppedMargin = '-1'
if ($writeStoppedFiles.Count -eq 1) {
    $writeStoppedItem = $writeStoppedFiles[0]
    $otherFiles = @($allFiles | Where-Object { $_.FullName -cne $writeStoppedItem.FullName })
    $maxOtherTicks = ($otherFiles | Measure-Object LastWriteTimeUtc -Maximum).Maximum.Ticks
    $filesAtOrAfter = @($otherFiles | Where-Object { $_.LastWriteTimeUtc.Ticks -ge $writeStoppedItem.LastWriteTimeUtc.Ticks }).Count
    $writeStoppedMargin = ($writeStoppedItem.LastWriteTimeUtc.Ticks - $maxOtherTicks).ToString()
}

Add-CheckError ($jsonParseFailures -eq 0) 'JSON parse failure found.'
Add-CheckError ($csvParseFailures -eq 0) 'CSV parse failure found.'
Add-CheckError ($pngCount -eq 116) "PNG denominator is not 116: $pngCount."
Add-CheckError ($pngParseFailures -eq 0) 'PNG parse failure found.'
Add-CheckError ($readonlyFiles -eq 145) "File read-only gate failed: $readonlyFiles/145."
Add-CheckError ($readonlyDirectories -eq $allDirectories.Count) "Directory read-only gate failed: $readonlyDirectories/$($allDirectories.Count)."
Add-CheckError ($adsCount -eq 0) 'Non-default ADS found.'
Add-CheckError ($pycCount -eq 0) 'PYC found.'
Add-CheckError ($cacheCount -eq 0) 'Cache directory found.'
Add-CheckError ($reparseCount -eq 0) 'Reparse point found.'
Add-CheckError ($writeStoppedFiles.Count -eq 1) 'WRITE_STOPPED is not unique.'
Add-CheckError ($filesAtOrAfter -eq 0) 'WRITE_STOPPED is not uniquely strictly latest.'
Add-CheckError ([int]$sealAudit.declared_final_payload_count -eq 142) 'SEAL_AUDIT payload count declaration mismatch.'
Add-CheckError ([int]$sealAudit.declared_final_control_count -eq 3) 'SEAL_AUDIT control count declaration mismatch.'
Add-CheckError ([int]$sealAudit.declared_final_ordinary_count -eq 145) 'SEAL_AUDIT ordinary count declaration mismatch.'

$result = [ordered]@{
    verdict = if ($Errors.Count -eq 0) { 'ROOT_ACCEPT_R7A_SA1_CONTENT_PASS_READY_FOR_FRESH_ISOLATED_SA3' } else { 'ROOT_REJECT_R7A' }
    pass = ($Errors.Count -eq 0)
    source_material_count = $copyIdentity.Count
    source_to_destination_identity_mismatch = $copyMismatch
    payload_manifest_rows = @($manifest.files).Count
    payload_unique_paths = $manifestMap.Count
    payload_duplicate_paths = $duplicatePaths
    payload_missing_or_identity_mismatch = $manifestIdentityMismatch
    payload_extra = $extraPayload
    payload_count = $actualPayload.Count
    control_count = ($allFiles.Count - $actualPayload.Count)
    ordinary_count = $allFiles.Count
    readonly_files = $readonlyFiles
    directory_count = $allDirectories.Count
    readonly_directories = $readonlyDirectories
    json_parse_failures = $jsonParseFailures
    csv_parse_failures = $csvParseFailures
    png_count = $pngCount
    png_parse_failures = $pngParseFailures
    ads_nondefault_count = $adsCount
    pyc_count = $pycCount
    cache_directory_count = $cacheCount
    reparse_point_count = $reparseCount
    write_stopped_count = $writeStoppedFiles.Count
    write_stopped_margin_ticks = $writeStoppedMargin
    files_at_or_after_marker_excluding_marker = $filesAtOrAfter
    postmarker_root_content_writes = $filesAtOrAfter
    payload_manifest_sha256 = Get-Sha256 $manifestPath
    seal_audit_sha256 = Get-Sha256 $auditPath
    errors = @($Errors)
    audited_at_utc = [datetime]::UtcNow.ToString('o')
}
$json = ($result | ConvertTo-Json -Depth 8) + "`n"
$outputDirectory = [System.IO.Path]::GetDirectoryName($output)
[System.IO.Directory]::CreateDirectory($outputDirectory) | Out-Null
[System.IO.File]::WriteAllText($output, $json, $Utf8NoBom)
$json
if ($Errors.Count -ne 0) { exit 1 }
