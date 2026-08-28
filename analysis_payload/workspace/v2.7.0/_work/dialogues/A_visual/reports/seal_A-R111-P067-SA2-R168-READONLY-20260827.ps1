$ErrorActionPreference = 'Stop'
$root = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P067-01\STRICT_R1_SA2_R168_READONLY_R111_20260827'
$temporaryMarker = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\handoff\A\A-R111-P067-SA2-R168-READONLY-20260827_WRITE_STOPPED.tmp'
$marker = Join-Path $root 'WRITE_STOPPED'

if (-not (Test-Path -LiteralPath $root -PathType Container)) { throw 'sealed root missing' }
if (Test-Path -LiteralPath $marker) { throw 'WRITE_STOPPED already exists; refusing a second seal' }
if (-not (Test-Path -LiteralPath $temporaryMarker -PathType Leaf)) { throw 'external marker payload missing' }
if (-not (Test-Path -LiteralPath (Join-Path $root 'audit\preseal_payload_manifest.csv') -PathType Leaf)) { throw 'preseal manifest missing' }
if (-not (Test-Path -LiteralPath (Join-Path $root 'audit\preseal_validation.json') -PathType Leaf)) { throw 'preseal validation missing' }

Get-ChildItem -LiteralPath $root -File -Recurse | ForEach-Object {
    $_.Attributes = $_.Attributes -bor [System.IO.FileAttributes]::ReadOnly
}
Get-ChildItem -LiteralPath $root -Directory -Recurse | Sort-Object FullName -Descending | ForEach-Object {
    $_.Attributes = $_.Attributes -bor [System.IO.FileAttributes]::ReadOnly
}
(Get-Item -LiteralPath $root).Attributes = (Get-Item -LiteralPath $root).Attributes -bor [System.IO.FileAttributes]::ReadOnly

$futureTick = [DateTime]::UtcNow.AddSeconds(5)
(Get-Item -LiteralPath $temporaryMarker).LastWriteTimeUtc = $futureTick
Move-Item -LiteralPath $temporaryMarker -Destination $marker
(Get-Item -LiteralPath $marker).Attributes = (Get-Item -LiteralPath $marker).Attributes -bor [System.IO.FileAttributes]::ReadOnly

[pscustomobject]@{
    Marker = $marker
    MarkerLastWriteTimeUtc = (Get-Item -LiteralPath $marker).LastWriteTimeUtc.ToString('o')
    MarkerAttributes = (Get-Item -LiteralPath $marker).Attributes.ToString()
} | ConvertTo-Json -Depth 2
