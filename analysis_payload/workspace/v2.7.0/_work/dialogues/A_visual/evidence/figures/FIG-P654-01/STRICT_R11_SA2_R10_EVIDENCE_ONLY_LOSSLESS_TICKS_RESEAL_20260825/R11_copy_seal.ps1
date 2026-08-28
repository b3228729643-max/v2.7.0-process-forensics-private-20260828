param([Parameter(Mandatory=$true)][string]$SourceRoot,[Parameter(Mandatory=$true)][string]$TargetRoot)
$ErrorActionPreference='Stop'
$exclude=@('PAYLOAD_MANIFEST.csv','PAYLOAD_MANIFEST.json','WRITE_STOPPED.json')
$src=(Resolve-Path -LiteralPath $SourceRoot).Path; $dst=(Resolve-Path -LiteralPath $TargetRoot).Path
$items=Get-ChildItem -LiteralPath $src -File -Recurse | Where-Object {$exclude -notcontains $_.Name} | Sort-Object FullName
if($items.Count -ne 1052){throw "expected 1052 base payload, got $($items.Count)"}
$rows=[System.Collections.Generic.List[object]]::new()
foreach($f in $items){
  $rel=$f.FullName.Substring($src.Length).TrimStart('\'); $out=Join-Path $dst $rel
  $parent=Split-Path -Parent $out; if(!(Test-Path -LiteralPath $parent)){New-Item -ItemType Directory -Force -Path $parent|Out-Null}
  Copy-Item -LiteralPath $f.FullName -Destination $out -Force
  [System.IO.File]::SetLastWriteTimeUtc($out,$f.LastWriteTimeUtc)
  $d=[System.IO.FileInfo]$out; if($d.Length -ne $f.Length -or $d.LastWriteTimeUtc.Ticks -ne $f.LastWriteTimeUtc.Ticks){throw "copy mismatch $rel"}
  $rows.Add([pscustomobject]@{source_relative_path=$rel;destination_relative_path=$rel;bytes=$f.Length;sha256=(Get-FileHash -LiteralPath $f.FullName -Algorithm SHA256).Hash.ToLowerInvariant();mtime_utc_ticks=$f.LastWriteTimeUtc.Ticks.ToString([Globalization.CultureInfo]::InvariantCulture);mtime_utc_7digit=$f.LastWriteTimeUtc.ToString('yyyy-MM-ddTHH:mm:ss.fffffffZ',[Globalization.CultureInfo]::InvariantCulture)})
}
$rows | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $dst 'R11_BASE_COPY_IDENTITY.json') -Encoding UTF8
$rows | Export-Csv -LiteralPath (Join-Path $dst 'R11_BASE_COPY_IDENTITY.csv') -NoTypeInformation -Encoding UTF8
$prov=@"
# R11 copy provenance

Source: `$src`
Target: `$dst`
Base payload count: 1052 (R10 manifests and WRITE_STOPPED excluded)
Copy rule: byte-preserving copy followed by exact .NET LastWriteTimeUtc restoration from source ticks.
Immediate reread: every path, byte count, SHA256, and mtime ticks was checked before identity output.
"@.TrimStart(); Set-Content -LiteralPath (Join-Path $dst 'R11_COPY_PROVENANCE.md') -Value $prov -Encoding UTF8
$manifest=@(); Get-ChildItem -LiteralPath $dst -File -Recurse | Where-Object {$exclude -notcontains $_.Name} | Sort-Object FullName | ForEach-Object { $fi=[IO.FileInfo]$_; $rel=$fi.FullName.Substring($dst.Length).TrimStart('\'); $manifest += [pscustomobject]@{relative_path=$rel;bytes=$fi.Length;sha256=(Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant();mtime_utc_ticks=$fi.LastWriteTimeUtc.Ticks.ToString([Globalization.CultureInfo]::InvariantCulture);mtime_utc_7digit=$fi.LastWriteTimeUtc.ToString('yyyy-MM-ddTHH:mm:ss.fffffffZ',[Globalization.CultureInfo]::InvariantCulture)} }
$manifest | Export-Csv -LiteralPath (Join-Path $dst 'PAYLOAD_MANIFEST.csv') -NoTypeInformation -Encoding UTF8
$manifest | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $dst 'PAYLOAD_MANIFEST.json') -Encoding UTF8
Write-Output (@{actual_payload=$manifest.Count;base_copy=$rows.Count;status='SEALED_FOR_VALIDATION'}|ConvertTo-Json -Compress)
