param(
  [Parameter(Mandatory=$true)][string]$EvidenceRoot,
  [Parameter(Mandatory=$true)][string]$ReportPath,
  [Parameter(Mandatory=$true)][string]$HandoffPath
)

$ErrorActionPreference = 'Stop'
$marker = Join-Path $EvidenceRoot 'WRITE_STOPPED'
if ([System.IO.File]::Exists($marker)) {
  throw 'Seal refused: WRITE_STOPPED already exists.'
}
if (-not [System.IO.Directory]::Exists($EvidenceRoot)) { throw 'Evidence root missing.' }
if (-not [System.IO.File]::Exists($ReportPath)) { throw 'External report missing.' }
if (-not [System.IO.File]::Exists($HandoffPath)) { throw 'External handoff missing.' }

$controlsPath = Join-Path $EvidenceRoot 'FINAL_CONTROLS.json'
$controls = Get-Content -LiteralPath $controlsPath -Raw | ConvertFrom-Json
if ($controls.N -ne 152 -or $controls.C -ne 11476 -or $controls.result -ne 'PASS') {
  throw 'Resolved controls failed fixed SA1 seal expectations.'
}
if ($controls.route_status -ne 'SA1_PASS_READY_FOR_FRESH_ISOLATED_SA3') {
  throw 'Unexpected route status.'
}

$atomPath = Join-Path $EvidenceRoot 'machine\atomic_denominator_machine.csv'
$pairPath = Join-Path $EvidenceRoot 'machine\all_unordered_pairs_machine.csv'
$manualPath = Join-Path $EvidenceRoot 'manual\SA1_manual_atom_ledger.csv'
$atoms = Import-Csv -LiteralPath $atomPath
$pairs = Import-Csv -LiteralPath $pairPath
$manual = Import-Csv -LiteralPath $manualPath
if ($atoms.Count -ne 152 -or ($atoms.atom_id | Sort-Object -Unique).Count -ne 152) { throw 'Atom gate failed.' }
if ($pairs.Count -ne 11476 -or ($pairs.unordered_key | Sort-Object -Unique).Count -ne 11476) { throw 'Pair gate failed.' }
if (($pairs | Where-Object { $_.atom_id_a -eq $_.atom_id_b }).Count -ne 0) { throw 'Self-pair gate failed.' }
if ($manual.Count -ne 152 -or ($manual.atom_id | Sort-Object -Unique).Count -ne 152) { throw 'Manual row gate failed.' }
$manualBad = $manual | Where-Object {
  [string]::IsNullOrWhiteSpace($_.reviewer) -or
  [string]::IsNullOrWhiteSpace($_.observed) -or
  [string]::IsNullOrWhiteSpace($_.decision) -or
  [string]::IsNullOrWhiteSpace($_.note) -or
  $_.PASS -ne 'TRUE'
}
if ($manualBad.Count -ne 0) { throw 'Manual completeness gate failed.' }

$machineCsv = Get-ChildItem -LiteralPath (Join-Path $EvidenceRoot 'machine') -File -Filter '*.csv'
$forbiddenHeaders = @('reviewer','observed','decision','note','pass','pass_fail')
foreach ($csvFile in $machineCsv) {
  $header = (Get-Content -LiteralPath $csvFile.FullName -TotalCount 1).ToLowerInvariant()
  foreach ($term in $forbiddenHeaders) {
    if ($header -match "(^|,)$term(,|$)") { throw "Machine manual-field gate failed: $($csvFile.Name) / $term" }
  }
}

$reportHash = (Get-FileHash -LiteralPath $ReportPath -Algorithm SHA256).Hash
$handoffHash = (Get-FileHash -LiteralPath $HandoffPath -Algorithm SHA256).Hash
$bindingPath = Join-Path $EvidenceRoot 'BOUND_EXTERNALS.sha256'
$bindingText = @(
  "REPORT_PATH=$ReportPath",
  "REPORT_SHA256=$reportHash",
  "HANDOFF_PATH=$HandoffPath",
  "HANDOFF_SHA256=$handoffHash"
) -join [Environment]::NewLine
[System.IO.File]::WriteAllText($bindingPath, $bindingText + [Environment]::NewLine, [System.Text.UTF8Encoding]::new($false))

$manifestPath = Join-Path $EvidenceRoot 'FINAL_SEAL_MANIFEST.csv'
$filesForManifest = Get-ChildItem -LiteralPath $EvidenceRoot -Recurse -File | Where-Object {
  $_.FullName -ne $manifestPath -and $_.FullName -ne $marker
} | Sort-Object FullName
$manifestRows = foreach ($file in $filesForManifest) {
  [pscustomobject]@{
    relative_path = $file.FullName.Substring($EvidenceRoot.Length + 1).Replace('\','/')
    bytes = $file.Length
    sha256 = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash
  }
}
$manifestRows | Export-Csv -LiteralPath $manifestPath -NoTypeInformation -Encoding utf8
$manifestHash = (Get-FileHash -LiteralPath $manifestPath -Algorithm SHA256).Hash

# All pre-marker files and every directory, including the root, become read-only
# before the marker is authored. On Windows the directory ReadOnly attribute is
# a sealing attribute and does not block creation of the one final marker file.
Get-ChildItem -LiteralPath $EvidenceRoot -Recurse -File | ForEach-Object { $_.IsReadOnly = $true }
Get-ChildItem -LiteralPath $EvidenceRoot -Recurse -Directory | Sort-Object FullName -Descending | ForEach-Object {
  $_.Attributes = $_.Attributes -bor [System.IO.FileAttributes]::ReadOnly
}
(Get-Item -LiteralPath $EvidenceRoot).Attributes = (Get-Item -LiteralPath $EvidenceRoot).Attributes -bor [System.IO.FileAttributes]::ReadOnly

$sealTimestamp = (Get-Date).ToString('yyyy-MM-ddTHH:mm:ss.fffffffK')
$markerText = @(
  'WRITE_STOPPED=true',
  "SEALED_AT=$sealTimestamp",
  'HANDOFF_ID=A-R111-P049-SA1-FRESH-ISOLATED-20260827',
  'CANONICAL_TASK=/root/p049_r111_fresh_sa1',
  'FIGURE_UID=FIG-P049-01',
  'ROLE=SA1',
  'RESULT=PASS',
  'ROUTE_STATUS=SA1_PASS_READY_FOR_FRESH_ISOLATED_SA3',
  'N=152',
  'C=11476',
  "FINAL_SEAL_MANIFEST_SHA256=$manifestHash",
  "REPORT_SHA256=$reportHash",
  "HANDOFF_SHA256=$handoffHash",
  'POSTMARKER_FILE_WRITES=0'
) -join [Environment]::NewLine
[System.IO.File]::WriteAllText($marker, $markerText + [Environment]::NewLine, [System.Text.UTF8Encoding]::new($false))
(Get-Item -LiteralPath $marker).IsReadOnly = $true

$markerItem = Get-Item -LiteralPath $marker
$postMarkerFiles = Get-ChildItem -LiteralPath $EvidenceRoot -Recurse -File | Where-Object {
  $_.FullName -ne $marker -and $_.LastWriteTimeUtc -gt $markerItem.LastWriteTimeUtc
}
$notReadOnlyFiles = Get-ChildItem -LiteralPath $EvidenceRoot -Recurse -File | Where-Object { -not $_.IsReadOnly }
$notReadOnlyDirs = @((Get-Item -LiteralPath $EvidenceRoot)) + @(Get-ChildItem -LiteralPath $EvidenceRoot -Recurse -Directory) | Where-Object {
  -not ($_.Attributes -band [System.IO.FileAttributes]::ReadOnly)
}

[pscustomobject]@{
  sealed = $true
  sealed_at = $sealTimestamp
  marker_path = $marker
  marker_sha256 = (Get-FileHash -LiteralPath $marker -Algorithm SHA256).Hash
  manifest_sha256 = $manifestHash
  report_sha256 = $reportHash
  handoff_sha256 = $handoffHash
  evidence_file_count_including_marker = (Get-ChildItem -LiteralPath $EvidenceRoot -Recurse -File).Count
  postmarker_file_writes = $postMarkerFiles.Count
  non_readonly_files = $notReadOnlyFiles.Count
  non_readonly_directories = $notReadOnlyDirs.Count
  marker_is_strictly_latest = ((Get-ChildItem -LiteralPath $EvidenceRoot -Recurse -File | Where-Object { $_.FullName -ne $marker } | Measure-Object -Property LastWriteTimeUtc -Maximum).Maximum -lt $markerItem.LastWriteTimeUtc)
} | ConvertTo-Json -Compress
