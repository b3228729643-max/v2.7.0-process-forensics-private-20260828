param(
  [Parameter(Mandatory=$true)][string]$Root
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

function Write-Utf8NoBom([string]$Path, [string]$Text) {
  [IO.File]::WriteAllText($Path, $Text, [Text.UTF8Encoding]::new($false))
}

function Get-Sha256([string]$Path) {
  return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToUpperInvariant()
}

function Get-RelativeForward([string]$Base, [string]$Path) {
  return ([IO.Path]::GetRelativePath($Base, $Path) -replace '\\','/')
}

function Csv-Escape([string]$Value) {
  return '"' + ($Value -replace '"','""') + '"'
}

$resolvedRoot = [IO.Path]::GetFullPath($Root)
if (-not [IO.Directory]::Exists($resolvedRoot)) { throw "Root does not exist: $resolvedRoot" }

$controlNames = @(
  'PAYLOAD_MANIFEST.csv',
  'PAYLOAD_MANIFEST.json',
  'PRESEAL_VALIDATION.json',
  'WRITE_STOPPED.json'
)
foreach ($name in $controlNames) {
  if ([IO.File]::Exists([IO.Path]::Combine($resolvedRoot, $name))) {
    throw "Control already exists: $name"
  }
}

$payloadFiles = @(Get-ChildItem -LiteralPath $resolvedRoot -Recurse -Force -File | Sort-Object FullName)
if ($payloadFiles.Count -lt 1) { throw 'Payload is empty' }

$payloadRows = @()
foreach ($file in $payloadFiles) {
  $payloadRows += [ordered]@{
    relative_path = Get-RelativeForward $resolvedRoot $file.FullName
    bytes = [int64]$file.Length
    sha256 = Get-Sha256 $file.FullName
    mtime_utc_ticks = $file.LastWriteTimeUtc.Ticks.ToString()
  }
}

$duplicatePaths = @($payloadRows | Group-Object relative_path | Where-Object { $_.Count -ne 1 })
if ($duplicatePaths.Count -ne 0) { throw 'Duplicate payload paths' }

$manifestCsvPath = [IO.Path]::Combine($resolvedRoot, 'PAYLOAD_MANIFEST.csv')
$csvLines = [Collections.Generic.List[string]]::new()
$csvLines.Add('relative_path,bytes,sha256,mtime_utc_ticks')
foreach ($row in $payloadRows) {
  $csvLines.Add((Csv-Escape $row.relative_path) + ',' + $row.bytes + ',' + $row.sha256 + ',' + $row.mtime_utc_ticks)
}
Write-Utf8NoBom $manifestCsvPath (($csvLines -join "`n") + "`n")

$manifestJsonPath = [IO.Path]::Combine($resolvedRoot, 'PAYLOAD_MANIFEST.json')
$manifestObject = [ordered]@{
  schema = 'P067_R3_PAYLOAD_MANIFEST_V1'
  resolved_root = $resolvedRoot
  payload_count = $payloadRows.Count
  rows = $payloadRows
}
Write-Utf8NoBom $manifestJsonPath (($manifestObject | ConvertTo-Json -Depth 8) + "`n")

$jsonRoundTrip = Get-Content -LiteralPath $manifestJsonPath -Raw -Encoding UTF8 | ConvertFrom-Json
$csvRoundTrip = @(Import-Csv -LiteralPath $manifestCsvPath -Encoding UTF8)
if ($jsonRoundTrip.rows.Count -ne $payloadRows.Count) { throw 'JSON manifest row count mismatch' }
if ($csvRoundTrip.Count -ne $payloadRows.Count) { throw 'CSV manifest row count mismatch' }

$livePayload = @(Get-ChildItem -LiteralPath $resolvedRoot -Recurse -Force -File | Where-Object { $controlNames -notcontains $_.Name } | Sort-Object FullName)
if ($livePayload.Count -ne $payloadRows.Count) { throw 'Live payload count mismatch before seal' }

$identityErrors = [Collections.Generic.List[string]]::new()
for ($i = 0; $i -lt $payloadRows.Count; $i++) {
  $expected = $payloadRows[$i]
  $actual = $livePayload[$i]
  $actualRel = Get-RelativeForward $resolvedRoot $actual.FullName
  if ($actualRel -cne $expected.relative_path) { $identityErrors.Add("path:$i") }
  if ([int64]$actual.Length -ne [int64]$expected.bytes) { $identityErrors.Add("bytes:$actualRel") }
  if ((Get-Sha256 $actual.FullName) -cne $expected.sha256) { $identityErrors.Add("sha:$actualRel") }
  if ($actual.LastWriteTimeUtc.Ticks.ToString() -cne $expected.mtime_utc_ticks) { $identityErrors.Add("ticks:$actualRel") }
  $csv = $csvRoundTrip[$i]
  $json = $jsonRoundTrip.rows[$i]
  if ($csv.relative_path -cne $expected.relative_path -or $json.relative_path -cne $expected.relative_path) { $identityErrors.Add("manifest-path:$i") }
  if ($csv.bytes -cne $expected.bytes.ToString() -or $json.bytes.ToString() -cne $expected.bytes.ToString()) { $identityErrors.Add("manifest-bytes:$i") }
  if ($csv.sha256 -cne $expected.sha256 -or $json.sha256 -cne $expected.sha256) { $identityErrors.Add("manifest-sha:$i") }
  if ($csv.mtime_utc_ticks -cne $expected.mtime_utc_ticks -or $json.mtime_utc_ticks -cne $expected.mtime_utc_ticks) { $identityErrors.Add("manifest-ticks:$i") }
}
if ($identityErrors.Count -ne 0) { throw "Preseal identity errors: $($identityErrors.Count)" }

$presealPath = [IO.Path]::Combine($resolvedRoot, 'PRESEAL_VALIDATION.json')
$preseal = [ordered]@{
  schema = 'P067_R3_PRESEAL_VALIDATION_V1'
  validated_at_utc = [DateTime]::UtcNow.ToString('o')
  resolved_root = $resolvedRoot
  payload_count = $payloadRows.Count
  manifest_control_count = 2
  preseal_control_count = 1
  write_stopped_control_count = 1
  control_count = 4
  projected_ordinary_count = $payloadRows.Count + 4
  duplicate_path_count = $duplicatePaths.Count
  identity_error_count = $identityErrors.Count
  manual_content_regenerated = $false
  business_evidence_rerun = $false
  status = 'PASS_READY_FOR_FINAL_MARKER'
}
Write-Utf8NoBom $presealPath (($preseal | ConvertTo-Json -Depth 6) + "`n")

$premarkerFiles = @(Get-ChildItem -LiteralPath $resolvedRoot -Recurse -Force -File)
if ($premarkerFiles.Count -ne ($payloadRows.Count + 3)) { throw 'Pre-marker ordinary count mismatch' }

foreach ($file in $premarkerFiles) {
  $file.Attributes = $file.Attributes -bor [IO.FileAttributes]::ReadOnly
}
$dirs = @(Get-ChildItem -LiteralPath $resolvedRoot -Recurse -Force -Directory | Sort-Object { $_.FullName.Length } -Descending)
foreach ($dir in $dirs) {
  $dir.Attributes = $dir.Attributes -bor [IO.FileAttributes]::ReadOnly
}
$rootItem = Get-Item -LiteralPath $resolvedRoot -Force
$rootItem.Attributes = $rootItem.Attributes -bor [IO.FileAttributes]::ReadOnly

$readonlyFileFailures = @($premarkerFiles | Where-Object { -not ((Get-Item -LiteralPath $_.FullName -Force).Attributes -band [IO.FileAttributes]::ReadOnly) })
if ($readonlyFileFailures.Count -ne 0) { throw 'Premarker file readonly failure' }
$allDirs = @((Get-Item -LiteralPath $resolvedRoot -Force)) + @(Get-ChildItem -LiteralPath $resolvedRoot -Recurse -Force -Directory)
$readonlyDirFailures = @($allDirs | Where-Object { -not ($_.Attributes -band [IO.FileAttributes]::ReadOnly) })
if ($readonlyDirFailures.Count -ne 0) { throw 'Premarker directory readonly failure' }

$maxPremarkerTicks = ($premarkerFiles | Measure-Object -Property LastWriteTimeUtc -Maximum).Maximum.Ticks
$markerTemp = [IO.Path]::Combine([IO.Path]::GetDirectoryName($resolvedRoot), '.P067_R3_WRITE_STOPPED_' + [Guid]::NewGuid().ToString('N') + '.json')
$markerFinal = [IO.Path]::Combine($resolvedRoot, 'WRITE_STOPPED.json')
$markerTicks = [Math]::Max([DateTime]::UtcNow.AddSeconds(5).Ticks, $maxPremarkerTicks + 1)
$marker = [ordered]@{
  schema = 'P067_R3_WRITE_STOPPED_V1'
  resolved_root = $resolvedRoot
  stopped_at_utc = ([DateTime]::new($markerTicks, [DateTimeKind]::Utc)).ToString('o')
  payload_count = $payloadRows.Count
  manifest_control_count = 2
  preseal_control_count = 1
  write_stopped_control_count = 1
  control_count = 4
  ordinary_count = $payloadRows.Count + 4
  max_premarker_ticks = $maxPremarkerTicks.ToString()
  write_stopped_ticks = $markerTicks.ToString()
  final_root_content_operation = 'Move prebuilt read-only WRITE_STOPPED.json into root'
  postmarker_root_writes_authorized = 0
}
Write-Utf8NoBom $markerTemp (($marker | ConvertTo-Json -Depth 6) + "`n")
[IO.File]::SetLastWriteTimeUtc($markerTemp, [DateTime]::new($markerTicks, [DateTimeKind]::Utc))
$markerTempItem = Get-Item -LiteralPath $markerTemp -Force
$markerTempItem.Attributes = $markerTempItem.Attributes -bor [IO.FileAttributes]::ReadOnly
Move-Item -LiteralPath $markerTemp -Destination $markerFinal

[pscustomobject]@{
  status = 'SEALED'
  resolved_root = $resolvedRoot
  payload_count = $payloadRows.Count
  control_count = 4
  ordinary_count = $payloadRows.Count + 4
  manifest_csv_sha256 = Get-Sha256 $manifestCsvPath
  manifest_json_sha256 = Get-Sha256 $manifestJsonPath
  preseal_sha256 = Get-Sha256 $presealPath
  write_stopped_sha256 = Get-Sha256 $markerFinal
  write_stopped_ticks = $markerTicks.ToString()
  max_premarker_ticks = $maxPremarkerTicks.ToString()
  write_stopped_margin_ticks = ($markerTicks - $maxPremarkerTicks).ToString()
} | ConvertTo-Json -Depth 5
