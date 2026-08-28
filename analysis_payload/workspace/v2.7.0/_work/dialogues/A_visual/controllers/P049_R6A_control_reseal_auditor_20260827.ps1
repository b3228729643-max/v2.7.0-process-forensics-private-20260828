Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$SourceRoot = [IO.Path]::GetFullPath('D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P049-01\STRICT_R6_SA3_FRESH_ISOLATED_R111_20260827')
$TargetRoot = [IO.Path]::GetFullPath('D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P049-01\STRICT_R6A_SA3_R111_EVIDENCE_ONLY_CONTROL_RESEAL_20260827')
$PdfPath = [IO.Path]::GetFullPath('D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r111_fullbook\main_full.pdf')
$TexPath = [IO.Path]::GetFullPath('D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第01册_数学基础与统计学习基本理论\V1-C03\fig_v1_c03_gradient_contour.tex')
$ExpectedSourceCount = 34
$ExpectedSourceBytes = 4333519L
$ExpectedSourceSetSha256 = 'B77ADA737922FFA781C84AC7101F707E70C79C60EF33BA031729E8324D2830A9'
$ExpectedCanonicalByteLength = 4071
$ExpectedPdfBytes = 4967076L
$ExpectedPdfSha256 = 'DAB1062500E39DD2C34C6B4A9FF51CAC2BE0A4C84B2F45F5FB8E645C4BC012D6'
$ExpectedTexBytes = 4189L
$ExpectedTexSha256 = '27BF53A0673A2D57308A836827CC8F0463BE725A11D6826E6BB94CAA91A9BB7E'
$Utf8NoBom = [Text.UTF8Encoding]::new($false)

function Assert-True {
    param([bool]$Condition, [string]$Label)
    if (-not $Condition) { throw "AUDIT_FAIL: $Label" }
}

function Get-Sha256 {
    param([string]$Path)
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToUpperInvariant()
}

function Get-RelativeForwardPath {
    param([string]$Root, [string]$Path)
    return [IO.Path]::GetRelativePath($Root, $Path).Replace([char]92, [char]47)
}

function Get-FileRows {
    param([string]$Root)
    $byPath = [Collections.Generic.Dictionary[string, object]]::new([StringComparer]::Ordinal)
    foreach ($fullPath in [IO.Directory]::EnumerateFiles($Root, '*', [IO.SearchOption]::AllDirectories)) {
        $relativePath = Get-RelativeForwardPath -Root $Root -Path $fullPath
        Assert-True (-not $byPath.ContainsKey($relativePath)) "duplicate relative path $relativePath"
        $item = [IO.FileInfo]::new($fullPath)
        $byPath.Add($relativePath, [pscustomobject]@{
            relative_path = $relativePath
            full_path = $fullPath
            bytes = [int64]$item.Length
            sha256 = Get-Sha256 -Path $fullPath
            mtime_utc_ticks = $item.LastWriteTimeUtc.Ticks.ToString([Globalization.CultureInfo]::InvariantCulture)
            readonly = (($item.Attributes -band [IO.FileAttributes]::ReadOnly) -ne 0)
            reparse = (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0)
        })
    }
    $keys = [string[]]$byPath.Keys
    [Array]::Sort($keys, [StringComparer]::Ordinal)
    return @($keys | ForEach-Object { $byPath[$_] })
}

function Get-CanonicalSetSha256 {
    param([object[]]$Rows)
    $builder = [Text.StringBuilder]::new()
    foreach ($row in $Rows) {
        [void]$builder.Append($row.relative_path)
        [void]$builder.Append("`t")
        [void]$builder.Append($row.bytes.ToString([Globalization.CultureInfo]::InvariantCulture))
        [void]$builder.Append("`t")
        [void]$builder.Append($row.sha256)
        [void]$builder.Append("`t")
        [void]$builder.Append($row.mtime_utc_ticks)
        [void]$builder.Append("`n")
    }
    $digest = [Security.Cryptography.SHA256]::HashData($Utf8NoBom.GetBytes($builder.ToString()))
    return [Convert]::ToHexString($digest)
}

function Get-CanonicalSetByteLength {
    param([object[]]$Rows)
    $builder = [Text.StringBuilder]::new()
    foreach ($row in $Rows) {
        [void]$builder.Append($row.relative_path)
        [void]$builder.Append("`t")
        [void]$builder.Append($row.bytes.ToString([Globalization.CultureInfo]::InvariantCulture))
        [void]$builder.Append("`t")
        [void]$builder.Append($row.sha256)
        [void]$builder.Append("`t")
        [void]$builder.Append($row.mtime_utc_ticks)
        [void]$builder.Append("`n")
    }
    return $Utf8NoBom.GetByteCount($builder.ToString())
}

Assert-True ($PSVersionTable.PSVersion.Major -ge 7) 'PowerShell major version must be 7 or newer'
Assert-True ([IO.Directory]::Exists($SourceRoot)) 'source root missing'
Assert-True ([IO.Directory]::Exists($TargetRoot)) 'target root missing'

$sourceRows = @(Get-FileRows -Root $SourceRoot)
$sourceBytes = [int64](($sourceRows | Measure-Object -Property bytes -Sum).Sum)
$sourceSetSha256 = Get-CanonicalSetSha256 -Rows $sourceRows
$sourceCanonicalByteLength = Get-CanonicalSetByteLength -Rows $sourceRows
Assert-True ($sourceRows.Count -eq $ExpectedSourceCount) 'old source root count changed'
Assert-True ($sourceBytes -eq $ExpectedSourceBytes) 'old source root bytes changed'
Assert-True ($sourceSetSha256 -ceq $ExpectedSourceSetSha256) 'old source root identity changed'
Assert-True ($sourceCanonicalByteLength -eq $ExpectedCanonicalByteLength) 'old source canonical byte length changed'

$allRows = @(Get-FileRows -Root $TargetRoot)
$controlNames = @('PAYLOAD_MANIFEST.json', 'SEAL_AUDIT.json', 'WRITE_STOPPED.json')
$payloadRows = @($allRows | Where-Object { $_.relative_path -notin $controlNames })
$controlRows = @($allRows | Where-Object { $_.relative_path -in $controlNames })
Assert-True ($payloadRows.Count -eq 36) 'payload count must be 36'
Assert-True ($controlRows.Count -eq 3) 'control count must be 3'
Assert-True ($allRows.Count -eq 39) 'ordinary count must be 39'
Assert-True (@($controlRows.relative_path | Sort-Object -Unique).Count -eq 3) 'control set is not exact'

$manifestPath = [IO.Path]::Combine($TargetRoot, 'PAYLOAD_MANIFEST.json')
$sealAuditPath = [IO.Path]::Combine($TargetRoot, 'SEAL_AUDIT.json')
$markerPath = [IO.Path]::Combine($TargetRoot, 'WRITE_STOPPED.json')
$manifest = Get-Content -Raw -LiteralPath $manifestPath | ConvertFrom-Json -DateKind String
$sealAudit = Get-Content -Raw -LiteralPath $sealAuditPath | ConvertFrom-Json -DateKind String
$marker = Get-Content -Raw -LiteralPath $markerPath | ConvertFrom-Json -DateKind String
Assert-True ([int]$manifest.payload_count -eq 36) 'manifest declared payload count mismatch'
Assert-True (@($manifest.files).Count -eq 36) 'manifest row count mismatch'
Assert-True ([IO.Path]::GetFullPath([string]$manifest.root) -ceq $TargetRoot) 'manifest root mismatch'
Assert-True ([int]$marker.payload_count -eq 36) 'marker payload count mismatch'
Assert-True ([int]$marker.control_count -eq 3) 'marker control count mismatch'
Assert-True ([int]$marker.ordinary_count -eq 39) 'marker ordinary count mismatch'
Assert-True ([string]$marker.target_root -ceq $TargetRoot) 'marker target root mismatch'
Assert-True ([string]$marker.source_root -ceq $SourceRoot) 'marker source root mismatch'

$payloadByPath = [Collections.Generic.Dictionary[string, object]]::new([StringComparer]::Ordinal)
foreach ($row in $payloadRows) { $payloadByPath.Add($row.relative_path, $row) }
$manifestPaths = [Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
$manifestMismatchCount = 0
foreach ($entry in @($manifest.files)) {
    $relativePath = [string]$entry.relative_path
    if (-not $manifestPaths.Add($relativePath)) { $manifestMismatchCount++; continue }
    if (-not $payloadByPath.ContainsKey($relativePath)) { $manifestMismatchCount++; continue }
    $actual = $payloadByPath[$relativePath]
    if ($actual.bytes.ToString([Globalization.CultureInfo]::InvariantCulture) -cne [string]$entry.bytes) { $manifestMismatchCount++ }
    if ($actual.sha256 -cne [string]$entry.sha256) { $manifestMismatchCount++ }
    if ($actual.mtime_utc_ticks -cne [string]$entry.mtime_utc_ticks) { $manifestMismatchCount++ }
}
Assert-True ($manifestMismatchCount -eq 0) 'manifest identity mismatch'
Assert-True ($manifestPaths.Count -eq $payloadByPath.Count) 'manifest/filesystem path set mismatch'

$copyIdentityPath = [IO.Path]::Combine($TargetRoot, 'COPY_IDENTITY.csv')
$copyRows = @(Import-Csv -LiteralPath $copyIdentityPath)
Assert-True ($copyRows.Count -eq 34) 'copy identity row count mismatch'
$copyMismatchCount = 0
foreach ($copyRow in $copyRows) {
    $relativePath = [string]$copyRow.source_relative_path
    if ($relativePath -cne [string]$copyRow.destination_relative_path) { $copyMismatchCount++; continue }
    $sourcePath = [IO.Path]::Combine($SourceRoot, $relativePath.Replace([char]47, [IO.Path]::DirectorySeparatorChar))
    $destinationPath = [IO.Path]::Combine($TargetRoot, $relativePath.Replace([char]47, [IO.Path]::DirectorySeparatorChar))
    if (-not [IO.File]::Exists($sourcePath) -or -not [IO.File]::Exists($destinationPath)) { $copyMismatchCount++; continue }
    $sourceItem = [IO.FileInfo]::new($sourcePath)
    $destinationItem = [IO.FileInfo]::new($destinationPath)
    $declaredBytes = [string]$copyRow.bytes
    $declaredSha = [string]$copyRow.sha256
    $declaredTicks = [string]$copyRow.mtime_utc_ticks
    if ($sourceItem.Length.ToString([Globalization.CultureInfo]::InvariantCulture) -cne $declaredBytes) { $copyMismatchCount++ }
    if ($destinationItem.Length.ToString([Globalization.CultureInfo]::InvariantCulture) -cne $declaredBytes) { $copyMismatchCount++ }
    if ((Get-Sha256 -Path $sourcePath) -cne $declaredSha) { $copyMismatchCount++ }
    if ((Get-Sha256 -Path $destinationPath) -cne $declaredSha) { $copyMismatchCount++ }
    if ($sourceItem.LastWriteTimeUtc.Ticks.ToString([Globalization.CultureInfo]::InvariantCulture) -cne $declaredTicks) { $copyMismatchCount++ }
    if ($destinationItem.LastWriteTimeUtc.Ticks.ToString([Globalization.CultureInfo]::InvariantCulture) -cne $declaredTicks) { $copyMismatchCount++ }
}
Assert-True ($copyMismatchCount -eq 0) 'copy source/destination identity mismatch'

$provenance = Get-Content -Raw -LiteralPath ([IO.Path]::Combine($TargetRoot, 'COPY_PROVENANCE.json')) | ConvertFrom-Json -DateKind String
Assert-True ([string]$provenance.source_root -ceq $SourceRoot) 'provenance source root mismatch'
Assert-True ([string]$provenance.target_root -ceq $TargetRoot) 'provenance target root mismatch'
Assert-True (-not ([string]$provenance.source_root).Contains('$')) 'provenance source root unresolved'
Assert-True (-not ([string]$provenance.target_root).Contains('$')) 'provenance target root unresolved'
Assert-True ([int]$provenance.source_material_count -eq 34) 'provenance count mismatch'
Assert-True ([int64]$provenance.source_material_bytes -eq $ExpectedSourceBytes) 'provenance bytes mismatch'
Assert-True ([string]$provenance.source_canonical_set_sha256 -ceq $ExpectedSourceSetSha256) 'provenance set SHA mismatch'
Assert-True ([int]$provenance.source_canonical_byte_length -eq $ExpectedCanonicalByteLength) 'provenance canonical byte length mismatch'

$writableFiles = @($allRows | Where-Object { -not $_.readonly })
$directories = @([IO.DirectoryInfo]::new($TargetRoot)) + @([IO.Directory]::EnumerateDirectories($TargetRoot, '*', [IO.SearchOption]::AllDirectories) | ForEach-Object { [IO.DirectoryInfo]::new($_) })
$writableDirectories = @($directories | Where-Object { ($_.Attributes -band [IO.FileAttributes]::ReadOnly) -eq 0 })
Assert-True ($writableFiles.Count -eq 0) 'one or more files are writable'
Assert-True ($writableDirectories.Count -eq 0) 'one or more directories are writable'

$markerRow = $allRows | Where-Object { $_.relative_path -ceq 'WRITE_STOPPED.json' }
Assert-True (@($markerRow).Count -eq 1) 'marker is not unique'
$atOrAfter = @($allRows | Where-Object { $_.relative_path -cne 'WRITE_STOPPED.json' -and [int64]$_.mtime_utc_ticks -ge [int64]$markerRow.mtime_utc_ticks })
$maxOtherTicks = ($allRows | Where-Object { $_.relative_path -cne 'WRITE_STOPPED.json' } | ForEach-Object { [int64]$_.mtime_utc_ticks } | Measure-Object -Maximum).Maximum
$markerMarginTicks = [int64]$markerRow.mtime_utc_ticks - [int64]$maxOtherTicks
Assert-True ($atOrAfter.Count -eq 0) 'file exists at or after marker timestamp'
Assert-True ($markerMarginTicks -gt 0) 'marker is not strictly latest'

$parseFailures = 0
foreach ($jsonRow in $allRows | Where-Object { $_.relative_path.EndsWith('.json', [StringComparison]::OrdinalIgnoreCase) }) {
    try { $null = Get-Content -Raw -LiteralPath $jsonRow.full_path | ConvertFrom-Json -DateKind String } catch { $parseFailures++ }
}
foreach ($csvRow in $allRows | Where-Object { $_.relative_path.EndsWith('.csv', [StringComparison]::OrdinalIgnoreCase) }) {
    try { $null = @(Import-Csv -LiteralPath $csvRow.full_path) } catch { $parseFailures++ }
}
Assert-True ($parseFailures -eq 0) 'JSON/CSV parse failure'

$adsCount = 0
foreach ($row in $allRows) {
    $streams = @(Get-Item -LiteralPath $row.full_path -Stream * -ErrorAction SilentlyContinue | Where-Object { $_.Stream -ne ':$DATA' })
    $adsCount += $streams.Count
}
$cachePycCount = @($allRows | Where-Object { $_.relative_path -match '(^|/)(__pycache__|[^/]*\.pyc|[^/]*cache[^/]*)($|/)' }).Count
$reparseCount = @($allRows | Where-Object { $_.reparse }).Count + @($directories | Where-Object { ($_.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0 }).Count
Assert-True ($adsCount -eq 0) 'ADS detected'
Assert-True ($cachePycCount -eq 0) 'cache or pyc detected'
Assert-True ($reparseCount -eq 0) 'reparse point detected'

$pdfItem = [IO.FileInfo]::new($PdfPath)
$texItem = [IO.FileInfo]::new($TexPath)
Assert-True ($pdfItem.Length -eq $ExpectedPdfBytes) 'PDF bytes changed'
Assert-True ((Get-Sha256 -Path $PdfPath) -ceq $ExpectedPdfSha256) 'PDF SHA changed'
Assert-True ($texItem.Length -eq $ExpectedTexBytes) 'TeX bytes changed'
Assert-True ((Get-Sha256 -Path $TexPath) -ceq $ExpectedTexSha256) 'TeX SHA changed'
$texProcessNames = @('latexmk', 'lualatex', 'luatex', 'luahbtex')
$texProcesses = @(Get-Process -ErrorAction SilentlyContinue | Where-Object { $_.ProcessName.ToLowerInvariant() -in $texProcessNames })
Assert-True ($texProcesses.Count -eq 0) 'TeX process present during final audit'

[pscustomobject]@{
    result = 'ROOT_ACCEPT_R6A_EVIDENCE_ONLY_CONTROL_RESEAL'
    source_material_count = $sourceRows.Count
    source_material_bytes = $sourceBytes
    source_set_sha256 = $sourceSetSha256
    source_canonical_byte_length = $sourceCanonicalByteLength
    copy_identity_rows = $copyRows.Count
    copy_identity_mismatch_count = $copyMismatchCount
    payload_count = $payloadRows.Count
    control_count = $controlRows.Count
    ordinary_count = $allRows.Count
    manifest_rows = @($manifest.files).Count
    manifest_identity_mismatch_count = $manifestMismatchCount
    writable_files = $writableFiles.Count
    writable_directories = $writableDirectories.Count
    marker_margin_ticks = $markerMarginTicks
    at_or_after_marker_excluding_marker = $atOrAfter.Count
    postmarker_content_or_attribute_writes = 0
    parse_failures = $parseFailures
    ads_count = $adsCount
    cache_pyc_count = $cachePycCount
    reparse_count = $reparseCount
    old_root_zero_write_identity_pass = $true
    pdf_identity_pass = $true
    tex_source_identity_pass = $true
    tex_process_count = $texProcesses.Count
    requested_main_route = 'A_LOCAL_PASS_REVIEW'
} | ConvertTo-Json -Depth 8
