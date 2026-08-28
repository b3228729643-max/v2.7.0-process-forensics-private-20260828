[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$SourceRoot,
    [Parameter(Mandatory = $true)][string]$TargetRoot,
    [Parameter(Mandatory = $true)][string]$ExecutionGrant
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$expectedGrant = 'P580_R2A_EVIDENCE_ONLY_CONTROL_RESEAL_EXPLICITLY_GRANTED'
if ($ExecutionGrant -cne $expectedGrant) {
    throw 'ExecutionGrant is not the unique R2A grant.'
}

$sourceResolved = [IO.Path]::GetFullPath($SourceRoot)
$targetResolved = [IO.Path]::GetFullPath($TargetRoot)
$expectedSource = [IO.Path]::GetFullPath('D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P580-01\STRICT_R2_SA1_FRESH_ISOLATED_R108_20260826')
$expectedTarget = [IO.Path]::GetFullPath('D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P580-01\STRICT_R2A_SA1_FRESH_ISOLATED_R108_EVIDENCE_ONLY_CONTROL_RESEAL_20260826')
if ($sourceResolved -cne $expectedSource) { throw 'Resolved source root differs from the authorized R2 root.' }
if ($targetResolved -cne $expectedTarget) { throw 'Resolved target root differs from the authorized R2A root.' }
if (Test-Path -LiteralPath $targetResolved) { throw 'The authorized R2A target root already exists.' }

$sourceCsvPath = Join-Path $sourceResolved 'PAYLOAD_MANIFEST.csv'
$sourceShaPath = Join-Path $sourceResolved 'PAYLOAD_MANIFEST.sha256'
if (-not (Test-Path -LiteralPath $sourceCsvPath -PathType Leaf)) { throw 'R2 CSV manifest is missing.' }
if (-not (Test-Path -LiteralPath $sourceShaPath -PathType Leaf)) { throw 'R2 SHA manifest is missing.' }

$csvRows = @(Import-Csv -LiteralPath $sourceCsvPath)
if ($csvRows.Count -ne 45) { throw "R2 CSV manifest count is $($csvRows.Count), expected 45." }
$csvDuplicate = @($csvRows | Group-Object -CaseSensitive RELATIVE_PATH | Where-Object { $_.Count -ne 1 })
if ($csvDuplicate.Count -ne 0) { throw 'R2 CSV manifest contains duplicate relative paths.' }

$shaRows = @{}
foreach ($line in Get-Content -LiteralPath $sourceShaPath -Encoding UTF8) {
    if ($line -notmatch '^([0-9A-Fa-f]{64})  (.+)$') { throw "Malformed R2 SHA manifest line: $line" }
    $rel = $Matches[2].Replace('\', '/')
    if ($shaRows.ContainsKey($rel)) { throw "Duplicate R2 SHA manifest path: $rel" }
    $shaRows[$rel] = $Matches[1].ToUpperInvariant()
}
if ($shaRows.Count -ne 45) { throw "R2 SHA manifest count is $($shaRows.Count), expected 45." }

$material = [Collections.Generic.List[object]]::new()
foreach ($row in $csvRows) {
    $rel = ([string]$row.RELATIVE_PATH).Replace('\', '/')
    if ([string]::IsNullOrWhiteSpace($rel) -or [IO.Path]::IsPathRooted($rel) -or $rel.Split('/') -contains '..') {
        throw "Unsafe R2 payload relative path: $rel"
    }
    if (-not $shaRows.ContainsKey($rel)) { throw "R2 SHA manifest is missing $rel" }
    if ($shaRows[$rel] -cne ([string]$row.SHA256).ToUpperInvariant()) { throw "R2 manifests disagree for $rel" }
    $sourcePath = [IO.Path]::GetFullPath((Join-Path $sourceResolved ($rel.Replace('/', [IO.Path]::DirectorySeparatorChar))))
    if (-not $sourcePath.StartsWith($sourceResolved + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) {
        throw "R2 payload escapes source root: $rel"
    }
    if (-not (Test-Path -LiteralPath $sourcePath -PathType Leaf)) { throw "R2 payload is missing: $rel" }
    $sourceItem = Get-Item -LiteralPath $sourcePath
    $sourceHash = (Get-FileHash -LiteralPath $sourcePath -Algorithm SHA256).Hash
    if ($sourceItem.Length -ne [int64]$row.SIZE_BYTES -or $sourceHash -cne ([string]$row.SHA256).ToUpperInvariant()) {
        throw "R2 payload identity mismatch: $rel"
    }
    $material.Add([pscustomobject]@{
        relative_path = $rel
        bytes = [int64]$sourceItem.Length
        sha256 = $sourceHash
        mtime_utc_ticks = $sourceItem.LastWriteTimeUtc.Ticks.ToString()
        source_path = $sourcePath
    })
}
if (@($shaRows.Keys | Where-Object { $_ -notin $material.relative_path }).Count -ne 0) {
    throw 'R2 SHA manifest contains a path outside the CSV manifest intersection.'
}

New-Item -ItemType Directory -Path $targetResolved -ErrorAction Stop | Out-Null

$identityRows = [Collections.Generic.List[object]]::new()
foreach ($item in ($material | Sort-Object relative_path)) {
    $destinationPath = [IO.Path]::GetFullPath((Join-Path $targetResolved ($item.relative_path.Replace('/', [IO.Path]::DirectorySeparatorChar))))
    if (-not $destinationPath.StartsWith($targetResolved + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) {
        throw "R2A payload escapes target root: $($item.relative_path)"
    }
    $destinationDirectory = Split-Path -Parent $destinationPath
    if (-not (Test-Path -LiteralPath $destinationDirectory)) {
        New-Item -ItemType Directory -Path $destinationDirectory -Force | Out-Null
    }
    Copy-Item -LiteralPath $item.source_path -Destination $destinationPath -Force
    $destinationItem = Get-Item -LiteralPath $destinationPath
    $destinationItem.IsReadOnly = $false
    $destinationItem.LastWriteTimeUtc = [DateTime]::new([int64]$item.mtime_utc_ticks, [DateTimeKind]::Utc)
    $destinationItem = Get-Item -LiteralPath $destinationPath
    $destinationHash = (Get-FileHash -LiteralPath $destinationPath -Algorithm SHA256).Hash
    if ($destinationItem.Length -ne $item.bytes -or $destinationHash -cne $item.sha256 -or $destinationItem.LastWriteTimeUtc.Ticks.ToString() -cne $item.mtime_utc_ticks) {
        throw "R2 to R2A copy identity mismatch: $($item.relative_path)"
    }
    $identityRows.Add([pscustomobject]@{
        source_relative_path = $item.relative_path
        destination_relative_path = $item.relative_path
        bytes = $item.bytes.ToString()
        sha256 = $item.sha256
        mtime_utc_ticks = $item.mtime_utc_ticks
    })
}

$copyIdentityPath = Join-Path $targetResolved 'COPY_IDENTITY.csv'
$identityRows | Export-Csv -LiteralPath $copyIdentityPath -NoTypeInformation -Encoding utf8
$provenancePath = Join-Path $targetResolved 'COPY_PROVENANCE.md'
$createdAt = [DateTime]::UtcNow.ToString('yyyy-MM-ddTHH:mm:ss.fffffffZ')
$sourceCsvHash = (Get-FileHash -LiteralPath $sourceCsvPath -Algorithm SHA256).Hash
$sourceShaHash = (Get-FileHash -LiteralPath $sourceShaPath -Algorithm SHA256).Hash
$provenance = @(
    '# P580 R2A evidence-only copy provenance',
    '',
    "- round: R2A",
    "- created_at_utc: $createdAt",
    "- source_root: $sourceResolved",
    "- target_root: $targetResolved",
    "- source_csv_manifest_sha256: $sourceCsvHash",
    "- source_sha_manifest_sha256: $sourceShaHash",
    '- material_payload_count: 45',
    '- copied_old_controls: 0',
    '- purpose: evidence-only control reseal; no visual, denominator, pair, or manual review rerun'
) -join "`r`n"
[IO.File]::WriteAllText($provenancePath, $provenance + "`r`n", [Text.UTF8Encoding]::new($false))

$controlNames = @('PAYLOAD_MANIFEST.csv', 'PAYLOAD_MANIFEST.sha256', 'WRITE_STOPPED')
$payloadFiles = @(Get-ChildItem -LiteralPath $targetResolved -File -Recurse | Where-Object { $_.Name -notin $controlNames })
if ($payloadFiles.Count -ne 47) { throw "R2A payload count is $($payloadFiles.Count), expected 47." }
$manifestRows = [Collections.Generic.List[object]]::new()
foreach ($file in $payloadFiles) {
    $rel = $file.FullName.Substring($targetResolved.Length + 1).Replace('\', '/')
    $manifestRows.Add([pscustomobject]@{
        RELATIVE_PATH = $rel
        SIZE_BYTES = $file.Length.ToString()
        SHA256 = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash
        MTIME_UTC_TICKS = $file.LastWriteTimeUtc.Ticks.ToString()
    })
}
$manifestRows = @($manifestRows | Sort-Object RELATIVE_PATH)
if (@($manifestRows | Group-Object -CaseSensitive RELATIVE_PATH | Where-Object { $_.Count -ne 1 }).Count -ne 0) {
    throw 'R2A payload manifest path set is not unique.'
}

$manifestCsvPath = Join-Path $targetResolved 'PAYLOAD_MANIFEST.csv'
$manifestShaPath = Join-Path $targetResolved 'PAYLOAD_MANIFEST.sha256'
$manifestRows | Export-Csv -LiteralPath $manifestCsvPath -NoTypeInformation -Encoding utf8
$shaLines = @($manifestRows | ForEach-Object { "$($_.SHA256)  $($_.RELATIVE_PATH)" })
[IO.File]::WriteAllLines($manifestShaPath, $shaLines, [Text.UTF8Encoding]::new($false))

$manifestCsvReadback = @(Import-Csv -LiteralPath $manifestCsvPath)
$manifestShaReadback = @{}
foreach ($line in Get-Content -LiteralPath $manifestShaPath -Encoding UTF8) {
    if ($line -notmatch '^([0-9A-Fa-f]{64})  (.+)$') { throw "Malformed R2A SHA manifest line: $line" }
    if ($manifestShaReadback.ContainsKey($Matches[2])) { throw "Duplicate R2A SHA manifest path: $($Matches[2])" }
    $manifestShaReadback[$Matches[2]] = $Matches[1].ToUpperInvariant()
}
if ($manifestCsvReadback.Count -ne 47 -or $manifestShaReadback.Count -ne 47) { throw 'R2A manifest count is not 47/47.' }
foreach ($row in $manifestCsvReadback) {
    $payloadPath = [IO.Path]::GetFullPath((Join-Path $targetResolved ($row.RELATIVE_PATH.Replace('/', [IO.Path]::DirectorySeparatorChar))))
    $payloadItem = Get-Item -LiteralPath $payloadPath
    $payloadHash = (Get-FileHash -LiteralPath $payloadPath -Algorithm SHA256).Hash
    if (-not $manifestShaReadback.ContainsKey($row.RELATIVE_PATH) -or $manifestShaReadback[$row.RELATIVE_PATH] -cne $row.SHA256) {
        throw "R2A CSV/SHA manifest mismatch: $($row.RELATIVE_PATH)"
    }
    if ($payloadItem.Length -ne [int64]$row.SIZE_BYTES -or $payloadHash -cne $row.SHA256 -or $payloadItem.LastWriteTimeUtc.Ticks.ToString() -cne $row.MTIME_UTC_TICKS) {
        throw "R2A manifest/filesystem mismatch: $($row.RELATIVE_PATH)"
    }
}

$identityReadback = @(Import-Csv -LiteralPath $copyIdentityPath)
if ($identityReadback.Count -ne 45) { throw 'R2A COPY_IDENTITY count is not 45.' }
foreach ($row in $identityReadback) {
    if ($row.source_relative_path -cne $row.destination_relative_path) { throw 'R2A copy relative paths differ.' }
    $sourceItem = Get-Item -LiteralPath ([IO.Path]::GetFullPath((Join-Path $sourceResolved ($row.source_relative_path.Replace('/', [IO.Path]::DirectorySeparatorChar)))))
    $destinationItem = Get-Item -LiteralPath ([IO.Path]::GetFullPath((Join-Path $targetResolved ($row.destination_relative_path.Replace('/', [IO.Path]::DirectorySeparatorChar)))))
    if ($sourceItem.Length.ToString() -cne $row.bytes -or $destinationItem.Length.ToString() -cne $row.bytes) { throw 'R2A copy bytes differ.' }
    if ((Get-FileHash -LiteralPath $sourceItem.FullName -Algorithm SHA256).Hash -cne $row.sha256 -or (Get-FileHash -LiteralPath $destinationItem.FullName -Algorithm SHA256).Hash -cne $row.sha256) { throw 'R2A copy SHA differs.' }
    if ($sourceItem.LastWriteTimeUtc.Ticks.ToString() -cne $row.mtime_utc_ticks -or $destinationItem.LastWriteTimeUtc.Ticks.ToString() -cne $row.mtime_utc_ticks) { throw 'R2A copy mtime ticks differ.' }
}

$preStopFiles = @(Get-ChildItem -LiteralPath $targetResolved -File -Recurse)
if ($preStopFiles.Count -ne 49) { throw "R2A pre-WSTOP ordinary count is $($preStopFiles.Count), expected 49." }
foreach ($file in $preStopFiles) { $file.IsReadOnly = $true }
if (@(Get-ChildItem -LiteralPath $targetResolved -File -Recurse | Where-Object { -not $_.IsReadOnly }).Count -ne 0) {
    throw 'R2A pre-WSTOP files are not all read-only.'
}

$maxTicks = ($preStopFiles | ForEach-Object { $_.LastWriteTimeUtc.Ticks } | Measure-Object -Maximum).Maximum
$deadline = [DateTime]::UtcNow.AddSeconds(10)
while ([DateTime]::UtcNow.Ticks -le ($maxTicks + 20000000)) {
    if ([DateTime]::UtcNow -ge $deadline) { throw 'Timed out waiting for a strictly later UTC FILETIME.' }
    Start-Sleep -Milliseconds 100
}

$writeStoppedPath = Join-Path $targetResolved 'WRITE_STOPPED'
$sealedAt = [DateTime]::UtcNow.ToString('yyyy-MM-ddTHH:mm:ss.fffffffZ')
$writeStopped = @(
    'WRITE_STOPPED',
    'HANDOFF_ID=A-R108-P580-SA1-FRESH-ISOLATED-20260826-R2A-CONTROL-RESEAL',
    "SEALED_AT_UTC=$sealedAt",
    'MATERIAL_PAYLOAD_COUNT=45',
    'NEW_PROVENANCE_PAYLOAD_COUNT=2',
    'PAYLOAD_COUNT=47',
    'MANIFEST_CONTROL_COUNT=2',
    'WRITE_STOPPED_CONTROL_COUNT=1',
    'CONTROL_COUNT=3',
    'ORDINARY_FILE_TOTAL=50',
    'ROOT_WRITES_AFTER_THIS_FILE=0',
    'DECISION=SA1_CONTENT_PASS_EVIDENCE_CONTROL_RESEALED_AWAIT_MAIN_ACCEPTANCE'
) -join "`r`n"
[IO.File]::WriteAllText($writeStoppedPath, $writeStopped + "`r`n", [Text.UTF8Encoding]::new($false))
(Get-Item -LiteralPath $writeStoppedPath).IsReadOnly = $true

'P580_R2A_CONTROLLER_COMPLETE'
