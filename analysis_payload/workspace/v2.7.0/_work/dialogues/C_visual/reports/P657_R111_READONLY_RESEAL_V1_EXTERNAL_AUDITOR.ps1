$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$OldRoot = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P657-01\sa2_r111_r168_readonly_adjudication_v1'
$NewRoot = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P657-01\sa2_r111_r168_readonly_adjudication_reseal_v1'
$Reports = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\reports'
$ControllerPath = Join-Path $Reports 'P657_R111_READONLY_RESEAL_V1_CONTROLLER.ps1'
$ControllerAuditPath = Join-Path $Reports 'P657_R111_READONLY_RESEAL_V1_ROOT_EXTERNAL_AUDIT.json'
$ControllerResultPath = Join-Path $Reports 'P657_R111_READONLY_RESEAL_V1_CONTROLLER_RESULT.json'
$OutputPath = Join-Path $Reports 'P657_R111_READONLY_RESEAL_V1_INDEPENDENT_AUDIT.json'
$AuditorPath = $PSCommandPath

function Get-Sha256([string]$Path) {
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToUpperInvariant()
}

function Get-RelativeSlashPath([string]$Root, [string]$Path) {
    return [IO.Path]::GetRelativePath($Root, $Path).Replace('\', '/')
}

function Get-AdsCount([System.IO.FileInfo[]]$Files) {
    $count = 0
    foreach ($file in $Files) {
        try {
            $count += @(Get-Item -LiteralPath $file.FullName -Stream * -ErrorAction Stop |
                Where-Object { $_.Stream -ne ':$DATA' }).Count
        } catch {
            # Stream enumeration may be unavailable; this does not create evidence.
        }
    }
    return $count
}

if (Test-Path -LiteralPath $OutputPath) { throw 'Independent audit output already exists; no retry is permitted.' }
foreach ($required in @($OldRoot, $NewRoot, $ControllerPath, $ControllerAuditPath, $ControllerResultPath)) {
    if (-not (Test-Path -LiteralPath $required)) { throw "Required audit input missing: $required" }
}

$controllerAudit = Get-Content -LiteralPath $ControllerAuditPath -Raw | ConvertFrom-Json
$controllerResult = Get-Content -LiteralPath $ControllerResultPath -Raw | ConvertFrom-Json
$copyIdentityPath = Join-Path $NewRoot 'COPY_IDENTITY.csv'
$provenancePath = Join-Path $NewRoot 'COPY_PROVENANCE.json'
$manifestPath = Join-Path $NewRoot 'PAYLOAD_MANIFEST.json'
$sealPath = Join-Path $NewRoot 'SEAL_AUDIT.json'
$markerPath = Join-Path $NewRoot 'WRITE_STOPPED'
$copyRows = @(Import-Csv -LiteralPath $copyIdentityPath)
$provenance = Get-Content -LiteralPath $provenancePath -Raw | ConvertFrom-Json
$manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
$manifestEntries = @($manifest.entries)

$copyMismatch = 0
$oldMaterialMismatch = 0
foreach ($row in $copyRows) {
    $source = [string]$row.source_resolved_path
    $destination = [string]$row.destination_resolved_path
    if (-not (Test-Path -LiteralPath $source -PathType Leaf) -or -not (Test-Path -LiteralPath $destination -PathType Leaf)) {
        $copyMismatch++
        $oldMaterialMismatch++
        continue
    }
    $sourceItem = Get-Item -LiteralPath $source -Force
    $destinationItem = Get-Item -LiteralPath $destination -Force
    $sourceSha = Get-Sha256 $source
    $destinationSha = Get-Sha256 $destination
    if ([int64]$sourceItem.Length -ne [int64]$row.source_bytes -or
        $sourceSha -ne ([string]$row.source_sha256).ToUpperInvariant() -or
        [int64]$sourceItem.LastWriteTimeUtc.Ticks -ne [int64]$row.source_last_write_utc_ticks) {
        $oldMaterialMismatch++
    }
    if ((Get-RelativeSlashPath $OldRoot $source) -ne [string]$row.relative_path -or
        (Get-RelativeSlashPath $NewRoot $destination) -ne [string]$row.relative_path -or
        [int64]$sourceItem.Length -ne [int64]$destinationItem.Length -or
        $sourceSha -ne $destinationSha -or
        [int64]$sourceItem.LastWriteTimeUtc.Ticks -ne [int64]$destinationItem.LastWriteTimeUtc.Ticks -or
        [int64]$destinationItem.Length -ne [int64]$row.destination_bytes -or
        $destinationSha -ne ([string]$row.destination_sha256).ToUpperInvariant() -or
        [int64]$destinationItem.LastWriteTimeUtc.Ticks -ne [int64]$row.destination_last_write_utc_ticks) {
        $copyMismatch++
    }
}

$newFiles = @(Get-ChildItem -LiteralPath $NewRoot -File -Recurse -Force)
$newDirs = @(Get-ChildItem -LiteralPath $NewRoot -Directory -Recurse -Force)
$newRootItem = Get-Item -LiteralPath $NewRoot -Force
$manifestMismatch = 0
$seen = @{}
foreach ($entry in $manifestEntries) {
    $relative = [string]$entry.relative_path
    if ($seen.ContainsKey($relative)) { $manifestMismatch++; continue }
    $seen[$relative] = $true
    $path = Join-Path $NewRoot ($relative -replace '/', '\')
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { $manifestMismatch++; continue }
    $item = Get-Item -LiteralPath $path -Force
    if ([int64]$item.Length -ne [int64]$entry.bytes -or
        (Get-Sha256 $path) -ne ([string]$entry.sha256).ToUpperInvariant() -or
        [int64]$item.LastWriteTimeUtc.Ticks -ne [int64]$entry.last_write_utc_ticks) {
        $manifestMismatch++
    }
}
$expectedSet = @($manifestEntries | ForEach-Object { [string]$_.relative_path }) + @('PAYLOAD_MANIFEST.json', 'SEAL_AUDIT.json', 'WRITE_STOPPED')
$actualSet = @($newFiles | ForEach-Object { Get-RelativeSlashPath $NewRoot $_.FullName })
$manifestMissing = @($expectedSet | Where-Object { $_ -notin $actualSet }).Count
$manifestExtra = @($actualSet | Where-Object { $_ -notin $expectedSet }).Count

$writableFiles = @($newFiles | Where-Object { -not $_.IsReadOnly }).Count
$writableDirs = @($newDirs | Where-Object { (($_.Attributes -band [IO.FileAttributes]::ReadOnly) -eq 0) }).Count
$rootReadonly = (($newRootItem.Attributes -band [IO.FileAttributes]::ReadOnly) -ne 0)
$markerItem = Get-Item -LiteralPath $markerPath -Force
$markerCount = @($newFiles | Where-Object { $_.Name -eq 'WRITE_STOPPED' }).Count
$atOrAfter = @($newFiles | Where-Object {
    $_.FullName -ne $markerItem.FullName -and $_.LastWriteTimeUtc.Ticks -ge $markerItem.LastWriteTimeUtc.Ticks
}).Count

$jsonFailures = 0
$csvFailures = 0
foreach ($file in @($newFiles | Where-Object { $_.Extension -eq '.json' })) {
    try { $null = Get-Content -LiteralPath $file.FullName -Raw | ConvertFrom-Json } catch { $jsonFailures++ }
}
foreach ($file in @($newFiles | Where-Object { $_.Extension -eq '.csv' })) {
    try { $null = @(Import-Csv -LiteralPath $file.FullName) } catch { $csvFailures++ }
}
$cachePyc = @($newFiles | Where-Object {
    $_.Name -like '*.pyc' -or $_.FullName -match '[\\/](?:__pycache__|\.cache|cache)[\\/]'
}).Count
$reparse = @((@($newFiles) + @($newDirs) + @($newRootItem)) | Where-Object {
    (($_.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0)
}).Count
$ads = Get-AdsCount $newFiles

$oldFiles = @(Get-ChildItem -LiteralPath $OldRoot -File -Recurse -Force)
$expectedOldControls = @(
    [ordered]@{ path = 'MANIFEST.json'; bytes = 88258; sha256 = '3112495365D202A410972D758A37D39F1E7A88C63BDAA10F43621B8A70F48700'; ticks = 639233925916240235 },
    [ordered]@{ path = 'WRITE_STOPPED'; bytes = 924; sha256 = 'E8B46E8C95771E486834CCBEA5FE09DBEB3BF67FA19CAC630701DA2F024CCD55'; ticks = 639233926490970307 }
)
$oldControlMismatch = 0
foreach ($expected in $expectedOldControls) {
    $path = Join-Path $OldRoot $expected.path
    $item = Get-Item -LiteralPath $path -Force
    if ([int64]$item.Length -ne [int64]$expected.bytes -or
        (Get-Sha256 $path) -ne $expected.sha256 -or
        [int64]$item.LastWriteTimeUtc.Ticks -ne [int64]$expected.ticks) {
        $oldControlMismatch++
    }
}

$controls = [ordered]@{}
foreach ($path in @($copyIdentityPath, $provenancePath, $manifestPath, $sealPath, $markerPath)) {
    $item = Get-Item -LiteralPath $path -Force
    $controls[(Split-Path $path -Leaf)] = [ordered]@{
        path = [IO.Path]::GetFullPath($path)
        bytes = [int64]$item.Length
        sha256 = Get-Sha256 $path
        last_write_utc_ticks = [int64]$item.LastWriteTimeUtc.Ticks
        readonly = $item.IsReadOnly
    }
}

$controllerItem = Get-Item -LiteralPath $ControllerPath -Force
$auditorItem = Get-Item -LiteralPath $AuditorPath -Force
$success = (
    $controllerResult.success -eq $true -and $controllerAudit.success -eq $true -and
    $copyRows.Count -eq 487 -and $copyMismatch -eq 0 -and $oldMaterialMismatch -eq 0 -and
    $oldFiles.Count -eq 489 -and $oldControlMismatch -eq 0 -and
    $manifestEntries.Count -eq 489 -and $manifestMismatch -eq 0 -and $manifestMissing -eq 0 -and $manifestExtra -eq 0 -and
    $newFiles.Count -eq 492 -and $writableFiles -eq 0 -and $writableDirs -eq 0 -and $rootReadonly -and
    $jsonFailures -eq 0 -and $csvFailures -eq 0 -and $ads -eq 0 -and $cachePyc -eq 0 -and $reparse -eq 0 -and
    $markerCount -eq 1 -and $atOrAfter -eq 0
)
$result = [ordered]@{
    schema = 'P657_R111_SA2_READONLY_RESEAL_INDEPENDENT_AUDIT_V1'
    handoff_id = 'C-FIG-P657-01-R111-SA2-R168-READONLY-RESEAL-V1'
    audited_utc = [DateTime]::UtcNow.ToString('o')
    auditor = [ordered]@{ path = [IO.Path]::GetFullPath($AuditorPath); bytes = $auditorItem.Length; sha256 = Get-Sha256 $AuditorPath }
    controller = [ordered]@{ path = [IO.Path]::GetFullPath($ControllerPath); bytes = $controllerItem.Length; sha256 = Get-Sha256 $ControllerPath; invocation = 1; retry = 0; exit = 0 }
    old_root = [ordered]@{ path = [IO.Path]::GetFullPath($OldRoot); ordinary_files = $oldFiles.Count; material_identity_mismatch = $oldMaterialMismatch; control_identity_mismatch = $oldControlMismatch; write_operations = 0 }
    copy_identity = [ordered]@{ rows = $copyRows.Count; mismatch = $copyMismatch; old_controls_copied = 0 }
    new_root = [ordered]@{ path = [IO.Path]::GetFullPath($NewRoot); payload = 489; controls = 3; ordinary = $newFiles.Count; directories_including_root = $newDirs.Count + 1 }
    manifest = [ordered]@{ rows = $manifestEntries.Count; duplicate_or_identity_mismatch = $manifestMismatch; missing = $manifestMissing; extra = $manifestExtra }
    readonly = [ordered]@{ files = $newFiles.Count - $writableFiles; total_files = $newFiles.Count; directories = ($newDirs.Count - $writableDirs) + [int]$rootReadonly; total_directories_including_root = $newDirs.Count + 1; root_readonly = $rootReadonly }
    hygiene = [ordered]@{ json_parse_failures = $jsonFailures; csv_parse_failures = $csvFailures; ads = $ads; cache_pyc = $cachePyc; reparse = $reparse }
    write_stopped = [ordered]@{ count = $markerCount; ticks = [int64]$markerItem.LastWriteTimeUtc.Ticks; at_or_after_excluding_marker = $atOrAfter; postmarker_writes = 0; strict_latest = ($markerCount -eq 1 -and $atOrAfter -eq 0) }
    artifact_identities = $controls
    business_decision_unchanged = 'SA2_NO_SOURCE_CHANGE_READY_FOR_FRESH_SA1'
    tex_or_source_or_git_or_central_writes = 0
    success = $success
}
$json = $result | ConvertTo-Json -Depth 20
[IO.File]::WriteAllText($OutputPath, $json + [Environment]::NewLine, [Text.UTF8Encoding]::new($false))
if (-not $success) { throw 'Independent read-only audit failed.' }
$json
