param(
    [Parameter(Mandatory = $true)][string]$EvidenceRoot
)

$ErrorActionPreference = 'Stop'
$root = [IO.Path]::GetFullPath($EvidenceRoot)
$expected = [IO.Path]::GetFullPath('D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P049-01\STRICT_R4_SA2_R3_GUIDE1_DIRECT_BUILD_R110_20260827')
if ($root -ne $expected) { throw "Unexpected evidence root: $root" }
if (-not (Test-Path -LiteralPath $root -PathType Container)) { throw 'Evidence root is missing' }

$manifestCsv = Join-Path $root 'PAYLOAD_MANIFEST.csv'
$manifestJson = Join-Path $root 'PAYLOAD_MANIFEST.json'
$marker = Join-Path $root 'WRITE_STOPPED.json'
foreach ($control in @($manifestCsv, $manifestJson, $marker)) {
    if (Test-Path -LiteralPath $control) { throw "Control already exists: $control" }
}

$controls = @('PAYLOAD_MANIFEST.csv', 'PAYLOAD_MANIFEST.json', 'WRITE_STOPPED.json')
$payloadFiles = @(Get-ChildItem -LiteralPath $root -Recurse -File -Force | Where-Object {
    $relative = [IO.Path]::GetRelativePath($root, $_.FullName).Replace('\', '/')
    $relative -notin $controls
} | Sort-Object FullName)

$rows = foreach ($file in $payloadFiles) {
    [ordered]@{
        relative_path = [IO.Path]::GetRelativePath($root, $file.FullName).Replace('\', '/')
        bytes = [int64]$file.Length
        sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $file.FullName).Hash
        mtime_utc_ticks = $file.LastWriteTimeUtc.Ticks.ToString()
    }
}

$rows | Export-Csv -LiteralPath $manifestCsv -NoTypeInformation -Encoding utf8
$rows | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $manifestJson -Encoding utf8

$csvRows = @(Import-Csv -LiteralPath $manifestCsv)
$jsonRows = @(Get-Content -LiteralPath $manifestJson -Raw | ConvertFrom-Json)
if ($csvRows.Count -ne $rows.Count -or $jsonRows.Count -ne $rows.Count) { throw 'Manifest count mismatch before seal' }
for ($i = 0; $i -lt $rows.Count; $i++) {
    foreach ($field in @('relative_path', 'bytes', 'sha256', 'mtime_utc_ticks')) {
        if ($csvRows[$i].$field.ToString() -ne $jsonRows[$i].$field.ToString()) { throw "Manifest disagreement at row $i field $field" }
    }
}

$preMarkerFiles = @(Get-ChildItem -LiteralPath $root -Recurse -File -Force)
foreach ($file in $preMarkerFiles) { $file.IsReadOnly = $true }
$directories = @(Get-ChildItem -LiteralPath $root -Recurse -Directory -Force | Sort-Object FullName -Descending)
foreach ($directory in $directories) { $directory.Attributes = $directory.Attributes -bor [IO.FileAttributes]::ReadOnly }
(Get-Item -LiteralPath $root -Force).Attributes = (Get-Item -LiteralPath $root -Force).Attributes -bor [IO.FileAttributes]::ReadOnly

$maxTicks = ($preMarkerFiles | Measure-Object -Property LastWriteTimeUtc -Maximum).Maximum.Ticks
while ([DateTime]::UtcNow.Ticks -le $maxTicks) { Start-Sleep -Milliseconds 10 }

$markerData = [ordered]@{
    UID = 'FIG-P049-01'
    HANDOFF_ID = 'A-R110-P049-SA2-DIRECT-BUILD-R4-20260827'
    route = 'LOCAL_SA2_PASS_AWAIT_OFFICIAL_CANDIDATE_AND_FRESH_SA1'
    payload_file_count = $rows.Count
    manifest_control_file_count = 2
    write_stopped_control_file_count = 1
    control_file_count = 3
    ordinary_file_total = $rows.Count + 3
    payload_manifest_csv_sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $manifestCsv).Hash
    payload_manifest_json_sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $manifestJson).Hash
    declared_root_write_stopped = $true
    created_at_utc = [DateTime]::UtcNow.ToString('o')
}
$markerData | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $marker -Encoding utf8
(Get-Item -LiteralPath $marker -Force).IsReadOnly = $true

[pscustomobject]@{
    root = $root
    payload = $rows.Count
    controls = 3
    ordinary = $rows.Count + 3
    manifest_csv_sha256 = $markerData.payload_manifest_csv_sha256
    manifest_json_sha256 = $markerData.payload_manifest_json_sha256
    write_stopped_ticks = (Get-Item -LiteralPath $marker -Force).LastWriteTimeUtc.Ticks.ToString()
    max_pre_marker_ticks = $maxTicks.ToString()
    exit = 0
} | ConvertTo-Json -Depth 5
