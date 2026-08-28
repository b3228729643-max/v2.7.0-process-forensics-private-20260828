param(
    [Parameter(Mandatory = $true)][string]$ZipPath,
    [Parameter(Mandatory = $true)][string]$ManifestPath
)

$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.IO.Compression.FileSystem

$resolvedZip = [System.IO.Path]::GetFullPath($ZipPath)
if (-not [System.IO.File]::Exists($resolvedZip)) {
    throw "ZIP not found: $resolvedZip"
}

$archive = [System.IO.Compression.ZipFile]::OpenRead($resolvedZip)
try {
    $entries = [System.Collections.Generic.List[object]]::new()
    $unsafe = [System.Collections.Generic.List[string]]::new()
    $topLevel = @{}
    $totalUncompressed = [int64]0
    $totalCompressed = [int64]0

    foreach ($entry in $archive.Entries) {
        $name = $entry.FullName.Replace('\', '/')
        $segments = $name.Split('/', [System.StringSplitOptions]::RemoveEmptyEntries)
        if ($segments.Count -gt 0) {
            $top = $segments[0]
            if (-not $topLevel.ContainsKey($top)) { $topLevel[$top] = 0 }
            $topLevel[$top] += 1
        }

        $isUnsafe = [System.IO.Path]::IsPathRooted($name) -or ($segments -contains '..') -or $name.StartsWith('/')
        if ($isUnsafe) { $unsafe.Add($name) }
        $totalUncompressed += $entry.Length
        $totalCompressed += $entry.CompressedLength
        $entries.Add([ordered]@{
            name = $name
            length = $entry.Length
            compressedLength = $entry.CompressedLength
            isDirectory = [string]::IsNullOrEmpty($entry.Name)
            lastWriteTime = $entry.LastWriteTime.ToString('o')
        })
    }

    $manifest = [ordered]@{
        zipPath = $resolvedZip
        entryCount = $entries.Count
        unsafeEntryCount = $unsafe.Count
        unsafeEntries = $unsafe
        totalUncompressedBytes = $totalUncompressed
        totalCompressedBytes = $totalCompressed
        topLevel = [ordered]@{}
        entries = $entries
    }
    foreach ($key in ($topLevel.Keys | Sort-Object)) {
        $manifest.topLevel[$key] = $topLevel[$key]
    }

    $manifestDir = [System.IO.Path]::GetDirectoryName([System.IO.Path]::GetFullPath($ManifestPath))
    [System.IO.Directory]::CreateDirectory($manifestDir) | Out-Null
    $json = $manifest | ConvertTo-Json -Depth 8
    [System.IO.File]::WriteAllText([System.IO.Path]::GetFullPath($ManifestPath), $json, [System.Text.UTF8Encoding]::new($false))

    Write-Output "ZIP=$resolvedZip"
    Write-Output "ENTRY_COUNT=$($entries.Count)"
    Write-Output "UNSAFE_ENTRY_COUNT=$($unsafe.Count)"
    Write-Output "UNCOMPRESSED_BYTES=$totalUncompressed"
    Write-Output "COMPRESSED_BYTES=$totalCompressed"
    Write-Output 'TOP_LEVEL:'
    foreach ($key in ($topLevel.Keys | Sort-Object)) {
        Write-Output "  $key`t$($topLevel[$key])"
    }
    Write-Output "MANIFEST=$([System.IO.Path]::GetFullPath($ManifestPath))"
}
finally {
    $archive.Dispose()
}
