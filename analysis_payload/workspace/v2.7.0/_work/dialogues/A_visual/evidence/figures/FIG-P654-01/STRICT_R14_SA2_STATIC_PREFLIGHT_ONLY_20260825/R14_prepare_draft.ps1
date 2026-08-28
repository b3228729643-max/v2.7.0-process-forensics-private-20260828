# STATIC DRAFT ONLY. DO NOT EXECUTE WITHOUT A NEW EXPLICIT MAINLINE COPY/SEAL GRANT.
[CmdletBinding()]
param(
  [Parameter(Mandatory=$true)][string]$SourceRoot,
  [Parameter(Mandatory=$true)][string]$TargetRoot,
  [Parameter(Mandatory=$true)][string]$ExecutionGrant
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
if ($ExecutionGrant -ne 'P654_R14_COPY_SEAL_EXPLICITLY_GRANTED') { throw 'R14 draft execution is not authorized' }

$expectedSource = [IO.Path]::GetFullPath('D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P654-01\STRICT_R10_SA2_TAXONOMY_R100_DIRECT_BUILD_20260825')
$expectedTarget = [IO.Path]::GetFullPath('D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P654-01\STRICT_R14_SA2_R10_EVIDENCE_ONLY_CONTROL_RESEAL_20260825')
$source = [IO.Path]::GetFullPath($SourceRoot)
$target = [IO.Path]::GetFullPath($TargetRoot)
if ($source -cne $expectedSource -or $target -cne $expectedTarget) { throw 'resolved root mismatch' }
if ($source.Contains('$') -or $target.Contains('$')) { throw 'unexpanded path placeholder' }
if (-not (Test-Path -LiteralPath $source -PathType Container)) { throw 'R10 source root missing' }
if (-not (Test-Path -LiteralPath $target -PathType Container)) { throw 'fresh R14 target root missing' }

$controls = @('PAYLOAD_MANIFEST.csv','PAYLOAD_MANIFEST.json','WRITE_STOPPED.json')
$materializedDrafts = @('R14_prepare.ps1','R14_preseal_validator.ps1','R14_seal.ps1')
function Get-Rel([string]$Root,[string]$FullName) { [IO.Path]::GetRelativePath($Root,$FullName).Replace('/','\') }
function Get-Sha([string]$Path) { (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant() }
function Get-Display([datetime]$Utc) { $Utc.ToString('yyyy-MM-ddTHH:mm:ss.fffffffZ',[Globalization.CultureInfo]::InvariantCulture) }

$sourceOrdinary = @(Get-ChildItem -LiteralPath $source -Recurse -File)
if ($sourceOrdinary.Count -ne 1055) { throw "R10 ordinary expected 1055, got $($sourceOrdinary.Count)" }
$sourcePayload = @($sourceOrdinary | Where-Object { $controls -notcontains (Get-Rel $source $_.FullName) } | Sort-Object FullName)
if ($sourcePayload.Count -ne 1052) { throw "R10 payload expected 1052, got $($sourcePayload.Count)" }

$targetBefore = @(Get-ChildItem -LiteralPath $target -Recurse -File | ForEach-Object { Get-Rel $target $_.FullName })
$unexpectedBefore = @($targetBefore | Where-Object { $materializedDrafts -notcontains $_ })
if ($unexpectedBefore.Count -ne 0 -or $targetBefore.Count -ne 3) { throw 'future target is not fresh except for three reviewed scripts' }

$identity = [Collections.Generic.List[object]]::new()
foreach ($file in $sourcePayload) {
  $rel = Get-Rel $source $file.FullName
  $dest = Join-Path $target $rel
  $parent = Split-Path -Parent $dest
  if (-not (Test-Path -LiteralPath $parent)) { New-Item -ItemType Directory -Path $parent -Force | Out-Null }
  Copy-Item -LiteralPath $file.FullName -Destination $dest
  [IO.File]::SetLastWriteTimeUtc($dest,$file.LastWriteTimeUtc)
  $destInfo = [IO.FileInfo]$dest
  $sourceTicks = $file.LastWriteTimeUtc.Ticks.ToString([Globalization.CultureInfo]::InvariantCulture)
  $destTicks = $destInfo.LastWriteTimeUtc.Ticks.ToString([Globalization.CultureInfo]::InvariantCulture)
  $sourceSha = Get-Sha $file.FullName
  if ($destInfo.Length -ne $file.Length -or (Get-Sha $dest) -cne $sourceSha -or $destTicks -cne $sourceTicks) { throw "copy identity mismatch: $rel" }
  $identity.Add([ordered]@{
    source_relative_path=$rel; destination_relative_path=$rel; bytes=[int64]$file.Length; sha256=$sourceSha
    mtime_utc_ticks=$sourceTicks; mtime_utc_7digit=(Get-Display $file.LastWriteTimeUtc)
  })
}

$identity | Export-Csv -LiteralPath (Join-Path $target 'R14_BASE_COPY_IDENTITY.csv') -NoTypeInformation -Encoding utf8
$identity | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $target 'R14_BASE_COPY_IDENTITY.json') -Encoding utf8
$provenance = [ordered]@{source_root=$source;target_root=$target;round='R14';created_at=[datetime]::UtcNow.ToString('yyyy-MM-ddTHH:mm:ss.fffffffZ',[Globalization.CultureInfo]::InvariantCulture)}
if (@($provenance.Values | Where-Object { "$_".Contains('$') }).Count -ne 0) { throw 'provenance placeholder before write' }
$provenance | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $target 'R14_COPY_PROVENANCE.json') -Encoding utf8
$roundTrip = Get-Content -LiteralPath (Join-Path $target 'R14_COPY_PROVENANCE.json') -Raw | ConvertFrom-Json
if ([IO.Path]::GetFullPath($roundTrip.source_root) -cne $source -or [IO.Path]::GetFullPath($roundTrip.target_root) -cne $target) { throw 'provenance root mismatch after write' }
if (@($roundTrip.psobject.Properties.Value | Where-Object { "$_".Contains('$') }).Count -ne 0) { throw 'provenance placeholder after write' }

$preparedPayload = @(Get-ChildItem -LiteralPath $target -Recurse -File | Where-Object { $controls -notcontains (Get-Rel $target $_.FullName) })
if ($preparedPayload.Count -ne 1058) { throw "prepared pre-report payload expected 1058, got $($preparedPayload.Count)" }
[ordered]@{status='PREPARED_AWAIT_INDEPENDENT_PRESEAL_VALIDATOR';base_payload=1052;current_payload=1058} | ConvertTo-Json -Compress
