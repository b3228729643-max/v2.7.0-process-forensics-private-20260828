$ErrorActionPreference = 'Stop'

$R7ARoot = Split-Path -Parent $PSScriptRoot
$R7Root = (Resolve-Path -LiteralPath (Join-Path $R7ARoot '..\STRICT_R7_SA2_NARROW_R100_DIRECT_BUILD_20260825')).Path
$DestinationRoot = Join-Path $R7ARoot 'machine_reuse'
$WorkRoot = (Resolve-Path -LiteralPath (Join-Path $R7ARoot '..\..\..\..\..\..')).Path
$Worktree = (Resolve-Path -LiteralPath (Join-Path $WorkRoot 'worktrees\dialogue_A_visual')).Path
$SourceMatches = @(Get-ChildItem -LiteralPath (Join-Path $Worktree 'src') -Recurse -File -Filter 'fig_v5_c05_dependency_graph.tex')
$WrapperMatches = @(Get-ChildItem -LiteralPath (Join-Path $Worktree 'src') -Recurse -File -Filter 'v260_FIG-P654-01_standalone.tex')
if ($SourceMatches.Count -ne 1) { throw "Expected one target source, found $($SourceMatches.Count)" }
if ($WrapperMatches.Count -ne 1) { throw "Expected one wrapper, found $($WrapperMatches.Count)" }
$SourcePath = $SourceMatches[0].FullName
$WrapperPath = $WrapperMatches[0].FullName

if (Test-Path -LiteralPath (Join-Path $R7ARoot 'MACHINE_REUSE_IDENTITY_LEDGER.csv')) {
    throw 'Identity ledger already exists; staging must not be rerun after success'
}
if (-not (Test-Path -LiteralPath $DestinationRoot)) {
    $null = New-Item -ItemType Directory -Path $DestinationRoot
}
$Rows = [System.Collections.Generic.List[object]]::new()

function Copy-WithIdentity {
    param(
        [Parameter(Mandatory)][string]$Source,
        [Parameter(Mandatory)][string]$DestinationRelative,
        [Parameter(Mandatory)][string]$Category
    )
    $Destination = Join-Path $R7ARoot $DestinationRelative
    $Parent = Split-Path -Parent $Destination
    if (-not (Test-Path -LiteralPath $Parent)) {
        $null = New-Item -ItemType Directory -Path $Parent
    }
    if (-not (Test-Path -LiteralPath $Destination)) {
        Copy-Item -LiteralPath $Source -Destination $Destination
    }
    $SourceItem = Get-Item -LiteralPath $Source
    $DestinationItem = Get-Item -LiteralPath $Destination
    $SourceHash = (Get-FileHash -LiteralPath $Source -Algorithm SHA256).Hash
    $DestinationHash = (Get-FileHash -LiteralPath $Destination -Algorithm SHA256).Hash
    $Rows.Add([pscustomobject]@{
        CATEGORY = $Category
        SOURCE_PATH = $SourceItem.FullName
        DESTINATION_PATH = $DestinationItem.FullName
        DESTINATION_RELATIVE_PATH = $DestinationItem.FullName.Substring($R7ARoot.Length + 1).Replace('\', '/')
        SOURCE_BYTES = $SourceItem.Length
        DESTINATION_BYTES = $DestinationItem.Length
        SOURCE_MTIME_UTC = $SourceItem.LastWriteTimeUtc.ToString('o')
        DESTINATION_MTIME_UTC = $DestinationItem.LastWriteTimeUtc.ToString('o')
        SOURCE_SHA256 = $SourceHash
        DESTINATION_SHA256 = $DestinationHash
        IDENTITY_MATCH = [bool](($SourceItem.Length -eq $DestinationItem.Length) -and ($SourceHash -eq $DestinationHash))
    })
}

$DirectoryAllowlist = @('build', 'contact_sheets', 'objects', 'pairs', 'views')
foreach ($DirectoryName in $DirectoryAllowlist) {
    $DirectoryPath = Join-Path $R7Root $DirectoryName
    foreach ($File in Get-ChildItem -LiteralPath $DirectoryPath -Recurse -File | Sort-Object FullName) {
        $Relative = $File.FullName.Substring($R7Root.Length + 1)
        Copy-WithIdentity -Source $File.FullName -DestinationRelative (Join-Path 'machine_reuse' $Relative) -Category 'R7_MACHINE_ARTIFACT'
    }
}

$RootFileAllowlist = @(
    'after_font_audit.csv',
    'after_overlap_report.csv',
    'after_pixel_measurements.csv',
    'all_unordered_pairs.csv',
    'all_unordered_pairs.json',
    'clearance_summary.csv',
    'DIRECT_INVOCATION_RESULT.json',
    'DIRECT_INVOCATION_START.json',
    'drawing_path_inventory.csv',
    'id_safe_filename_map.csv',
    'math_rule_inventory.csv',
    'object_manifest.csv',
    'object_manifest.json',
    'pdf_text_dual_inventory.csv',
    'raw_ownership_ledger.csv',
    'role_hierarchy_ledger.csv',
    'run_direct_lualatex_once.ps1'
)
foreach ($Name in $RootFileAllowlist) {
    Copy-WithIdentity -Source (Join-Path $R7Root $Name) -DestinationRelative (Join-Path 'machine_reuse' $Name) -Category 'R7_MACHINE_LEDGER_OR_CONTROLLER'
}

foreach ($Relative in @('machine\machine_summary_pre_manual.json', 'machine\render_identity.json')) {
    Copy-WithIdentity -Source (Join-Path $R7Root $Relative) -DestinationRelative (Join-Path 'machine_reuse' $Relative) -Category 'R7_PRE_MANUAL_MACHINE_SUMMARY'
}

Copy-WithIdentity -Source $SourcePath -DestinationRelative 'frozen_identity\fig_v5_c05_dependency_graph.tex' -Category 'CURRENT_SOURCE_SNAPSHOT'
Copy-WithIdentity -Source $WrapperPath -DestinationRelative 'frozen_identity\v260_FIG-P654-01_standalone.tex' -Category 'CURRENT_WRAPPER_SNAPSHOT'

$BannedPattern = '(?i)(glyph_manual_review|graphic_manual_review|critical_pair_manual_review|semantic_manual_review|view_manual_review|manual_decisions|manual_row_decisions|manual_review_summary|finalize_r7|terminal_crosscheck|SA2_REPORT|after_visual_acceptance|[\\/](RESULT\.txt|PACKAGE_STATUS\.json|MANIFEST\.(csv|json)|WRITE_STOPPED)$)'
$Banned = @($Rows | Where-Object { $_.SOURCE_PATH -match $BannedPattern -or $_.DESTINATION_PATH -match $BannedPattern })
$Mismatches = @($Rows | Where-Object { -not $_.IDENTITY_MATCH })
if ($Banned.Count -ne 0) {
    throw "Banned R7 artifact entered staging: $($Banned[0].SOURCE_PATH)"
}
if ($Mismatches.Count -ne 0) {
    throw "Source/destination identity mismatch: $($Mismatches[0].SOURCE_PATH)"
}

$LedgerCsv = Join-Path $R7ARoot 'MACHINE_REUSE_IDENTITY_LEDGER.csv'
$LedgerJson = Join-Path $R7ARoot 'MACHINE_REUSE_IDENTITY_LEDGER.json'
$Rows | Export-Csv -LiteralPath $LedgerCsv -NoTypeInformation -Encoding utf8
$Rows | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $LedgerJson -Encoding utf8

$PdfRow = @($Rows | Where-Object { $_.DESTINATION_RELATIVE_PATH -eq 'machine_reuse/build/v260_FIG-P654-01_standalone.pdf' })
$SourceRow = @($Rows | Where-Object { $_.CATEGORY -eq 'CURRENT_SOURCE_SNAPSHOT' })
$WrapperRow = @($Rows | Where-Object { $_.CATEGORY -eq 'CURRENT_WRAPPER_SNAPSHOT' })
$Summary = [ordered]@{
    staged_at_utc = (Get-Date).ToUniversalTime().ToString('o')
    source_r7_root = $R7Root
    destination_r7a_root = $R7ARoot
    staged_file_count = $Rows.Count
    identity_mismatch_count = $Mismatches.Count
    banned_artifact_count = $Banned.Count
    source_sha256 = $SourceRow[0].SOURCE_SHA256
    wrapper_sha256 = $WrapperRow[0].SOURCE_SHA256
    pdf_bytes = $PdfRow[0].SOURCE_BYTES
    pdf_sha256 = $PdfRow[0].SOURCE_SHA256
}
$Summary | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $R7ARoot 'MACHINE_REUSE_STAGING_SUMMARY.json') -Encoding utf8

if ($Summary.source_sha256 -ne 'EA4A19FF940A177D4D754C4277896A2F38B75C1E6F252D8A374F418B84E31E6D') { throw 'Frozen source SHA mismatch' }
if ($Summary.wrapper_sha256 -ne 'FE44F2E6005D884A6916A11C6EBCB89CF40BD523A64D8F8C6BC8124DBABC0CA1') { throw 'Frozen wrapper SHA mismatch' }
if ($Summary.pdf_bytes -ne 43385) { throw 'Frozen PDF byte count mismatch' }
if ($Summary.pdf_sha256 -ne 'A7DBDECEA7B54C1649CD341112B7BB37FF379600CB6A61B54EDDBAF154E9E5D6') { throw 'Frozen PDF SHA mismatch' }

Write-Output ($Summary | ConvertTo-Json -Compress)
