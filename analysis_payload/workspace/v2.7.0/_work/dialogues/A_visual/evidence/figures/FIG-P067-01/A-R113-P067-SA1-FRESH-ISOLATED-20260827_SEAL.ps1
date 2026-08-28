$ErrorActionPreference = 'Stop'

$EvidenceRoot = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P067-01\STRICT_R8_SA1_FRESH_ISOLATED_R113_20260827'
$ManifestPath = Join-Path $EvidenceRoot 'SEAL_MANIFEST.json'
$MarkerPath = Join-Path $EvidenceRoot 'WRITE_STOPPED'

if (-not (Test-Path -LiteralPath $EvidenceRoot -PathType Container)) {
    throw 'Evidence root is absent or not a directory.'
}
if (Test-Path -LiteralPath $ManifestPath) {
    throw 'Seal manifest already exists; refusing a second seal.'
}
if (Test-Path -LiteralPath $MarkerPath) {
    throw 'WRITE_STOPPED already exists; refusing a second seal.'
}
$ExpectedResult = 'SA1_PASS_READY_FOR_FRESH_ISOLATED_SA3'
$ActualResult = (Get-Content -LiteralPath (Join-Path $EvidenceRoot 'RESULT.txt') -Raw).Trim()
if ($ActualResult -cne $ExpectedResult) {
    throw "Unexpected RESULT: $ActualResult"
}

$PayloadFiles = @(Get-ChildItem -LiteralPath $EvidenceRoot -Recurse -File -Force | Sort-Object FullName)
$NamedStreams = @()
foreach ($File in $PayloadFiles) {
    $Streams = @(Get-Item -LiteralPath $File.FullName -Stream * -ErrorAction Stop)
    foreach ($Stream in $Streams) {
        if ($Stream.Stream -ne ':$DATA') {
            $NamedStreams += "$($File.FullName)::$($Stream.Stream)"
        }
    }
}
if ($NamedStreams.Count -ne 0) {
    throw "Named alternate data streams found: $($NamedStreams -join ', ')"
}

$ManifestFiles = foreach ($File in $PayloadFiles) {
    $Relative = [System.IO.Path]::GetRelativePath($EvidenceRoot, $File.FullName).Replace('\', '/')
    [ordered]@{
        relative_path = $Relative
        bytes = $File.Length
        sha256 = (Get-FileHash -LiteralPath $File.FullName -Algorithm SHA256).Hash
    }
}
$ManifestObject = [ordered]@{
    uid = 'FIG-P067-01'
    handoff_id = 'A-R113-P067-SA1-FRESH-ISOLATED-20260827'
    reviewer = '/root/p067_r113_fresh_sa1'
    evidence_root = $EvidenceRoot
    official_pdf_sha256 = '6B48D215721463EA2A9B94EFA54200F8D767B609E47714A70D9B441328F2BB9D'
    source_sha256 = '2881377AEEF78E8C7BD7502AD8A303E19AAC395F1936475BDC6D569195900920'
    payload_file_count_before_seal_controls = $PayloadFiles.Count
    files = @($ManifestFiles)
    planned_terminal_marker = 'WRITE_STOPPED'
    final_status = $ExpectedResult
}
$ManifestJson = $ManifestObject | ConvertTo-Json -Depth 8
[System.IO.File]::WriteAllText($ManifestPath, $ManifestJson + [Environment]::NewLine, [System.Text.UTF8Encoding]::new($false))

$PriorLatest = (Get-ChildItem -LiteralPath $EvidenceRoot -Recurse -File -Force | Measure-Object LastWriteTimeUtc -Maximum).Maximum
do {
    Start-Sleep -Milliseconds 50
} while ([DateTime]::UtcNow -le $PriorLatest)
$MarkerText = @(
    'WRITE_STOPPED'
    'UID=FIG-P067-01'
    'HANDOFF_ID=A-R113-P067-SA1-FRESH-ISOLATED-20260827'
    'STATUS=SA1_PASS_READY_FOR_FRESH_ISOLATED_SA3'
    "SEALED_UTC=$([DateTime]::UtcNow.ToString('o'))"
) -join [Environment]::NewLine
[System.IO.File]::WriteAllText($MarkerPath, $MarkerText + [Environment]::NewLine, [System.Text.UTF8Encoding]::new($false))

$FilesAfterMarker = @(Get-ChildItem -LiteralPath $EvidenceRoot -Recurse -File -Force)
$MarkerTime = (Get-Item -LiteralPath $MarkerPath -Force).LastWriteTimeUtc
$OtherTimes = @($FilesAfterMarker | Where-Object FullName -ne $MarkerPath | Select-Object -ExpandProperty LastWriteTimeUtc)
if ($OtherTimes.Count -gt 0 -and $MarkerTime -le (($OtherTimes | Measure-Object -Maximum).Maximum)) {
    throw 'WRITE_STOPPED is not strictly later than every other file; seal aborted before attribute freeze.'
}

foreach ($File in $FilesAfterMarker) {
    [System.IO.File]::SetAttributes($File.FullName, ($File.Attributes -bor [System.IO.FileAttributes]::ReadOnly))
}
$Directories = @(
    Get-ChildItem -LiteralPath $EvidenceRoot -Recurse -Directory -Force |
        Sort-Object { $_.FullName.Length } -Descending
)
foreach ($Directory in $Directories) {
    [System.IO.File]::SetAttributes($Directory.FullName, ($Directory.Attributes -bor [System.IO.FileAttributes]::ReadOnly))
}
$RootItem = Get-Item -LiteralPath $EvidenceRoot -Force
[System.IO.File]::SetAttributes($RootItem.FullName, ($RootItem.Attributes -bor [System.IO.FileAttributes]::ReadOnly))

[ordered]@{
    seal_result = 'SEALED_ONCE'
    evidence_root = $EvidenceRoot
    payload_file_count_before_seal_controls = $PayloadFiles.Count
    final_file_count = $FilesAfterMarker.Count
    directory_count_including_root = $Directories.Count + 1
    write_stopped_utc = $MarkerTime.ToString('o')
    no_root_writes_performed_after_root_attribute_freeze = $true
} | ConvertTo-Json -Depth 4

