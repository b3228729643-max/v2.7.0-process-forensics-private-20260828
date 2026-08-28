param(
  [Parameter(Mandatory=$true)][string]$Root,
  [Parameter(Mandatory=$true)][string]$Snapshot1,
  [Parameter(Mandatory=$true)][string]$Snapshot2,
  [Parameter(Mandatory=$true)][string]$AuditOutput
)

$ErrorActionPreference = 'Stop'

function Get-RootSnapshot([string]$TargetRoot) {
  $rootItem = Get-Item -LiteralPath $TargetRoot
  $items = @($rootItem) + @(Get-ChildItem -LiteralPath $TargetRoot -Recurse -Force)
  $rows = foreach ($item in ($items | Sort-Object FullName)) {
    $relative = if ($item.FullName -eq $rootItem.FullName) { '.' } else { $item.FullName.Substring($rootItem.FullName.Length + 1).Replace('\','/') }
    [ordered]@{
      RelativePath = $relative
      ItemType = if ($item.PSIsContainer) { 'Directory' } else { 'File' }
      Bytes = if ($item.PSIsContainer) { $null } else { $item.Length }
      SHA256 = if ($item.PSIsContainer) { $null } else { (Get-FileHash -LiteralPath $item.FullName -Algorithm SHA256).Hash }
      Attributes = $item.Attributes.ToString()
      LastWriteTimeUtc = $item.LastWriteTimeUtc.ToString('o')
    }
  }
  return @($rows)
}

$first = Get-RootSnapshot $Root
[ordered]@{CapturedUtc=(Get-Date).ToUniversalTime().ToString('o');Root=$Root;Items=$first} | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $Snapshot1 -Encoding utf8

Start-Sleep -Seconds 2

$second = Get-RootSnapshot $Root
[ordered]@{CapturedUtc=(Get-Date).ToUniversalTime().ToString('o');Root=$Root;Items=$second} | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $Snapshot2 -Encoding utf8

$canonical1 = $first | ConvertTo-Json -Depth 8 -Compress
$canonical2 = $second | ConvertTo-Json -Depth 8 -Compress
$marker = $second | Where-Object RelativePath -eq 'WRITE_STOPPED'
$others = $second | Where-Object RelativePath -ne 'WRITE_STOPPED'
$allReadonly = (@($second | Where-Object { $_.Attributes -notmatch 'ReadOnly' })).Count -eq 0
$markerLater = $null -ne $marker -and (@($others | Where-Object { [datetime]$_.LastWriteTimeUtc -ge [datetime]$marker.LastWriteTimeUtc })).Count -eq 0
$audit = [ordered]@{
  CapturedUtc = (Get-Date).ToUniversalTime().ToString('o')
  Root = $Root
  Snapshot1 = $Snapshot1
  Snapshot2 = $Snapshot2
  Snapshot1SHA256 = (Get-FileHash -LiteralPath $Snapshot1 -Algorithm SHA256).Hash
  Snapshot2SHA256 = (Get-FileHash -LiteralPath $Snapshot2 -Algorithm SHA256).Hash
  RootItemCountSnapshot1 = $first.Count
  RootItemCountSnapshot2 = $second.Count
  RootFileCount = @($second | Where-Object ItemType -eq 'File').Count
  RootDirectoryCountIncludingRoot = @($second | Where-Object ItemType -eq 'Directory').Count
  SnapshotsContentAndAttributesIdentical = ($canonical1 -ceq $canonical2)
  EveryRootFileAndDirectoryReadOnly = $allReadonly
  WriteStoppedExists = ($null -ne $marker)
  WriteStoppedReadOnly = ($null -ne $marker -and $marker.Attributes -match 'ReadOnly')
  WriteStoppedMtimeStrictlyLaterThanEveryOtherRootItem = $markerLater
  PostmarkerRootContentAttributeWrites = if (($canonical1 -ceq $canonical2) -and $allReadonly) { 0 } else { -1 }
}
$audit['AuditPass'] = $audit.SnapshotsContentAndAttributesIdentical -and $audit.EveryRootFileAndDirectoryReadOnly -and $audit.WriteStoppedExists -and $audit.WriteStoppedReadOnly -and $audit.WriteStoppedMtimeStrictlyLaterThanEveryOtherRootItem -and $audit.PostmarkerRootContentAttributeWrites -eq 0
$audit | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $AuditOutput -Encoding utf8

foreach ($path in @($Snapshot1,$Snapshot2,$AuditOutput)) {
  $item = Get-Item -LiteralPath $path
  [IO.File]::SetAttributes($item.FullName, ($item.Attributes -bor [IO.FileAttributes]::ReadOnly))
}

$audit | ConvertTo-Json -Compress
