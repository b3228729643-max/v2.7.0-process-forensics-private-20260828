param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("CheckOnly", "Seal")]
    [string]$Mode
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$AddendumRoot = $PSScriptRoot
$EvidenceManifestPath = Join-Path $AddendumRoot "evidence_manifest.json"
$HashManifestPath = Join-Path $AddendumRoot "MANIFEST.sha256"
$WriteStoppedPath = Join-Path $AddendumRoot "WRITE_STOPPED.md"
$Excluded = @("evidence_manifest.json", "MANIFEST.sha256", "WRITE_STOPPED.md")
$ExpectedPayload = @(
    "ADDENDUM_REPORT.md",
    "ADDENDUM_TERMINAL.md",
    "R7_LONGPATH_RECONCILIATION.json",
    "R7_OMITTED_LONGPATH_60.csv",
    "enumerate_r7_longpath_gap.ps1",
    "seal_r7a_addendum.ps1"
)
$ExpectedR7EvidenceHash = "9CDE425189C7149504C95DF4658B5572ED06EA2379CC6897178EC4E04AEE032E"
$ExpectedR7ManifestHash = "E09227E2B66CE15F76891ADF7F943AB90402F27DF0CEADC37DECA2A2232A2C0F"
$ExpectedR7WriteStoppedHash = "01871051A57F9A64F0EE6D6935A41198D7350D74414EDB1B0A677643B8C4F80A"
$ExpectedSourceHash = "DF3D4415EDC56D02E056CAE0F3E38830DF28E781BC67ECDFB69863C5038F1600"

function Assert-True {
    param([bool]$Condition, [string]$Message)
    if (-not $Condition) {
        throw "ASSERT_FAIL: $Message"
    }
}

function Get-Sha256 {
    param([string]$Path)
    $algorithm = [System.Security.Cryptography.SHA256]::Create()
    try {
        $stream = [System.IO.File]::Open(
            $Path,
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

function Write-NewUtf8 {
    param([string]$Path, [string]$Text)
    $stream = [System.IO.File]::Open(
        $Path,
        [System.IO.FileMode]::CreateNew,
        [System.IO.FileAccess]::Write,
        [System.IO.FileShare]::None
    )
    try {
        $writer = [System.IO.StreamWriter]::new($stream, [System.Text.UTF8Encoding]::new($false))
        try {
            $writer.Write($Text)
        }
        finally {
            $writer.Dispose()
        }
    }
    finally {
        $stream.Dispose()
    }
}

foreach ($sealFile in @($EvidenceManifestPath, $HashManifestPath, $WriteStoppedPath)) {
    Assert-True (-not [System.IO.File]::Exists($sealFile)) "seal file already exists: $sealFile"
}

$actualPayload = @(
    [System.IO.Directory]::EnumerateFiles(
        $AddendumRoot,
        "*",
        [System.IO.SearchOption]::AllDirectories
    ) | ForEach-Object {
        [System.IO.Path]::GetRelativePath($AddendumRoot, $_).Replace("\", "/")
    } | Where-Object { $_ -notin $Excluded } | Sort-Object
)
Assert-True ($actualPayload.Count -eq 6) "payload count"
Assert-True (@(Compare-Object -ReferenceObject $ExpectedPayload -DifferenceObject $actualPayload).Count -eq 0) "payload path set"

$entries = [System.Collections.Generic.List[object]]::new()
foreach ($relative in $actualPayload) {
    $path = Join-Path $AddendumRoot ($relative.Replace("/", "\"))
    $info = [System.IO.FileInfo]::new($path)
    $info.Refresh()
    Assert-True ($info.Length -gt 0) "zero-byte payload: $relative"
    [void]$entries.Add([ordered]@{
        path = $relative
        bytes = $info.Length
        sha256 = Get-Sha256 $path
        classification = "ACTIVE_ADDENDUM_EVIDENCE"
    })
}

$summary = Get-Content -LiteralPath (Join-Path $AddendumRoot "R7_LONGPATH_RECONCILIATION.json") -Raw | ConvertFrom-Json
$omitted = @(Import-Csv -LiteralPath (Join-Path $AddendumRoot "R7_OMITTED_LONGPATH_60.csv"))
$terminal = Get-Content -LiteralPath (Join-Path $AddendumRoot "ADDENDUM_TERMINAL.md") -Raw
Assert-True ($summary.decision -eq "PASS_EXACT_60_LONGPATH_GAP_BOUND") "summary decision"
Assert-True ($summary.r7_set_reconciliation.actual_file_count -eq 6732) "R7 actual count"
Assert-True ($summary.r7_set_reconciliation.covered_union_count_including_manifest_self_and_write_stopped -eq 6672) "R7 covered count"
Assert-True ($summary.r7_set_reconciliation.omitted_count -eq 60) "R7 omitted count"
Assert-True ($summary.omission_classification.active_count -eq 0) "active omission"
Assert-True ($summary.r7_seal_temporal_integrity.files_last_written_after_write_stopped -eq 0) "post-WSTOP write"
Assert-True ($summary.r7_declared_manifest_verification.sha256_mismatches -eq 0) "R7 manifest hash mismatch"
Assert-True ($summary.bound_identity.r7_evidence_manifest_sha256 -eq $ExpectedR7EvidenceHash) "bound R7 evidence hash"
Assert-True ($summary.bound_identity.r7_manifest_sha256 -eq $ExpectedR7ManifestHash) "bound R7 manifest hash"
Assert-True ($summary.bound_identity.r7_write_stopped_sha256 -eq $ExpectedR7WriteStoppedHash) "bound R7 WSTOP hash"
Assert-True ($summary.bound_identity.authorized_source_sha256 -eq $ExpectedSourceHash) "bound source hash"
Assert-True ($omitted.Count -eq 60) "omitted CSV row count"
Assert-True (@($omitted | Where-Object { $_.classification -ne "SUPERSEDED_EXCLUDED_FROM_ACCEPTANCE" }).Count -eq 0) "omitted classification"
Assert-True (@($omitted | Where-Object { $_.written_after_r7_write_stopped -ne "NO" }).Count -eq 0) "omitted post-WSTOP"
Assert-True ($terminal.Contains("LOCAL_PASS_TO_ROOT_BUILD")) "terminal recommendation"
Assert-True ($terminal.Contains("FINAL_OFFICIAL_PASS: false")) "terminal official-pass boundary"

if ($Mode -eq "CheckOnly") {
    [pscustomobject]@{
        check = "PASS"
        payload_entry_count = $entries.Count
        expected_final_actual_file_count = 9
        zero_byte_count = 0
        r7_gap_count = 60
        active_gap_count = 0
    } | ConvertTo-Json -Compress
    exit 0
}

$generatedUtc = [datetime]::UtcNow.ToString("o")
$evidenceManifest = [ordered]@{
    schema = "FIG-P547-01_R7A_ADDENDUM_EVIDENCE_MANIFEST_V1"
    terminal = "LOCAL_PASS_TO_ROOT_BUILD"
    final_official_pass = $false
    generated_utc = $generatedUtc
    package_root = $AddendumRoot
    payload_entry_count = $entries.Count
    expected_final_actual_file_count = 9
    closure_equation = "6 payload + 1 evidence_manifest + 1 MANIFEST + 1 WRITE_STOPPED = 9 actual"
    entries = @($entries)
    seal_exclusions = [ordered]@{
        evidence_manifest_json = "self"
        manifest_sha256 = "written after evidence manifest and cannot hash itself"
        write_stopped_md = "future final write"
    }
}
$evidenceText = ($evidenceManifest | ConvertTo-Json -Depth 10) + [Environment]::NewLine
Write-NewUtf8 -Path $EvidenceManifestPath -Text $evidenceText

$manifestEntries = [System.Collections.Generic.List[object]]::new()
foreach ($entry in $entries) {
    [void]$manifestEntries.Add($entry)
}
$evidenceInfo = [System.IO.FileInfo]::new($EvidenceManifestPath)
$evidenceInfo.Refresh()
[void]$manifestEntries.Add([ordered]@{
    path = "evidence_manifest.json"
    bytes = $evidenceInfo.Length
    sha256 = Get-Sha256 $EvidenceManifestPath
    classification = "ACTIVE_ADDENDUM_EVIDENCE"
})
$manifestEntries = @($manifestEntries | Sort-Object { $_.path })
$manifestText = [string]::Join(
    [char]10,
    @($manifestEntries | ForEach-Object { "$($_.sha256)  $($_.path)" })
) + [char]10
Write-NewUtf8 -Path $HashManifestPath -Text $manifestText

$manifestLines = [System.IO.File]::ReadAllLines($HashManifestPath, [System.Text.Encoding]::UTF8)
Assert-True ($manifestLines.Count -eq 7) "addendum manifest line count"
$manifestMismatch = 0
foreach ($line in $manifestLines) {
    $match = [regex]::Match($line, "^(?<hash>[A-Fa-f0-9]{64})  (?<path>.+)$")
    Assert-True $match.Success "addendum manifest line parse"
    $relative = $match.Groups["path"].Value
    $path = Join-Path $AddendumRoot ($relative.Replace("/", "\"))
    if ((Get-Sha256 $path) -ne $match.Groups["hash"].Value.ToUpperInvariant()) {
        $manifestMismatch++
    }
}
Assert-True ($manifestMismatch -eq 0) "addendum manifest per-entry verification"

$manifestHash = Get-Sha256 $HashManifestPath
$evidenceHash = Get-Sha256 $EvidenceManifestPath
$writeStoppedText = @(
    "# WRITE_STOPPED"
    ""
    "ADDENDUM_RESULT=PASS_EXACT_60_LONGPATH_GAP_BOUND"
    "RESULT=LOCAL_PASS_TO_ROOT_BUILD"
    "FINAL_OFFICIAL_PASS=false"
    "R7_ACTUAL_FILE_COUNT=6732"
    "R7_COVERED_UNION_COUNT=6672"
    "R7_OMITTED_LONGPATH_COUNT=60"
    "R7_ACTIVE_OMISSION_COUNT=0"
    "R7_FILES_WRITTEN_AFTER_WRITE_STOPPED=0"
    "R7_EVIDENCE_MANIFEST_SHA256=$ExpectedR7EvidenceHash"
    "R7_MANIFEST_SHA256=$ExpectedR7ManifestHash"
    "R7_WRITE_STOPPED_SHA256=$ExpectedR7WriteStoppedHash"
    "SOURCE_SHA256=$ExpectedSourceHash"
    "ADDENDUM_PAYLOAD_ENTRY_COUNT=6"
    "ADDENDUM_MANIFEST_ENTRY_COUNT=7"
    "ADDENDUM_EXPECTED_FINAL_ACTUAL_FILE_COUNT=9"
    "ADDENDUM_CLOSURE=6_PAYLOAD+1_EVIDENCE_MANIFEST+1_MANIFEST+1_WRITE_STOPPED=9"
    "ADDENDUM_EVIDENCE_MANIFEST_SHA256=$evidenceHash"
    "ADDENDUM_MANIFEST_SHA256=$manifestHash"
    "SEALED_UTC=$generatedUtc"
    "WRITE_STOPPED_WAS_FINAL_FILESYSTEM_WRITE=true"
    "NO_FURTHER_WRITES_PERMITTED_IN_THIS_R7A_TASK"
)
Write-NewUtf8 -Path $WriteStoppedPath -Text ([string]::Join([char]10, $writeStoppedText) + [char]10)
