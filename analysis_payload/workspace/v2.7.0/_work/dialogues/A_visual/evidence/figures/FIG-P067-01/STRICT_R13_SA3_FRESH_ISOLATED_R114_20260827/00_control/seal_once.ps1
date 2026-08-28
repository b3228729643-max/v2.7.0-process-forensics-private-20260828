param(
  [Parameter(Mandatory=$true)][string]$Root,
  [Parameter(Mandatory=$true)][string]$StagedMarker
)

$ErrorActionPreference = 'Stop'
$rootItem = Get-Item -LiteralPath $Root
$stageItem = Get-Item -LiteralPath $StagedMarker
$destination = Join-Path $Root 'WRITE_STOPPED'

if (Test-Path -LiteralPath $destination) {
  throw "WRITE_STOPPED already exists at destination"
}
if (($stageItem.Attributes -band [IO.FileAttributes]::ReadOnly) -eq 0) {
  throw "Staged marker is not ReadOnly"
}

$existing = @($rootItem) + @(Get-ChildItem -LiteralPath $Root -Recurse -Force)
$maxMtime = ($existing | Measure-Object -Property LastWriteTimeUtc -Maximum).Maximum
if ($stageItem.LastWriteTimeUtc -le $maxMtime) {
  throw "Staged marker mtime is not strictly later than every existing destination item"
}

foreach ($item in ($existing | Sort-Object { $_.FullName.Length } -Descending)) {
  [IO.File]::SetAttributes($item.FullName, ($item.Attributes -bor [IO.FileAttributes]::ReadOnly))
}

$verified = @((Get-Item -LiteralPath $Root)) + @(Get-ChildItem -LiteralPath $Root -Recurse -Force)
$notReadOnly = @($verified | Where-Object { ($_.Attributes -band [IO.FileAttributes]::ReadOnly) -eq 0 })
if ($notReadOnly.Count -ne 0) {
  throw "ReadOnly recursion verification failed"
}

$stageItem = Get-Item -LiteralPath $StagedMarker
$maxAfterReadonly = ($verified | Measure-Object -Property LastWriteTimeUtc -Maximum).Maximum
if (($stageItem.Attributes -band [IO.FileAttributes]::ReadOnly) -eq 0 -or $stageItem.LastWriteTimeUtc -le $maxAfterReadonly) {
  throw "Staged marker lost ReadOnly or strict-later mtime before final move"
}

Move-Item -LiteralPath $StagedMarker -Destination $destination

$moved = Get-Item -LiteralPath $destination
[pscustomobject]@{
  Root = $Root
  Marker = $moved.FullName
  MarkerReadOnly = (($moved.Attributes -band [IO.FileAttributes]::ReadOnly) -ne 0)
  MarkerLastWriteTimeUtc = $moved.LastWriteTimeUtc.ToString('o')
  FinalOperation = 'MOVE_ALREADY_READONLY_WRITE_STOPPED_INTO_ROOT'
} | ConvertTo-Json -Compress
