$ErrorActionPreference = 'Stop'

$root = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P640-01\sa1_r105_fresh_isolated_v2_main_replacement_20260826'
$report = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\reports\FIG-P640-01-SA1-R105-FRESH-ISOLATED-MAIN-REPLACEMENT-20260826.md'
$handoff = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\handoff\C\FIG-P640-01-SA1-R105-FRESH-ISOLATED-MAIN-REPLACEMENT-20260826.md'
$manifestPath = Join-Path $root 'seal\manifest.json'
$closurePath = Join-Path $root 'seal\closure.json'
$wstopPath = Join-Path $root 'seal\WSTOP'

foreach ($path in @($manifestPath, $closurePath, $wstopPath)) {
    if (Test-Path -LiteralPath $path) {
        throw "Refusing a second seal: $path already exists"
    }
}

$cacheEntries = @(Get-ChildItem -LiteralPath $root -Recurse -Force | Where-Object {
    $_.Name -eq '__pycache__' -or $_.Extension -eq '.pyc' -or $_.Name -eq '.cache'
})
if ($cacheEntries.Count -ne 0) {
    throw "Cache gate failed: $($cacheEntries.Count) entries"
}

$alternateStreams = @(Get-ChildItem -LiteralPath $root -Recurse -File | ForEach-Object {
    Get-Item -LiteralPath $_.FullName -Stream *
} | Where-Object { $_.Stream -ne ':$DATA' })
if ($alternateStreams.Count -ne 0) {
    throw "ADS gate failed: $($alternateStreams.Count) alternate streams"
}

$files = @(Get-ChildItem -LiteralPath $root -Recurse -File | Where-Object {
    -not $_.FullName.StartsWith((Join-Path $root 'seal') + '\', [System.StringComparison]::OrdinalIgnoreCase)
} | Sort-Object FullName)

$entries = @($files | ForEach-Object {
    [ordered]@{
        path = $_.FullName.Substring($root.Length + 1).Replace('\', '/')
        bytes = $_.Length
        sha256 = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToUpperInvariant()
    }
})

$external = @($report, $handoff | ForEach-Object {
    $item = Get-Item -LiteralPath $_
    [ordered]@{
        path = $item.FullName
        bytes = $item.Length
        sha256 = (Get-FileHash -LiteralPath $item.FullName -Algorithm SHA256).Hash.ToUpperInvariant()
    }
})

$sealedAt = (Get-Date).ToUniversalTime().ToString('o')
$manifest = [ordered]@{
    schema = 'FIG-P640-01-R105-SA1-FRESH-ISOLATED-SEAL-v1'
    handoff_id = 'MAIN-R105-P640-SA1-FRESH-ISOLATED-REPLACEMENT-20260826'
    result = 'FAIL_TO_SA2'
    sealed_at_utc = $sealedAt
    evidence_root = $root
    official_pdf_sha256 = 'F86E89047BA09FEA72FD8F79BF524A04DA367BFF3057806A879106A1032626A1'
    physical_page_1based = 690
    manifest_scope = 'All pre-seal ordinary files under evidence root; seal directory excluded to avoid self-hash recursion.'
    file_count = $entries.Count
    total_bytes = ($entries | Measure-Object -Property bytes -Sum).Sum
    files = $entries
    external_deliverables = $external
}
$manifest | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $manifestPath -Encoding utf8

@(
    'WSTOP'
    'RESULT=FAIL_TO_SA2'
    'HANDOFF_ID=MAIN-R105-P640-SA1-FRESH-ISOLATED-REPLACEMENT-20260826'
    "SEALED_AT_UTC=$sealedAt"
) | Set-Content -LiteralPath $wstopPath -Encoding utf8

$closure = [ordered]@{
    result = 'FAIL_TO_SA2'
    sealed_at_utc = $sealedAt
    manifest_file_count = $entries.Count
    manifest_total_bytes = ($entries | Measure-Object -Property bytes -Sum).Sum
    cache_entry_count = 0
    alternate_stream_count = 0
    expected_unordered_pairs = 31878
    actual_unordered_pairs = 31878
    hard_fail_pair_count = 1
    wstop_present = $true
    readonly_applied_after_this_write = $true
    second_seal_forbidden = $true
}
$closure | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $closurePath -Encoding utf8

Get-ChildItem -LiteralPath $root -Recurse -File | ForEach-Object { $_.IsReadOnly = $true }
foreach ($path in @($report, $handoff)) { (Get-Item -LiteralPath $path).IsReadOnly = $true }
Get-ChildItem -LiteralPath $root -Recurse -Directory | ForEach-Object {
    $_.Attributes = $_.Attributes -bor [System.IO.FileAttributes]::ReadOnly
}
(Get-Item -LiteralPath $root).Attributes = (Get-Item -LiteralPath $root).Attributes -bor [System.IO.FileAttributes]::ReadOnly

[pscustomobject]@{
    Result = 'FAIL_TO_SA2'
    ManifestFileCount = $entries.Count
    ManifestTotalBytes = ($entries | Measure-Object -Property bytes -Sum).Sum
    AlternateStreams = 0
    CacheEntries = 0
    WSTOP = (Test-Path -LiteralPath $wstopPath)
}
