param(
    [Parameter(Mandatory = $true)][string]$SourceRoot,
    [Parameter(Mandatory = $true)][string]$TargetRoot,
    [Parameter(Mandatory = $true)][string]$ExecutionGrant,
    [switch]$StaticCheckOnly
)

$ErrorActionPreference = 'Stop'
$expectedGrant = 'P608_R14A_CONTROL_RESEAL_EXPLICITLY_GRANTED'
$expectedSource = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P608-01\STRICT_R14_SA3_FRESH_ISOLATED_R105_20260826'
$expectedTarget = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P608-01\STRICT_R14A_SA3_EVIDENCE_ONLY_CONTROL_RESEAL_R105_20260826'
$excludedNames = @(
    'WRITE_STOPPED',
    'seal_evidence.ps1',
    'SEAL_AUDIT.json',
    'POSTSEAL_WRITE_CHECKS.json',
    'SEALED_MANIFEST.csv'
)

function Get-NormalizedRoot([string]$Path) {
    return [IO.Path]::GetFullPath($Path).TrimEnd('\')
}

function Get-RelativeForwardPath([string]$Root, [string]$FullName) {
    return $FullName.Substring($Root.Length).TrimStart('\') -replace '\\', '/'
}

function Get-Sha256([string]$Path) {
    return (Get-FileHash -Algorithm SHA256 -LiteralPath $Path).Hash
}

$source = Get-NormalizedRoot $SourceRoot
$target = Get-NormalizedRoot $TargetRoot
if ($ExecutionGrant -cne $expectedGrant) { throw 'ExecutionGrant mismatch' }
if ($source -cne $expectedSource) { throw "SourceRoot mismatch: $source" }
if ($target -cne $expectedTarget) { throw "TargetRoot mismatch: $target" }
if (-not (Test-Path -LiteralPath $source -PathType Container)) { throw 'Source root does not exist' }
if (Test-Path -LiteralPath $target) { throw 'Target root must not exist' }

$excludedFull = @($excludedNames | ForEach-Object { Join-Path $source $_ })
if (@($excludedFull | Where-Object { -not (Test-Path -LiteralPath $_ -PathType Leaf) }).Count -ne 0) {
    throw 'One or more authorized source exclusions are absent'
}
$sourceFiles = @(Get-ChildItem -LiteralPath $source -Recurse -File -Force)
if ($sourceFiles.Count -ne 193) { throw "Unexpected R14 ordinary count: $($sourceFiles.Count)" }
$material = @($sourceFiles | Where-Object { $_.FullName -notin $excludedFull } | Sort-Object FullName)
if ($material.Count -ne 188) { throw "Unexpected material payload count: $($material.Count)" }
if (@($sourceFiles | Where-Object { -not $_.IsReadOnly }).Count -ne 0) { throw 'R14 contains a non-read-only file' }

$tex = @(Get-Process -ErrorAction SilentlyContinue | Where-Object { $_.ProcessName -match '^(latexmk|lualatex|luatex|luahbtex)$' })
if ($tex.Count -ne 0) { throw "TeX process count must be zero, got $($tex.Count)" }

$sourceRecords = foreach ($file in $material) {
    [ordered]@{
        relative_path = Get-RelativeForwardPath $source $file.FullName
        bytes = $file.Length
        sha256 = Get-Sha256 $file.FullName
        mtime_utc_ticks = $file.LastWriteTimeUtc.Ticks.ToString()
        mtime_utc_7digit = $file.LastWriteTimeUtc.ToString('yyyy-MM-ddTHH:mm:ss.fffffffZ')
    }
}
if (@($sourceRecords.relative_path | Group-Object | Where-Object Count -ne 1).Count -ne 0) {
    throw 'Duplicate source relative path'
}

if ($StaticCheckOnly) {
    Write-Output "STATIC_PREFLIGHT_PASS source=193 excluded=5 material=188 target_absent=true tex=0"
    exit 0
}

[IO.Directory]::CreateDirectory($target) | Out-Null
foreach ($record in $sourceRecords) {
    $srcFile = Join-Path $source ($record.relative_path -replace '/', '\')
    $dstFile = Join-Path $target ($record.relative_path -replace '/', '\')
    $dstDir = Split-Path -Parent $dstFile
    [IO.Directory]::CreateDirectory($dstDir) | Out-Null
    [IO.File]::Copy($srcFile, $dstFile, $false)
    $dstInfo = Get-Item -LiteralPath $dstFile -Force
    $dstInfo.IsReadOnly = $false
    [IO.File]::SetLastWriteTimeUtc($dstFile, [DateTime]::new([int64]$record.mtime_utc_ticks, [DateTimeKind]::Utc))
}

$copyMismatch = 0
foreach ($record in $sourceRecords) {
    $srcFile = Join-Path $source ($record.relative_path -replace '/', '\')
    $dstFile = Join-Path $target ($record.relative_path -replace '/', '\')
    $srcInfo = Get-Item -LiteralPath $srcFile -Force
    $dstInfo = Get-Item -LiteralPath $dstFile -Force
    if ($srcInfo.Length -ne $dstInfo.Length -or
        (Get-Sha256 $srcFile) -cne (Get-Sha256 $dstFile) -or
        $srcInfo.LastWriteTimeUtc.Ticks -ne $dstInfo.LastWriteTimeUtc.Ticks) {
        $copyMismatch++
    }
}
if ($copyMismatch -ne 0) { throw "Copy identity mismatch count: $copyMismatch" }

$manifestPath = Join-Path $target 'SEALED_MANIFEST.csv'
$auditPath = Join-Path $target 'SEAL_AUDIT.json'
$writeStoppedPath = Join-Path $target 'WRITE_STOPPED'
$sourceRecords | ConvertTo-Csv -NoTypeInformation | Set-Content -LiteralPath $manifestPath -Encoding utf8NoBOM

$manifestRows = @(Import-Csv -LiteralPath $manifestPath)
$targetMaterial = @(Get-ChildItem -LiteralPath $target -Recurse -File -Force | Where-Object { $_.FullName -ne $manifestPath })
$targetMap = @{}
foreach ($file in $targetMaterial) {
    $relative = Get-RelativeForwardPath $target $file.FullName
    if ($targetMap.ContainsKey($relative)) { throw "Duplicate target path: $relative" }
    $targetMap[$relative] = $file
}
$manifestSeen = @{}
$manifestMismatch = 0
foreach ($row in $manifestRows) {
    if ($manifestSeen.ContainsKey($row.relative_path)) { throw "Duplicate manifest path: $($row.relative_path)" }
    $manifestSeen[$row.relative_path] = $true
    if (-not $targetMap.ContainsKey($row.relative_path)) { $manifestMismatch++; continue }
    $dstFile = $targetMap[$row.relative_path]
    $srcFile = Join-Path $source ($row.relative_path -replace '/', '\')
    $srcInfo = Get-Item -LiteralPath $srcFile -Force
    if ([string]$dstFile.Length -ne [string]$row.bytes -or
        (Get-Sha256 $dstFile.FullName) -cne $row.sha256 -or
        $dstFile.LastWriteTimeUtc.Ticks.ToString() -cne $row.mtime_utc_ticks -or
        $srcInfo.Length -ne $dstFile.Length -or
        (Get-Sha256 $srcFile) -cne (Get-Sha256 $dstFile.FullName) -or
        $srcInfo.LastWriteTimeUtc.Ticks -ne $dstFile.LastWriteTimeUtc.Ticks) {
        $manifestMismatch++
    }
}
$targetExtra = @($targetMap.Keys | Where-Object { -not $manifestSeen.ContainsKey($_) }).Count
if ($manifestRows.Count -ne 188 -or $manifestMismatch -ne 0 -or $targetExtra -ne 0) {
    throw "Manifest readback failed: rows=$($manifestRows.Count) mismatch=$manifestMismatch extra=$targetExtra"
}

$audit = [ordered]@{
    status = 'PASS'
    handoff_id = 'A-R105-P608-SA3-R14A-EVIDENCE-ONLY-CONTROL-RESEAL-20260826'
    source_root = $source
    target_root = $target
    source_ordinary_count = 193
    excluded_old_control_count = 5
    excluded_old_controls = $excludedNames
    material_payload_count = 188
    manifest_control_count = 1
    seal_audit_control_count = 1
    write_stopped_control_count = 1
    control_count = 3
    declared_final_ordinary_count = 191
    copy_path_bytes_sha_mtime_mismatch_count = $copyMismatch
    manifest_rows = $manifestRows.Count
    manifest_readback_mismatch_count = $manifestMismatch
    manifest_extra_path_count = $targetExtra
    tex_process_count = 0
    central_a_local_pass_claimed = $false
    route = 'R14A_CONTROL_RESEAL_READY_FOR_ROOT_AUDIT'
    created_at_utc = [DateTime]::UtcNow.ToString('o')
}
$audit | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $auditPath -Encoding utf8NoBOM

$preStopFiles = @(Get-ChildItem -LiteralPath $target -Recurse -File -Force)
if ($preStopFiles.Count -ne 190) { throw "Pre-WSTOP ordinary count mismatch: $($preStopFiles.Count)" }
$ads = 0
foreach ($file in $preStopFiles) {
    $ads += @((Get-Item -LiteralPath $file.FullName -Stream * -ErrorAction SilentlyContinue) | Where-Object Stream -ne ':$DATA').Count
}
$bytecode = @($preStopFiles | Where-Object { $_.Extension -in @('.pyc', '.pyo') }).Count
$cacheDirs = @(Get-ChildItem -LiteralPath $target -Recurse -Directory -Force | Where-Object { $_.Name -in @('__pycache__', '.pytest_cache') }).Count
if ($ads -ne 0 -or $bytecode -ne 0 -or $cacheDirs -ne 0) {
    throw "Pre-WSTOP hygiene failed: ads=$ads bytecode=$bytecode cacheDirs=$cacheDirs"
}
foreach ($file in $preStopFiles) { $file.IsReadOnly = $true }
if (@(Get-ChildItem -LiteralPath $target -Recurse -File -Force | Where-Object { -not $_.IsReadOnly }).Count -ne 0) {
    throw 'Pre-WSTOP read-only closure failed'
}

Start-Sleep -Milliseconds 100
$stop = @(
    'HANDOFF_ID=A-R105-P608-SA3-R14A-EVIDENCE-ONLY-CONTROL-RESEAL-20260826',
    'SOURCE_ROLE=A-R105-P608-SA3-FRESH-ISOLATED-20260826',
    'RESULT=CONTENT_PASS_DIRECTION',
    'ROUTE=R14A_CONTROL_RESEAL_READY_FOR_ROOT_AUDIT',
    'MATERIAL_PAYLOAD_COUNT=188',
    'CONTROL_COUNT=3',
    'FINAL_ORDINARY_COUNT=191',
    'MANIFEST_ROWS=188',
    'COPY_PATH_BYTES_SHA_MTIME_MISMATCH=0',
    'CENTRAL_A_LOCAL_PASS_CLAIMED=false',
    ('WRITTEN_AT_UTC=' + [DateTime]::UtcNow.ToString('o')),
    'WRITE_STOPPED=true'
)
$stop | Set-Content -LiteralPath $writeStoppedPath -Encoding utf8NoBOM
(Get-Item -LiteralPath $writeStoppedPath -Force).IsReadOnly = $true
Write-Output 'R14A_WRITE_STOPPED_WRITTEN_NO_FURTHER_ROOT_WRITES'
