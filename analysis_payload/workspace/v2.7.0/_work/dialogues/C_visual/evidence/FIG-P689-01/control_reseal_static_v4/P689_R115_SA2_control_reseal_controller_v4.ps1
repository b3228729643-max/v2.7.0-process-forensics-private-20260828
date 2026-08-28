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
        AdsCount = Get-NonDefaultAdsCount -LiteralPath $rootItem.FullName
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
            AdsCount = Get-NonDefaultAdsCount -LiteralPath $directory.FullName
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

function Write-Utf8NoBom {
    param(
        [Parameter(Mandatory)][string]$LiteralPath,
        [Parameter(Mandatory)][string]$Text
    )
    [System.IO.File]::WriteAllText($LiteralPath, $Text, [System.Text.UTF8Encoding]::new($false))
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

function Assert-Utf8NoBomJsonFile {
    param([Parameter(Mandatory)][string]$LiteralPath)
    $bytes = [System.IO.File]::ReadAllBytes($LiteralPath)
    if ($bytes.Length -ge 3 -and $bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF) {
        throw "JSON has BOM: $LiteralPath"
    }
    $text = [System.Text.UTF8Encoding]::new($false, $true).GetString($bytes)
    $text | ConvertFrom-Json -Depth 20
}

function Assert-ReadOnlyItem {
    param([Parameter(Mandatory)][string]$LiteralPath)
    $attributes = [System.IO.File]::GetAttributes($LiteralPath)
    if (($attributes -band [System.IO.FileAttributes]::ReadOnly) -eq 0) {
        throw "item is not ReadOnly: $LiteralPath"
    }
}

function Set-ReadOnlyItem {
    param([Parameter(Mandatory)][string]$LiteralPath)
    $attributes = [System.IO.File]::GetAttributes($LiteralPath)
    [System.IO.File]::SetAttributes($LiteralPath, $attributes -bor [System.IO.FileAttributes]::ReadOnly)
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

function Invoke-ControlReseal {
    $handoffId = 'C-FIG-P689-01-R115-SA2-R168-READONLY-ADJUDICATION-CONTROL-RESEAL-V2'
    $uid = 'FIG-P689-01'
    $operation = 'P689_R115_SA2_EVIDENCE_ONLY_CONTROL_RESEAL_V2'
    $verdict = 'SA2_NO_SOURCE_CHANGE_READY_FOR_FRESH_SA1'
    $oldRootLiteral = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P689-01\sa2_r115_r168_readonly_adjudication_v1'
    $newRootLiteral = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P689-01\sa2_r115_r168_readonly_adjudication_v1_control_reseal_v2'
    $uidParentLiteral = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P689-01'
    $destinationMarkerName = 'WRITE_STOPPED'
    $controlRootLiteral = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P689-01\control_reseal_static_v4'

    $oldRoot = Resolve-ExistingDirectoryCanonical -LiteralPath $oldRootLiteral
    $uidParent = Resolve-ExistingDirectoryCanonical -LiteralPath $uidParentLiteral
    $controlRoot = Resolve-ExistingDirectoryCanonical -LiteralPath $controlRootLiteral
    $newRoot = [System.IO.Path]::TrimEndingDirectorySeparator([System.IO.Path]::GetFullPath($newRootLiteral))
    $stagedMarkerPath = Resolve-ContainedPath -Root $controlRoot -RelativePath 'STAGED_WRITE_STOPPED.marker'
    $postMarkerStatePath = Resolve-ContainedPath -Root $controlRoot -RelativePath 'POSTMARKER_ROOT_STATE.json'
    $controllerResultPath = Resolve-ContainedPath -Root $controlRoot -RelativePath 'CONTROLLER_RESULT.json'
    $auditorResultPath = Resolve-ContainedPath -Root $controlRoot -RelativePath 'AUDITOR_RESULT.json'
    if (-not [System.IO.Path]::GetDirectoryName($newRoot).Equals($uidParent, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw 'new root is not directly contained by the fixed UID parent'
    }
    if (Test-Path -LiteralPath $newRoot) { throw 'new root already exists' }
    foreach ($path in @($stagedMarkerPath, $postMarkerStatePath, $controllerResultPath, $auditorResultPath)) {
        if (Test-Path -LiteralPath $path) { throw "root-external runtime artifact already exists: $path" }
    }

    $cleanExpected = @(Get-ExpectedCleanMaterialRelativePaths)
    $oldControls = @(Get-ExpectedOldControlRelativePaths)
    $oldCache = @(Get-ExpectedOldCacheRelativePaths)
    if ($cleanExpected.Count -ne 43) { throw 'clean material declaration is not 43' }
    Assert-ExactOrdinalSet -Expected $cleanExpected -Actual $cleanExpected -Label 'clean declaration uniqueness'
    $oldFilesExpected = @($cleanExpected + $oldControls + $oldCache)
    $oldFilesActual = @(Get-RelativeFileSet -Root $oldRoot)
    Assert-ExactOrdinalSet -Expected $oldFilesExpected -Actual $oldFilesActual -Label 'old root complete files'
    Assert-ExactOrdinalSet -Expected @('__pycache__') -Actual @(Get-RelativeDirectorySet -Root $oldRoot) -Label 'old root directories'
    $excludeSet = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::Ordinal)
    foreach ($relative in @($oldControls + $oldCache)) { [void]$excludeSet.Add($relative) }
    $cleanActual = @($oldFilesActual | Where-Object { -not $excludeSet.Contains($_) })
    Assert-ExactOrdinalSet -Expected $cleanExpected -Actual $cleanActual -Label 'old root clean 43'

    $oldBefore = Get-TreeSnapshot -Root $oldRoot
    $oldBeforeHash = Get-SnapshotHash -Snapshot $oldBefore
    if (@($oldBefore.Entries | Where-Object { $_.Reparse -or $_.AdsCount -ne 0 }).Count -ne 0) {
        throw 'old root contains reparse point or ADS'
    }

    [void][System.IO.Directory]::CreateDirectory($newRoot)
    if (-not (Test-Path -LiteralPath $newRoot -PathType Container)) { throw 'new root creation failed' }
    if (@(Get-ChildItem -LiteralPath $newRoot -Force).Count -ne 0) { throw 'new root is not empty after creation' }

    $copyRows = [System.Collections.Generic.List[object]]::new()
    foreach ($relative in @($cleanExpected | Sort-Object -CaseSensitive)) {
        if ([System.IO.Path]::GetFileName($relative) -cne $relative) { throw "clean material is not root-level: $relative" }
        $source = Resolve-ContainedPath -Root $oldRoot -RelativePath $relative
        $destination = Resolve-ContainedPath -Root $newRoot -RelativePath $relative
        $sourceItem = Get-Item -LiteralPath $source -Force -ErrorAction Stop
        if ($sourceItem.PSIsContainer -or (($sourceItem.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0)) {
            throw "invalid source material: $source"
        }
        if ((Get-NonDefaultAdsCount -LiteralPath $source) -ne 0) { throw "source material has ADS: $source" }
        $sourceBytes = [System.IO.File]::ReadAllBytes($source)
        $sourceSha = Get-BytesSha256 -Bytes $sourceBytes
        [System.IO.File]::WriteAllBytes($destination, $sourceBytes)
        [System.IO.File]::SetCreationTimeUtc($destination, $sourceItem.CreationTimeUtc)
        [System.IO.File]::SetLastWriteTimeUtc($destination, $sourceItem.LastWriteTimeUtc)
        $destinationItem = Get-Item -LiteralPath $destination -Force -ErrorAction Stop
        $destinationSha = Get-Sha256Hex -LiteralPath $destination
        $identityPass = (
            $destinationItem.Length -eq $sourceItem.Length -and
            $destinationSha -ceq $sourceSha -and
            $destinationItem.CreationTimeUtc.ToFileTimeUtc() -eq $sourceItem.CreationTimeUtc.ToFileTimeUtc() -and
            $destinationItem.LastWriteTimeUtc.ToFileTimeUtc() -eq $sourceItem.LastWriteTimeUtc.ToFileTimeUtc() -and
            [System.IO.Path]::GetFullPath($source) -ceq $source -and
            [System.IO.Path]::GetFullPath($destination) -ceq $destination
        )
        if (-not $identityPass) { throw "copy identity failed: $relative" }
        $copyRows.Add([pscustomobject][ordered]@{
            RELATIVE_PATH = $relative
            SOURCE_RESOLVED_PATH = $source
            DESTINATION_RESOLVED_PATH = $destination
            SOURCE_BYTES = [int64]$sourceItem.Length
            DESTINATION_BYTES = [int64]$destinationItem.Length
            SOURCE_SHA256 = $sourceSha
            DESTINATION_SHA256 = $destinationSha
            SOURCE_CREATION_FILETIME_UTC = $sourceItem.CreationTimeUtc.ToFileTimeUtc()
            DESTINATION_CREATION_FILETIME_UTC = $destinationItem.CreationTimeUtc.ToFileTimeUtc()
            SOURCE_LASTWRITE_FILETIME_UTC = $sourceItem.LastWriteTimeUtc.ToFileTimeUtc()
            DESTINATION_LASTWRITE_FILETIME_UTC = $destinationItem.LastWriteTimeUtc.ToFileTimeUtc()
            IDENTITY_PASS = 'true'
        })
    }
    if ($copyRows.Count -ne 43) { throw 'copied material count is not 43' }

    $oldAfter = Get-TreeSnapshot -Root $oldRoot
    $oldAfterHash = Get-SnapshotHash -Snapshot $oldAfter
    if ($oldAfterHash -cne $oldBeforeHash) { throw 'old root changed during copy' }

    $copyIdentityPath = Resolve-ContainedPath -Root $newRoot -RelativePath 'COPY_IDENTITY.csv'
    $copyCsv = (($copyRows | ConvertTo-Csv -NoTypeInformation -UseQuotes AsNeeded) -join "`n") + "`n"
    Write-Utf8NoBom -LiteralPath $copyIdentityPath -Text $copyCsv
    $parsedCopyRows = @(Import-Utf8NoBomCsvFile -LiteralPath $copyIdentityPath)
    if ($parsedCopyRows.Count -ne 43) { throw 'COPY_IDENTITY parse row count is not 43' }
    Assert-ExactOrdinalSet -Expected $cleanExpected -Actual @($parsedCopyRows.RELATIVE_PATH) -Label 'COPY_IDENTITY parsed paths'
    $copyFields = @(
        'RELATIVE_PATH', 'SOURCE_RESOLVED_PATH', 'DESTINATION_RESOLVED_PATH',
        'SOURCE_BYTES', 'DESTINATION_BYTES', 'SOURCE_SHA256', 'DESTINATION_SHA256',
        'SOURCE_CREATION_FILETIME_UTC', 'DESTINATION_CREATION_FILETIME_UTC',
        'SOURCE_LASTWRITE_FILETIME_UTC', 'DESTINATION_LASTWRITE_FILETIME_UTC', 'IDENTITY_PASS'
    )
    $copyOriginalByPath = [System.Collections.Generic.Dictionary[string,object]]::new([System.StringComparer]::Ordinal)
    foreach ($row in $copyRows) { $copyOriginalByPath.Add($row.RELATIVE_PATH, $row) }
    foreach ($row in $parsedCopyRows) {
        if (-not $copyOriginalByPath.ContainsKey($row.RELATIVE_PATH)) { throw "parsed copy row is unexpected: $($row.RELATIVE_PATH)" }
        $original = $copyOriginalByPath[$row.RELATIVE_PATH]
        foreach ($field in $copyFields) {
            if ([string]$row.$field -cne [string]$original.$field) { throw "COPY_IDENTITY parse mismatch: $($row.RELATIVE_PATH)/$field" }
        }
    }

    $provenancePath = Resolve-ContainedPath -Root $newRoot -RelativePath 'COPY_PROVENANCE.json'
    $provenance = [pscustomobject][ordered]@{
        handoffId = $handoffId
        uid = $uid
        operation = $operation
        controlOnly = $true
        businessRerun = $false
        sourceRootResolved = $oldRoot
        destinationRootResolved = $newRoot
        copiedMaterialCount = 43
        oldRootBeforeSnapshotSha256 = $oldBeforeHash
        oldRootAfterSnapshotSha256 = $oldAfterHash
        oldRootChangeCount = 0
        excludedOldControls = $oldControls
        excludedCacheFiles = $oldCache
        copies = @($copyRows)
    }
    Write-Utf8NoBom -LiteralPath $provenancePath -Text (($provenance | ConvertTo-Json -Depth 10) + "`n")
    $parsedProvenance = Assert-Utf8NoBomJsonFile -LiteralPath $provenancePath
    if ($parsedProvenance.handoffId -cne $handoffId -or $parsedProvenance.uid -cne $uid -or
        $parsedProvenance.operation -cne $operation -or $parsedProvenance.sourceRootResolved -cne $oldRoot -or
        $parsedProvenance.destinationRootResolved -cne $newRoot -or $parsedProvenance.controlOnly -ne $true -or
        $parsedProvenance.businessRerun -ne $false -or [int]$parsedProvenance.copiedMaterialCount -ne 43 -or
        @($parsedProvenance.copies).Count -ne 43) {
        throw 'COPY_PROVENANCE parse/identity mismatch'
    }
    Assert-ExactOrdinalSet -Expected $cleanExpected -Actual @($parsedProvenance.copies.RELATIVE_PATH) -Label 'COPY_PROVENANCE parsed paths'
    Assert-ExactOrdinalSet -Expected $oldControls -Actual @($parsedProvenance.excludedOldControls) -Label 'COPY_PROVENANCE excluded controls'
    Assert-ExactOrdinalSet -Expected $oldCache -Actual @($parsedProvenance.excludedCacheFiles) -Label 'COPY_PROVENANCE excluded cache'

    $payloadExpected = @($cleanExpected + @('COPY_IDENTITY.csv', 'COPY_PROVENANCE.json'))
    Assert-ExactOrdinalSet -Expected $payloadExpected -Actual @(Get-RelativeFileSet -Root $newRoot) -Label 'payload 45 before controls'
    if ($payloadExpected.Count -ne 45) { throw 'payload declaration is not 45' }
    if (@(Get-RelativeDirectorySet -Root $newRoot).Count -ne 0) { throw 'new root unexpectedly has subdirectories' }

    $payloadRows = [System.Collections.Generic.List[object]]::new()
    foreach ($relative in @($payloadExpected | Sort-Object -CaseSensitive)) {
        $path = Resolve-ContainedPath -Root $newRoot -RelativePath $relative
        $item = Get-Item -LiteralPath $path -Force -ErrorAction Stop
        $payloadRows.Add([pscustomobject][ordered]@{
            RELATIVE_PATH = $relative
            RESOLVED_PATH = $path
            BYTES = [int64]$item.Length
            SHA256 = Get-Sha256Hex -LiteralPath $path
            CREATION_FILETIME_UTC = $item.CreationTimeUtc.ToFileTimeUtc()
            LASTWRITE_FILETIME_UTC = $item.LastWriteTimeUtc.ToFileTimeUtc()
        })
    }
    $payloadManifestPath = Resolve-ContainedPath -Root $newRoot -RelativePath 'PAYLOAD_MANIFEST.csv'
    $payloadCsv = (($payloadRows | ConvertTo-Csv -NoTypeInformation -UseQuotes AsNeeded) -join "`n") + "`n"
    Write-Utf8NoBom -LiteralPath $payloadManifestPath -Text $payloadCsv
    $payloadManifestSha = Get-Sha256Hex -LiteralPath $payloadManifestPath
    $parsedPayloadRows = @(Import-Utf8NoBomCsvFile -LiteralPath $payloadManifestPath)
    if ($parsedPayloadRows.Count -ne 45) { throw 'PAYLOAD_MANIFEST parse row count is not 45' }
    Assert-ExactOrdinalSet -Expected $payloadExpected -Actual @($parsedPayloadRows.RELATIVE_PATH) -Label 'PAYLOAD_MANIFEST parsed paths'
    foreach ($row in $parsedPayloadRows) {
        $path = Resolve-ContainedPath -Root $newRoot -RelativePath $row.RELATIVE_PATH
        $item = Get-Item -LiteralPath $path -Force -ErrorAction Stop
        if ($row.RESOLVED_PATH -cne $path -or [int64]$row.BYTES -ne $item.Length -or
            $row.SHA256 -cne (Get-Sha256Hex -LiteralPath $path) -or
            [int64]$row.CREATION_FILETIME_UTC -ne $item.CreationTimeUtc.ToFileTimeUtc() -or
            [int64]$row.LASTWRITE_FILETIME_UTC -ne $item.LastWriteTimeUtc.ToFileTimeUtc()) {
            throw "PAYLOAD_MANIFEST parse/identity mismatch: $($row.RELATIVE_PATH)"
        }
    }

    $sealAuditPath = Resolve-ContainedPath -Root $newRoot -RelativePath 'SEAL_AUDIT.json'
    $sealAudit = [pscustomobject][ordered]@{
        handoffId = $handoffId
        uid = $uid
        operation = $operation
        verdict = $verdict
        controlOnly = $true
        businessRerun = $false
        sourceRootResolved = $oldRoot
        destinationRootResolved = $newRoot
        cleanMaterialCount = 43
        payloadCount = 45
        premarkerOrdinaryFileCount = 47
        finalOrdinaryFileCount = 48
        directoryCountIncludingRoot = 1
        payloadManifestSha256 = $payloadManifestSha
        oldRootBeforeSnapshotSha256 = $oldBeforeHash
        oldRootAfterSnapshotSha256 = $oldAfterHash
        oldRootChangeCount = 0
        canonicalContainmentPass = $true
        ordinalSetsPass = $true
        copyIdentityPass = $true
        csvJsonParseExpected = $true
        adsExpectedCount = 0
        cachePycExpectedCount = 0
        reparseExpectedCount = 0
        expectedMarkerName = $destinationMarkerName
        postmarkerRootContentWrites = 0
        postmarkerRootAttributeWrites = 0
    }
    Write-Utf8NoBom -LiteralPath $sealAuditPath -Text (($sealAudit | ConvertTo-Json -Depth 8) + "`n")
    $sealAuditSha = Get-Sha256Hex -LiteralPath $sealAuditPath
    $parsedSeal = Assert-Utf8NoBomJsonFile -LiteralPath $sealAuditPath
    if ($parsedSeal.handoffId -cne $handoffId -or $parsedSeal.uid -cne $uid -or
        $parsedSeal.operation -cne $operation -or $parsedSeal.verdict -cne $verdict -or
        $parsedSeal.controlOnly -ne $true -or $parsedSeal.businessRerun -ne $false -or
        [int]$parsedSeal.cleanMaterialCount -ne 43 -or [int]$parsedSeal.payloadCount -ne 45 -or
        [int]$parsedSeal.premarkerOrdinaryFileCount -ne 47 -or [int]$parsedSeal.finalOrdinaryFileCount -ne 48 -or
        [int]$parsedSeal.directoryCountIncludingRoot -ne 1 -or
        $parsedSeal.payloadManifestSha256 -cne $payloadManifestSha -or
        $parsedSeal.oldRootBeforeSnapshotSha256 -cne $oldBeforeHash -or
        $parsedSeal.oldRootAfterSnapshotSha256 -cne $oldAfterHash -or [int]$parsedSeal.oldRootChangeCount -ne 0 -or
        $parsedSeal.canonicalContainmentPass -ne $true -or $parsedSeal.ordinalSetsPass -ne $true -or
        $parsedSeal.copyIdentityPass -ne $true -or $parsedSeal.csvJsonParseExpected -ne $true -or
        [int]$parsedSeal.adsExpectedCount -ne 0 -or [int]$parsedSeal.cachePycExpectedCount -ne 0 -or
        [int]$parsedSeal.reparseExpectedCount -ne 0 -or $parsedSeal.expectedMarkerName -cne $destinationMarkerName -or
        [int]$parsedSeal.postmarkerRootContentWrites -ne 0 -or [int]$parsedSeal.postmarkerRootAttributeWrites -ne 0) {
        throw 'SEAL_AUDIT parse/binding mismatch'
    }

    $premarkerExpected = @($payloadExpected + @('PAYLOAD_MANIFEST.csv', 'SEAL_AUDIT.json'))
    Assert-ExactOrdinalSet -Expected $premarkerExpected -Actual @(Get-RelativeFileSet -Root $newRoot) -Label 'premarker files'
    if ($premarkerExpected.Count -ne 47) { throw 'premarker ordinary file count is not 47' }
    if (@(Get-RelativeDirectorySet -Root $newRoot).Count -ne 0) { throw 'premarker directory count including root is not 1' }
    foreach ($relative in $premarkerExpected) {
        $path = Resolve-ContainedPath -Root $newRoot -RelativePath $relative
        if ((Get-NonDefaultAdsCount -LiteralPath $path) -ne 0) { throw "premarker ADS found: $relative" }
        $item = Get-Item -LiteralPath $path -Force
        if (($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) { throw "premarker reparse found: $relative" }
        if ($relative -match '(?i)(^|[\\/])__pycache__([\\/]|$)|\.pyc$') { throw "premarker cache/pyc found: $relative" }
    }

    foreach ($relative in $premarkerExpected) {
        Set-ReadOnlyItem -LiteralPath (Resolve-ContainedPath -Root $newRoot -RelativePath $relative)
    }
    Set-ReadOnlyItem -LiteralPath $newRoot
    foreach ($relative in $premarkerExpected) {
        Assert-ReadOnlyItem -LiteralPath (Resolve-ContainedPath -Root $newRoot -RelativePath $relative)
    }
    Assert-ReadOnlyItem -LiteralPath $newRoot

    $premarkerItems = @((Get-Item -LiteralPath $newRoot -Force)) + @(Get-ChildItem -LiteralPath $newRoot -File -Force)
    $maxFileTime = [int64]0
    foreach ($item in $premarkerItems) {
        foreach ($fileTime in @($item.CreationTimeUtc.ToFileTimeUtc(), $item.LastWriteTimeUtc.ToFileTimeUtc())) {
            if ($fileTime -gt $maxFileTime) { $maxFileTime = $fileTime }
        }
    }
    $futureUtc = [datetime]::UtcNow.AddYears(10)
    if ($futureUtc.ToFileTimeUtc() -le $maxFileTime) {
        $futureUtc = [datetime]::FromFileTimeUtc($maxFileTime).AddYears(1)
    }

    $markerLines = @(
        "HANDOFF_ID=$handoffId"
        "UID=$uid"
        "OPERATION=$operation"
        "SOURCE_ROOT_RESOLVED=$oldRoot"
        "DESTINATION_ROOT_RESOLVED=$newRoot"
        'CLEAN_MATERIAL_FILE_COUNT=43'
        'PAYLOAD_FILE_COUNT=45'
        'ORDINARY_FILE_COUNT=48'
        'DIRECTORY_COUNT_INCLUDING_ROOT=1'
        "PAYLOAD_MANIFEST_SHA256=$payloadManifestSha"
        "SEAL_AUDIT_SHA256=$sealAuditSha"
        "VERDICT=$verdict"
        'CONTROL_ONLY=true'
        'BUSINESS_RERUN=false'
        'SOURCE_CHANGE=NONE'
        'POSTMARKER_ROOT_CONTENT_WRITES=0'
        'POSTMARKER_ROOT_ATTRIBUTE_WRITES=0'
    )
    $markerText = ($markerLines -join "`n") + "`n"
    Write-Utf8NoBom -LiteralPath $stagedMarkerPath -Text $markerText
    [System.IO.File]::SetCreationTimeUtc($stagedMarkerPath, $futureUtc)
    [System.IO.File]::SetLastWriteTimeUtc($stagedMarkerPath, $futureUtc)
    Set-ReadOnlyItem -LiteralPath $stagedMarkerPath
    $parsedMarker = Get-StrictKeyValueMap -LiteralPath $stagedMarkerPath
    if ($parsedMarker.Lines.Count -ne $markerLines.Count -or $parsedMarker.Map.Count -ne $markerLines.Count) {
        throw 'external marker line/key count mismatch'
    }
    Assert-ReadOnlyItem -LiteralPath $stagedMarkerPath
    $stagedMarkerItem = Get-Item -LiteralPath $stagedMarkerPath -Force
    if ($stagedMarkerItem.CreationTimeUtc.ToFileTimeUtc() -le $maxFileTime -or $stagedMarkerItem.LastWriteTimeUtc.ToFileTimeUtc() -le $maxFileTime) {
        throw 'staged marker is not strictly future FILETIME'
    }

    $destinationMarker = Resolve-ContainedPath -Root $newRoot -RelativePath $destinationMarkerName
    if (Test-Path -LiteralPath $destinationMarker) { throw 'destination marker unexpectedly exists' }
    Move-Item -LiteralPath $stagedMarkerPath -Destination $destinationMarker -ErrorAction Stop

    $finalFiles = @(Get-RelativeFileSet -Root $newRoot)
    $finalExpected = @($premarkerExpected + @($destinationMarkerName))
    Assert-ExactOrdinalSet -Expected $finalExpected -Actual $finalFiles -Label 'final files'
    if ($finalFiles.Count -ne 48) { throw 'final ordinary file count is not 48' }
    if (@(Get-RelativeDirectorySet -Root $newRoot).Count -ne 0) { throw 'final directory count including root is not 1' }
    $finalItems = @((Get-Item -LiteralPath $newRoot -Force)) + @(Get-ChildItem -LiteralPath $newRoot -File -Force)
    $markerItem = Get-Item -LiteralPath $destinationMarker -Force
    $atOrAfter = 0
    foreach ($item in $finalItems) {
        Assert-ReadOnlyItem -LiteralPath $item.FullName
        if ($item.FullName -cne $markerItem.FullName) {
            if ($item.CreationTimeUtc.ToFileTimeUtc() -ge $markerItem.CreationTimeUtc.ToFileTimeUtc() -or
                $item.LastWriteTimeUtc.ToFileTimeUtc() -ge $markerItem.LastWriteTimeUtc.ToFileTimeUtc()) {
                $atOrAfter++
            }
        }
    }
    if ($atOrAfter -ne 0) { throw 'final strict-latest check failed' }
    if (Test-Path -LiteralPath $stagedMarkerPath) { throw 'staged marker remains after move' }

    $nonMarkerMaxFileTime = [int64]0
    foreach ($item in $finalItems) {
        if ($item.FullName -cne $markerItem.FullName) {
            foreach ($fileTime in @($item.CreationTimeUtc.ToFileTimeUtc(), $item.LastWriteTimeUtc.ToFileTimeUtc())) {
                if ($fileTime -gt $nonMarkerMaxFileTime) { $nonMarkerMaxFileTime = $fileTime }
            }
        }
    }
    $markerMinimumFileTime = [Math]::Min(
        $markerItem.CreationTimeUtc.ToFileTimeUtc(),
        $markerItem.LastWriteTimeUtc.ToFileTimeUtc()
    )
    $strictLatestMarginFileTimeTicks = [int64]($markerMinimumFileTime - $nonMarkerMaxFileTime)
    if ($strictLatestMarginFileTimeTicks -le 0) { throw 'strict-latest margin is not positive' }
    if (Test-Path -LiteralPath $stagedMarkerPath) { throw 'staged marker unexpectedly exists after marker move' }

    $postMarkerSnapshotS1 = Get-TreeSnapshot -Root $newRoot
    $postMarkerSnapshotS2 = Get-TreeSnapshot -Root $newRoot
    $postMarkerSnapshotS1Hash = Get-SnapshotHash -Snapshot $postMarkerSnapshotS1
    $postMarkerSnapshotS2Hash = Get-SnapshotHash -Snapshot $postMarkerSnapshotS2
    if ($postMarkerSnapshotS1Hash -cne $postMarkerSnapshotS2Hash) { throw 'postmarker root snapshots are not identical' }

    $markerSha = Get-Sha256Hex -LiteralPath $destinationMarker
    $postMarkerState = [pscustomobject][ordered]@{
        handoffId = $handoffId
        uid = $uid
        operation = $operation
        verdict = $verdict
        controlOnly = $true
        businessRerun = $false
        controllerInvocationCount = 1
        controllerRetryCount = 0
        sourceRootResolved = $oldRoot
        destinationRootResolved = $newRoot
        postMarkerStateResolvedPath = $postMarkerStatePath
        controllerResultResolvedPath = $controllerResultPath
        stagedMarkerResolvedPath = $stagedMarkerPath
        stageAbsent = $true
        cleanMaterialCount = 43
        payloadCount = 45
        premarkerOrdinaryFileCount = 47
        finalOrdinaryFileCount = 48
        directoryCountIncludingRoot = 1
        payloadManifestSha256 = $payloadManifestSha
        sealAuditSha256 = $sealAuditSha
        markerSha256 = $markerSha
        oldRootBeforeSnapshotSha256 = $oldBeforeHash
        oldRootAfterSnapshotSha256 = $oldAfterHash
        oldRootChangeCount = 0
        rootSnapshotS1Sha256 = $postMarkerSnapshotS1Hash
        rootSnapshotS2Sha256 = $postMarkerSnapshotS2Hash
        strictLatestMarginFileTimeTicks = $strictLatestMarginFileTimeTicks
        atOrAfterExcludingMarker = 0
        postmarkerRootContentWrites = 0
        postmarkerRootAttributeWrites = 0
        rootSnapshotS1 = $postMarkerSnapshotS1
        rootSnapshotS2 = $postMarkerSnapshotS2
    }
    Write-Utf8NoBom -LiteralPath $postMarkerStatePath -Text (($postMarkerState | ConvertTo-Json -Depth 12) + "`n")
    Set-ReadOnlyItem -LiteralPath $postMarkerStatePath
    Assert-ReadOnlyItem -LiteralPath $postMarkerStatePath
    $postMarkerStateItem = Get-Item -LiteralPath $postMarkerStatePath -Force -ErrorAction Stop
    if (($postMarkerStateItem.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0 -or
        (Get-NonDefaultAdsCount -LiteralPath $postMarkerStatePath) -ne 0) {
        throw 'POSTMARKER_ROOT_STATE.json hygiene failure'
    }
    [void](Assert-Utf8NoBomJsonFile -LiteralPath $postMarkerStatePath)
    $postMarkerStateSha = Get-Sha256Hex -LiteralPath $postMarkerStatePath

    $controllerResult = [pscustomobject][ordered]@{
        handoffId = $handoffId
        uid = $uid
        operation = $operation
        verdict = $verdict
        result = 'CONTROL_RESEAL_COMPLETE_AWAITING_INDEPENDENT_AUDITOR'
        controlOnly = $true
        businessRerun = $false
        controllerInvocationCount = 1
        controllerRetryCount = 0
        sourceRootResolved = $oldRoot
        destinationRootResolved = $newRoot
        postMarkerStateResolvedPath = $postMarkerStatePath
        controllerResultResolvedPath = $controllerResultPath
        stagedMarkerResolvedPath = $stagedMarkerPath
        stageAbsent = $true
        cleanMaterialCount = 43
        payloadCount = 45
        premarkerOrdinaryFileCount = 47
        finalOrdinaryFileCount = 48
        directoryCountIncludingRoot = 1
        payloadManifestSha256 = $payloadManifestSha
        sealAuditSha256 = $sealAuditSha
        markerSha256 = $markerSha
        postMarkerStateSha256 = $postMarkerStateSha
        oldRootBeforeSnapshotSha256 = $oldBeforeHash
        oldRootAfterSnapshotSha256 = $oldAfterHash
        oldRootChangeCount = 0
        rootSnapshotS1Sha256 = $postMarkerSnapshotS1Hash
        rootSnapshotS2Sha256 = $postMarkerSnapshotS2Hash
        rootSnapshotHashEquality = $true
        strictLatestMarginFileTimeTicks = $strictLatestMarginFileTimeTicks
        atOrAfterExcludingMarker = 0
        postmarkerRootContentWrites = 0
        postmarkerRootAttributeWrites = 0
    }
    Write-Utf8NoBom -LiteralPath $controllerResultPath -Text (($controllerResult | ConvertTo-Json -Depth 8) + "`n")
    Set-ReadOnlyItem -LiteralPath $controllerResultPath
    Assert-ReadOnlyItem -LiteralPath $controllerResultPath
    $controllerResultItem = Get-Item -LiteralPath $controllerResultPath -Force -ErrorAction Stop
    if (($controllerResultItem.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0 -or
        (Get-NonDefaultAdsCount -LiteralPath $controllerResultPath) -ne 0) {
        throw 'CONTROLLER_RESULT.json hygiene failure'
    }
    [void](Assert-Utf8NoBomJsonFile -LiteralPath $controllerResultPath)
    $controllerResult | ConvertTo-Json -Depth 8 -Compress
}

Invoke-ControlReseal
