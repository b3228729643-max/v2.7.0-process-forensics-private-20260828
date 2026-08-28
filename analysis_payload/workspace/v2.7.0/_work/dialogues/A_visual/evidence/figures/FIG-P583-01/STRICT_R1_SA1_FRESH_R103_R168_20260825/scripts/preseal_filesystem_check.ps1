param([Parameter(Mandatory = $true)][string]$EvidenceRoot)
$ErrorActionPreference = 'Stop'
$root = $EvidenceRoot
$files = @(Get-ChildItem -LiteralPath $root -Recurse -File)
$namedStreams = @()
foreach ($file in $files) {
    $streams = @(Get-Item -LiteralPath $file.FullName -Stream * -ErrorAction Stop)
    foreach ($stream in $streams) {
        if ($stream.Stream -ne ':$DATA') {
            $namedStreams += [pscustomobject]@{ Path = $file.FullName; Stream = $stream.Stream; Length = $stream.Length }
        }
    }
}
$cacheDirs = @(Get-ChildItem -LiteralPath $root -Recurse -Directory | Where-Object { $_.Name -in @('__pycache__','.pytest_cache','.mypy_cache','.ruff_cache') })
$pycFiles = @(Get-ChildItem -LiteralPath $root -Recurse -File | Where-Object { $_.Extension -in @('.pyc','.pyo') })
$colonNames = @($files | Where-Object { $_.Name.Contains(':') })
$result = [ordered]@{
    evidence_root = $root
    ordinary_file_count = $files.Count
    named_ads_count = $namedStreams.Count
    named_ads = $namedStreams
    pyc_pyo_count = $pycFiles.Count
    cache_directory_count = $cacheDirs.Count
    colon_filename_count = $colonNames.Count
    pass = ($namedStreams.Count -eq 0 -and $pycFiles.Count -eq 0 -and $cacheDirs.Count -eq 0 -and $colonNames.Count -eq 0)
    check_is_machine_only = $true
    manual_fields_generated = $false
}
$json = $result | ConvertTo-Json -Depth 6
$out = Join-Path $root 'machine\preseal_filesystem_check.json'
[System.IO.File]::WriteAllText($out, $json + [Environment]::NewLine, [System.Text.UTF8Encoding]::new($false))
if (-not $result.pass) { throw 'Preseal filesystem check failed.' }
$json
