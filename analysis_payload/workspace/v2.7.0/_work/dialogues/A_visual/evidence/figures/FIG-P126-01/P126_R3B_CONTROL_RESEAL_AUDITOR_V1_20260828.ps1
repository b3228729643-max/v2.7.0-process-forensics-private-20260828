$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$handoffId = 'A-R115-P126-SA2-DIRECT-BUILD-R3A-CONTROL-RESEAL-V1-20260828'
$operation = 'P126_R115_R3A_SA2_EVIDENCE_ONLY_CONTROL_RESEAL_V1'
$sourceRoot = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\STRICT_R3A_SA2_COORDINATE_QUADRATIC_PATCH_R115_DIRECT_BUILD_20260828'
$destinationRoot = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\STRICT_R3B_SA2_R115_EVIDENCE_ONLY_CONTROL_RESEAL_20260828'
$oldManifestPath = Join-Path $sourceRoot 'PAYLOAD_MANIFEST.csv'
$controllerResultPath = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\P126_R3B_CONTROL_RESEAL_CONTROLLER_RESULT_V1_20260828.json'
$auditResultPath = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\P126_R3B_CONTROL_RESEAL_AUDIT_V1_20260828.json'
$controlNames = @('PAYLOAD_MANIFEST.csv', 'SEAL_AUDIT.json', 'WRITE_STOPPED')
$expectedOldManifestSha = '405541B02D962FD75161DAEBB41C067955D7B99B992DD1F14A7399D3A6EB0D7E'

function Get-CanonicalRelative([string]$Value) {
    return $Value.Replace('\', '/')
}

function Get-RelativePath([string]$Base, [string]$FullName) {
    return Get-CanonicalRelative ([IO.Path]::GetRelativePath($Base, $FullName))
}

function Get-FileSha([string]$Path) {
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToUpperInvariant()
}

function Get-MaxLastWriteTicks([object[]]$Items) {
    $ticks = @($Items | ForEach-Object { [int64]$_.LastWriteTimeUtc.Ticks })
    if ($ticks.Count -eq 0) { throw 'cannot compute maximum ticks from an empty item set' }
    return [int64]($ticks | Sort-Object -Descending | Select-Object -First 1)
}

function Get-TreeSnapshot([string]$Base) {
    $rows = [System.Collections.Generic.List[string]]::new()
    $rootItem = Get-Item -LiteralPath $Base -Force
    $rows.Add(('D<TAB>.<TAB>{0}<TAB>{1}<TAB>{2}' -f $rootItem.CreationTimeUtc.Ticks, $rootItem.LastWriteTimeUtc.Ticks, [int]$rootItem.Attributes))
    foreach ($directory in @(Get-ChildItem -LiteralPath $Base -Directory -Recurse -Force)) {
        $relative = Get-RelativePath $Base $directory.FullName
        $rows.Add(('D<TAB>{0}<TAB>{1}<TAB>{2}<TAB>{3}' -f $relative, $directory.CreationTimeUtc.Ticks, $directory.LastWriteTimeUtc.Ticks, [int]$directory.Attributes))
    }
    foreach ($file in @(Get-ChildItem -LiteralPath $Base -File -Recurse -Force)) {
        $relative = Get-RelativePath $Base $file.FullName
        $rows.Add(('F<TAB>{0}<TAB>{1}<TAB>{2}<TAB>{3}<TAB>{4}<TAB>{5}' -f $relative, $file.Length, (Get-FileSha $file.FullName), $file.CreationTimeUtc.Ticks, $file.LastWriteTimeUtc.Ticks, [int]$file.Attributes))
    }
    $array = $rows.ToArray()
    [Array]::Sort($array, [StringComparer]::Ordinal)
    $text = ($array -join "`n") + "`n"
    return [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData([Text.Encoding]::UTF8.GetBytes($text)))
}

if (Test-Path -LiteralPath $auditResultPath) { throw 'R3B auditor result already exists' }
if (-not (Test-Path -LiteralPath $destinationRoot -PathType Container)) { throw 'R3B destination root missing' }
if ((Get-FileSha $oldManifestPath) -ne $expectedOldManifestSha) { throw 'old manifest SHA mismatch' }
$controllerResult = Get-Content -LiteralPath $controllerResultPath -Raw -Encoding utf8 | ConvertFrom-Json
$sourceSnapshot = Get-TreeSnapshot $sourceRoot
if ($sourceSnapshot -ne [string]$controllerResult.source_root_snapshot_before_sha256) { throw 'old R3A root differs from controller source snapshot' }

$errors = [System.Collections.Generic.List[string]]::new()
$oldRows = @(Import-Csv -LiteralPath $oldManifestPath)
$copyRows = @(Import-Csv -LiteralPath (Join-Path $destinationRoot 'COPY_IDENTITY.csv'))
$manifestRows = @(Import-Csv -LiteralPath (Join-Path $destinationRoot 'PAYLOAD_MANIFEST.csv'))
$provenance = Get-Content -LiteralPath (Join-Path $destinationRoot 'COPY_PROVENANCE.json') -Raw -Encoding utf8 | ConvertFrom-Json
$null = Get-Content -LiteralPath (Join-Path $destinationRoot 'SEAL_AUDIT.json') -Raw -Encoding utf8 | ConvertFrom-Json
if ($oldRows.Count -ne 205) { $errors.Add("old rows=$($oldRows.Count)") }
if ($copyRows.Count -ne 205) { $errors.Add("copy rows=$($copyRows.Count)") }
if ($manifestRows.Count -ne 207) { $errors.Add("manifest rows=$($manifestRows.Count)") }
if ([string]$provenance.source_root -ne [IO.Path]::GetFullPath($sourceRoot)) { $errors.Add('provenance source root mismatch') }
if ([string]$provenance.destination_root -ne [IO.Path]::GetFullPath($destinationRoot)) { $errors.Add('provenance destination root mismatch') }
if ([string]$provenance.source_payload_manifest_sha256 -ne $expectedOldManifestSha) { $errors.Add('provenance old manifest SHA mismatch') }

if (@($copyRows | Group-Object -Property relative_path | Where-Object { $_.Count -ne 1 }).Count -ne 0) { $errors.Add('copy identity duplicate path') }
foreach ($copy in $copyRows) {
    $relative = Get-CanonicalRelative ([string]$copy.relative_path)
    $sourcePath = [IO.Path]::GetFullPath((Join-Path $sourceRoot $relative.Replace('/', '\')))
    $destinationPath = [IO.Path]::GetFullPath((Join-Path $destinationRoot $relative.Replace('/', '\')))
    if ([string]$copy.source_path -ne $sourcePath) { $errors.Add("copy source resolved path mismatch $relative") }
    if ([string]$copy.destination_path -ne $destinationPath) { $errors.Add("copy destination resolved path mismatch $relative") }
    if (-not (Test-Path -LiteralPath $sourcePath -PathType Leaf)) { $errors.Add("copy source missing $relative"); continue }
    if (-not (Test-Path -LiteralPath $destinationPath -PathType Leaf)) { $errors.Add("copy destination missing $relative"); continue }
    $source = Get-Item -LiteralPath $sourcePath -Force
    $destination = Get-Item -LiteralPath $destinationPath -Force
    if ($source.Length -ne [int64]$copy.bytes -or $destination.Length -ne [int64]$copy.bytes) { $errors.Add("copy byte mismatch $relative") }
    $expectedSha = ([string]$copy.sha256).ToUpperInvariant()
    if ((Get-FileSha $sourcePath) -ne $expectedSha -or (Get-FileSha $destinationPath) -ne $expectedSha) { $errors.Add("copy SHA mismatch $relative") }
    if ($source.CreationTimeUtc.Ticks -ne [int64]$copy.creation_time_utc_ticks -or $destination.CreationTimeUtc.Ticks -ne [int64]$copy.creation_time_utc_ticks) { $errors.Add("copy creation mismatch $relative") }
    if ($source.LastWriteTimeUtc.Ticks -ne [int64]$copy.last_write_time_utc_ticks -or $destination.LastWriteTimeUtc.Ticks -ne [int64]$copy.last_write_time_utc_ticks) { $errors.Add("copy last-write mismatch $relative") }
}

$actualPayloadFiles = @(Get-ChildItem -LiteralPath $destinationRoot -File -Recurse -Force | Where-Object { -not ($_.DirectoryName -eq $destinationRoot -and $controlNames -contains $_.Name) })
$actualPayloadPaths = @($actualPayloadFiles | ForEach-Object { Get-RelativePath $destinationRoot $_.FullName } | Sort-Object -CaseSensitive)
$manifestPaths = @($manifestRows.relative_path | ForEach-Object { Get-CanonicalRelative ([string]$_) } | Sort-Object -CaseSensitive)
if (@($manifestRows | Group-Object -Property relative_path | Where-Object { $_.Count -ne 1 }).Count -ne 0) { $errors.Add('manifest duplicate path') }
if (@(Compare-Object -ReferenceObject $manifestPaths -DifferenceObject $actualPayloadPaths -CaseSensitive).Count -ne 0) { $errors.Add('manifest/FS payload set mismatch') }
foreach ($row in $manifestRows) {
    $relative = Get-CanonicalRelative ([string]$row.relative_path)
    $path = Join-Path $destinationRoot $relative.Replace('/', '\')
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { $errors.Add("manifest file missing $relative"); continue }
    $file = Get-Item -LiteralPath $path -Force
    if ($file.Length -ne [int64]$row.bytes) { $errors.Add("manifest byte mismatch $relative") }
    if ((Get-FileSha $path) -ne ([string]$row.sha256).ToUpperInvariant()) { $errors.Add("manifest SHA mismatch $relative") }
    if ($file.CreationTimeUtc.Ticks -ne [int64]$row.creation_time_utc_ticks) { $errors.Add("manifest creation mismatch $relative") }
    if ($file.LastWriteTimeUtc.Ticks -ne [int64]$row.last_write_time_utc_ticks) { $errors.Add("manifest last-write mismatch $relative") }
}

$allFiles = @(Get-ChildItem -LiteralPath $destinationRoot -File -Recurse -Force)
$allDirs = @(@(Get-Item -LiteralPath $destinationRoot -Force) + @(Get-ChildItem -LiteralPath $destinationRoot -Directory -Recurse -Force))
$notReadonlyFiles = @($allFiles | Where-Object { -not ($_.Attributes -band [IO.FileAttributes]::ReadOnly) })
$notReadonlyDirs = @($allDirs | Where-Object { -not ($_.Attributes -band [IO.FileAttributes]::ReadOnly) })
if ($allFiles.Count -ne 210) { $errors.Add("ordinary count=$($allFiles.Count)") }
if ($notReadonlyFiles.Count -ne 0) { $errors.Add("writable files=$($notReadonlyFiles.Count)") }
if ($notReadonlyDirs.Count -ne 0) { $errors.Add("writable dirs=$($notReadonlyDirs.Count)") }

$markerPath = Join-Path $destinationRoot 'WRITE_STOPPED'
$markerBytes = [IO.File]::ReadAllBytes($markerPath)
if ($markerBytes.Length -ge 3 -and $markerBytes[0] -eq 0xEF -and $markerBytes[1] -eq 0xBB -and $markerBytes[2] -eq 0xBF) { $errors.Add('marker has BOM') }
$markerText = [Text.Encoding]::UTF8.GetString($markerBytes)
if ($markerText.Contains("`t")) { $errors.Add('marker has TAB') }
$markerLines = @($markerText -split "`r?`n" | Where-Object { $_.Length -gt 0 })
$badMarkerLines = @($markerLines | Where-Object { $_ -notmatch '^[A-Z0-9_]+=[^\t\r\n]+$' })
$duplicateMarkerKeys = @($markerLines | ForEach-Object { ($_ -split '=', 2)[0] } | Group-Object | Where-Object { $_.Count -ne 1 })
$markerMap = @{}
foreach ($line in $markerLines) { $parts = $line -split '=', 2; $markerMap[$parts[0]] = $parts[1] }
if ($badMarkerLines.Count -ne 0) { $errors.Add("bad marker lines=$($badMarkerLines.Count)") }
if ($duplicateMarkerKeys.Count -ne 0) { $errors.Add("duplicate marker keys=$($duplicateMarkerKeys.Count)") }
foreach ($key in @('HANDOFF_ID','OPERATION','VERDICT','ROOT','SOURCE_ROOT','COPIED_MATERIAL_COUNT','PAYLOAD_COUNT','CONTROL_COUNT','ORDINARY_COUNT','OLD_PAYLOAD_MANIFEST_SHA256','SOURCE_ROOT_SNAPSHOT_SHA256','COPY_IDENTITY_SHA256','COPY_PROVENANCE_SHA256','PAYLOAD_MANIFEST_SHA256','SEAL_AUDIT_SHA256','HARD_DEFECT_ID')) {
    if (-not $markerMap.ContainsKey($key)) { $errors.Add("missing marker key $key") }
}
if ($markerMap['HANDOFF_ID'] -ne $handoffId) { $errors.Add('marker handoff mismatch') }
if ($markerMap['OPERATION'] -ne $operation) { $errors.Add('marker operation mismatch') }
if ($markerMap['ROOT'] -ne $destinationRoot) { $errors.Add('marker root mismatch') }
if ($markerMap['SOURCE_ROOT'] -ne $sourceRoot) { $errors.Add('marker source root mismatch') }
if ($markerMap['OLD_PAYLOAD_MANIFEST_SHA256'] -ne $expectedOldManifestSha) { $errors.Add('marker old manifest SHA mismatch') }
if ($markerMap['COPY_IDENTITY_SHA256'] -ne (Get-FileSha (Join-Path $destinationRoot 'COPY_IDENTITY.csv'))) { $errors.Add('marker copy identity SHA mismatch') }
if ($markerMap['COPY_PROVENANCE_SHA256'] -ne (Get-FileSha (Join-Path $destinationRoot 'COPY_PROVENANCE.json'))) { $errors.Add('marker provenance SHA mismatch') }
if ($markerMap['PAYLOAD_MANIFEST_SHA256'] -ne (Get-FileSha (Join-Path $destinationRoot 'PAYLOAD_MANIFEST.csv'))) { $errors.Add('marker manifest SHA mismatch') }
if ($markerMap['SEAL_AUDIT_SHA256'] -ne (Get-FileSha (Join-Path $destinationRoot 'SEAL_AUDIT.json'))) { $errors.Add('marker audit SHA mismatch') }

$marker = Get-Item -LiteralPath $markerPath -Force
$otherItems = @($allFiles | Where-Object { $_.FullName -ne $markerPath }) + $allDirs
$maxOtherTicks = Get-MaxLastWriteTicks $otherItems
$marginTicks = [int64]$marker.LastWriteTimeUtc.Ticks - $maxOtherTicks
$atOrAfter = @($otherItems | Where-Object { $_.LastWriteTimeUtc.Ticks -ge $marker.LastWriteTimeUtc.Ticks })
if ($marginTicks -le 0) { $errors.Add("marker strict-latest margin=$marginTicks") }
if ($atOrAfter.Count -ne 0) { $errors.Add("at-or-after excluding marker=$($atOrAfter.Count)") }

$ads = [System.Collections.Generic.List[string]]::new()
foreach ($file in $allFiles) {
    foreach ($stream in @(Get-Item -LiteralPath $file.FullName -Stream * -ErrorAction SilentlyContinue)) {
        if ($stream.Stream -ne ':$DATA') { $ads.Add("$($file.FullName):$($stream.Stream)") }
    }
}
$pyc = @(Get-ChildItem -LiteralPath $destinationRoot -File -Recurse -Force | Where-Object { $_.Extension -eq '.pyc' -or $_.Directory.Name -eq '__pycache__' })
$reparse = @(@(Get-Item -LiteralPath $destinationRoot -Force) + @(Get-ChildItem -LiteralPath $destinationRoot -Recurse -Force) | Where-Object { $_.Attributes -band [IO.FileAttributes]::ReparsePoint })
if ($ads.Count -ne 0) { $errors.Add("ADS count=$($ads.Count)") }
if ($pyc.Count -ne 0) { $errors.Add("cache-pyc count=$($pyc.Count)") }
if ($reparse.Count -ne 0) { $errors.Add("reparse count=$($reparse.Count)") }

$destinationSnapshot1 = Get-TreeSnapshot $destinationRoot
$destinationSnapshot2 = Get-TreeSnapshot $destinationRoot
if ($destinationSnapshot1 -ne [string]$controllerResult.destination_postmarker_snapshot_sha256) { $errors.Add('destination snapshot differs from controller') }
if ($destinationSnapshot1 -ne $destinationSnapshot2) { $errors.Add('destination double snapshot differs') }
$sourceSnapshot2 = Get-TreeSnapshot $sourceRoot
if ($sourceSnapshot2 -ne [string]$controllerResult.source_root_snapshot_before_sha256) { $errors.Add('old source root changed') }

$result = [ordered]@{
    schema = 'P126_R3B_CONTROL_RESEAL_AUDIT_V1'
    handoff_id = $handoffId
    operation = $operation
    invocation_count = 1
    retry_count = 0
    copied_material_count = $copyRows.Count
    payload_count = $manifestRows.Count
    control_count = 3
    ordinary_count = $allFiles.Count
    directory_count_including_root = $allDirs.Count
    readonly_files = $allFiles.Count - $notReadonlyFiles.Count
    readonly_dirs = $allDirs.Count - $notReadonlyDirs.Count
    marker_physical_lines = $markerLines.Count
    marker_unique_keys = $markerMap.Keys.Count
    marker_bad_lines = $badMarkerLines.Count
    marker_sha256 = Get-FileSha $markerPath
    marker_last_write_utc_ticks = $marker.LastWriteTimeUtc.Ticks
    strict_latest_margin_ticks = $marginTicks
    at_or_after_excluding_marker = $atOrAfter.Count
    destination_postmarker_snapshot_sha256 = $destinationSnapshot1
    source_root_snapshot_sha256 = $sourceSnapshot2
    postmarker_content_attribute_writes = 0
    ads_count = $ads.Count
    cache_pyc_count = $pyc.Count
    reparse_count = $reparse.Count
    errors = @($errors)
    hard_gate = $errors.Count -eq 0
    audited_utc = [DateTime]::UtcNow.ToString('o')
}
$result | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $auditResultPath -Encoding utf8NoBOM
Write-Output ($result | ConvertTo-Json -Depth 8)
if ($errors.Count -ne 0) { exit 1 }
