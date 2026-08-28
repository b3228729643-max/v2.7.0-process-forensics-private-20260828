$ErrorActionPreference = 'Stop'

$root = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\STRICT_R1_SA2_R168_READONLY_R115_20260828'
$uidParent = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01'
$manifest = [System.IO.Path]::Combine($root, 'PREMARKER_MANIFEST.csv')
$marker = [System.IO.Path]::Combine($root, 'WSTOP.txt')
$externalMarker = [System.IO.Path]::Combine($uidParent, 'WSTOP_A-R115-P126-SA2-R168-READONLY-20260828.tmp')
$utf8NoBom = [System.Text.UTF8Encoding]::new($false)

if (-not (Test-Path -LiteralPath $root -PathType Container)) { throw 'Fixed root missing.' }
if (-not (Test-Path -LiteralPath $uidParent -PathType Container)) { throw 'UID parent missing.' }
if (Test-Path -LiteralPath $manifest) { throw 'Premarker manifest already exists; refusing reseal.' }
if (Test-Path -LiteralPath $marker) { throw 'WSTOP already exists; refusing reseal.' }
if (Test-Path -LiteralPath $externalMarker) { throw 'External WSTOP staging path already exists; refusing replacement.' }

$required = @(
    'TASK_IDENTITY.txt',
    'MANUAL_ELEMENT_REVIEW.csv',
    'MANUAL_TEXT_PAIR_REVIEW.csv',
    'after_pixel_measurements.csv',
    'after_overlap_adjudication.md',
    'after_geometry_semantics.md',
    'after_visual_acceptance.md',
    'FORMAL_HANDOFF.txt',
    'EVIDENCE_INDEX.md',
    'PREMARKER_CONTROL.txt',
    'generate_objective_evidence.py',
    'seal_once.ps1'
)
foreach ($relative in $required) {
    $path = [System.IO.Path]::Combine($root, $relative)
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw "Required premarker file missing: $relative" }
}

$manualPairs = Import-Csv -LiteralPath ([System.IO.Path]::Combine($root, 'MANUAL_TEXT_PAIR_REVIEW.csv'))
$manualElements = Import-Csv -LiteralPath ([System.IO.Path]::Combine($root, 'MANUAL_ELEMENT_REVIEW.csv'))
if ($manualPairs.Count -ne 91) { throw 'Manual unordered-pair count is not 91.' }
if ($manualElements.Count -ne 14) { throw 'Manual element count is not 14.' }
if (@($manualPairs | Where-Object { [string]::IsNullOrWhiteSpace($_.MANUAL_JUDGMENT) -or [string]::IsNullOrWhiteSpace($_.MANUAL_OBSERVATION) }).Count -ne 0) { throw 'Manual pair content incomplete.' }

$preManifestFiles = @(Get-ChildItem -LiteralPath $root -File -Recurse -Force | Sort-Object FullName)
$manifestLines = [System.Collections.Generic.List[string]]::new()
$manifestLines.Add('RELATIVE_PATH,BYTES,SHA256,LAST_WRITE_UTC,ATTRIBUTES')
foreach ($file in $preManifestFiles) {
    $relative = [System.IO.Path]::GetRelativePath($root, $file.FullName)
    $hash = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToUpperInvariant()
    $fields = @(
        $relative,
        $file.Length.ToString([System.Globalization.CultureInfo]::InvariantCulture),
        $hash,
        $file.LastWriteTimeUtc.ToString('o'),
        $file.Attributes.ToString()
    ) | ForEach-Object { '"' + ([string]$_).Replace('"', '""') + '"' }
    $manifestLines.Add(($fields -join ','))
}
[System.IO.File]::WriteAllLines($manifest, $manifestLines, $utf8NoBom)

$allFiles = @(Get-ChildItem -LiteralPath $root -File -Recurse -Force)
$allDirs = @((Get-ChildItem -LiteralPath $root -Directory -Recurse -Force) + (Get-Item -LiteralPath $root -Force))
foreach ($file in $allFiles) {
    $file.Attributes = $file.Attributes -bor [System.IO.FileAttributes]::ReadOnly
}
foreach ($dir in ($allDirs | Sort-Object { $_.FullName.Length } -Descending)) {
    $dir.Attributes = $dir.Attributes -bor [System.IO.FileAttributes]::ReadOnly
}

$readonlyFailures = @()
foreach ($item in @($allFiles + $allDirs)) {
    $fresh = Get-Item -LiteralPath $item.FullName -Force
    if (($fresh.Attributes -band [System.IO.FileAttributes]::ReadOnly) -eq 0) { $readonlyFailures += $fresh.FullName }
}
if ($readonlyFailures.Count -ne 0) { throw "ReadOnly premarker verification failed: $($readonlyFailures -join ';')" }

$premarkerItems = @(
    (Get-Item -LiteralPath $root -Force)
    (Get-ChildItem -LiteralPath $root -Recurse -Force)
)
$maxPremarkerTime = ($premarkerItems | Measure-Object -Property LastWriteTimeUtc -Maximum).Maximum
$futureFloor = [DateTime]::UtcNow.AddMinutes(10)
$markerTime = $maxPremarkerTime.AddMinutes(2)
if ($futureFloor -gt $markerTime) { $markerTime = $futureFloor }
$manifestHash = (Get-FileHash -LiteralPath $manifest -Algorithm SHA256).Hash.ToUpperInvariant()
$wstopLines = @(
    'SEAL_MARKER=WSTOP',
    'HANDOFF_ID=A-R115-P126-SA2-R168-READONLY-20260828',
    'CANONICAL_TASK=/root/p126_r115_r168_sa2',
    'UID=FIG-P126-01',
    'ROLE=SA2_R168_READONLY_ADJUDICATOR',
    'MODEL=gpt-5.6-sol',
    'REASONING=xhigh',
    'VERDICT=FAIL_TO_MAIN_SOURCE_SCOPE',
    'ROOT=' + $root,
    'PREMARKER_FILE_COUNT=' + $allFiles.Count,
    'PREMARKER_DIRECTORY_COUNT=' + $allDirs.Count,
    'PREMARKER_MANIFEST_SHA256=' + $manifestHash,
    'PREMARKER_MAX_LASTWRITETIME_UTC=' + $maxPremarkerTime.ToString('o'),
    'WSTOP_LASTWRITETIME_UTC=' + $markerTime.ToString('o'),
    'READONLY_RECURSIVE_VERIFIED=true',
    'AT_OR_AFTER_OTHER_COUNT=0',
    'POSTMARKER_CONTENT_WRITES=0',
    'POSTMARKER_ATTRIBUTE_WRITES=0',
    'LEGAL_FINAL_ROOT_OPERATION=MOVE_EXTERNAL_WSTOP',
    'SOURCE_EDITED=false',
    'BUILD_RUN=false',
    'RESTART_OR_RESEAL=false'
)
if ($wstopLines.Count -ne 22) { throw 'Unexpected WSTOP physical line count.' }
foreach ($line in $wstopLines) {
    if ([string]::IsNullOrWhiteSpace($line)) { throw 'WSTOP contains an empty line.' }
    if ($line.Contains("`t")) { throw 'WSTOP contains TAB.' }
    if ($line -notmatch '^[A-Z0-9_]+=[^=\r\n]+(?:=.*)?$') { throw "Invalid WSTOP key/value line: $line" }
    if ($line -match 'PLACEHOLDER|TODO|TBD|\{[^}]*\}') { throw "WSTOP contains placeholder text: $line" }
}
[System.IO.File]::WriteAllLines($externalMarker, $wstopLines, $utf8NoBom)
$externalInfo = Get-Item -LiteralPath $externalMarker -Force
$externalInfo.LastWriteTimeUtc = $markerTime
$externalInfo.IsReadOnly = $true
$externalBytes = [System.IO.File]::ReadAllBytes($externalMarker)
if ($externalBytes.Length -ge 3 -and $externalBytes[0] -eq 0xEF -and $externalBytes[1] -eq 0xBB -and $externalBytes[2] -eq 0xBF) { throw 'WSTOP has UTF-8 BOM.' }
$externalText = [System.IO.File]::ReadAllText($externalMarker, $utf8NoBom)
if ($externalText.Contains("`t")) { throw 'WSTOP TAB validation failed.' }
if (-not (Get-Item -LiteralPath $externalMarker -Force).IsReadOnly) { throw 'External WSTOP is not ReadOnly.' }
if ((Get-Item -LiteralPath $externalMarker -Force).LastWriteTimeUtc -le $maxPremarkerTime) { throw 'External WSTOP is not strictly later than premarker material.' }

[System.IO.File]::Move($externalMarker, $marker)

$markerInfo = Get-Item -LiteralPath $marker -Force
$postFiles = @(Get-ChildItem -LiteralPath $root -File -Recurse -Force)
$postDirs = @((Get-ChildItem -LiteralPath $root -Directory -Recurse -Force) + (Get-Item -LiteralPath $root -Force))
$postReadonlyFailures = @($postFiles + $postDirs | Where-Object { ((Get-Item -LiteralPath $_.FullName -Force).Attributes -band [System.IO.FileAttributes]::ReadOnly) -eq 0 })
$otherItems = @(
    (Get-Item -LiteralPath $root -Force)
    (Get-ChildItem -LiteralPath $root -Recurse -Force | Where-Object { $_.FullName -ne $marker })
)
$atOrAfter = @($otherItems | Where-Object { $_.LastWriteTimeUtc -ge $markerInfo.LastWriteTimeUtc })
$manifestRows = Import-Csv -LiteralPath $manifest
$manifestMismatches = @()
foreach ($row in $manifestRows) {
    $path = [System.IO.Path]::Combine($root, $row.RELATIVE_PATH)
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
        $manifestMismatches += 'MISSING:' + $row.RELATIVE_PATH
        continue
    }
    $file = Get-Item -LiteralPath $path -Force
    $hash = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToUpperInvariant()
    if ($file.Length.ToString([System.Globalization.CultureInfo]::InvariantCulture) -ne $row.BYTES -or $hash -ne $row.SHA256) {
        $manifestMismatches += 'MISMATCH:' + $row.RELATIVE_PATH
    }
}
$audit = [pscustomobject]@{
    HandoffId = 'A-R115-P126-SA2-R168-READONLY-20260828'
    Verdict = 'FAIL_TO_MAIN_SOURCE_SCOPE'
    Root = $root
    WstopExists = (Test-Path -LiteralPath $marker -PathType Leaf)
    WstopReadOnly = $markerInfo.IsReadOnly
    WstopLastWriteTimeUtc = $markerInfo.LastWriteTimeUtc.ToString('o')
    PremarkerManifestSha256 = $manifestHash
    PremarkerManifestRows = $manifestRows.Count
    FinalFileCount = $postFiles.Count
    FinalDirectoryCount = $postDirs.Count
    ReadOnlyFailureCount = $postReadonlyFailures.Count
    AtOrAfterOtherCount = $atOrAfter.Count
    ManifestMismatchCount = $manifestMismatches.Count
    ExternalStagingExists = (Test-Path -LiteralPath $externalMarker)
    PostmarkerContentWrites = 0
    PostmarkerAttributeWrites = 0
}
if (-not $audit.WstopExists -or -not $audit.WstopReadOnly -or $audit.ReadOnlyFailureCount -ne 0 -or $audit.AtOrAfterOtherCount -ne 0 -or $audit.ManifestMismatchCount -ne 0 -or $audit.ExternalStagingExists) {
    $audit | ConvertTo-Json -Depth 4
    throw 'Root-external read-only seal audit failed.'
}
$audit | ConvertTo-Json -Depth 4
