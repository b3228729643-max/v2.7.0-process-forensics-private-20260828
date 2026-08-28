$ErrorActionPreference = 'Stop'
$Root = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P049-01\STRICT_R6_SA3_FRESH_ISOLATED_R111_20260827'
$AuditOut = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P049-01\SA3_FRESH_ISOLATED_R111_20260827_POSTSEAL_AUDIT.json'
$ManifestPath = Join-Path $Root 'PAYLOAD_MANIFEST.json'
$MarkerPath = Join-Path $Root 'WRITE_STOPPED'

function Get-Sha256([string]$Path) {
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash
}

function Add-StringLeaves($Value, [System.Collections.Generic.List[string]]$Leaves) {
    if ($null -eq $Value) { return }
    if ($Value -is [string]) { $Leaves.Add($Value); return }
    if ($Value -is [System.Collections.IDictionary]) {
        foreach ($Key in $Value.Keys) { Add-StringLeaves $Value[$Key] $Leaves }
        return
    }
    if ($Value -is [System.Collections.IEnumerable] -and -not ($Value -is [string])) {
        foreach ($Item in $Value) { Add-StringLeaves $Item $Leaves }
        return
    }
    foreach ($Property in $Value.PSObject.Properties) { Add-StringLeaves $Property.Value $Leaves }
}

if (-not [System.IO.Directory]::Exists($Root)) { throw 'Sealed root is absent.' }
if (-not [System.IO.File]::Exists($ManifestPath)) { throw 'Manifest is absent.' }
if (-not [System.IO.File]::Exists($MarkerPath)) { throw 'WRITE_STOPPED is absent.' }

$Manifest = Get-Content -LiteralPath $ManifestPath -Raw | ConvertFrom-Json
$Marker = Get-Content -LiteralPath $MarkerPath -Raw | ConvertFrom-Json
$AllFiles = @(Get-ChildItem -LiteralPath $Root -File -Recurse -Force | Sort-Object FullName)
$AllDirectories = @((Get-Item -LiteralPath $Root)) + @(Get-ChildItem -LiteralPath $Root -Directory -Recurse -Force)
$RelativeFiles = @($AllFiles | ForEach-Object { [System.IO.Path]::GetRelativePath($Root, $_.FullName).Replace('\', '/') })
$ManifestPaths = @($Manifest.files | ForEach-Object { $_.path })
$ExpectedFsPaths = @($ManifestPaths + 'PAYLOAD_MANIFEST.json' + 'WRITE_STOPPED' | Sort-Object)
$ActualFsPaths = @($RelativeFiles | Sort-Object)

$ManifestEntryChecks = foreach ($Entry in $Manifest.files) {
    $Target = Join-Path $Root ($Entry.path.Replace('/', '\'))
    $Exists = [System.IO.File]::Exists($Target)
    $BytesOk = $Exists -and (Get-Item -LiteralPath $Target).Length -eq [int64]$Entry.bytes
    $HashOk = $Exists -and (Get-Sha256 $Target) -eq $Entry.sha256
    [pscustomobject]@{ path=$Entry.path; exists=$Exists; bytes_match=$BytesOk; sha256_match=$HashOk }
}

$JsonParseErrors = @()
foreach ($File in $AllFiles | Where-Object { $_.Extension -eq '.json' }) {
    try { $null = Get-Content -LiteralPath $File.FullName -Raw | ConvertFrom-Json }
    catch { $JsonParseErrors += [System.IO.Path]::GetRelativePath($Root, $File.FullName) }
}
$CsvParseErrors = @()
foreach ($File in $AllFiles | Where-Object { $_.Extension -eq '.csv' }) {
    try { $null = @(Import-Csv -LiteralPath $File.FullName) }
    catch { $CsvParseErrors += [System.IO.Path]::GetRelativePath($Root, $File.FullName) }
}

$Denominator = @(Import-Csv -LiteralPath (Join-Path $Root 'machine_atomic_denominator.csv'))
$Pairs = @(Import-Csv -LiteralPath (Join-Path $Root 'machine_all_unordered_pairs.csv'))
$Candidates = @(Import-Csv -LiteralPath (Join-Path $Root 'machine_relation_candidates.csv'))
$ManualGlyph = @(Import-Csv -LiteralPath (Join-Path $Root 'manual_glyph_ledger.csv'))
$ManualPath = @(Import-Csv -LiteralPath (Join-Path $Root 'manual_path_ledger.csv'))
$ManualRelation = @(Import-Csv -LiteralPath (Join-Path $Root 'manual_relation_candidate_ledger.csv'))
$Controls = Get-Content -LiteralPath (Join-Path $Root 'controls_resolved.json') -Raw | ConvertFrom-Json
$Bindings = Get-Content -LiteralPath (Join-Path $Root 'external_bindings.json') -Raw | ConvertFrom-Json

$ReadonlyFiles = @($AllFiles | Where-Object { -not ($_.Attributes -band [System.IO.FileAttributes]::ReadOnly) })
$ReadonlyDirectories = @($AllDirectories | Where-Object { -not ($_.Attributes -band [System.IO.FileAttributes]::ReadOnly) })
$ReparseItems = @($AllFiles + $AllDirectories | Where-Object { $_.Attributes -band [System.IO.FileAttributes]::ReparsePoint })
$CacheItems = @(Get-ChildItem -LiteralPath $Root -Recurse -Force | Where-Object { $_.Name -in @('__pycache__','.pytest_cache','.mypy_cache','.ruff_cache') })
$PycItems = @(Get-ChildItem -LiteralPath $Root -File -Recurse -Force | Where-Object { $_.Extension -eq '.pyc' })
$AlternateStreams = @()
foreach ($File in $AllFiles) {
    foreach ($Stream in @(Get-Item -LiteralPath $File.FullName -Stream * -ErrorAction Stop)) {
        if ($Stream.Stream -ne ':$DATA') { $AlternateStreams += "$($File.FullName)::$($Stream.Stream)" }
    }
}

$PlaceholderHits = @()
$PlaceholderPattern = '(?i)(^|[^A-Za-z0-9_])(TBD|TODO|PENDING|UNKNOWN|UNRESOLVED|PLACEHOLDER)([^A-Za-z0-9_]|$)|\{\{|\}\}'
foreach ($File in $AllFiles) {
    if ($File.Extension -eq '.json') {
        $Object = Get-Content -LiteralPath $File.FullName -Raw | ConvertFrom-Json
        $Leaves = [System.Collections.Generic.List[string]]::new()
        Add-StringLeaves $Object $Leaves
        foreach ($Leaf in $Leaves) { if ($Leaf -match $PlaceholderPattern) { $PlaceholderHits += "$($File.Name):$Leaf" } }
    } elseif ($File.Extension -eq '.csv') {
        foreach ($Row in @(Import-Csv -LiteralPath $File.FullName)) {
            foreach ($Property in $Row.PSObject.Properties) {
                if ([string]$Property.Value -match $PlaceholderPattern) { $PlaceholderHits += "$($File.Name):$($Property.Name):$($Property.Value)" }
            }
        }
    } elseif ($File.Extension -eq '.md') {
        $Text = Get-Content -LiteralPath $File.FullName -Raw
        if ($Text -match $PlaceholderPattern) { $PlaceholderHits += $File.Name }
    }
}

$BuilderText = Get-Content -LiteralPath (Join-Path $Root 'build_machine_evidence.py') -Raw
$ValidatorText = Get-Content -LiteralPath (Join-Path $Root 'preseal_validator.py') -Raw
$ManualScriptWritePattern = '(?im)(write_text|open\([^\r\n]*["''][wa])[^\r\n]*manual_|manual_[^\r\n]*(write_text|open\([^\r\n]*["''][wa])'
$ManualScriptsClean = ($BuilderText -notmatch 'manual_') -and ($ValidatorText -notmatch $ManualScriptWritePattern)
$MachineObservationFiles = @($AllFiles | Where-Object { $_.Name -like 'machine_*' -or $_.Name -like '*sheet*' -or $_.Name -like 'atomic_overlay*' -or $_.Name -like 'figure_crop_native*' })
$LatestMachineObservation = ($MachineObservationFiles | Measure-Object -Property LastWriteTimeUtc -Maximum).Maximum
$ManualFiles = @($AllFiles | Where-Object { $_.Name -like 'manual_*' })
$ManualAfterMachine = @($ManualFiles | Where-Object { $_.LastWriteTimeUtc -le $LatestMachineObservation }).Count -eq 0

$BindingChecks = foreach ($Binding in $Bindings.files) {
    $Exists = [System.IO.File]::Exists($Binding.path)
    [pscustomobject]@{
        path = $Binding.path
        exists = $Exists
        bytes_match = $Exists -and (Get-Item -LiteralPath $Binding.path).Length -eq [int64]$Binding.bytes
        sha256_match = $Exists -and (Get-Sha256 $Binding.path) -eq $Binding.sha256
    }
}

$MarkerItem = Get-Item -LiteralPath $MarkerPath
$PostMarkerFiles = @($AllFiles | Where-Object { $_.FullName -ne $MarkerPath -and $_.LastWriteTimeUtc -gt $MarkerItem.LastWriteTimeUtc })
$MarkerNamedFiles = @($AllFiles | Where-Object { $_.Name -like 'WRITE_STOPPED*' })
$ManifestHashMatchesMarker = (Get-Sha256 $ManifestPath) -eq $Marker.manifest_sha256

$Checks = [ordered]@{
    manifest_path_set_exact = @(Compare-Object -ReferenceObject $ExpectedFsPaths -DifferenceObject $ActualFsPaths).Count -eq 0
    manifest_payload_count_exact = [int]$Manifest.payload_file_count -eq $ManifestPaths.Count
    manifest_entries_bytes_sha_exact = @($ManifestEntryChecks | Where-Object { -not $_.exists -or -not $_.bytes_match -or -not $_.sha256_match }).Count -eq 0
    manifest_hash_bound_by_marker = $ManifestHashMatchesMarker
    denominator_count_152 = $Denominator.Count -eq 152
    pair_count_11476 = $Pairs.Count -eq 11476
    pair_ids_unique_11476 = @($Pairs.pair_id | Sort-Object -Unique).Count -eq 11476
    manual_counts_135_17_122 = $ManualGlyph.Count -eq 135 -and $ManualPath.Count -eq 17 -and $ManualRelation.Count -eq 122 -and $Candidates.Count -eq 122
    all_files_readonly = $ReadonlyFiles.Count -eq 0
    all_directories_including_root_readonly = $ReadonlyDirectories.Count -eq 0
    unique_write_stopped = $MarkerNamedFiles.Count -eq 1 -and $Marker.marker -eq 'WRITE_STOPPED'
    write_stopped_latest = $PostMarkerFiles.Count -eq 0
    postmarker_root_writes_0 = $PostMarkerFiles.Count -eq 0
    resolved_controls_empty = @($Controls.unresolved_control_values).Count -eq 0
    placeholder_hits_0 = $PlaceholderHits.Count -eq 0
    json_parse_errors_0 = $JsonParseErrors.Count -eq 0
    csv_parse_errors_0 = $CsvParseErrors.Count -eq 0
    ads_0 = $AlternateStreams.Count -eq 0
    cache_0 = $CacheItems.Count -eq 0
    pyc_0 = $PycItems.Count -eq 0
    reparse_0 = $ReparseItems.Count -eq 0
    manual_files_postdate_machine_sheets = $ManualAfterMachine
    manual_not_script_generated_or_overwritten = $ManualScriptsClean
    external_report_handoff_bindings_exact = @($BindingChecks | Where-Object { -not $_.exists -or -not $_.bytes_match -or -not $_.sha256_match }).Count -eq 0
}
$FirstFailure = @($Checks.GetEnumerator() | Where-Object { -not $_.Value } | Select-Object -First 1)
$Result = [ordered]@{
    audit_kind = 'root-external read-only postseal auditor'
    uid = 'FIG-P049-01'
    root = $Root
    audit_state = if ($FirstFailure.Count -eq 0) { 'SEALED_CLEAR' } else { 'SEALED_NOT_CLEAR' }
    first_failure = if ($FirstFailure.Count -eq 0) { $null } else { $FirstFailure[0].Key }
    checks = $Checks
    counts = [ordered]@{
        filesystem_files = $AllFiles.Count
        manifest_payload_files = $ManifestPaths.Count
        denominator_N = $Denominator.Count
        unordered_pairs_C = $Pairs.Count
        machine_relation_candidates = $Candidates.Count
        manual_glyph_rows = $ManualGlyph.Count
        manual_path_rows = $ManualPath.Count
        manual_relation_rows = $ManualRelation.Count
        alternate_streams = $AlternateStreams.Count
        caches = $CacheItems.Count
        pyc = $PycItems.Count
        reparse = $ReparseItems.Count
        postmarker_files = $PostMarkerFiles.Count
    }
    manifest_entry_failures = @($ManifestEntryChecks | Where-Object { -not $_.exists -or -not $_.bytes_match -or -not $_.sha256_match })
    placeholder_hits = $PlaceholderHits
    external_binding_failures = @($BindingChecks | Where-Object { -not $_.exists -or -not $_.bytes_match -or -not $_.sha256_match })
    marker_last_write_utc = $MarkerItem.LastWriteTimeUtc.ToString('o')
}
$Utf8NoBom = [System.Text.UTF8Encoding]::new($false)
[System.IO.File]::WriteAllText($AuditOut, ($Result | ConvertTo-Json -Depth 10), $Utf8NoBom)
$Result | ConvertTo-Json -Depth 10 -Compress
if ($FirstFailure.Count -ne 0) { exit 2 }
