$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$root = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\STRICT_R3A_SA2_COORDINATE_QUADRATIC_PATCH_R115_DIRECT_BUILD_20260828'
$controllerResultPath = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\P126_R3A_SEAL_CONTROLLER_RESULT_20260828.json'
$auditResultPath = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\P126_R3A_POSTSEAL_AUDIT_20260828.json'
$controlNames = @('PAYLOAD_MANIFEST.csv', 'PAYLOAD_MANIFEST.json', 'SEAL_AUDIT.json', 'WRITE_STOPPED')

function Get-RelativePath([string]$Base, [string]$FullName) {
    return [IO.Path]::GetRelativePath($Base, $FullName).Replace('\', '/')
}

function Get-TreeSnapshot([string]$Base) {
    $rows = [System.Collections.Generic.List[string]]::new()
    $rootItem = Get-Item -LiteralPath $Base -Force
    $rows.Add(('D<TAB>.<TAB>{0}<TAB>{1}<TAB>{2}' -f $rootItem.CreationTimeUtc.Ticks, $rootItem.LastWriteTimeUtc.Ticks, [int]$rootItem.Attributes))
    foreach ($directory in @(Get-ChildItem -LiteralPath $Base -Directory -Recurse -Force | Sort-Object -Property FullName -CaseSensitive)) {
        $relative = Get-RelativePath $Base $directory.FullName
        $rows.Add(('D<TAB>{0}<TAB>{1}<TAB>{2}<TAB>{3}' -f $relative, $directory.CreationTimeUtc.Ticks, $directory.LastWriteTimeUtc.Ticks, [int]$directory.Attributes))
    }
    foreach ($file in @(Get-ChildItem -LiteralPath $Base -File -Recurse -Force | Sort-Object -Property FullName -CaseSensitive)) {
        $relative = Get-RelativePath $Base $file.FullName
        $hash = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToUpperInvariant()
        $rows.Add(('F<TAB>{0}<TAB>{1}<TAB>{2}<TAB>{3}<TAB>{4}<TAB>{5}' -f $relative, $file.Length, $hash, $file.CreationTimeUtc.Ticks, $file.LastWriteTimeUtc.Ticks, [int]$file.Attributes))
    }
    $text = ($rows -join "`n") + "`n"
    $bytes = [Text.Encoding]::UTF8.GetBytes($text)
    return [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($bytes))
}

if (Test-Path -LiteralPath $auditResultPath) { throw 'auditor result already exists' }
$controllerResult = Get-Content -LiteralPath $controllerResultPath -Raw -Encoding utf8 | ConvertFrom-Json
$csvPath = Join-Path $root 'PAYLOAD_MANIFEST.csv'
$jsonPath = Join-Path $root 'PAYLOAD_MANIFEST.json'
$sealAuditPath = Join-Path $root 'SEAL_AUDIT.json'
$markerPath = Join-Path $root 'WRITE_STOPPED'
$rows = @(Import-Csv -LiteralPath $csvPath)
$jsonManifest = Get-Content -LiteralPath $jsonPath -Raw -Encoding utf8 | ConvertFrom-Json
$null = Get-Content -LiteralPath $sealAuditPath -Raw -Encoding utf8 | ConvertFrom-Json
$errors = [System.Collections.Generic.List[string]]::new()

if ($rows.Count -ne 205) { $errors.Add("manifest rows=$($rows.Count)") }
if (@($jsonManifest.rows).Count -ne 205) { $errors.Add('JSON manifest row count mismatch') }
if (@($rows | Group-Object -Property relative_path | Where-Object { $_.Count -ne 1 }).Count -ne 0) { $errors.Add('duplicate manifest path') }

$actualPayloadFiles = @(Get-ChildItem -LiteralPath $root -File -Recurse -Force | Where-Object { -not ($_.DirectoryName -eq $root -and $controlNames -contains $_.Name) })
$actualPaths = @($actualPayloadFiles | ForEach-Object { Get-RelativePath $root $_.FullName } | Sort-Object -CaseSensitive)
$expectedPaths = @($rows.relative_path | Sort-Object -CaseSensitive)
if (@(Compare-Object -ReferenceObject $expectedPaths -DifferenceObject $actualPaths -CaseSensitive).Count -ne 0) { $errors.Add('manifest/FS payload set mismatch') }
foreach ($row in $rows) {
    $path = Join-Path $root ([string]$row.relative_path).Replace('/', '\')
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { $errors.Add("missing payload $($row.relative_path)"); continue }
    $item = Get-Item -LiteralPath $path -Force
    if ($item.Length -ne [int64]$row.bytes) { $errors.Add("byte mismatch $($row.relative_path)") }
    if ((Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToUpperInvariant() -ne [string]$row.sha256) { $errors.Add("SHA mismatch $($row.relative_path)") }
    if ($item.CreationTimeUtc.Ticks -ne [int64]$row.creation_time_utc_ticks) { $errors.Add("creation mismatch $($row.relative_path)") }
    if ($item.LastWriteTimeUtc.Ticks -ne [int64]$row.last_write_time_utc_ticks) { $errors.Add("last-write mismatch $($row.relative_path)") }
}

$allFiles = @(Get-ChildItem -LiteralPath $root -File -Recurse -Force)
$allDirs = @(@(Get-Item -LiteralPath $root -Force) + @(Get-ChildItem -LiteralPath $root -Directory -Recurse -Force))
$notReadonlyFiles = @($allFiles | Where-Object { -not ($_.Attributes -band [IO.FileAttributes]::ReadOnly) })
$notReadonlyDirs = @($allDirs | Where-Object { -not ($_.Attributes -band [IO.FileAttributes]::ReadOnly) })
if ($allFiles.Count -ne 209) { $errors.Add("ordinary count=$($allFiles.Count)") }
if ($notReadonlyFiles.Count -ne 0) { $errors.Add("writable files=$($notReadonlyFiles.Count)") }
if ($notReadonlyDirs.Count -ne 0) { $errors.Add("writable dirs=$($notReadonlyDirs.Count)") }

$markerBytes = [IO.File]::ReadAllBytes($markerPath)
if ($markerBytes.Length -ge 3 -and $markerBytes[0] -eq 0xEF -and $markerBytes[1] -eq 0xBB -and $markerBytes[2] -eq 0xBF) { $errors.Add('marker has UTF-8 BOM') }
$markerText = [Text.Encoding]::UTF8.GetString($markerBytes)
if ($markerText.Contains("`t")) { $errors.Add('marker has TAB') }
$markerLines = @($markerText -split "`r?`n" | Where-Object { $_.Length -gt 0 })
$badLines = @($markerLines | Where-Object { $_ -notmatch '^[A-Z0-9_]+=[^\t\r\n]+$' })
$duplicateKeys = @($markerLines | ForEach-Object { ($_ -split '=', 2)[0] } | Group-Object | Where-Object { $_.Count -ne 1 })
if ($badLines.Count -ne 0) { $errors.Add("bad marker lines=$($badLines.Count)") }
if ($duplicateKeys.Count -ne 0) { $errors.Add("duplicate marker keys=$($duplicateKeys.Count)") }
$markerMap = @{}
foreach ($line in $markerLines) { $parts = $line -split '=', 2; $markerMap[$parts[0]] = $parts[1] }
foreach ($key in @('HANDOFF_ID','VERDICT','ROOT','PAYLOAD_COUNT','CONTROL_COUNT','ORDINARY_COUNT','PDF_SHA256','SOURCE_SHA256','HARD_DEFECT_ID')) {
    if (-not $markerMap.ContainsKey($key)) { $errors.Add("missing marker key $key") }
}

$marker = Get-Item -LiteralPath $markerPath -Force
$otherItems = @($allFiles | Where-Object { $_.FullName -ne $markerPath }) + $allDirs
$atOrAfter = @($otherItems | Where-Object { $_.LastWriteTimeUtc.Ticks -ge $marker.LastWriteTimeUtc.Ticks })
$maxOtherTicks = ($otherItems | Measure-Object -Property @{ Expression = { $_.LastWriteTimeUtc.Ticks } } -Maximum).Maximum
$margin = [int64]$marker.LastWriteTimeUtc.Ticks - [int64]$maxOtherTicks
if ($margin -le 0) { $errors.Add("marker strict-latest margin=$margin") }
if ($atOrAfter.Count -ne 0) { $errors.Add("items at-or-after marker=$($atOrAfter.Count)") }

$ads = [System.Collections.Generic.List[string]]::new()
foreach ($file in $allFiles) {
    foreach ($stream in @(Get-Item -LiteralPath $file.FullName -Stream * -ErrorAction SilentlyContinue)) {
        if ($stream.Stream -ne ':$DATA') { $ads.Add("$($file.FullName):$($stream.Stream)") }
    }
}
if ($ads.Count -ne 0) { $errors.Add("ADS count=$($ads.Count)") }
$pyc = @(Get-ChildItem -LiteralPath $root -File -Recurse -Force | Where-Object { $_.Extension -eq '.pyc' -or $_.Name -eq '__pycache__' })
$reparse = @(@(Get-Item -LiteralPath $root -Force) + @(Get-ChildItem -LiteralPath $root -Recurse -Force) | Where-Object { $_.Attributes -band [IO.FileAttributes]::ReparsePoint })
if ($pyc.Count -ne 0) { $errors.Add("pyc/cache artifacts=$($pyc.Count)") }
if ($reparse.Count -ne 0) { $errors.Add("reparse points=$($reparse.Count)") }

$snapshot = Get-TreeSnapshot $root
if ($snapshot -ne [string]$controllerResult.postmarker_snapshot_sha256) { $errors.Add('postmarker snapshot differs from controller') }
$snapshot2 = Get-TreeSnapshot $root
if ($snapshot -ne $snapshot2) { $errors.Add('auditor double snapshot differs') }

$result = [ordered]@{
    schema = 'P126_R3A_POSTSEAL_AUDIT_V1'
    handoff_id = 'A-R115-P126-SA2-DIRECT-BUILD-R3A-20260828'
    verdict = 'LOCAL_SA2_FAIL_RETURN_TO_MAIN_SOURCE_SCOPE'
    invocation_count = 1
    retry_count = 0
    payload_count = $rows.Count
    control_count = 4
    ordinary_count = $allFiles.Count
    directory_count_including_root = $allDirs.Count
    readonly_files = $allFiles.Count - $notReadonlyFiles.Count
    readonly_dirs = $allDirs.Count - $notReadonlyDirs.Count
    marker_physical_lines = $markerLines.Count
    marker_unique_keys = $markerMap.Keys.Count
    marker_bad_lines = $badLines.Count
    marker_sha256 = (Get-FileHash -LiteralPath $markerPath -Algorithm SHA256).Hash.ToUpperInvariant()
    marker_last_write_utc_ticks = $marker.LastWriteTimeUtc.Ticks
    strict_latest_margin_ticks = $margin
    at_or_after_excluding_marker = $atOrAfter.Count
    postmarker_snapshot_sha256 = $snapshot
    postmarker_content_attribute_writes = 0
    manifest_identity_errors = $errors.Count
    ads_count = $ads.Count
    pyc_count = $pyc.Count
    reparse_count = $reparse.Count
    errors = @($errors)
    hard_gate = $errors.Count -eq 0
    audited_utc = [DateTime]::UtcNow.ToString('o')
}
$result | ConvertTo-Json -Depth 7 | Set-Content -LiteralPath $auditResultPath -Encoding utf8NoBOM
Write-Output ($result | ConvertTo-Json -Depth 7)
if ($errors.Count -ne 0) { exit 1 }
