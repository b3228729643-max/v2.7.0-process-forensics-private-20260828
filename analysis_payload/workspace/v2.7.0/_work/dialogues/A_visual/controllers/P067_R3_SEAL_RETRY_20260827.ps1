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
function Get-DuplicateGroups([object[]]$Rows) {
  return @($Rows | Group-Object -Property { $_['relative_path'] } | Where-Object { $_.Count -ne 1 })
}

# StrictMode, empty-safe grouping microtests. These run before any root write.
$microEmpty = @(Get-DuplicateGroups @())
$microOne = @(Get-DuplicateGroups @([ordered]@{relative_path='a'}))
$microTwoUnique = @(Get-DuplicateGroups @([ordered]@{relative_path='a'},[ordered]@{relative_path='b'}))
$microDuplicate = @(Get-DuplicateGroups @([ordered]@{relative_path='a'},[ordered]@{relative_path='a'}))
if ($microEmpty.Count -ne 0) { throw 'Microtest empty failed' }
if ($microOne.Count -ne 0) { throw 'Microtest one failed' }
if ($microTwoUnique.Count -ne 0) { throw 'Microtest two-unique failed' }
if ($microDuplicate.Count -ne 1 -or $microDuplicate[0].Count -ne 2) { throw 'Microtest duplicate failed' }

$resolvedRoot = [IO.Path]::GetFullPath($Root)
if (-not [IO.Directory]::Exists($resolvedRoot)) { throw "Root does not exist: $resolvedRoot" }

$controlNames = @('PAYLOAD_MANIFEST.csv','PAYLOAD_MANIFEST.json','PRESEAL_VALIDATION.json','WRITE_STOPPED.json')
$controlPaths = @{}
foreach ($name in $controlNames) {
  $controlPath = [IO.Path]::Combine($resolvedRoot, $name)
  $controlPaths[$controlPath.ToUpperInvariant()] = $true
  if ([IO.File]::Exists($controlPath)) { throw "Control already exists: $name" }
}

$initialFiles = @(Get-ChildItem -LiteralPath $resolvedRoot -Recurse -Force -File)
if ($initialFiles.Count -ne 129) { throw "Initial ordinary count must be 129, got $($initialFiles.Count)" }

$requiredIdentities = @(
  [ordered]@{path='FINAL_CROSSCHECK.json';bytes=1022;sha='35B6995A92CD194F3304663910904EADB4DE42360DFF3173E02CEB6B7D9771B4'},
  [ordered]@{path='FINAL_RESULT.json';bytes=1460;sha='A681399BE56D3F6FDA4799C94412E92978827C8A86F53FA94829A69A32123D20'},
  [ordered]@{path='LOCAL_SA2_PASS_REPORT.md';bytes=2332;sha='22FA464A75C1DB4BA357B6CD1B5F7B177014413943AEB2A1B8D437B3BBEF8D6C'},
  [ordered]@{path='MACHINE_RESULT.json';bytes=424;sha='E9D48B3834BAD412B55D973B94F9547CE3E65060EBD2793CB36AD54330EDA6D8'}
)
foreach ($identity in $requiredIdentities) {
  $path = [IO.Path]::Combine($resolvedRoot, [string]$identity['path'])
  if (-not [IO.File]::Exists($path)) { throw "Required file missing: $($identity['path'])" }
  if ((Get-Item -LiteralPath $path).Length -ne [int64]$identity['bytes']) { throw "Required bytes mismatch: $($identity['path'])" }
  if ((Get-Sha256 $path) -cne [string]$identity['sha']) { throw "Required SHA mismatch: $($identity['path'])" }
}

$source = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_A_visual\src\绘图源码\第01册_数学基础与统计学习基本理论\V1-C04\fig_v1_c04_cdf.tex'
$wrapper = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_A_visual\src\讲义源码\合并总册\v260_FIG-P067-01_standalone.tex'
$pdf = [IO.Path]::Combine($resolvedRoot, 'build\v260_FIG-P067-01_standalone.pdf')
if ((Get-Sha256 $source) -cne 'C570597B72EEA4610380359A84EA078B24C810EC89039215BC9B42AB0F8AFFA0') { throw 'Source identity mismatch' }
if ((Get-Item -LiteralPath $source).Length -ne 4015) { throw 'Source bytes mismatch' }
if ((Get-Sha256 $wrapper) -cne 'ADDF75D1C82DAB9AB4D5A76E6B241DA1CEB7AED9C2E536106ECFD7710B2D14BF') { throw 'Wrapper identity mismatch' }
if ((Get-Item -LiteralPath $wrapper).Length -ne 388) { throw 'Wrapper bytes mismatch' }
if ((Get-Sha256 $pdf) -cne 'C1C06D877227E407F85678C0842182EE3629AEC78B62A4418C94A1D81860609E') { throw 'PDF identity mismatch' }
if ((Get-Item -LiteralPath $pdf).Length -ne 34208) { throw 'PDF bytes mismatch' }
$texProcesses = @(Get-Process -Name latexmk,lualatex,luatex,luahbtex -ErrorAction SilentlyContinue)
if ($texProcesses.Count -ne 0) { throw 'TeX process count is not zero' }

$payloadFiles = @($initialFiles | Sort-Object FullName)
$payloadRows = @()
foreach ($file in $payloadFiles) {
  $payloadRows += [ordered]@{
    relative_path = Get-RelativeForward $resolvedRoot $file.FullName
    bytes = [int64]$file.Length
    sha256 = Get-Sha256 $file.FullName
    mtime_utc_ticks = $file.LastWriteTimeUtc.Ticks.ToString()
  }
}
$duplicatePaths = @(Get-DuplicateGroups $payloadRows)
if ($duplicatePaths.Count -ne 0) { throw 'Duplicate payload paths' }

$manifestCsvPath = [IO.Path]::Combine($resolvedRoot, 'PAYLOAD_MANIFEST.csv')
$csvLines = [Collections.Generic.List[string]]::new()
$csvLines.Add('relative_path,bytes,sha256,mtime_utc_ticks')
foreach ($row in $payloadRows) {
  $csvLines.Add((Csv-Escape ([string]$row['relative_path'])) + ',' + $row['bytes'] + ',' + $row['sha256'] + ',' + $row['mtime_utc_ticks'])
}
Write-Utf8NoBom $manifestCsvPath (($csvLines -join "`n") + "`n")

$manifestJsonPath = [IO.Path]::Combine($resolvedRoot, 'PAYLOAD_MANIFEST.json')
$manifestObject = [ordered]@{
  schema = 'P067_R3_PAYLOAD_MANIFEST_V2'
  resolved_root = $resolvedRoot
  payload_count = $payloadRows.Count
  rows = $payloadRows
}
Write-Utf8NoBom $manifestJsonPath (($manifestObject | ConvertTo-Json -Depth 8) + "`n")

$jsonRoundTrip = Get-Content -LiteralPath $manifestJsonPath -Raw -Encoding UTF8 | ConvertFrom-Json
$csvRoundTrip = @(Import-Csv -LiteralPath $manifestCsvPath -Encoding UTF8)
if (@($jsonRoundTrip.rows).Count -ne $payloadRows.Count) { throw 'JSON manifest row count mismatch' }
if ($csvRoundTrip.Count -ne $payloadRows.Count) { throw 'CSV manifest row count mismatch' }

$livePayload = @(Get-ChildItem -LiteralPath $resolvedRoot -Recurse -Force -File | Where-Object { -not $controlPaths.ContainsKey($_.FullName.ToUpperInvariant()) } | Sort-Object FullName)
if ($livePayload.Count -ne $payloadRows.Count) { throw 'Live payload count mismatch before seal' }
$identityErrors = [Collections.Generic.List[string]]::new()
for ($i = 0; $i -lt $payloadRows.Count; $i++) {
  $expected = $payloadRows[$i]
  $actual = $livePayload[$i]
  $actualRel = Get-RelativeForward $resolvedRoot $actual.FullName
  if ($actualRel -cne [string]$expected['relative_path']) { $identityErrors.Add("path:$i") }
  if ([int64]$actual.Length -ne [int64]$expected['bytes']) { $identityErrors.Add("bytes:$actualRel") }
  if ((Get-Sha256 $actual.FullName) -cne [string]$expected['sha256']) { $identityErrors.Add("sha:$actualRel") }
  if ($actual.LastWriteTimeUtc.Ticks.ToString() -cne [string]$expected['mtime_utc_ticks']) { $identityErrors.Add("ticks:$actualRel") }
  $csv = $csvRoundTrip[$i]
  $json = @($jsonRoundTrip.rows)[$i]
  if ($csv.relative_path -cne [string]$expected['relative_path'] -or $json.relative_path -cne [string]$expected['relative_path']) { $identityErrors.Add("manifest-path:$i") }
  if ($csv.bytes -cne $expected['bytes'].ToString() -or $json.bytes.ToString() -cne $expected['bytes'].ToString()) { $identityErrors.Add("manifest-bytes:$i") }
  if ($csv.sha256 -cne [string]$expected['sha256'] -or $json.sha256 -cne [string]$expected['sha256']) { $identityErrors.Add("manifest-sha:$i") }
  if ($csv.mtime_utc_ticks -cne [string]$expected['mtime_utc_ticks'] -or $json.mtime_utc_ticks -cne [string]$expected['mtime_utc_ticks']) { $identityErrors.Add("manifest-ticks:$i") }
}
if ($identityErrors.Count -ne 0) { throw "Preseal identity errors: $($identityErrors.Count)" }

$presealPath = [IO.Path]::Combine($resolvedRoot, 'PRESEAL_VALIDATION.json')
$preseal = [ordered]@{
  schema = 'P067_R3_PRESEAL_VALIDATION_V2'
  validated_at_utc = [DateTime]::UtcNow.ToString('o')
  resolved_root = $resolvedRoot
  payload_count = $payloadRows.Count
  control_count = 4
  projected_ordinary_count = $payloadRows.Count + 4
  duplicate_path_count = $duplicatePaths.Count
  identity_error_count = $identityErrors.Count
  strictmode_group_microtests = [ordered]@{empty=0;one=0;two_unique=0;duplicate_groups=1;duplicate_group_size=2}
  original_failed_controller_frozen = $true
  original_failed_controller_sha256 = 'A6D959A59D32ED71F1ADE74DF74036EBA77B1AE82B536403D29683E37AC7CAD6'
  manual_content_regenerated = $false
  business_evidence_rerun = $false
  status = 'PASS_READY_FOR_FINAL_MARKER'
}
Write-Utf8NoBom $presealPath (($preseal | ConvertTo-Json -Depth 8) + "`n")

$premarkerFiles = @(Get-ChildItem -LiteralPath $resolvedRoot -Recurse -Force -File)
if ($premarkerFiles.Count -ne 132) { throw "Premarker ordinary count must be 132, got $($premarkerFiles.Count)" }
foreach ($file in $premarkerFiles) { $file.Attributes = $file.Attributes -bor [IO.FileAttributes]::ReadOnly }
$dirs = @(Get-ChildItem -LiteralPath $resolvedRoot -Recurse -Force -Directory | Sort-Object { $_.FullName.Length } -Descending)
foreach ($dir in $dirs) { $dir.Attributes = $dir.Attributes -bor [IO.FileAttributes]::ReadOnly }
$rootItem = Get-Item -LiteralPath $resolvedRoot -Force
$rootItem.Attributes = $rootItem.Attributes -bor [IO.FileAttributes]::ReadOnly

$readonlyFileFailures = @($premarkerFiles | Where-Object { -not ((Get-Item -LiteralPath $_.FullName -Force).Attributes -band [IO.FileAttributes]::ReadOnly) })
$allDirs = @((Get-Item -LiteralPath $resolvedRoot -Force)) + @(Get-ChildItem -LiteralPath $resolvedRoot -Recurse -Force -Directory)
$readonlyDirFailures = @($allDirs | Where-Object { -not ($_.Attributes -band [IO.FileAttributes]::ReadOnly) })
if ($readonlyFileFailures.Count -ne 0) { throw 'Premarker file readonly failure' }
if ($readonlyDirFailures.Count -ne 0) { throw 'Premarker directory readonly failure' }

$maxPremarkerTicks = ($premarkerFiles | Measure-Object -Property LastWriteTimeUtc -Maximum).Maximum.Ticks
$markerTemp = [IO.Path]::Combine([IO.Path]::GetDirectoryName($resolvedRoot), '.P067_R3_WRITE_STOPPED_' + [Guid]::NewGuid().ToString('N') + '.json')
$markerFinal = [IO.Path]::Combine($resolvedRoot, 'WRITE_STOPPED.json')
$markerTicks = [Math]::Max([DateTime]::UtcNow.AddSeconds(5).Ticks, $maxPremarkerTicks + 1)
$marker = [ordered]@{
  schema = 'P067_R3_WRITE_STOPPED_V2'
  resolved_root = $resolvedRoot
  stopped_at_utc = ([DateTime]::new($markerTicks,[DateTimeKind]::Utc)).ToString('o')
  payload_count = 129
  control_count = 4
  ordinary_count = 133
  max_premarker_ticks = $maxPremarkerTicks.ToString()
  write_stopped_ticks = $markerTicks.ToString()
  final_root_content_operation = 'Move prebuilt read-only WRITE_STOPPED.json into root'
  postmarker_root_content_writes = 0
  postmarker_root_attribute_writes = 0
}
Write-Utf8NoBom $markerTemp (($marker | ConvertTo-Json -Depth 6) + "`n")
[IO.File]::SetLastWriteTimeUtc($markerTemp,[DateTime]::new($markerTicks,[DateTimeKind]::Utc))
$markerTempItem = Get-Item -LiteralPath $markerTemp -Force
$markerTempItem.Attributes = $markerTempItem.Attributes -bor [IO.FileAttributes]::ReadOnly
Move-Item -LiteralPath $markerTemp -Destination $markerFinal

[pscustomobject]@{
  status = 'SEALED'
  resolved_root = $resolvedRoot
  payload_count = 129
  control_count = 4
  ordinary_count = 133
  manifest_csv_sha256 = Get-Sha256 $manifestCsvPath
  manifest_json_sha256 = Get-Sha256 $manifestJsonPath
  preseal_sha256 = Get-Sha256 $presealPath
  write_stopped_sha256 = Get-Sha256 $markerFinal
  write_stopped_ticks = $markerTicks.ToString()
  max_premarker_ticks = $maxPremarkerTicks.ToString()
  write_stopped_margin_ticks = ($markerTicks - $maxPremarkerTicks).ToString()
} | ConvertTo-Json -Depth 5
