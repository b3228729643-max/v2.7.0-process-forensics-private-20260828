$ErrorActionPreference = 'Stop'

$root = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P582-01\STRICT_R4_SA3_FRESH_ISOLATED_R109_20260826'
$sealDir = Join-Path $root '08_seal'
$handoffDir = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\handoff\A'
$stage = Join-Path $handoffDir '.FIG-P582-01_R109_R4_SA3_WRITE_STOPPED.stage'
$marker = Join-Path $root 'WRITE_STOPPED'
$payloadManifest = Join-Path $sealDir 'MANIFEST_PAYLOAD.csv'
$payloadDigest = Join-Path $sealDir 'MANIFEST_PAYLOAD.sha256'
$sealManifest = Join-Path $sealDir 'MANIFEST_SEAL.csv'
$sealDigest = Join-Path $sealDir 'MANIFEST_SEAL.sha256'

if ((Resolve-Path -LiteralPath $root).Path -ne $root) { throw 'root identity mismatch' }
if (Test-Path -LiteralPath $marker) { throw 'WRITE_STOPPED already exists; seal is single-use' }
if (Test-Path -LiteralPath $stage) { throw 'external marker stage already exists' }
if (Get-ChildItem -LiteralPath $sealDir -Force | Select-Object -First 1) { throw '08_seal must be empty before the single seal' }

$sealedAt = [DateTime]::UtcNow.ToString('o')
$markerText = @"
FIGURE_ID=FIG-P582-01
HANDOFF_ID=A-R109-P582-SA3-FRESH-ISOLATED-20260826
PDF_REVISION=R109
RESULT=FAIL
SEALED_AT_UTC=$sealedAt
ROOT_WRITES_AFTER_THIS_MARKER=FORBIDDEN
"@
$markerText = $markerText.Replace("`r`n", "`n")
$utf8NoBom = [System.Text.UTF8Encoding]::new($false)
$markerBytes = $utf8NoBom.GetBytes($markerText)
$markerHash = [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($markerBytes))

$payloadFiles = Get-ChildItem -LiteralPath $root -Recurse -Force -File |
    Where-Object { -not $_.FullName.StartsWith($sealDir + '\', [StringComparison]::OrdinalIgnoreCase) } |
    Sort-Object FullName
$payloadRows = foreach ($file in $payloadFiles) {
    $relative = $file.FullName.Substring($root.Length + 1).Replace('\', '/')
    $hash = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToUpperInvariant()
    [PSCustomObject]@{
        relative_path = $relative
        size_bytes = [UInt64]$file.Length
        sha256 = $hash
        last_write_utc = $file.LastWriteTimeUtc.ToString('o')
    }
}
$payloadRows | Export-Csv -LiteralPath $payloadManifest -NoTypeInformation -Encoding utf8
$payloadManifestHash = (Get-FileHash -LiteralPath $payloadManifest -Algorithm SHA256).Hash.ToUpperInvariant()
[IO.File]::WriteAllText($payloadDigest, "$payloadManifestHash  MANIFEST_PAYLOAD.csv`n", $utf8NoBom)

$sealRows = @(
    [PSCustomObject]@{
        relative_path = '08_seal/MANIFEST_PAYLOAD.csv'
        size_bytes = [UInt64](Get-Item -LiteralPath $payloadManifest).Length
        sha256 = $payloadManifestHash
    },
    [PSCustomObject]@{
        relative_path = '08_seal/MANIFEST_PAYLOAD.sha256'
        size_bytes = [UInt64](Get-Item -LiteralPath $payloadDigest).Length
        sha256 = (Get-FileHash -LiteralPath $payloadDigest -Algorithm SHA256).Hash.ToUpperInvariant()
    },
    [PSCustomObject]@{
        relative_path = 'WRITE_STOPPED'
        size_bytes = [UInt64]$markerBytes.Length
        sha256 = $markerHash
    }
)
$sealRows | Export-Csv -LiteralPath $sealManifest -NoTypeInformation -Encoding utf8
$sealManifestHash = (Get-FileHash -LiteralPath $sealManifest -Algorithm SHA256).Hash.ToUpperInvariant()
[IO.File]::WriteAllText($sealDigest, "$sealManifestHash  MANIFEST_SEAL.csv`n", $utf8NoBom)

# Complete payload and both manifests become read-only before the final marker enters the root.
foreach ($file in Get-ChildItem -LiteralPath $root -Recurse -Force -File) {
    [IO.File]::SetAttributes($file.FullName, $file.Attributes -bor [IO.FileAttributes]::ReadOnly)
}
$notReadOnly = @(Get-ChildItem -LiteralPath $root -Recurse -Force -File | Where-Object { -not ($_.Attributes -band [IO.FileAttributes]::ReadOnly) })
if ($notReadOnly.Count -ne 0) { throw 'pre-marker read-only gate failed' }

# Stage the already-read-only marker outside the evidence root; moving it is the unique final root mutation.
[IO.File]::WriteAllBytes($stage, $markerBytes)
Start-Sleep -Milliseconds 1100
[IO.File]::SetLastWriteTimeUtc($stage, [DateTime]::UtcNow)
[IO.File]::SetAttributes($stage, [IO.FileAttributes]::ReadOnly)
Move-Item -LiteralPath $stage -Destination $marker

Write-Output "SEALED_RESULT=FAIL"
Write-Output "SEALED_AT_UTC=$sealedAt"
Write-Output "PAYLOAD_FILE_COUNT=$($payloadRows.Count)"
Write-Output "PAYLOAD_MANIFEST_SHA256=$payloadManifestHash"
Write-Output "SEAL_MANIFEST_SHA256=$sealManifestHash"
