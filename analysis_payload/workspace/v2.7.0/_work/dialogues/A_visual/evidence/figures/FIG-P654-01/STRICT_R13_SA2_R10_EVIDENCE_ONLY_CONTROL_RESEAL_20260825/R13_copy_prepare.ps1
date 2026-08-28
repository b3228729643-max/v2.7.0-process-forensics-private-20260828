$ErrorActionPreference='Stop'
$src=[IO.Path]::GetFullPath('D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P654-01\STRICT_R10_SA2_TAXONOMY_R100_DIRECT_BUILD_20260825')
$dst=[IO.Path]::GetFullPath('D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P654-01\STRICT_R13_SA2_R10_EVIDENCE_ONLY_CONTROL_RESEAL_20260825')
if(!(Test-Path -LiteralPath $src -PathType Container)-or !(Test-Path -LiteralPath $dst -PathType Container)){throw 'roots missing'}
if($src -eq $dst){throw 'roots equal'}
$exclude=@('PAYLOAD_MANIFEST.csv','PAYLOAD_MANIFEST.json','WRITE_STOPPED.json')
$files=Get-ChildItem -LiteralPath $src -File -Recurse | Where-Object { $_.FullName.Substring($src.Length+1) -notin $exclude }
if($files.Count -ne 1052){throw "base count $($files.Count)"}
foreach($f in $files){$rel=$f.FullName.Substring($src.Length+1);$out=Join-Path $dst $rel;$dir=Split-Path -Parent $out;if(!(Test-Path -LiteralPath $dir)){New-Item -ItemType Directory -Force -Path $dir|Out-Null};Copy-Item -LiteralPath $f.FullName -Destination $out -Force;[IO.File]::SetLastWriteTimeUtc($out,$f.LastWriteTimeUtc)}
$rows=@();foreach($f in $files){$rel=$f.FullName.Substring($src.Length+1);$out=Join-Path $dst $rel;$sf=Get-Item -LiteralPath $f.FullName;$df=Get-Item -LiteralPath $out;$h=(Get-FileHash -LiteralPath $f.FullName -Algorithm SHA256).Hash.ToLowerInvariant();$dh=(Get-FileHash -LiteralPath $out -Algorithm SHA256).Hash.ToLowerInvariant();if($sf.Length-ne$df.Length-or$h-ne$dh-or$sf.LastWriteTimeUtc.Ticks-ne$df.LastWriteTimeUtc.Ticks){throw "copy mismatch $rel"};$rows += [pscustomobject]@{relative_path=$rel;source_bytes=[int64]$sf.Length;dest_bytes=[int64]$df.Length;source_sha256=$h;dest_sha256=$dh;source_mtime_utc_ticks=$sf.LastWriteTimeUtc.Ticks.ToString([Globalization.CultureInfo]::InvariantCulture);dest_mtime_utc_ticks=$df.LastWriteTimeUtc.Ticks.ToString([Globalization.CultureInfo]::InvariantCulture);source_mtime_utc_7digit=$sf.LastWriteTimeUtc.ToString('yyyy-MM-ddTHH:mm:ss.fffffffZ');dest_mtime_utc_7digit=$df.LastWriteTimeUtc.ToString('yyyy-MM-ddTHH:mm:ss.fffffffZ')}}
$rows|Export-Csv -LiteralPath (Join-Path $dst 'R13_BASE_COPY_IDENTITY.csv') -NoTypeInformation -Encoding UTF8
$prov=[ordered]@{source_root=$src;target_root=$dst;round='R13';created_at=[DateTime]::UtcNow.ToString('o');base_file_count=1052;excluded_controls=$exclude};$prov|ConvertTo-Json -Depth 5|Set-Content -LiteralPath (Join-Path $dst 'R13_COPY_PROVENANCE.json') -Encoding UTF8
$rows|ConvertTo-Json -Depth 4|Set-Content -LiteralPath (Join-Path $dst 'R13_BASE_COPY_IDENTITY.json') -Encoding UTF8
if((Get-ChildItem -LiteralPath $dst -File -Recurse|Measure-Object).Count -lt 1056){throw 'copy outputs missing'}
