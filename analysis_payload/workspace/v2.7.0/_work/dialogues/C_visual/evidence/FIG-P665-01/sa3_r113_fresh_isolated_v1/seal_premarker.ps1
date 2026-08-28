$ErrorActionPreference = 'Stop'

$root = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P665-01\sa3_r113_fresh_isolated_v1'
$manifest = Join-Path $root 'manifest.csv'
$marker = Join-Path $root 'FINAL_SEAL_MARKER.txt'
$dirSnapshot = Join-Path $root 'directory_attributes_premarker.csv'
$preseal = Join-Path $root 'preseal_validation.json'

if (-not (Test-Path -LiteralPath $root -PathType Container)) { throw 'ASSIGNED_ROOT_MISSING' }
if (Test-Path -LiteralPath $manifest) { throw 'MANIFEST_ALREADY_EXISTS' }
if (Test-Path -LiteralPath $marker) { throw 'FINAL_MARKER_ALREADY_EXISTS' }
if (Test-Path -LiteralPath $dirSnapshot) { throw 'DIRECTORY_SNAPSHOT_ALREADY_EXISTS' }
if (-not (Select-String -LiteralPath $preseal -SimpleMatch '"status": "PRESEAL_VALID"' -Quiet)) { throw 'PRESEAL_VALIDATION_NOT_VALID' }

$items = @(Get-ChildItem -LiteralPath $root -Force -Recurse)
$reparse = @($items | Where-Object { ($_.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0 })
if ($reparse.Count -ne 0) { throw ('REPARSE_ITEMS=' + $reparse.Count) }

$cache = @($items | Where-Object { $_.Name -in @('__pycache__','.pytest_cache','.mypy_cache','.ruff_cache') -or $_.Extension -in @('.pyc','.pyo') })
if ($cache.Count -ne 0) { throw ('CACHE_PYC_ITEMS=' + $cache.Count) }

$filesBefore = @(Get-ChildItem -LiteralPath $root -Force -Recurse -File)
$badAds = 0
foreach ($file in $filesBefore) {
    $streams = @(Get-Item -LiteralPath $file.FullName -Stream *)
    $badAds += @($streams | Where-Object { $_.Stream -ne ':$DATA' }).Count
}
if ($badAds -ne 0) { throw ('NONDEFAULT_ADS=' + $badAds) }

foreach ($file in $filesBefore) {
    & attrib.exe +R $file.FullName
    if ($LASTEXITCODE -ne 0) { throw ('ATTRIB_FILE_FAILED=' + $file.FullName) }
}

$dirs = @(Get-ChildItem -LiteralPath $root -Force -Recurse -Directory | Sort-Object FullName -Descending)
foreach ($dir in $dirs) {
    & attrib.exe +R $dir.FullName
    if ($LASTEXITCODE -ne 0) { throw ('ATTRIB_DIR_FAILED=' + $dir.FullName) }
}
& attrib.exe +R $root
if ($LASTEXITCODE -ne 0) { throw 'ATTRIB_ROOT_FAILED' }

$dirLines = @('"REL_DIR","ATTRIBUTES_DECIMAL"')
$rootItem = Get-Item -LiteralPath $root -Force
$dirLines += ('".","' + [int]$rootItem.Attributes + '"')
$dirsAscending = @(Get-ChildItem -LiteralPath $root -Force -Recurse -Directory | Sort-Object FullName)
foreach ($dir in $dirsAscending) {
    $rel = $dir.FullName.Substring($root.Length + 1).Replace('\','/')
    $dirLines += ('"' + $rel + '","' + [int]$dir.Attributes + '"')
}
Set-Content -LiteralPath $dirSnapshot -Value $dirLines -Encoding utf8
& attrib.exe +R $dirSnapshot
if ($LASTEXITCODE -ne 0) { throw 'ATTRIB_DIR_SNAPSHOT_FAILED' }

$manifestLines = @('"REL_PATH","BYTES","SHA256","LAST_WRITE_FILETIME_UTC","CREATION_FILETIME_UTC","ATTRIBUTES_DECIMAL"')
$payloadFiles = @(Get-ChildItem -LiteralPath $root -Force -Recurse -File | Where-Object { $_.FullName -ne $manifest -and $_.FullName -ne $marker } | Sort-Object FullName)
foreach ($file in $payloadFiles) {
    $rel = $file.FullName.Substring($root.Length + 1).Replace('\','/')
    $hash = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToUpperInvariant()
    $manifestLines += ('"' + $rel + '","' + $file.Length + '","' + $hash + '","' + $file.LastWriteTimeUtc.ToFileTimeUtc() + '","' + $file.CreationTimeUtc.ToFileTimeUtc() + '","' + [int]$file.Attributes + '"')
}
Set-Content -LiteralPath $manifest -Value $manifestLines -Encoding utf8
& attrib.exe +R $manifest
if ($LASTEXITCODE -ne 0) { throw 'ATTRIB_MANIFEST_FAILED' }

$manifestRows = @(Import-Csv -LiteralPath $manifest)
if ($manifestRows.Count -ne $payloadFiles.Count) { throw 'MANIFEST_ROW_COUNT_MISMATCH' }
foreach ($row in $manifestRows) {
    $path = Join-Path $root ($row.REL_PATH.Replace('/','\'))
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw ('MANIFEST_PATH_MISSING=' + $row.REL_PATH) }
    $file = Get-Item -LiteralPath $path -Force
    if ([string]$file.Length -ne $row.BYTES) { throw ('MANIFEST_BYTES_MISMATCH=' + $row.REL_PATH) }
    $hash = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToUpperInvariant()
    if ($hash -ne $row.SHA256) { throw ('MANIFEST_SHA_MISMATCH=' + $row.REL_PATH) }
    if ([string]$file.LastWriteTimeUtc.ToFileTimeUtc() -ne $row.LAST_WRITE_FILETIME_UTC) { throw ('MANIFEST_MTIME_MISMATCH=' + $row.REL_PATH) }
    if ([string]$file.CreationTimeUtc.ToFileTimeUtc() -ne $row.CREATION_FILETIME_UTC) { throw ('MANIFEST_CTIME_MISMATCH=' + $row.REL_PATH) }
    if ([string][int]$file.Attributes -ne $row.ATTRIBUTES_DECIMAL) { throw ('MANIFEST_ATTRIBUTE_MISMATCH=' + $row.REL_PATH) }
}

$allFiles = @(Get-ChildItem -LiteralPath $root -Force -Recurse -File)
$notReadonlyFiles = @($allFiles | Where-Object { -not $_.IsReadOnly })
if ($notReadonlyFiles.Count -ne 0) { throw ('NOT_READONLY_FILES=' + $notReadonlyFiles.Count) }
$allDirs = @((Get-Item -LiteralPath $root -Force)) + @(Get-ChildItem -LiteralPath $root -Force -Recurse -Directory)
$notReadonlyDirs = @($allDirs | Where-Object { ($_.Attributes -band [System.IO.FileAttributes]::ReadOnly) -eq 0 })
if ($notReadonlyDirs.Count -ne 0) { throw ('NOT_READONLY_DIRS=' + $notReadonlyDirs.Count) }

Write-Output ('PREMARKER_SEAL_READY=1')
Write-Output ('MANIFEST_ROWS=' + $manifestRows.Count)
Write-Output ('MANIFEST_SHA256=' + (Get-FileHash -LiteralPath $manifest -Algorithm SHA256).Hash.ToUpperInvariant())
Write-Output ('NONDEFAULT_ADS=0')
Write-Output ('REPARSE_ITEMS=0')
Write-Output ('CACHE_PYC_ITEMS=0')
Write-Output ('NOT_READONLY_FILES=0')
Write-Output ('NOT_READONLY_DIRS=0')
