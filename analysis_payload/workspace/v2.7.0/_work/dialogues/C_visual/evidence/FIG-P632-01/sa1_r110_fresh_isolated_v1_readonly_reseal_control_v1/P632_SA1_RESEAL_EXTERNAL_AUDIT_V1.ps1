param(
    [Parameter(Mandatory = $true)][string]$OldRoot,
    [Parameter(Mandatory = $true)][string]$NewRoot,
    [Parameter(Mandatory = $true)][string]$OutputPath
)

$ErrorActionPreference = 'Stop'
$utf8NoBom = [System.Text.UTF8Encoding]::new($false)

function Get-Sha256([string]$Path) { (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToUpperInvariant() }
function Rel([string]$Base, [string]$Path) { [IO.Path]::GetRelativePath($Base, $Path).Replace('/', '\') }

$oldResolved = (Resolve-Path -LiteralPath $OldRoot).Path
$newResolved = (Resolve-Path -LiteralPath $NewRoot).Path
$manifestPath = Join-Path $newResolved 'PAYLOAD_MANIFEST.json'
$sealPath = Join-Path $newResolved 'SEAL_AUDIT.json'
$wstopPath = Join-Path $newResolved 'WRITE_STOPPED'
$identityPath = Join-Path $newResolved 'COPY_IDENTITY.csv'
$provenancePath = Join-Path $newResolved 'COPY_PROVENANCE.json'
$manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
$seal = Get-Content -LiteralPath $sealPath -Raw | ConvertFrom-Json
$wstop = Get-Content -LiteralPath $wstopPath -Raw | ConvertFrom-Json
$provenance = Get-Content -LiteralPath $provenancePath -Raw | ConvertFrom-Json
$identity = @(Import-Csv -LiteralPath $identityPath)
$files = @(Get-ChildItem -LiteralPath $newResolved -File -Recurse)
$dirs = @((Get-Item -LiteralPath $newResolved)) + @(Get-ChildItem -LiteralPath $newResolved -Directory -Recurse)
$rows = @($manifest.entries)

$duplicate = @($rows.path | Group-Object | Where-Object Count -gt 1).Count
$missing = 0
$bytesMismatch = 0
$shaMismatch = 0
$ticksMismatch = 0
foreach ($row in $rows) {
    $path = Join-Path $newResolved $row.path
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { $missing++; continue }
    $item = Get-Item -LiteralPath $path
    if ($item.Length -ne [int64]$row.bytes) { $bytesMismatch++ }
    if ((Get-Sha256 $path) -ne $row.sha256.ToUpperInvariant()) { $shaMismatch++ }
    if ($item.LastWriteTimeUtc.Ticks -ne [int64]$row.mtime_utc_ticks) { $ticksMismatch++ }
}
$allowedControls = @('PAYLOAD_MANIFEST.json', 'SEAL_AUDIT.json', 'WRITE_STOPPED')
$extra = @($files | ForEach-Object { Rel $newResolved $_.FullName } | Where-Object { $_ -notin @($rows.path) -and $_ -notin $allowedControls }).Count
$oldControlCopied = @($rows.path | Where-Object { $_ -in @('MANIFEST.json', 'WRITE_STOPPED') }).Count

$identityPathMismatch = 0
$identityBytesMismatch = 0
$identityShaMismatch = 0
$identityTicksMismatch = 0
foreach ($row in $identity) {
    $source = Get-Item -LiteralPath $row.source_resolved_path
    $destination = Get-Item -LiteralPath $row.destination_resolved_path
    if ((Rel $oldResolved $source.FullName) -ne $row.relative_path -or (Rel $newResolved $destination.FullName) -ne $row.relative_path) { $identityPathMismatch++ }
    if ($source.Length -ne $destination.Length -or $source.Length -ne [int64]$row.source_bytes -or $destination.Length -ne [int64]$row.destination_bytes) { $identityBytesMismatch++ }
    if ((Get-Sha256 $source.FullName) -ne (Get-Sha256 $destination.FullName) -or (Get-Sha256 $source.FullName) -ne $row.source_sha256 -or (Get-Sha256 $destination.FullName) -ne $row.destination_sha256) { $identityShaMismatch++ }
    if ($source.LastWriteTimeUtc.Ticks -ne $destination.LastWriteTimeUtc.Ticks -or $source.LastWriteTimeUtc.Ticks -ne [int64]$row.source_mtime_utc_ticks -or $destination.LastWriteTimeUtc.Ticks -ne [int64]$row.destination_mtime_utc_ticks) { $identityTicksMismatch++ }
}

$jsonFailures = 0
$csvFailures = 0
foreach ($file in $files) {
    if ($file.Extension -ieq '.json') { try { Get-Content -LiteralPath $file.FullName -Raw | ConvertFrom-Json | Out-Null } catch { $jsonFailures++ } }
    elseif ($file.Extension -ieq '.csv') { try { Import-Csv -LiteralPath $file.FullName | Out-Null } catch { $csvFailures++ } }
}
$ads = 0
foreach ($file in $files) { $ads += @(Get-Item -LiteralPath $file.FullName -Stream * | Where-Object { $_.Stream -ne ':$DATA' }).Count }
$cache = @($files | Where-Object { $_.Name -match '\.(pyc|pyo)$' -or $_.FullName -match '([\\/])(__pycache__|\.cache)([\\/]|$)' }).Count
$reparse = @($files + $dirs | Where-Object { $_.Attributes -band [IO.FileAttributes]::ReparsePoint }).Count
$writableFiles = @($files | Where-Object { -not $_.IsReadOnly }).Count
$writableDirs = @($dirs | Where-Object { -not ($_.Attributes -band [IO.FileAttributes]::ReadOnly) }).Count
$marker = Get-Item -LiteralPath $wstopPath
$atOrAfter = @($files | Where-Object { $_.FullName -ne $marker.FullName -and $_.LastWriteTimeUtc -ge $marker.LastWriteTimeUtc }).Count
$manifestSha = Get-Sha256 $manifestPath
$sealSha = Get-Sha256 $sealPath

$pass = (
    $identity.Count -eq 46 -and $rows.Count -eq 48 -and $files.Count -eq 51 -and
    $duplicate -eq 0 -and $missing -eq 0 -and $extra -eq 0 -and
    $bytesMismatch -eq 0 -and $shaMismatch -eq 0 -and $ticksMismatch -eq 0 -and
    $oldControlCopied -eq 0 -and $identityPathMismatch -eq 0 -and
    $identityBytesMismatch -eq 0 -and $identityShaMismatch -eq 0 -and $identityTicksMismatch -eq 0 -and
    $jsonFailures -eq 0 -and $csvFailures -eq 0 -and $ads -eq 0 -and $cache -eq 0 -and $reparse -eq 0 -and
    $writableFiles -eq 0 -and $writableDirs -eq 0 -and $atOrAfter -eq 0 -and
    $manifestSha -eq $wstop.payload_manifest_sha256 -and $sealSha -eq $wstop.seal_audit_sha256 -and
    $wstop.postmarker_content_writes -eq 0 -and
    $provenance.original_root -eq $oldResolved -and $provenance.destination_root -eq $newResolved
)

$audit = [ordered]@{
    schema_version = '1.0'
    audit = 'root-external read-only P632 SA1 evidence reseal audit'
    audited_utc = [DateTime]::UtcNow.ToString('o')
    old_root = $oldResolved
    new_root = $newResolved
    pass = $pass
    counts = [ordered]@{ source_material = 46; copy_identity_rows = $identity.Count; payload_manifest_rows = $rows.Count; payload = 48; controls = 3; ordinary = $files.Count; directories = $dirs.Count }
    source_destination = [ordered]@{ path_mismatch = $identityPathMismatch; bytes_mismatch = $identityBytesMismatch; sha256_mismatch = $identityShaMismatch; mtime_ticks_mismatch = $identityTicksMismatch }
    manifest_filesystem = [ordered]@{ duplicate = $duplicate; missing = $missing; extra = $extra; bytes_mismatch = $bytesMismatch; sha256_mismatch = $shaMismatch; mtime_ticks_mismatch = $ticksMismatch; old_controls_copied = $oldControlCopied }
    readonly = [ordered]@{ files_readonly = $files.Count - $writableFiles; files_total = $files.Count; writable_files = $writableFiles; directories_readonly = $dirs.Count - $writableDirs; directories_total = $dirs.Count; writable_directories = $writableDirs }
    hygiene = [ordered]@{ json_parse_failures = $jsonFailures; csv_parse_failures = $csvFailures; ads = $ads; cache_pyc_pyo = $cache; reparse = $reparse }
    marker = [ordered]@{ unique_strict_latest = ($atOrAfter -eq 0); at_or_after_excluding_marker = $atOrAfter; mtime_utc = $marker.LastWriteTimeUtc.ToString('o'); mtime_utc_ticks = $marker.LastWriteTimeUtc.Ticks; postmarker_content_writes = $wstop.postmarker_content_writes }
    controls = [ordered]@{ payload_manifest_bytes = (Get-Item $manifestPath).Length; payload_manifest_sha256 = $manifestSha; seal_audit_bytes = (Get-Item $sealPath).Length; seal_audit_sha256 = $sealSha; write_stopped_bytes = (Get-Item $wstopPath).Length; write_stopped_sha256 = Get-Sha256 $wstopPath }
}

$tmp = $OutputPath + '.tmp-' + [Guid]::NewGuid().ToString('N')
[IO.File]::WriteAllText($tmp, ($audit | ConvertTo-Json -Depth 30), $utf8NoBom)
[IO.File]::Move($tmp, $OutputPath)
if (-not $pass) { exit 1 }
exit 0
