$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$Root = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\STRICT_R11_SA2_STATIC_LABEL6_REPOSITION_R115_20260828'
$Stage = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\P126_R11_STATIC_WRITE_STOPPED_STAGE_20260828.tmp'
$Result = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\P126_R11_STATIC_SEAL_CONTROLLER_RESULT_20260828.json'
$ControlNames = @('PAYLOAD_MANIFEST.csv', 'SEAL_AUDIT.json', 'WRITE_STOPPED')

function Get-Hash([string]$Path) {
    (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToUpperInvariant()
}
function Get-Rel([string]$Path) {
    [IO.Path]::GetRelativePath($Root, $Path).Replace('\', '/')
}
function Get-Ticks([datetime]$Value) {
    $Value.ToUniversalTime().Ticks
}
function Set-FileReadOnly([string]$Path) {
    $item = Get-Item -LiteralPath $Path -Force
    $item.IsReadOnly = $true
}
function Set-DirectoryReadOnly([string]$Path) {
    $item = Get-Item -LiteralPath $Path -Force
    $item.Attributes = $item.Attributes -bor [IO.FileAttributes]::ReadOnly
}
function Get-TreeSnapshot {
    $rows = [Collections.Generic.List[string]]::new()
    foreach ($file in @(Get-ChildItem -LiteralPath $Root -Recurse -Force -File | Sort-Object FullName)) {
        $rows.Add(('F`t{0}`t{1}`t{2}`t{3}`t{4}`t{5}' -f (Get-Rel $file.FullName), $file.Length, (Get-Hash $file.FullName), (Get-Ticks $file.CreationTimeUtc), (Get-Ticks $file.LastWriteTimeUtc), [int]$file.Attributes))
    }
    foreach ($dir in @((Get-Item -LiteralPath $Root -Force)) + @(Get-ChildItem -LiteralPath $Root -Recurse -Force -Directory | Sort-Object FullName)) {
        $relative = if ($dir.FullName -eq $Root) { '.' } else { Get-Rel $dir.FullName }
        $rows.Add(('D`t{0}`t{1}`t{2}`t{3}' -f $relative, (Get-Ticks $dir.CreationTimeUtc), (Get-Ticks $dir.LastWriteTimeUtc), [int]$dir.Attributes))
    }
    $bytes = [Text.UTF8Encoding]::new($false).GetBytes((($rows -join "`n") + "`n"))
    [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($bytes))
}
function Test-MarkerLines([string[]]$Lines) {
    $bad = @($Lines | Where-Object { $_ -notmatch '^[A-Z0-9_]+=[^=\t\r\n]+$' })
    $keys = @($Lines | ForEach-Object { ($_ -split '=', 2)[0] })
    $duplicate = @($keys | Group-Object -CaseSensitive | Where-Object { $_.Count -ne 1 })
    [pscustomobject]@{ Bad = $bad.Count; Duplicate = $duplicate.Count }
}

if (-not (Test-Path -LiteralPath $Root -PathType Container)) { throw 'ROOT_MISSING' }
if (Test-Path -LiteralPath $Stage) { throw 'STAGE_EXISTS' }
if (Test-Path -LiteralPath $Result) { throw 'RESULT_EXISTS' }
foreach ($name in $ControlNames) {
    if (Test-Path -LiteralPath (Join-Path $Root $name)) { throw "CONTROL_EXISTS:$name" }
}

$payload = @(Get-ChildItem -LiteralPath $Root -Recurse -Force -File | Sort-Object FullName)
if ($payload.Count -ne 10) { throw "PAYLOAD_COUNT:$($payload.Count)" }
$rows = @($payload | ForEach-Object {
    [pscustomobject][ordered]@{
        relative_path = Get-Rel $_.FullName
        bytes = [int64]$_.Length
        sha256 = Get-Hash $_.FullName
        creation_time_utc_ticks = Get-Ticks $_.CreationTimeUtc
        last_write_time_utc_ticks = Get-Ticks $_.LastWriteTimeUtc
    }
})
$duplicates = @($rows | Group-Object -Property relative_path -CaseSensitive | Where-Object { $_.Count -ne 1 })
if ($duplicates.Count -ne 0) { throw 'DUPLICATE_PATH' }

$manifestPath = Join-Path $Root 'PAYLOAD_MANIFEST.csv'
$auditPath = Join-Path $Root 'SEAL_AUDIT.json'
$rows | Export-Csv -LiteralPath $manifestPath -NoTypeInformation -Encoding utf8
$audit = [ordered]@{
    schema = 'P126_R11_STATIC_SEAL_AUDIT_V1'
    handoff_id = 'A-R115-P126-SA2-STATIC-LABEL6-REPOSITION-R11-20260828'
    status = 'STATIC_ONLY_NOT_RENDERED_NOT_PASS'
    static_content_gate = 'PASS_READY_REQUEST_BUILD_SLOT'
    payload_count = 10
    control_count = 3
    ordinary_count = 13
    manifest_sha256 = Get-Hash $manifestPath
    source_sha256 = '81EFC188FA5E4827CAAB034C1EA3F7F4AFE25375DEE4046CD46F3FF49B0789BD'
    tex_invocations = 0
}
[IO.File]::WriteAllText($auditPath, (($audit | ConvertTo-Json -Depth 5) + "`n"), [Text.UTF8Encoding]::new($false))

$premarkerFiles = @(Get-ChildItem -LiteralPath $Root -Recurse -Force -File)
if ($premarkerFiles.Count -ne 12) { throw "PREMARKER_COUNT:$($premarkerFiles.Count)" }
foreach ($file in $premarkerFiles) { Set-FileReadOnly $file.FullName }
$childDirs = @(Get-ChildItem -LiteralPath $Root -Recurse -Force -Directory | Sort-Object { $_.FullName.Length } -Descending)
foreach ($dir in $childDirs) { Set-DirectoryReadOnly $dir.FullName }
Set-DirectoryReadOnly $Root

# Refresh the objects after attribute mutations; this is the real RO gate.
$checkedFiles = @(Get-ChildItem -LiteralPath $Root -Recurse -Force -File)
$checkedDirs = @((Get-Item -LiteralPath $Root -Force)) + @(Get-ChildItem -LiteralPath $Root -Recurse -Force -Directory)
$writableFiles = @($checkedFiles | Where-Object { -not $_.IsReadOnly })
$writableDirs = @($checkedDirs | Where-Object { ($_.Attributes -band [IO.FileAttributes]::ReadOnly) -eq 0 })
if ($writableFiles.Count -ne 0 -or $writableDirs.Count -ne 0) { throw 'RO_GATE' }

$maxTicks = (@($checkedFiles | ForEach-Object { $_.LastWriteTimeUtc.Ticks }) + @($checkedDirs | ForEach-Object { $_.LastWriteTimeUtc.Ticks }) | Measure-Object -Maximum).Maximum
$futureTicks = [Math]::Max([DateTime]::UtcNow.AddMinutes(5).Ticks, [int64]$maxTicks + [TimeSpan]::FromMinutes(2).Ticks)
$markerLines = @(
    'SCHEMA=P126_R11_STATIC_WRITE_STOPPED_V1',
    'HANDOFF_ID=A-R115-P126-SA2-STATIC-LABEL6-REPOSITION-R11-20260828',
    'UID=FIG-P126-01',
    'STATUS=STATIC_ONLY_NOT_RENDERED_NOT_PASS',
    'STATIC_CONTENT_GATE=PASS_READY_REQUEST_BUILD_SLOT',
    'PAYLOAD_COUNT=10',
    'CONTROL_COUNT=3',
    'ORDINARY_COUNT=13',
    'SOURCE_SHA256=81EFC188FA5E4827CAAB034C1EA3F7F4AFE25375DEE4046CD46F3FF49B0789BD',
    ('MANIFEST_SHA256=' + (Get-Hash $manifestPath)),
    ('SEAL_AUDIT_SHA256=' + (Get-Hash $auditPath)),
    'TEX_INVOCATIONS=0',
    'CONTROLLER_INVOCATION_COUNT=1',
    'CONTROLLER_RETRY_COUNT=0',
    'POSTMARKER_WRITES=0'
)
$markerTest = Test-MarkerLines $markerLines
if ($markerTest.Bad -ne 0 -or $markerTest.Duplicate -ne 0) { throw 'MARKER_GATE' }
[IO.File]::WriteAllLines($Stage, $markerLines, [Text.UTF8Encoding]::new($false))
Set-FileReadOnly $Stage
[IO.File]::SetLastWriteTimeUtc($Stage, [DateTime]::new($futureTicks, [DateTimeKind]::Utc))
Set-FileReadOnly $Stage
$stageInfo = Get-Item -LiteralPath $Stage -Force
if (-not $stageInfo.IsReadOnly -or $stageInfo.LastWriteTimeUtc.Ticks -le $maxTicks) { throw 'STAGE_GATE' }

$markerPath = Join-Path $Root 'WRITE_STOPPED'
Move-Item -LiteralPath $Stage -Destination $markerPath

$snapshot1 = Get-TreeSnapshot
Start-Sleep -Milliseconds 300
$snapshot2 = Get-TreeSnapshot
if ($snapshot1 -ne $snapshot2) { throw 'POSTMARKER_CHANGE' }
$finalFiles = @(Get-ChildItem -LiteralPath $Root -Recurse -Force -File)
$finalDirs = @((Get-Item -LiteralPath $Root -Force)) + @(Get-ChildItem -LiteralPath $Root -Recurse -Force -Directory)
$marker = Get-Item -LiteralPath $markerPath -Force
$atOrAfter = @($finalFiles + $finalDirs | Where-Object { $_.FullName -ne $marker.FullName -and $_.LastWriteTimeUtc.Ticks -ge $marker.LastWriteTimeUtc.Ticks })
$nonMarkerMax = ($finalFiles + $finalDirs | Where-Object { $_.FullName -ne $marker.FullName } | ForEach-Object { $_.LastWriteTimeUtc.Ticks } | Measure-Object -Maximum).Maximum
if ($finalFiles.Count -ne 13 -or @($finalFiles | Where-Object { -not $_.IsReadOnly }).Count -ne 0 -or @($finalDirs | Where-Object { ($_.Attributes -band [IO.FileAttributes]::ReadOnly) -eq 0 }).Count -ne 0 -or $atOrAfter.Count -ne 0) { throw 'FINAL_GATE' }

$output = [ordered]@{
    schema = 'P126_R11_STATIC_SEAL_CONTROLLER_RESULT_V1'
    invocation_count = 1
    retry_count = 0
    exit = 0
    payload_count = 10
    control_count = 3
    ordinary_count = 13
    directories_including_root = $finalDirs.Count
    readonly_files = $finalFiles.Count
    readonly_directories = $finalDirs.Count
    marker_sha256 = Get-Hash $markerPath
    marker_ticks = $marker.LastWriteTimeUtc.Ticks
    strict_latest_margin_ticks = [int64]$marker.LastWriteTimeUtc.Ticks - [int64]$nonMarkerMax
    at_or_after = 0
    postmarker_snapshot1 = $snapshot1
    postmarker_snapshot2 = $snapshot2
    postmarker_writes = 0
}
[IO.File]::WriteAllText($Result, (($output | ConvertTo-Json -Depth 5) + "`n"), [Text.UTF8Encoding]::new($false))
$output | ConvertTo-Json -Compress
