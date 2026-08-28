[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Get-ExpectedCleanMaterialRelativePaths {
    @(
        'build_seal_manifest.py'
        'figure_caption_grayscale_300dpi.png'
        'figure_caption_native_300dpi.png'
        'foreground_candidate_mask_300dpi.png'
        'full_page_200dpi.png'
        'full_page_300dpi.png'
        'generate_pair_index.py'
        'glyph_codepoint_ledger.csv'
        'input_identity.txt'
        'manual_object_ledger.csv'
        'manual_overlap_adjudication.md'
        'manual_pair_ledger.txt'
        'manual_visual_acceptance.md'
        'math_semantic_ledger.md'
        'object_index.csv'
        'object_overlay_300dpi.png'
        'page_739_bbox.xhtml'
        'page_integration_ledger.md'
        'pair_index_no_verdict.csv'
        'preseal_validation.txt'
        'render_evidence.py'
        'roi01_left_bar_formula_note_native1x.png'
        'roi01_left_bar_formula_note_nearest8x.png'
        'roi02_right_title_upper_bound_native1x.png'
        'roi02_right_title_upper_bound_nearest8x.png'
        'roi03_right_staircase_local_label_native1x.png'
        'roi03_right_staircase_local_label_nearest8x.png'
        'roi04_right_axis_ticks_label_native1x.png'
        'roi04_right_axis_ticks_label_nearest8x.png'
        'roi05_formula_codepoints_native1x.png'
        'roi05_formula_codepoints_nearest8x.png'
        'roi06_left_lower_note_native1x.png'
        'roi06_left_lower_note_nearest8x.png'
        'roi07_caption_all_lines_native1x.png'
        'roi07_caption_all_lines_nearest8x.png'
        'roi08_panel_gutter_boundaries_native1x.png'
        'roi08_panel_gutter_boundaries_nearest8x.png'
        'scope_and_denominator.md'
        'semantic_overlay_300dpi.png'
        'source_font_and_readability_adjudication.csv'
        'text_geometry_metrics.csv'
        'text_overlay_300dpi.png'
        'validate_evidence.py'
    )
}

function Get-ExpectedOldControlRelativePaths {
    @(
        'material_manifest.tsv'
        'seal_manifest.txt'
        'WSTOP.SA2_NO_SOURCE_CHANGE_READY_FOR_FRESH_SA1.marker'
    )
}

function Get-ExpectedOldCacheRelativePaths {
    @('__pycache__\render_evidence.cpython-312.pyc')
}

function Assert-ExactOrdinalSet {
    param(
        [Parameter(Mandatory)][string[]]$Expected,
        [Parameter(Mandatory)][string[]]$Actual,
        [Parameter(Mandatory)][string]$Label
    )
    $expectedSet = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::Ordinal)
    foreach ($value in $Expected) {
        if (-not $expectedSet.Add($value)) { throw "$Label expected duplicate: $value" }
    }
    $actualSet = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::Ordinal)
    foreach ($value in $Actual) {
        if (-not $actualSet.Add($value)) { throw "$Label actual duplicate: $value" }
    }
    if (-not $expectedSet.SetEquals($actualSet)) {
        $missing = @($expectedSet | Where-Object { -not $actualSet.Contains($_) } | Sort-Object -CaseSensitive)
        $extra = @($actualSet | Where-Object { -not $expectedSet.Contains($_) } | Sort-Object -CaseSensitive)
        throw "$Label ordinal set mismatch; missing=[$($missing -join ',')]; extra=[$($extra -join ',')]"
    }
}

function Assert-SafeRelativePath {
    param([Parameter(Mandatory)][AllowEmptyString()][string]$RelativePath)
    if ([string]::IsNullOrWhiteSpace($RelativePath)) { throw 'relative path is empty' }
    if ($RelativePath.Trim() -cne $RelativePath) { throw "relative path has edge whitespace: $RelativePath" }
    if ([System.IO.Path]::IsPathRooted($RelativePath)) { throw "relative path is rooted: $RelativePath" }
    if ($RelativePath.Contains(':')) { throw "relative path contains ADS/drive separator: $RelativePath" }
    $segments = @($RelativePath -split '[\\/]')
    if ($segments.Count -eq 0) { throw "relative path has no segments: $RelativePath" }
    foreach ($segment in $segments) {
        if ([string]::IsNullOrWhiteSpace($segment) -or $segment -ceq '.' -or $segment -ceq '..') {
            throw "relative path has empty/dot/parent segment: $RelativePath"
        }
    }
}

function Resolve-ContainedPath {
    param(
        [Parameter(Mandatory)][string]$Root,
        [Parameter(Mandatory)][AllowEmptyString()][string]$RelativePath
    )
    Assert-SafeRelativePath -RelativePath $RelativePath
    $rootFull = [System.IO.Path]::TrimEndingDirectorySeparator([System.IO.Path]::GetFullPath($Root))
    $segments = @($RelativePath -split '[\\/]')
    $normalized = $segments -join [System.IO.Path]::DirectorySeparatorChar
    $candidate = [System.IO.Path]::GetFullPath([System.IO.Path]::Combine($rootFull, $normalized))
    $prefix = $rootFull + [System.IO.Path]::DirectorySeparatorChar
    if (-not $candidate.StartsWith($prefix, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "contained-path escape: $RelativePath"
    }
    $roundTrip = [System.IO.Path]::GetRelativePath($rootFull, $candidate)
    if ($roundTrip -cne $normalized) { throw "noncanonical relative path: $RelativePath => $roundTrip" }
    $candidate
}

function Resolve-ExistingDirectoryCanonical {
    param([Parameter(Mandatory)][string]$LiteralPath)
    $item = Get-Item -LiteralPath $LiteralPath -Force -ErrorAction Stop
    if (-not $item.PSIsContainer) { throw "not a directory: $LiteralPath" }
    if (($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
        throw "reparse directory forbidden: $LiteralPath"
    }
    [System.IO.Path]::TrimEndingDirectorySeparator([System.IO.Path]::GetFullPath($item.FullName))
}

function Get-RelativeFileSet {
    param([Parameter(Mandatory)][string]$Root)
    @(
        Get-ChildItem -LiteralPath $Root -File -Recurse -Force -ErrorAction Stop |
            ForEach-Object { [System.IO.Path]::GetRelativePath($Root, $_.FullName) }
    )
}

function Get-RelativeDirectorySet {
    param([Parameter(Mandatory)][string]$Root)
    @(
        Get-ChildItem -LiteralPath $Root -Directory -Recurse -Force -ErrorAction Stop |
            ForEach-Object { [System.IO.Path]::GetRelativePath($Root, $_.FullName) }
    )
}

function Get-Sha256Hex {
    param([Parameter(Mandatory)][string]$LiteralPath)
    [System.Convert]::ToHexString(
        [System.Security.Cryptography.SHA256]::HashData([System.IO.File]::ReadAllBytes($LiteralPath))
    )
}

function Get-BytesSha256 {
    param([Parameter(Mandatory)][byte[]]$Bytes)
    [System.Convert]::ToHexString([System.Security.Cryptography.SHA256]::HashData($Bytes))
}

function Get-NonDefaultAdsCount {
    param([Parameter(Mandatory)][string]$LiteralPath)
    @(
        Get-Item -LiteralPath $LiteralPath -Stream * -Force -ErrorAction Stop |
            Where-Object { $_.Stream -cne ':$DATA' }
    ).Count
}

function Get-TreeSnapshot {
    param([Parameter(Mandatory)][string]$Root)
    $rootItem = Get-Item -LiteralPath $Root -Force -ErrorAction Stop
    $entries = [System.Collections.Generic.List[object]]::new()
    $entries.Add([pscustomobject][ordered]@{
        RelativePath = '.'
        Kind = 'DIRECTORY'
        Bytes = 0
        Sha256 = ''
        CreationFileTimeUtc = $rootItem.CreationTimeUtc.ToFileTimeUtc()
        LastWriteFileTimeUtc = $rootItem.LastWriteTimeUtc.ToFileTimeUtc()
        Attributes = [int64]$rootItem.Attributes
        AdsCount = 0
        Reparse = (($rootItem.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0)
    })
    foreach ($directory in @(Get-ChildItem -LiteralPath $Root -Directory -Recurse -Force -ErrorAction Stop | Sort-Object FullName -CaseSensitive)) {
        $entries.Add([pscustomobject][ordered]@{
            RelativePath = [System.IO.Path]::GetRelativePath($Root, $directory.FullName)
            Kind = 'DIRECTORY'
            Bytes = 0
            Sha256 = ''
            CreationFileTimeUtc = $directory.CreationTimeUtc.ToFileTimeUtc()
            LastWriteFileTimeUtc = $directory.LastWriteTimeUtc.ToFileTimeUtc()
            Attributes = [int64]$directory.Attributes
            AdsCount = 0
            Reparse = (($directory.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0)
        })
    }
    foreach ($file in @(Get-ChildItem -LiteralPath $Root -File -Recurse -Force -ErrorAction Stop | Sort-Object FullName -CaseSensitive)) {
        $entries.Add([pscustomobject][ordered]@{
            RelativePath = [System.IO.Path]::GetRelativePath($Root, $file.FullName)
            Kind = 'FILE'
            Bytes = [int64]$file.Length
            Sha256 = Get-Sha256Hex -LiteralPath $file.FullName
            CreationFileTimeUtc = $file.CreationTimeUtc.ToFileTimeUtc()
            LastWriteFileTimeUtc = $file.LastWriteTimeUtc.ToFileTimeUtc()
            Attributes = [int64]$file.Attributes
            AdsCount = Get-NonDefaultAdsCount -LiteralPath $file.FullName
            Reparse = (($file.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0)
        })
    }
    [pscustomobject][ordered]@{
        RootResolved = [System.IO.Path]::TrimEndingDirectorySeparator([System.IO.Path]::GetFullPath($Root))
        Entries = @($entries)
    }
}

function Get-SnapshotHash {
    param([Parameter(Mandatory)]$Snapshot)
    $json = $Snapshot | ConvertTo-Json -Depth 8 -Compress
    Get-BytesSha256 -Bytes ([System.Text.UTF8Encoding]::new($false).GetBytes($json))
}

function Assert-ReadOnlyItem {
    param([Parameter(Mandatory)][string]$LiteralPath)
    $attributes = [System.IO.File]::GetAttributes($LiteralPath)
    if (($attributes -band [System.IO.FileAttributes]::ReadOnly) -eq 0) {
        throw "item is not ReadOnly: $LiteralPath"
    }
}

function Get-StrictKeyValueMap {
    param([Parameter(Mandatory)][string]$LiteralPath)
    $bytes = [System.IO.File]::ReadAllBytes($LiteralPath)
    if ($bytes.Length -ge 3 -and $bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF) {
        throw 'marker has UTF-8 BOM'
    }
    $text = [System.Text.UTF8Encoding]::new($false, $true).GetString($bytes)
    if (-not $text.EndsWith("`n", [System.StringComparison]::Ordinal)) { throw 'marker lacks final LF' }
    if ($text.Contains("`r")) { throw 'marker contains CR' }
    $lines = @($text.Substring(0, $text.Length - 1).Split("`n"))
    $map = [System.Collections.Generic.Dictionary[string,string]]::new([System.StringComparer]::Ordinal)
    foreach ($line in $lines) {
        if ([string]::IsNullOrEmpty($line)) { throw 'marker has empty physical line' }
        if (($line.ToCharArray() | Where-Object { $_ -ceq '=' }).Count -ne 1) { throw "marker line is not one KEY=VALUE: $line" }
        $parts = $line.Split('=', 2)
        if ($parts[0] -notmatch '^[A-Z0-9_]+$' -or [string]::IsNullOrEmpty($parts[1])) { throw "invalid marker key/value: $line" }
        if (-not $map.TryAdd($parts[0], $parts[1])) { throw "duplicate marker key: $($parts[0])" }
        if ($parts[1] -match '(?i)TODO|TBD|PLACEHOLDER|UNKNOWN|<[^>]+>') { throw "marker placeholder: $line" }
    }
    [pscustomobject]@{ Bytes = $bytes; Lines = $lines; Map = $map }
}

function Assert-Utf8NoBomJsonFile {
    param([Parameter(Mandatory)][string]$LiteralPath)
    $bytes = [System.IO.File]::ReadAllBytes($LiteralPath)
    if ($bytes.Length -ge 3 -and $bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF) {
        throw "JSON has BOM: $LiteralPath"
    }
    $text = [System.Text.UTF8Encoding]::new($false, $true).GetString($bytes)
    $text | ConvertFrom-Json -Depth 20
}

function Import-Utf8NoBomCsvFile {
    param([Parameter(Mandatory)][string]$LiteralPath)
    $bytes = [System.IO.File]::ReadAllBytes($LiteralPath)
    if ($bytes.Length -ge 3 -and $bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF) {
        throw "CSV has BOM: $LiteralPath"
    }
    $text = [System.Text.UTF8Encoding]::new($false, $true).GetString($bytes)
    @($text | ConvertFrom-Csv)
}

function Invoke-ControlResealAudit {
    $handoffId = 'C-FIG-P689-01-R115-SA2-R168-READONLY-ADJUDICATION-CONTROL-RESEAL-V1'
    $uid = 'FIG-P689-01'
    $operation = 'P689_R115_SA2_EVIDENCE_ONLY_CONTROL_RESEAL_V1'
    $verdict = 'SA2_NO_SOURCE_CHANGE_READY_FOR_FRESH_SA1'
    $oldRootLiteral = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P689-01\sa2_r115_r168_readonly_adjudication_v1'
    $newRootLiteral = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P689-01\sa2_r115_r168_readonly_adjudication_v1_control_reseal_v1'

    $oldRoot = Resolve-ExistingDirectoryCanonical -LiteralPath $oldRootLiteral
    $newRoot = Resolve-ExistingDirectoryCanonical -LiteralPath $newRootLiteral
    $cleanExpected = @(Get-ExpectedCleanMaterialRelativePaths)
    $oldControls = @(Get-ExpectedOldControlRelativePaths)
    $oldCache = @(Get-ExpectedOldCacheRelativePaths)
    $oldExpected = @($cleanExpected + $oldControls + $oldCache)
    Assert-ExactOrdinalSet -Expected $oldExpected -Actual @(Get-RelativeFileSet -Root $oldRoot) -Label 'old root files'
    Assert-ExactOrdinalSet -Expected @('__pycache__') -Actual @(Get-RelativeDirectorySet -Root $oldRoot) -Label 'old root directories'

    $copyIdentityPath = Resolve-ContainedPath -Root $newRoot -RelativePath 'COPY_IDENTITY.csv'
    $provenancePath = Resolve-ContainedPath -Root $newRoot -RelativePath 'COPY_PROVENANCE.json'
    $payloadManifestPath = Resolve-ContainedPath -Root $newRoot -RelativePath 'PAYLOAD_MANIFEST.csv'
    $sealAuditPath = Resolve-ContainedPath -Root $newRoot -RelativePath 'SEAL_AUDIT.json'
    $markerPath = Resolve-ContainedPath -Root $newRoot -RelativePath 'WRITE_STOPPED'

    $copyRows = @(Import-Utf8NoBomCsvFile -LiteralPath $copyIdentityPath)
    if ($copyRows.Count -ne 43) { throw 'COPY_IDENTITY row count is not 43' }
    Assert-ExactOrdinalSet -Expected $cleanExpected -Actual @($copyRows.RELATIVE_PATH) -Label 'COPY_IDENTITY relative paths'
    foreach ($row in $copyRows) {
        Assert-SafeRelativePath -RelativePath $row.RELATIVE_PATH
        $source = Resolve-ContainedPath -Root $oldRoot -RelativePath $row.RELATIVE_PATH
        $destination = Resolve-ContainedPath -Root $newRoot -RelativePath $row.RELATIVE_PATH
        if ($row.SOURCE_RESOLVED_PATH -cne $source -or $row.DESTINATION_RESOLVED_PATH -cne $destination) {
            throw "resolved copy path mismatch: $($row.RELATIVE_PATH)"
        }
        $sourceItem = Get-Item -LiteralPath $source -Force -ErrorAction Stop
        $destinationItem = Get-Item -LiteralPath $destination -Force -ErrorAction Stop
        $sourceSha = Get-Sha256Hex -LiteralPath $source
        $destinationSha = Get-Sha256Hex -LiteralPath $destination
        $identityPass = (
            [int64]$row.SOURCE_BYTES -eq $sourceItem.Length -and
            [int64]$row.DESTINATION_BYTES -eq $destinationItem.Length -and
            $row.SOURCE_SHA256 -ceq $sourceSha -and
            $row.DESTINATION_SHA256 -ceq $destinationSha -and
            $sourceSha -ceq $destinationSha -and
            [int64]$row.SOURCE_CREATION_FILETIME_UTC -eq $sourceItem.CreationTimeUtc.ToFileTimeUtc() -and
            [int64]$row.DESTINATION_CREATION_FILETIME_UTC -eq $destinationItem.CreationTimeUtc.ToFileTimeUtc() -and
            [int64]$row.SOURCE_LASTWRITE_FILETIME_UTC -eq $sourceItem.LastWriteTimeUtc.ToFileTimeUtc() -and
            [int64]$row.DESTINATION_LASTWRITE_FILETIME_UTC -eq $destinationItem.LastWriteTimeUtc.ToFileTimeUtc() -and
            $row.IDENTITY_PASS -ceq 'true'
        )
        if (-not $identityPass) { throw "copy identity audit failed: $($row.RELATIVE_PATH)" }
    }

    $provenance = Assert-Utf8NoBomJsonFile -LiteralPath $provenancePath
    if ($provenance.handoffId -cne $handoffId -or $provenance.uid -cne $uid -or $provenance.operation -cne $operation) {
        throw 'provenance identity mismatch'
    }
    if ($provenance.controlOnly -ne $true -or $provenance.businessRerun -ne $false -or [int]$provenance.copiedMaterialCount -ne 43) {
        throw 'provenance control contract mismatch'
    }
    if ($provenance.sourceRootResolved -cne $oldRoot -or $provenance.destinationRootResolved -cne $newRoot) {
        throw 'provenance resolved roots mismatch'
    }
    if (@($provenance.copies).Count -ne 43) { throw 'provenance copy count mismatch' }
    Assert-ExactOrdinalSet -Expected $cleanExpected -Actual @($provenance.copies.RELATIVE_PATH) -Label 'provenance relative paths'
    Assert-ExactOrdinalSet -Expected $oldControls -Actual @($provenance.excludedOldControls) -Label 'provenance excluded controls'
    Assert-ExactOrdinalSet -Expected $oldCache -Actual @($provenance.excludedCacheFiles) -Label 'provenance excluded cache'
    $copyFields = @(
        'RELATIVE_PATH', 'SOURCE_RESOLVED_PATH', 'DESTINATION_RESOLVED_PATH',
        'SOURCE_BYTES', 'DESTINATION_BYTES', 'SOURCE_SHA256', 'DESTINATION_SHA256',
        'SOURCE_CREATION_FILETIME_UTC', 'DESTINATION_CREATION_FILETIME_UTC',
        'SOURCE_LASTWRITE_FILETIME_UTC', 'DESTINATION_LASTWRITE_FILETIME_UTC', 'IDENTITY_PASS'
    )
    $copyByPath = [System.Collections.Generic.Dictionary[string,object]]::new([System.StringComparer]::Ordinal)
    foreach ($row in $copyRows) { $copyByPath.Add($row.RELATIVE_PATH, $row) }
    foreach ($row in @($provenance.copies)) {
        if (-not $copyByPath.ContainsKey($row.RELATIVE_PATH)) { throw "unexpected provenance copy: $($row.RELATIVE_PATH)" }
        $csvRow = $copyByPath[$row.RELATIVE_PATH]
        foreach ($field in $copyFields) {
            if ([string]$row.$field -cne [string]$csvRow.$field) { throw "provenance/COPY_IDENTITY mismatch: $($row.RELATIVE_PATH)/$field" }
        }
    }

    $oldCurrent = Get-TreeSnapshot -Root $oldRoot
    $oldCurrentHash = Get-SnapshotHash -Snapshot $oldCurrent
    if (@($oldCurrent.Entries | Where-Object { $_.Reparse -or $_.AdsCount -ne 0 }).Count -ne 0) {
        throw 'old root contains reparse point or ADS'
    }
    if ($provenance.oldRootBeforeSnapshotSha256 -cne $oldCurrentHash -or
        $provenance.oldRootAfterSnapshotSha256 -cne $oldCurrentHash -or
        [int]$provenance.oldRootChangeCount -ne 0) {
        throw 'old root before/after/current snapshot mismatch'
    }

    $payloadExpected = @($cleanExpected + @('COPY_IDENTITY.csv', 'COPY_PROVENANCE.json'))
    $payloadRows = @(Import-Utf8NoBomCsvFile -LiteralPath $payloadManifestPath)
    if ($payloadRows.Count -ne 45) { throw 'PAYLOAD_MANIFEST row count is not 45' }
    Assert-ExactOrdinalSet -Expected $payloadExpected -Actual @($payloadRows.RELATIVE_PATH) -Label 'payload manifest relative paths'
    foreach ($row in $payloadRows) {
        $path = Resolve-ContainedPath -Root $newRoot -RelativePath $row.RELATIVE_PATH
        if ($row.RESOLVED_PATH -cne $path) { throw "payload resolved path mismatch: $($row.RELATIVE_PATH)" }
        $item = Get-Item -LiteralPath $path -Force -ErrorAction Stop
        if ([int64]$row.BYTES -ne $item.Length -or $row.SHA256 -cne (Get-Sha256Hex -LiteralPath $path) -or
            [int64]$row.CREATION_FILETIME_UTC -ne $item.CreationTimeUtc.ToFileTimeUtc() -or
            [int64]$row.LASTWRITE_FILETIME_UTC -ne $item.LastWriteTimeUtc.ToFileTimeUtc()) {
            throw "payload manifest identity mismatch: $($row.RELATIVE_PATH)"
        }
    }

    $seal = Assert-Utf8NoBomJsonFile -LiteralPath $sealAuditPath
    if ($seal.handoffId -cne $handoffId -or $seal.uid -cne $uid -or $seal.operation -cne $operation -or $seal.verdict -cne $verdict) {
        throw 'seal identity mismatch'
    }
    if ($seal.controlOnly -ne $true -or $seal.businessRerun -ne $false -or
        [int]$seal.cleanMaterialCount -ne 43 -or [int]$seal.payloadCount -ne 45 -or
        [int]$seal.premarkerOrdinaryFileCount -ne 47 -or [int]$seal.finalOrdinaryFileCount -ne 48 -or
        [int]$seal.directoryCountIncludingRoot -ne 1 -or $seal.canonicalContainmentPass -ne $true -or
        $seal.ordinalSetsPass -ne $true -or $seal.copyIdentityPass -ne $true -or
        $seal.csvJsonParseExpected -ne $true -or [int]$seal.adsExpectedCount -ne 0 -or
        [int]$seal.cachePycExpectedCount -ne 0 -or [int]$seal.reparseExpectedCount -ne 0 -or
        $seal.expectedMarkerName -cne 'WRITE_STOPPED' -or
        [int]$seal.postmarkerRootContentWrites -ne 0 -or [int]$seal.postmarkerRootAttributeWrites -ne 0) {
        throw 'seal counts/control mismatch'
    }
    $payloadManifestSha = Get-Sha256Hex -LiteralPath $payloadManifestPath
    $sealAuditSha = Get-Sha256Hex -LiteralPath $sealAuditPath
    if ($seal.payloadManifestSha256 -cne $payloadManifestSha -or
        $seal.oldRootBeforeSnapshotSha256 -cne $oldCurrentHash -or
        $seal.oldRootAfterSnapshotSha256 -cne $oldCurrentHash -or [int]$seal.oldRootChangeCount -ne 0) {
        throw 'seal hash/old-root mismatch'
    }

    $marker = Get-StrictKeyValueMap -LiteralPath $markerPath
    $requiredMarker = [ordered]@{
        HANDOFF_ID = $handoffId
        UID = $uid
        OPERATION = $operation
        SOURCE_ROOT_RESOLVED = $oldRoot
        DESTINATION_ROOT_RESOLVED = $newRoot
        CLEAN_MATERIAL_FILE_COUNT = '43'
        PAYLOAD_FILE_COUNT = '45'
        ORDINARY_FILE_COUNT = '48'
        DIRECTORY_COUNT_INCLUDING_ROOT = '1'
        PAYLOAD_MANIFEST_SHA256 = $payloadManifestSha
        SEAL_AUDIT_SHA256 = $sealAuditSha
        VERDICT = $verdict
        CONTROL_ONLY = 'true'
        BUSINESS_RERUN = 'false'
        SOURCE_CHANGE = 'NONE'
        POSTMARKER_ROOT_CONTENT_WRITES = '0'
        POSTMARKER_ROOT_ATTRIBUTE_WRITES = '0'
    }
    if ($marker.Map.Count -ne $requiredMarker.Count -or $marker.Lines.Count -ne $requiredMarker.Count) {
        throw 'marker key/physical-line count mismatch'
    }
    foreach ($key in $requiredMarker.Keys) {
        if (-not $marker.Map.ContainsKey($key) -or $marker.Map[$key] -cne $requiredMarker[$key]) {
            throw "marker binding mismatch: $key"
        }
    }

    $finalExpected = @($payloadExpected + @('PAYLOAD_MANIFEST.csv', 'SEAL_AUDIT.json', 'WRITE_STOPPED'))
    $finalFiles = @(Get-RelativeFileSet -Root $newRoot)
    Assert-ExactOrdinalSet -Expected $finalExpected -Actual $finalFiles -Label 'final ordinary files'
    if ($finalFiles.Count -ne 48) { throw 'final ordinary file count is not 48' }
    $subdirectories = @(Get-RelativeDirectorySet -Root $newRoot)
    if ($subdirectories.Count -ne 0) { throw 'new root contains subdirectories'
    }

    $items = @((Get-Item -LiteralPath $newRoot -Force)) + @(Get-ChildItem -LiteralPath $newRoot -File -Force)
    $markerItem = Get-Item -LiteralPath $markerPath -Force
    $atOrAfter = 0
    $adsCount = 0
    $reparseCount = 0
    $cachePycCount = 0
    foreach ($item in $items) {
        Assert-ReadOnlyItem -LiteralPath $item.FullName
        if (($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) { $reparseCount++ }
        if (-not $item.PSIsContainer) {
            $adsCount += Get-NonDefaultAdsCount -LiteralPath $item.FullName
            $relative = [System.IO.Path]::GetRelativePath($newRoot, $item.FullName)
            if ($relative -match '(?i)(^|[\\/])__pycache__([\\/]|$)|\.pyc$') { $cachePycCount++ }
        }
        if ($item.FullName -cne $markerItem.FullName) {
            if ($item.CreationTimeUtc.ToFileTimeUtc() -ge $markerItem.CreationTimeUtc.ToFileTimeUtc() -or
                $item.LastWriteTimeUtc.ToFileTimeUtc() -ge $markerItem.LastWriteTimeUtc.ToFileTimeUtc()) {
                $atOrAfter++
            }
        }
    }
    if ($adsCount -ne 0 -or $reparseCount -ne 0 -or $cachePycCount -ne 0 -or $atOrAfter -ne 0) {
        throw "hygiene/latest failure: ADS=$adsCount reparse=$reparseCount cachePyc=$cachePycCount atOrAfter=$atOrAfter"
    }

    [pscustomobject][ordered]@{
        HANDOFF_ID = $handoffId
        OPERATION = $operation
        AUDIT_RESULT = 'PASS'
        OLD_ROOT_BEFORE_AFTER_CHANGE_COUNT = 0
        COPY_IDENTITY_ROWS = 43
        PAYLOAD_MANIFEST_ROWS = 45
        ORDINARY_FILE_COUNT = 48
        DIRECTORY_COUNT_INCLUDING_ROOT = 1
        ALL_FILES_DIRS_ROOT_READONLY = $true
        MARKER_PHYSICAL_LINES = $marker.Lines.Count
        MARKER_UNIQUE_KEYS = $marker.Map.Count
        MARKER_BYTES = $marker.Bytes.Length
        MARKER_SHA256 = Get-BytesSha256 -Bytes $marker.Bytes
        STRICT_LATEST_INCLUDING_FILES_DIRS_ROOT = $true
        AT_OR_AFTER_EXCLUDING_MARKER = 0
        POSTMARKER_ROOT_CONTENT_WRITES = 0
        POSTMARKER_ROOT_ATTRIBUTE_WRITES = 0
        CSV_JSON_PARSE_PASS = $true
        ADS_COUNT = 0
        CACHE_PYC_COUNT = 0
        REPARSE_COUNT = 0
    } | ConvertTo-Json -Depth 5 -Compress
}

Invoke-ControlResealAudit
