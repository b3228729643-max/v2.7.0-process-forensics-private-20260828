param(
    [Parameter(Mandatory = $true)][string]$ZipPath,
    [Parameter(Mandatory = $true)][string]$Destination,
    [switch]$StripSingleTopLevelDirectory
)

$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.IO.Compression.FileSystem

$resolvedZip = [System.IO.Path]::GetFullPath($ZipPath)
$resolvedDestination = [System.IO.Path]::GetFullPath($Destination)
if (-not [System.IO.File]::Exists($resolvedZip)) { throw "ZIP not found: $resolvedZip" }

if ([System.IO.Directory]::Exists($resolvedDestination)) {
    if ((Get-ChildItem -LiteralPath $resolvedDestination -Force | Select-Object -First 1)) {
        throw "Destination is not empty: $resolvedDestination"
    }
}
else {
    [System.IO.Directory]::CreateDirectory($resolvedDestination) | Out-Null
}

$destinationPrefix = $resolvedDestination.TrimEnd([System.IO.Path]::DirectorySeparatorChar) + [System.IO.Path]::DirectorySeparatorChar
$archive = [System.IO.Compression.ZipFile]::OpenRead($resolvedZip)
try {
    $entries = @($archive.Entries)
    $topLevel = $null
    if ($StripSingleTopLevelDirectory) {
        $topNames = @($entries | ForEach-Object {
            $normalized = $_.FullName.Replace('\', '/')
            ($normalized.Split('/', [System.StringSplitOptions]::RemoveEmptyEntries) | Select-Object -First 1)
        } | Where-Object { $_ } | Sort-Object -Unique)
        if ($topNames.Count -ne 1) { throw 'ZIP does not have exactly one top-level entry.' }
        $topLevel = $topNames[0]
    }

    $planned = [System.Collections.Generic.List[object]]::new()
    foreach ($entry in $entries) {
        $normalized = $entry.FullName.Replace('\', '/')
        $segments = @($normalized.Split('/', [System.StringSplitOptions]::RemoveEmptyEntries))
        if ([System.IO.Path]::IsPathRooted($normalized) -or ($segments -contains '..') -or $normalized.StartsWith('/')) {
            throw "Unsafe ZIP entry: $normalized"
        }

        $relativeName = $normalized
        if ($StripSingleTopLevelDirectory) {
            if ($normalized -eq $topLevel -or $normalized -eq "$topLevel/") { continue }
            $prefix = "$topLevel/"
            if (-not $normalized.StartsWith($prefix, [System.StringComparison]::Ordinal)) {
                throw "Entry is outside expected top-level directory: $normalized"
            }
            $relativeName = $normalized.Substring($prefix.Length)
        }
        if ([string]::IsNullOrWhiteSpace($relativeName)) { continue }

        $target = [System.IO.Path]::GetFullPath((Join-Path $resolvedDestination $relativeName))
        if (-not $target.StartsWith($destinationPrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
            throw "Entry escapes destination: $normalized"
        }
        $planned.Add([pscustomobject]@{ Entry = $entry; Target = $target; RelativeName = $relativeName })
    }

    $fileCount = 0
    foreach ($item in $planned) {
        if ([string]::IsNullOrEmpty($item.Entry.Name)) {
            [System.IO.Directory]::CreateDirectory($item.Target) | Out-Null
            continue
        }
        $parent = [System.IO.Path]::GetDirectoryName($item.Target)
        [System.IO.Directory]::CreateDirectory($parent) | Out-Null
        [System.IO.Compression.ZipFileExtensions]::ExtractToFile($item.Entry, $item.Target, $false)
        $fileCount += 1
    }

    Write-Output "ZIP=$resolvedZip"
    Write-Output "DESTINATION=$resolvedDestination"
    Write-Output "STRIPPED_TOP_LEVEL=$topLevel"
    Write-Output "EXTRACTED_FILES=$fileCount"
}
finally {
    $archive.Dispose()
}
