$ErrorActionPreference = 'Stop'

$RootPath = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P109-01\STRICT_R1_SA2_R168_READONLY_R114_20260828'
$ReportPath = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P109-01\STRICT_R1_SA2_R168_READONLY_R114_20260828_AUDIT_REPORT.json'
$PythonPath = 'C:\Users\ASUS\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'

if (-not (Test-Path -LiteralPath $RootPath -PathType Container)) {
    throw "Fixed root missing: $RootPath"
}

$rootItem = Get-Item -LiteralPath $RootPath -Force
$entries = @(Get-ChildItem -LiteralPath $RootPath -Force -Recurse)
$files = @($entries | Where-Object { -not $_.PSIsContainer })
$directories = @($entries | Where-Object { $_.PSIsContainer })

$manifestPath = Join-Path $RootPath 'MANIFEST.json'
$manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
$expectedFiles = @($manifest.expected_files | ForEach-Object { [string]$_ })
$actualFiles = @($files | ForEach-Object { [System.IO.Path]::GetRelativePath($RootPath, $_.FullName) })
$expectedDirectories = @($manifest.expected_directories_below_root | ForEach-Object { [string]$_ })
$actualDirectories = @($directories | ForEach-Object { [System.IO.Path]::GetRelativePath($RootPath, $_.FullName) })
$missingFiles = @($expectedFiles | Where-Object { $_ -notin $actualFiles })
$extraFiles = @($actualFiles | Where-Object { $_ -notin $expectedFiles })
$missingDirectories = @($expectedDirectories | Where-Object { $_ -notin $actualDirectories })
$extraDirectories = @($actualDirectories | Where-Object { $_ -notin $expectedDirectories })

$parseErrors = [System.Collections.Generic.List[string]]::new()
foreach ($file in $files) {
    try {
        switch ($file.Extension.ToLowerInvariant()) {
            '.json' {
                Get-Content -LiteralPath $file.FullName -Raw | ConvertFrom-Json | Out-Null
            }
            '.csv' {
                $parsed = @(Import-Csv -LiteralPath $file.FullName)
                if ($parsed.Count -eq 0) { throw 'CSV has no data rows' }
            }
            '.py' {
                $code = "import ast,pathlib,sys; ast.parse(pathlib.Path(sys.argv[1]).read_text(encoding='utf-8'))"
                & $PythonPath -B -c $code $file.FullName
                if ($LASTEXITCODE -ne 0) { throw "Python AST exit $LASTEXITCODE" }
            }
            '.png' {
                $code = "from PIL import Image; import sys; im=Image.open(sys.argv[1]); im.verify()"
                & $PythonPath -B -c $code $file.FullName
                if ($LASTEXITCODE -ne 0) { throw "PNG verify exit $LASTEXITCODE" }
            }
            '.md' {
                [System.IO.File]::ReadAllText($file.FullName, [System.Text.Encoding]::UTF8) | Out-Null
            }
            '.txt' {
                [System.IO.File]::ReadAllText($file.FullName, [System.Text.Encoding]::UTF8) | Out-Null
            }
        }
    }
    catch {
        $parseErrors.Add("$($file.Name): $($_.Exception.Message)")
    }
}

$ads = [System.Collections.Generic.List[string]]::new()
foreach ($file in $files) {
    try {
        foreach ($stream in @(Get-Item -LiteralPath $file.FullName -Stream * -ErrorAction Stop)) {
            if ($stream.Stream -ne ':$DATA') {
                $ads.Add("$($file.Name):$($stream.Stream)")
            }
        }
    }
    catch {
        $ads.Add("STREAM_QUERY_ERROR:$($file.Name):$($_.Exception.Message)")
    }
}

$cacheOrPyc = @($entries | Where-Object {
    $_.Name -eq '__pycache__' -or
    $_.Name -eq '.cache' -or
    $_.Extension -in @('.pyc', '.pyo')
})
$reparse = @(@($rootItem) + $entries | Where-Object {
    ($_.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0
})
$notReadOnly = @(@($rootItem) + $entries | Where-Object {
    ($_.Attributes -band [System.IO.FileAttributes]::ReadOnly) -eq 0
})

$wstop = @($files | Where-Object { $_.Name -eq 'WSTOP.json' })
$wstopCount = $wstop.Count
$wstopParseError = $null
$wstopRoute = $null
if ($wstopCount -eq 1) {
    try {
        $wstopData = Get-Content -LiteralPath $wstop[0].FullName -Raw | ConvertFrom-Json
        $wstopRoute = [string]$wstopData.route
    }
    catch {
        $wstopParseError = $_.Exception.Message
    }
}

$excludingMarkerAtOrAfter = @()
$postMarkerContent = @()
$postMarkerAttribute = @()
$wstopStrictlyLatest = $false
if ($wstopCount -eq 1) {
    $markerTime = $wstop[0].LastWriteTimeUtc
    $otherEntries = @($rootItem) + @($entries | Where-Object { $_.FullName -ne $wstop[0].FullName })
    $excludingMarkerAtOrAfter = @($otherEntries | Where-Object { $_.LastWriteTimeUtc -ge $markerTime })
    $postMarkerContent = @($otherEntries | Where-Object { $_.LastWriteTimeUtc -gt $markerTime })
    $postMarkerAttribute = @($otherEntries | Where-Object {
        $_.LastWriteTimeUtc -gt $markerTime -or
        ($_.Attributes -band [System.IO.FileAttributes]::ReadOnly) -eq 0
    })
    $wstopStrictlyLatest = ($excludingMarkerAtOrAfter.Count -eq 0)
}

$manifestClosureErrorCount = $missingFiles.Count + $extraFiles.Count + $missingDirectories.Count + $extraDirectories.Count
$status = if (
    $manifestClosureErrorCount -eq 0 -and
    $actualFiles.Count -eq [int]$manifest.expected_file_count -and
    $actualDirectories.Count -eq [int]$manifest.expected_directory_count_below_root -and
    $notReadOnly.Count -eq 0 -and
    $wstopCount -eq 1 -and
    $wstopStrictlyLatest -and
    $excludingMarkerAtOrAfter.Count -eq 0 -and
    $postMarkerContent.Count -eq 0 -and
    $postMarkerAttribute.Count -eq 0 -and
    $parseErrors.Count -eq 0 -and
    $ads.Count -eq 0 -and
    $cacheOrPyc.Count -eq 0 -and
    $reparse.Count -eq 0 -and
    $null -eq $wstopParseError -and
    $wstopRoute -eq 'FAIL_TO_MAIN_SOURCE_SCOPE'
) { 'PASS' } else { 'FAIL' }

$report = [ordered]@{
    schema = 'SA2_R168_ROOT_EXTERNAL_READONLY_AUDIT_V1'
    status = $status
    root = $RootPath
    manifest_path = $manifestPath
    manifest_expected_file_count = [int]$manifest.expected_file_count
    actual_file_count = $actualFiles.Count
    manifest_expected_directory_count_below_root = [int]$manifest.expected_directory_count_below_root
    actual_directory_count_below_root = $actualDirectories.Count
    manifest_closure_error_count = $manifestClosureErrorCount
    missing_files = $missingFiles
    extra_files = $extraFiles
    missing_directories = $missingDirectories
    extra_directories = $extraDirectories
    readonly_missing_count = $notReadOnly.Count
    readonly_missing_paths = @($notReadOnly | ForEach-Object FullName)
    unique_wstop_count = $wstopCount
    wstop_route = $wstopRoute
    wstop_parse_error = $wstopParseError
    wstop_strictly_latest_including_root = $wstopStrictlyLatest
    excluding_marker_at_or_after_count = $excludingMarkerAtOrAfter.Count
    excluding_marker_at_or_after_paths = @($excludingMarkerAtOrAfter | ForEach-Object FullName)
    postmarker_content_count = $postMarkerContent.Count
    postmarker_content_paths = @($postMarkerContent | ForEach-Object FullName)
    postmarker_attribute_count = $postMarkerAttribute.Count
    postmarker_attribute_paths = @($postMarkerAttribute | ForEach-Object FullName)
    parse_error_count = $parseErrors.Count
    parse_errors = @($parseErrors)
    ads_count = $ads.Count
    ads_entries = @($ads)
    cache_pyc_count = $cacheOrPyc.Count
    cache_pyc_paths = @($cacheOrPyc | ForEach-Object FullName)
    reparse_count = $reparse.Count
    reparse_paths = @($reparse | ForEach-Object FullName)
}

[System.IO.File]::WriteAllText($ReportPath, ($report | ConvertTo-Json -Depth 10), [System.Text.UTF8Encoding]::new($false))
Write-Output ($report | ConvertTo-Json -Depth 10)
if ($status -ne 'PASS') { exit 1 }
