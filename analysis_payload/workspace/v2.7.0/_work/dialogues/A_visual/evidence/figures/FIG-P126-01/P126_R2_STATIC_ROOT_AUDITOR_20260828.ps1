#requires -Version 7.0
[CmdletBinding()]
param()
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$root = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\STRICT_R2_SA2_STATIC_COORDINATE_QUADRATIC_PATCH_R115_20260828'
$source = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_A_visual\src\绘图源码\第01册_数学基础与统计学习基本理论\V1-C08\fig_v1_c08_coordinate.tex'
$output = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\P126_R2_STATIC_ROOT_EXTERNAL_AUDIT_20260828.json'
$payloadNames = @('CLEARANCE_PROJECTION.json','MATHEMATICAL_PROOF.json','SCOPE_AUDIT.json','SOURCE_EXACT_DIFF.md','SOURCE_IDENTITY.json','STATIC_RESULT.json')
$controlNames = @('PAYLOAD_MANIFEST.csv','SEAL_AUDIT.json','WRITE_STOPPED')
$utf8 = [Text.UTF8Encoding]::new($false)
function Sha([string]$Path) { (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToUpperInvariant() }
function IsReadOnly($Item) { (($Item.Attributes -band [IO.FileAttributes]::ReadOnly) -ne 0) }
function Assert-True([bool]$Value,[string]$Message) { if (-not $Value) { throw $Message } }
function CanonicalSnapshot {
    $items = @((Get-Item -LiteralPath $root -Force)) + @(Get-ChildItem -LiteralPath $root -Recurse -Force)
    $rows = foreach ($item in @($items | Sort-Object FullName)) {
        $relative = if ($item.FullName -eq $root) { '.' } else { [IO.Path]::GetRelativePath($root,$item.FullName).Replace('\','/') }
        $kind = if ($item.PSIsContainer) { 'D' } else { 'F' }
        $bytes = if ($item.PSIsContainer) { 0 } else { [int64]$item.Length }
        $hash = if ($item.PSIsContainer) { '-' } else { Sha $item.FullName }
        '{0}`t{1}`t{2}`t{3}`t{4}`t{5}`t{6}' -f $relative,$kind,$bytes,$hash,[int64]$item.CreationTimeUtc.Ticks,[int64]$item.LastWriteTimeUtc.Ticks,[int64]$item.Attributes
    }
    $bytes = $utf8.GetBytes((($rows -join "`n") + "`n"))
    $memory = [IO.MemoryStream]::new($bytes)
    try { ([Security.Cryptography.SHA256]::Create().ComputeHash($memory) | ForEach-Object { $_.ToString('X2') }) -join '' }
    finally { $memory.Dispose() }
}

Assert-True (Test-Path -LiteralPath $root -PathType Container) 'Root missing.'
$files = @(Get-ChildItem -LiteralPath $root -Recurse -File -Force)
$dirs = @((Get-Item -LiteralPath $root -Force)) + @(Get-ChildItem -LiteralPath $root -Recurse -Directory -Force)
Assert-True ($files.Count -eq 9) 'Ordinary count mismatch.'
Assert-True ($dirs.Count -eq 1) 'Directory count mismatch.'
$expectedSet = @(($payloadNames + $controlNames) | Sort-Object -CaseSensitive)
$actualSet = @($files | ForEach-Object { [IO.Path]::GetRelativePath($root,$_.FullName).Replace('\','/') } | Sort-Object -CaseSensitive)
$setDiff = @(Compare-Object -ReferenceObject $expectedSet -DifferenceObject $actualSet -CaseSensitive)
Assert-True ($setDiff.Count -eq 0) 'Ordinary set mismatch.'

$manifestPath = [IO.Path]::Combine($root,'PAYLOAD_MANIFEST.csv')
$manifestRows = @(Import-Csv -LiteralPath $manifestPath)
Assert-True ($manifestRows.Count -eq 6) 'Manifest row count mismatch.'
$manifestDup = @($manifestRows | Group-Object -Property { [string]$_.relative_path } | Where-Object { $_.Count -ne 1 })
Assert-True ($manifestDup.Count -eq 0) 'Manifest duplicate path.'
$manifestSet = @($manifestRows | ForEach-Object { [string]$_.relative_path } | Sort-Object -CaseSensitive)
$manifestSetDiff = @(Compare-Object -ReferenceObject @($payloadNames | Sort-Object -CaseSensitive) -DifferenceObject $manifestSet -CaseSensitive)
Assert-True ($manifestSetDiff.Count -eq 0) 'Manifest set mismatch.'
$identityErrors = @()
foreach ($row in $manifestRows) {
    $path = [IO.Path]::Combine($root,([string]$row.relative_path).Replace('/','\'))
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { $identityErrors += "missing:$($row.relative_path)"; continue }
    $item = Get-Item -LiteralPath $path -Force
    if ([int64]$row.bytes -ne [int64]$item.Length) { $identityErrors += "bytes:$($row.relative_path)" }
    if ([string]$row.sha256 -cne (Sha $path)) { $identityErrors += "sha:$($row.relative_path)" }
    if ([int64]$row.creation_time_utc_ticks -ne [int64]$item.CreationTimeUtc.Ticks) { $identityErrors += "creation:$($row.relative_path)" }
    if ([int64]$row.last_write_time_utc_ticks -ne [int64]$item.LastWriteTimeUtc.Ticks) { $identityErrors += "lastwrite:$($row.relative_path)" }
}
Assert-True ($identityErrors.Count -eq 0) 'Manifest identity mismatch.'

$writableFiles = @($files | Where-Object { -not (IsReadOnly $_) })
$writableDirs = @($dirs | Where-Object { -not (IsReadOnly $_) })
Assert-True ($writableFiles.Count -eq 0) 'Writable file.'
Assert-True ($writableDirs.Count -eq 0) 'Writable directory.'
$markerPath = [IO.Path]::Combine($root,'WRITE_STOPPED')
$marker = Get-Item -LiteralPath $markerPath -Force
$markerLines = @([IO.File]::ReadAllLines($markerPath,$utf8) | Where-Object { $_.Length -gt 0 })
$badMarkerLines = @($markerLines | Where-Object { $_ -notmatch '^[^=\s]+=[^=\r\n\t]+$' })
$duplicateMarkerKeys = @($markerLines | ForEach-Object { ($_ -split '=',2)[0] } | Group-Object -Property { [string]$_ } | Where-Object { $_.Count -ne 1 })
Assert-True ($markerLines.Count -eq 15) 'Marker line count mismatch.'
Assert-True ($badMarkerLines.Count -eq 0) 'Marker syntax mismatch.'
Assert-True ($duplicateMarkerKeys.Count -eq 0) 'Marker duplicate key.'
$otherItems = @((Get-Item -LiteralPath $root -Force)) + @(Get-ChildItem -LiteralPath $root -Recurse -Force | Where-Object { $_.FullName -ne $marker.FullName })
$atOrAfter = @($otherItems | Where-Object { $_.LastWriteTimeUtc.Ticks -ge $marker.LastWriteTimeUtc.Ticks })
$otherMax = (@($otherItems | ForEach-Object { $_.LastWriteTimeUtc.Ticks }) | Measure-Object -Maximum).Maximum
$margin = [int64]$marker.LastWriteTimeUtc.Ticks - [int64]$otherMax
Assert-True ($atOrAfter.Count -eq 0) 'Item at or after marker.'
Assert-True ($margin -gt 0) 'Marker not strictly latest.'

$jsonFiles = @($files | Where-Object { $_.Extension -eq '.json' })
$jsonErrors = @()
foreach ($json in $jsonFiles) { try { [void](Get-Content -LiteralPath $json.FullName -Raw | ConvertFrom-Json) } catch { $jsonErrors += $json.Name } }
Assert-True ($jsonErrors.Count -eq 0) 'JSON parse failure.'
$ads = @()
foreach ($file in $files) { $ads += @(Get-Item -LiteralPath $file.FullName -Stream * -ErrorAction SilentlyContinue | Where-Object { $_.Stream -ne ':$DATA' }) }
$cacheArtifacts = @($files | Where-Object { $_.Name -match '(?i)(\.pyc$|\.pyo$|^__pycache__$|\.cache$)' })
$reparseItems = @((@($files) + @($dirs)) | Where-Object { (($_.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) })
Assert-True ($ads.Count -eq 0) 'ADS found.'
Assert-True ($cacheArtifacts.Count -eq 0) 'Cache artifact found.'
Assert-True ($reparseItems.Count -eq 0) 'Reparse point found.'

$snapshot1 = CanonicalSnapshot
$snapshot2 = CanonicalSnapshot
Assert-True ($snapshot1 -ceq $snapshot2) 'Postmarker snapshot changed.'
$sourceItem = Get-Item -LiteralPath $source -Force
Assert-True ([int64]$sourceItem.Length -eq 4224) 'Source byte identity changed.'
Assert-True ((Sha $source) -ceq '366C905854F0F3952225600D5BD66AAB706B637A453FD23DDF9611E4C002AC20') 'Source SHA changed.'

$result = [ordered]@{
    status = 'ROOT_EXTERNAL_AUDIT_PASS_STATIC_ONLY_NOT_RENDERED_NOT_PASS'
    payload_count = 6
    control_count = 3
    ordinary_count = $files.Count
    directory_count = $dirs.Count
    manifest_rows = $manifestRows.Count
    manifest_set_mismatch = $manifestSetDiff.Count
    manifest_identity_errors = $identityErrors.Count
    readonly_files = $files.Count - $writableFiles.Count
    readonly_directories = $dirs.Count - $writableDirs.Count
    marker_physical_nonempty_lines = $markerLines.Count
    marker_bad_lines = $badMarkerLines.Count
    marker_duplicate_keys = $duplicateMarkerKeys.Count
    marker_margin_ticks = $margin
    at_or_after_excluding_marker = $atOrAfter.Count
    postmarker_snapshot_mismatch = [int]($snapshot1 -cne $snapshot2)
    ads_count = $ads.Count
    cache_pyc_count = $cacheArtifacts.Count
    reparse_count = $reparseItems.Count
    json_parse_errors = $jsonErrors.Count
    payload_manifest_sha256 = Sha $manifestPath
    seal_audit_sha256 = Sha ([IO.Path]::Combine($root,'SEAL_AUDIT.json'))
    write_stopped_sha256 = Sha $markerPath
    root_snapshot_sha256 = $snapshot2
    source_bytes = [int64]$sourceItem.Length
    source_sha256 = Sha $source
    tex_invocations = 0
    build_invocations = 0
    commit_count = 0
}
[IO.File]::WriteAllText($output,(($result | ConvertTo-Json -Depth 8) + "`n"),$utf8)
$result | ConvertTo-Json -Compress
