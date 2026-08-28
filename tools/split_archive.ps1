param(
  [string]$ArchivePath = 'D:\Users\ASUS\Desktop\机器学习\github_exports\v2.7.0-process-forensics-private-20260828\full_archive\v2.7.0-full-workspace-20260828.tar.zst',
  [int64]$PartBytes = 1500MB
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$archive = Get-Item -LiteralPath $ArchivePath -Force
$buffer = [byte[]]::new(8MB)
$input = [IO.File]::Open($archive.FullName, [IO.FileMode]::Open, [IO.FileAccess]::Read, [IO.FileShare]::Read)
$parts = [Collections.Generic.List[object]]::new()

try {
  $partNumber = 1
  $totalWritten = [int64]0
  while ($totalWritten -lt $archive.Length) {
    $partPath = '{0}.part-{1:D3}' -f $archive.FullName, $partNumber
    $output = [IO.File]::Open($partPath, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write, [IO.FileShare]::None)
    try {
      $partWritten = [int64]0
      while ($partWritten -lt $PartBytes -and $totalWritten -lt $archive.Length) {
        $remainingPart = $PartBytes - $partWritten
        $remainingArchive = $archive.Length - $totalWritten
        $requested = [int][Math]::Min($buffer.Length, [Math]::Min($remainingPart, $remainingArchive))
        $read = $input.Read($buffer, 0, $requested)
        if ($read -le 0) { throw 'Unexpected end of archive while splitting' }
        $output.Write($buffer, 0, $read)
        $partWritten += $read
        $totalWritten += $read
      }
    } finally {
      $output.Dispose()
    }
    $partItem = Get-Item -LiteralPath $partPath -Force
    $parts.Add([pscustomobject][ordered]@{
      part = $partNumber
      file_name = $partItem.Name
      bytes = [int64]$partItem.Length
      sha256 = (Get-FileHash -LiteralPath $partItem.FullName -Algorithm SHA256).Hash.ToUpperInvariant()
    })
    $partNumber++
  }
} finally {
  $input.Dispose()
}

$sum = [int64](($parts | Measure-Object bytes -Sum).Sum)
if ($sum -ne $archive.Length) { throw "Split byte mismatch: $sum != $($archive.Length)" }

$manifestPath = Join-Path $archive.DirectoryName 'FULL_ARCHIVE_PARTS.csv'
$parts | Export-Csv -LiteralPath $manifestPath -NoTypeInformation -Encoding utf8NoBOM

$summary = [ordered]@{
  schema = 'V270_FULL_ARCHIVE_PARTS_V1'
  archive_file_name = $archive.Name
  archive_bytes = [int64]$archive.Length
  archive_sha256 = (Get-FileHash -LiteralPath $archive.FullName -Algorithm SHA256).Hash.ToUpperInvariant()
  part_bytes_target = $PartBytes
  part_count = $parts.Count
  parts_total_bytes = $sum
  reconstruction_windows = "copy /b $((@($parts | ForEach-Object file_name)) -join '+') $($archive.Name)"
  reconstruction_posix = "cat $($archive.Name).part-* > $($archive.Name)"
}
[IO.File]::WriteAllText((Join-Path $archive.DirectoryName 'FULL_ARCHIVE_SUMMARY.json'), ($summary | ConvertTo-Json -Depth 5), [Text.UTF8Encoding]::new($false))
$summary | ConvertTo-Json -Depth 5
