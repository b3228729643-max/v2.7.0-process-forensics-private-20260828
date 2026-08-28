$ErrorActionPreference = 'Stop'

$EvidenceRoot = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P067-01\STRICT_R8_SA1_FRESH_ISOLATED_R113_20260827'
$ManifestPath = Join-Path $EvidenceRoot 'SEAL_MANIFEST.json'
$MarkerPath = Join-Path $EvidenceRoot 'WRITE_STOPPED'
$Errors = [System.Collections.Generic.List[string]]::new()

if (-not (Test-Path -LiteralPath $EvidenceRoot -PathType Container)) {
    $Errors.Add('root missing')
}
if (-not (Test-Path -LiteralPath $ManifestPath -PathType Leaf)) {
    $Errors.Add('seal manifest missing')
}
if (-not (Test-Path -LiteralPath $MarkerPath -PathType Leaf)) {
    $Errors.Add('WRITE_STOPPED missing')
}
if ($Errors.Count -gt 0) {
    throw ($Errors -join '; ')
}

$Manifest = Get-Content -LiteralPath $ManifestPath -Raw | ConvertFrom-Json
$Files = @(Get-ChildItem -LiteralPath $EvidenceRoot -Recurse -File -Force)
$Directories = @(Get-ChildItem -LiteralPath $EvidenceRoot -Recurse -Directory -Force)
$RootItem = Get-Item -LiteralPath $EvidenceRoot -Force

foreach ($Entry in $Manifest.files) {
    $Path = Join-Path $EvidenceRoot ($Entry.relative_path -replace '/', '\')
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        $Errors.Add("manifest file missing: $($Entry.relative_path)")
        continue
    }
    $Item = Get-Item -LiteralPath $Path -Force
    if ($Item.Length -ne [int64]$Entry.bytes) {
        $Errors.Add("size mismatch: $($Entry.relative_path)")
    }
    $Hash = (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash
    if ($Hash -cne [string]$Entry.sha256) {
        $Errors.Add("hash mismatch: $($Entry.relative_path)")
    }
}

$ExpectedFinalCount = [int]$Manifest.payload_file_count_before_seal_controls + 2
if ($Files.Count -ne $ExpectedFinalCount) {
    $Errors.Add("final file count mismatch: $($Files.Count) != $ExpectedFinalCount")
}
foreach ($File in $Files) {
    if (($File.Attributes -band [System.IO.FileAttributes]::ReadOnly) -eq 0) {
        $Errors.Add("file not ReadOnly: $($File.FullName)")
    }
    $Streams = @(Get-Item -LiteralPath $File.FullName -Stream * -ErrorAction Stop)
    foreach ($Stream in $Streams) {
        if ($Stream.Stream -ne ':$DATA') {
            $Errors.Add("named ADS: $($File.FullName)::$($Stream.Stream)")
        }
    }
}
foreach ($Directory in $Directories) {
    if (($Directory.Attributes -band [System.IO.FileAttributes]::ReadOnly) -eq 0) {
        $Errors.Add("directory not ReadOnly: $($Directory.FullName)")
    }
}
if (($RootItem.Attributes -band [System.IO.FileAttributes]::ReadOnly) -eq 0) {
    $Errors.Add('root directory not ReadOnly')
}

$Sorted = @($Files | Sort-Object LastWriteTimeUtc -Descending)
$Marker = Get-Item -LiteralPath $MarkerPath -Force
if ($Sorted[0].FullName -cne $Marker.FullName) {
    $Errors.Add('WRITE_STOPPED is not the latest file')
}
$TiedLatest = @($Files | Where-Object LastWriteTimeUtc -eq $Marker.LastWriteTimeUtc)
if ($TiedLatest.Count -ne 1) {
    $Errors.Add("WRITE_STOPPED latest timestamp is not unique: $($TiedLatest.Count)")
}
if ($Sorted.Count -gt 1 -and $Marker.LastWriteTimeUtc -le $Sorted[1].LastWriteTimeUtc) {
    $Errors.Add('WRITE_STOPPED is not strictly later than second-latest file')
}

$Result = (Get-Content -LiteralPath (Join-Path $EvidenceRoot 'RESULT.txt') -Raw).Trim()
if ($Result -cne 'SA1_PASS_READY_FOR_FRESH_ISOLATED_SA3') {
    $Errors.Add("RESULT mismatch: $Result")
}

$Audit = [ordered]@{
    audit_result = $(if ($Errors.Count -eq 0) { 'PASS' } else { 'FAIL' })
    uid = 'FIG-P067-01'
    handoff_id = 'A-R113-P067-SA1-FRESH-ISOLATED-20260827'
    evidence_root = $EvidenceRoot
    final_file_count = $Files.Count
    directory_count_including_root = $Directories.Count + 1
    readonly_file_count = @($Files | Where-Object { ($_.Attributes -band [System.IO.FileAttributes]::ReadOnly) -ne 0 }).Count
    readonly_directory_count_including_root = @($Directories | Where-Object { ($_.Attributes -band [System.IO.FileAttributes]::ReadOnly) -ne 0 }).Count + $(if (($RootItem.Attributes -band [System.IO.FileAttributes]::ReadOnly) -ne 0) { 1 } else { 0 })
    write_stopped_is_unique_strict_latest = ($Errors -notcontains 'WRITE_STOPPED is not the latest file') -and ($TiedLatest.Count -eq 1) -and ($Sorted.Count -le 1 -or $Marker.LastWriteTimeUtc -gt $Sorted[1].LastWriteTimeUtc)
    write_stopped_utc = $Marker.LastWriteTimeUtc.ToString('o')
    seal_manifest_sha256 = (Get-FileHash -LiteralPath $ManifestPath -Algorithm SHA256).Hash
    write_stopped_sha256 = (Get-FileHash -LiteralPath $MarkerPath -Algorithm SHA256).Hash
    result = $Result
    errors = @($Errors)
}
$Audit | ConvertTo-Json -Depth 6
if ($Errors.Count -ne 0) {
    exit 1
}
