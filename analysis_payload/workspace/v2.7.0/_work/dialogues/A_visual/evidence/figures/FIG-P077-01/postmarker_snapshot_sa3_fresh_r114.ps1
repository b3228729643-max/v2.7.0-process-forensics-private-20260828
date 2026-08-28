param(
  [Parameter(Mandatory=$true)][string]$EvidenceRoot,
  [Parameter(Mandatory=$true)][string]$OutputPath
)
$ErrorActionPreference = 'Stop'
$resolvedRoot = [System.IO.Path]::GetFullPath($EvidenceRoot)
$items = @()
$rootItem = Get-Item -LiteralPath $resolvedRoot -Force
$items += [pscustomobject]@{
  RelativePath = '.'
  Kind = 'Directory'
  Length = $null
  SHA256 = $null
  Attributes = $rootItem.Attributes.ToString()
  LastWriteTimeUtc = $rootItem.LastWriteTimeUtc.ToString('o')
}
foreach($item in Get-ChildItem -LiteralPath $resolvedRoot -Force -Recurse | Sort-Object FullName) {
  $relative = [System.IO.Path]::GetRelativePath($resolvedRoot, $item.FullName)
  if($item.PSIsContainer) {
    $items += [pscustomobject]@{
      RelativePath = $relative
      Kind = 'Directory'
      Length = $null
      SHA256 = $null
      Attributes = $item.Attributes.ToString()
      LastWriteTimeUtc = $item.LastWriteTimeUtc.ToString('o')
    }
  } else {
    $items += [pscustomobject]@{
      RelativePath = $relative
      Kind = 'File'
      Length = $item.Length
      SHA256 = (Get-FileHash -LiteralPath $item.FullName -Algorithm SHA256).Hash
      Attributes = $item.Attributes.ToString()
      LastWriteTimeUtc = $item.LastWriteTimeUtc.ToString('o')
    }
  }
}
$snapshot = [pscustomobject]@{
  CapturedAt = (Get-Date).ToString('o')
  EvidenceRoot = $resolvedRoot
  ItemCount = $items.Count
  Items = $items
}
$json = $snapshot | ConvertTo-Json -Depth 8
[System.IO.File]::WriteAllText($OutputPath, $json, [System.Text.UTF8Encoding]::new($false))
