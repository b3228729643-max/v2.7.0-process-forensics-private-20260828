param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("Generate", "VerifyOnly")]
    [string]$Mode
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$R7Root = "D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\evidence\figures\FIG-P547-01\STRICT_R7_SA2_REPAIR_R97_LOCAL_20260824"
$SourcePath = "D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C01\fig_v5_c01_transition_graph.tex"
$AddendumRoot = $PSScriptRoot
$CsvPath = Join-Path $AddendumRoot "R7_OMITTED_LONGPATH_60.csv"
$SummaryPath = Join-Path $AddendumRoot "R7_LONGPATH_RECONCILIATION.json"

$ExpectedEvidenceHash = "9CDE425189C7149504C95DF4658B5572ED06EA2379CC6897178EC4E04AEE032E"
$ExpectedManifestHash = "E09227E2B66CE15F76891ADF7F943AB90402F27DF0CEADC37DECA2A2232A2C0F"
$ExpectedWriteStoppedHash = "01871051A57F9A64F0EE6D6935A41198D7350D74414EDB1B0A677643B8C4F80A"
$ExpectedSourceHash = "DF3D4415EDC56D02E056CAE0F3E38830DF28E781BC67ECDFB69863C5038F1600"
$Gen2Prefix = "superseded/GEN2_027EC3_AUDIT_ALGO_PRECHECK_20260824T162500/final_audit/low_profile_calibration/texmfvar/"
$Gen3Prefix = "superseded/GEN3_DF3D4415_C0114_MASK_PRECHECK_20260824T164500/final_audit/low_profile_calibration/texmfvar/"

function Assert-True {
    param([bool]$Condition, [string]$Message)
    if (-not $Condition) {
        throw "ASSERT_FAIL: $Message"
    }
}

function Convert-ToExtendedPath {
    param([string]$Path)
    $full = [System.IO.Path]::GetFullPath($Path)
    if ($full.StartsWith("\\", [System.StringComparison]::Ordinal)) {
        return "\\?\UNC\" + $full.Substring(2)
    }
    return "\\?\" + $full
}

function Get-Sha256Long {
    param([string]$Path)
    $extended = Convert-ToExtendedPath $Path
    $algorithm = [System.Security.Cryptography.SHA256]::Create()
    try {
        $stream = [System.IO.File]::Open(
            $extended,
            [System.IO.FileMode]::Open,
            [System.IO.FileAccess]::Read,
            [System.IO.FileShare]::Read
        )
        try {
            return [System.BitConverter]::ToString($algorithm.ComputeHash($stream)).Replace("-", "")
        }
        finally {
            $stream.Dispose()
        }
    }
    finally {
        $algorithm.Dispose()
    }
}

function Get-PathSetHash {
    param([string[]]$Paths)
    $sorted = @($Paths | Sort-Object)
    $text = [string]::Join([char]10, $sorted) + [char]10
    $bytes = [System.Text.UTF8Encoding]::new($false).GetBytes($text)
    $algorithm = [System.Security.Cryptography.SHA256]::Create()
    try {
        return [System.BitConverter]::ToString($algorithm.ComputeHash($bytes)).Replace("-", "")
    }
    finally {
        $algorithm.Dispose()
    }
}

function Write-NewUtf8Lines {
    param([string]$Path, [string[]]$Lines)
    $extended = Convert-ToExtendedPath $Path
    $stream = [System.IO.File]::Open(
        $extended,
        [System.IO.FileMode]::CreateNew,
        [System.IO.FileAccess]::Write,
        [System.IO.FileShare]::None
    )
    try {
        $writer = [System.IO.StreamWriter]::new($stream, [System.Text.UTF8Encoding]::new($false))
        try {
            foreach ($line in $Lines) {
                $writer.WriteLine($line)
            }
        }
        finally {
            $writer.Dispose()
        }
    }
    finally {
        $stream.Dispose()
    }
}

function Get-Reconciliation {
    $r7Extended = Convert-ToExtendedPath $R7Root
    $actualPaths = [System.Collections.Generic.List[string]]::new()
    $extendedByRelative = @{}
    foreach ($extendedPath in [System.IO.Directory]::EnumerateFiles(
        $r7Extended,
        "*",
        [System.IO.SearchOption]::AllDirectories
    )) {
        $normalPath = $extendedPath.Substring(4)
        $relative = [System.IO.Path]::GetRelativePath($R7Root, $normalPath).Replace("\", "/")
        [void]$actualPaths.Add($relative)
        $extendedByRelative[$relative] = $extendedPath
    }
    $actualPaths = @($actualPaths | Sort-Object)
    $actualSet = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::Ordinal)
    foreach ($relative in $actualPaths) {
        Assert-True ($actualSet.Add($relative)) "duplicate actual relative path: $relative"
    }

    $evidencePath = Join-Path $R7Root "evidence_manifest.json"
    $manifestPath = Join-Path $R7Root "MANIFEST.sha256"
    $writeStoppedPath = Join-Path $R7Root "WRITE_STOPPED.md"
    Assert-True ((Get-Sha256Long $evidencePath) -eq $ExpectedEvidenceHash) "R7 evidence_manifest hash"
    Assert-True ((Get-Sha256Long $manifestPath) -eq $ExpectedManifestHash) "R7 MANIFEST hash"
    Assert-True ((Get-Sha256Long $writeStoppedPath) -eq $ExpectedWriteStoppedHash) "R7 WRITE_STOPPED hash"
    Assert-True ((Get-Sha256Long $SourcePath) -eq $ExpectedSourceHash) "authorized source hash"

    $evidence = [System.IO.File]::ReadAllText(
        (Convert-ToExtendedPath $evidencePath),
        [System.Text.Encoding]::UTF8
    ) | ConvertFrom-Json
    $manifestLines = [System.IO.File]::ReadAllLines(
        (Convert-ToExtendedPath $manifestPath),
        [System.Text.Encoding]::UTF8
    )
    $manifestMap = @{}
    $manifestDuplicatePathCount = 0
    $manifestParseFailureCount = 0
    foreach ($line in $manifestLines) {
        $match = [regex]::Match($line, "^(?<hash>[A-Fa-f0-9]{64})  (?<path>.+)$")
        if (-not $match.Success) {
            $manifestParseFailureCount++
            continue
        }
        $relative = $match.Groups["path"].Value
        if ($manifestMap.ContainsKey($relative)) {
            $manifestDuplicatePathCount++
        }
        else {
            $manifestMap[$relative] = $match.Groups["hash"].Value.ToUpperInvariant()
        }
    }

    $manifestMissingReferenceCount = 0
    $manifestHashMismatchCount = 0
    foreach ($relative in $manifestMap.Keys) {
        $normalPath = Join-Path $R7Root ($relative.Replace("/", "\"))
        $extendedPath = Convert-ToExtendedPath $normalPath
        if (-not [System.IO.File]::Exists($extendedPath)) {
            $manifestMissingReferenceCount++
            continue
        }
        if ((Get-Sha256Long $normalPath) -ne $manifestMap[$relative]) {
            $manifestHashMismatchCount++
        }
    }

    $evidencePathSet = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::Ordinal)
    $evidenceDuplicatePathCount = 0
    $evidenceToManifestHashMismatchCount = 0
    foreach ($entry in $evidence.entries) {
        $relative = [string]$entry.path
        if (-not $evidencePathSet.Add($relative)) {
            $evidenceDuplicatePathCount++
        }
        if (-not $manifestMap.ContainsKey($relative)) {
            $evidenceToManifestHashMismatchCount++
        }
        elseif ($manifestMap[$relative] -ne ([string]$entry.sha256).ToUpperInvariant()) {
            $evidenceToManifestHashMismatchCount++
        }
    }

    $coveredSet = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::Ordinal)
    foreach ($relative in $manifestMap.Keys) {
        [void]$coveredSet.Add($relative)
    }
    [void]$coveredSet.Add("MANIFEST.sha256")
    [void]$coveredSet.Add("WRITE_STOPPED.md")

    $missing = @($actualPaths | Where-Object { -not $coveredSet.Contains($_) } | Sort-Object)
    $stale = @($coveredSet | Where-Object { -not $actualSet.Contains($_) } | Sort-Object)
    $unexpectedMissing = @($missing | Where-Object {
        -not $_.StartsWith($Gen2Prefix, [System.StringComparison]::Ordinal) -and
        -not $_.StartsWith($Gen3Prefix, [System.StringComparison]::Ordinal)
    })
    $activeMissing = @($missing | Where-Object {
        -not $_.StartsWith("superseded/", [System.StringComparison]::Ordinal)
    })

    $writeStoppedLastWriteUtc = [System.IO.File]::GetLastWriteTimeUtc(
        (Convert-ToExtendedPath $writeStoppedPath)
    )
    $allPostWrite = [System.Collections.Generic.List[string]]::new()
    $allPostCreation = [System.Collections.Generic.List[string]]::new()
    foreach ($relative in $actualPaths) {
        $extendedPath = $extendedByRelative[$relative]
        if ([System.IO.File]::GetLastWriteTimeUtc($extendedPath) -gt $writeStoppedLastWriteUtc) {
            [void]$allPostWrite.Add($relative)
        }
        if ([System.IO.File]::GetCreationTimeUtc($extendedPath) -gt $writeStoppedLastWriteUtc) {
            [void]$allPostCreation.Add($relative)
        }
    }

    $records = [System.Collections.Generic.List[object]]::new()
    foreach ($relative in $missing) {
        $extendedPath = $extendedByRelative[$relative]
        $normalPath = $extendedPath.Substring(4)
        $info = [System.IO.FileInfo]::new($extendedPath)
        $info.Refresh()
        $creationUtc = [System.IO.File]::GetCreationTimeUtc($extendedPath)
        $lastWriteUtc = [System.IO.File]::GetLastWriteTimeUtc($extendedPath)
        $generation = if ($relative.StartsWith($Gen2Prefix, [System.StringComparison]::Ordinal)) {
            "GEN2_SUPERSEDED"
        }
        else {
            "GEN3_SUPERSEDED"
        }
        [void]$records.Add([pscustomobject]@{
            relative_path = $relative
            bytes = $info.Length
            sha256 = Get-Sha256Long $normalPath
            creation_time_local = $creationUtc.ToLocalTime().ToString("o")
            creation_time_utc = $creationUtc.ToString("o")
            last_write_time_local = $lastWriteUtc.ToLocalTime().ToString("o")
            last_write_time_utc = $lastWriteUtc.ToString("o")
            classification = "SUPERSEDED_EXCLUDED_FROM_ACCEPTANCE"
            generation = $generation
            r7_manifest_covered = "NO"
            written_after_r7_write_stopped = if ($lastWriteUtc -gt $writeStoppedLastWriteUtc) { "YES" } else { "NO" }
        })
    }

    Assert-True ($actualPaths.Count -eq 6732) "R7 actual file count"
    Assert-True ($actualSet.Count -eq 6732) "R7 unique path count"
    Assert-True ($evidence.entries.Count -eq 6669) "R7 evidence payload count"
    Assert-True ($manifestLines.Count -eq 6670) "R7 manifest line count"
    Assert-True ($manifestMap.Count -eq 6670) "R7 manifest unique path count"
    Assert-True ($coveredSet.Count -eq 6672) "R7 covered union count"
    Assert-True ($missing.Count -eq 60) "R7 omitted count"
    Assert-True ($stale.Count -eq 0) "R7 stale covered path count"
    Assert-True ($unexpectedMissing.Count -eq 0) "omission outside two exact texmfvar prefixes"
    Assert-True ($activeMissing.Count -eq 0) "active omission count"
    Assert-True (@($missing | Where-Object { $_.StartsWith($Gen2Prefix, [System.StringComparison]::Ordinal) }).Count -eq 30) "GEN2 omitted count"
    Assert-True (@($missing | Where-Object { $_.StartsWith($Gen3Prefix, [System.StringComparison]::Ordinal) }).Count -eq 30) "GEN3 omitted count"
    Assert-True ($manifestParseFailureCount -eq 0) "R7 manifest parse failures"
    Assert-True ($manifestDuplicatePathCount -eq 0) "R7 manifest duplicate paths"
    Assert-True ($manifestMissingReferenceCount -eq 0) "R7 manifest missing references"
    Assert-True ($manifestHashMismatchCount -eq 0) "R7 manifest hash mismatches"
    Assert-True ($evidenceDuplicatePathCount -eq 0) "R7 evidence duplicate paths"
    Assert-True ($evidenceToManifestHashMismatchCount -eq 0) "R7 evidence-to-manifest mismatch"
    Assert-True ($allPostWrite.Count -eq 0) "R7 files written after WRITE_STOPPED"
    Assert-True ($allPostCreation.Count -eq 0) "R7 files created after WRITE_STOPPED"
    Assert-True (@($records | Where-Object { $_.written_after_r7_write_stopped -eq "YES" }).Count -eq 0) "omitted files written after WRITE_STOPPED"

    $creationUtcValues = @($records | ForEach-Object { [datetimeoffset]::Parse($_.creation_time_utc).UtcDateTime })
    $lastWriteUtcValues = @($records | ForEach-Object { [datetimeoffset]::Parse($_.last_write_time_utc).UtcDateTime })
    $summary = [ordered]@{
        schema = "FIG-P547-01_R7A_LONGPATH_RECONCILIATION_V1"
        generated_utc = [datetime]::UtcNow.ToString("o")
        r7_root = $R7Root
        enumeration_engine = "System.IO.Directory.EnumerateFiles with Win32 extended path prefix"
        bound_identity = [ordered]@{
            r7_evidence_manifest_sha256 = $ExpectedEvidenceHash
            r7_manifest_sha256 = $ExpectedManifestHash
            r7_write_stopped_sha256 = $ExpectedWriteStoppedHash
            authorized_source_sha256 = $ExpectedSourceHash
        }
        r7_set_reconciliation = [ordered]@{
            actual_file_count = $actualPaths.Count
            actual_unique_relative_path_count = $actualSet.Count
            evidence_manifest_payload_count = $evidence.entries.Count
            manifest_line_count = $manifestLines.Count
            manifest_unique_path_count = $manifestMap.Count
            covered_union_count_including_manifest_self_and_write_stopped = $coveredSet.Count
            omitted_count = $missing.Count
            stale_covered_path_count = $stale.Count
            closure_equation = "6672 covered + 60 omitted = 6732 actual"
            actual_pathset_sha256 = Get-PathSetHash $actualPaths
            covered_pathset_sha256 = Get-PathSetHash @($coveredSet)
            omitted_pathset_sha256 = Get-PathSetHash $missing
        }
        omission_classification = [ordered]@{
            gen2_superseded_texmfvar_count = @($missing | Where-Object { $_.StartsWith($Gen2Prefix, [System.StringComparison]::Ordinal) }).Count
            gen3_superseded_texmfvar_count = @($missing | Where-Object { $_.StartsWith($Gen3Prefix, [System.StringComparison]::Ordinal) }).Count
            superseded_count = @($missing | Where-Object { $_.StartsWith("superseded/", [System.StringComparison]::Ordinal) }).Count
            active_count = $activeMissing.Count
            outside_exact_expected_prefix_count = $unexpectedMissing.Count
            omitted_total_bytes = ($records | Measure-Object -Property bytes -Sum).Sum
            creation_time_utc_min = ($creationUtcValues | Measure-Object -Minimum).Minimum.ToUniversalTime().ToString("o")
            creation_time_utc_max = ($creationUtcValues | Measure-Object -Maximum).Maximum.ToUniversalTime().ToString("o")
            last_write_time_utc_min = ($lastWriteUtcValues | Measure-Object -Minimum).Minimum.ToUniversalTime().ToString("o")
            last_write_time_utc_max = ($lastWriteUtcValues | Measure-Object -Maximum).Maximum.ToUniversalTime().ToString("o")
        }
        r7_seal_temporal_integrity = [ordered]@{
            r7_write_stopped_last_write_utc = $writeStoppedLastWriteUtc.ToString("o")
            files_last_written_after_write_stopped = $allPostWrite.Count
            files_created_after_write_stopped = $allPostCreation.Count
            omitted_files_last_written_after_write_stopped = @($records | Where-Object { $_.written_after_r7_write_stopped -eq "YES" }).Count
        }
        r7_declared_manifest_verification = [ordered]@{
            parsed_rows = $manifestLines.Count
            parse_failures = $manifestParseFailureCount
            duplicate_paths = $manifestDuplicatePathCount
            missing_references = $manifestMissingReferenceCount
            sha256_mismatches = $manifestHashMismatchCount
            evidence_duplicate_paths = $evidenceDuplicatePathCount
            evidence_to_manifest_hash_mismatches = $evidenceToManifestHashMismatchCount
        }
        correction = [ordered]@{
            incorrect_r7_claim = "all superseded files were hash-covered"
            corrected_claim = "60 pre-seal superseded texmfvar cache files were omitted by R7 manifests and are exhaustively bound by this addendum"
            active_acceptance_evidence_omitted = 0
            local_recommendation = "LOCAL_PASS_TO_ROOT_BUILD"
            local_recommendation_changed = $false
        }
        decision = "PASS_EXACT_60_LONGPATH_GAP_BOUND"
    }
    return [pscustomobject]@{
        Records = @($records)
        Summary = $summary
    }
}

$result = Get-Reconciliation
if ($Mode -eq "Generate") {
    Assert-True (-not [System.IO.File]::Exists((Convert-ToExtendedPath $CsvPath))) "CSV already exists"
    Assert-True (-not [System.IO.File]::Exists((Convert-ToExtendedPath $SummaryPath))) "summary already exists"
    $csvLines = @($result.Records | ConvertTo-Csv -NoTypeInformation)
    Write-NewUtf8Lines -Path $CsvPath -Lines $csvLines
    $summaryText = ($result.Summary | ConvertTo-Json -Depth 12) + [Environment]::NewLine
    Write-NewUtf8Lines -Path $SummaryPath -Lines @($summaryText.TrimEnd([char]13, [char]10))
}
else {
    Assert-True ([System.IO.File]::Exists((Convert-ToExtendedPath $CsvPath))) "CSV missing"
    Assert-True ([System.IO.File]::Exists((Convert-ToExtendedPath $SummaryPath))) "summary missing"
    $savedRows = @(Import-Csv -LiteralPath $CsvPath)
    $savedSummary = Get-Content -LiteralPath $SummaryPath -Raw | ConvertFrom-Json
    Assert-True ($savedRows.Count -eq 60) "saved CSV row count"
    Assert-True ($savedSummary.decision -eq "PASS_EXACT_60_LONGPATH_GAP_BOUND") "saved summary decision"
    foreach ($current in $result.Records) {
        $saved = @($savedRows | Where-Object { $_.relative_path -eq $current.relative_path })
        Assert-True ($saved.Count -eq 1) "saved row identity: $($current.relative_path)"
        Assert-True ($saved[0].sha256 -eq $current.sha256) "saved row hash: $($current.relative_path)"
        Assert-True ([long]$saved[0].bytes -eq [long]$current.bytes) "saved row bytes: $($current.relative_path)"
        Assert-True ($saved[0].creation_time_utc -eq $current.creation_time_utc) "saved row creation: $($current.relative_path)"
        Assert-True ($saved[0].last_write_time_utc -eq $current.last_write_time_utc) "saved row write: $($current.relative_path)"
    }
}

[pscustomobject]@{
    mode = $Mode
    decision = $result.Summary.decision
    actual_r7_files = $result.Summary.r7_set_reconciliation.actual_file_count
    covered = $result.Summary.r7_set_reconciliation.covered_union_count_including_manifest_self_and_write_stopped
    omitted = $result.Summary.r7_set_reconciliation.omitted_count
    active_omitted = $result.Summary.omission_classification.active_count
    post_write_stopped = $result.Summary.r7_seal_temporal_integrity.files_last_written_after_write_stopped
    r7_manifest_hash_mismatches = $result.Summary.r7_declared_manifest_verification.sha256_mismatches
} | ConvertTo-Json -Compress
