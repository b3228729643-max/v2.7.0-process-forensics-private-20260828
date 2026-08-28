$ErrorActionPreference='Stop'
$src=[IO.Path]::GetFullPath('D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P654-01\STRICT_R10_SA2_TAXONOMY_R100_DIRECT_BUILD_20260825')
$dst=[IO.Path]::GetFullPath('D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P654-01\STRICT_R12_SA2_R10_EVIDENCE_ONLY_CONTROL_RESEAL_20260825')
$expectedSrc='D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P654-01\STRICT_R10_SA2_TAXONOMY_R100_DIRECT_BUILD_20260825'
$expectedDst='D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P654-01\STRICT_R12_SA2_R10_EVIDENCE_ONLY_CONTROL_RESEAL_20260825'
if($src -ne [IO.Path]::GetFullPath($expectedSrc) -or $dst -ne [IO.Path]::GetFullPath($expectedDst)){throw 'root identity mismatch'}
$controls=@('PAYLOAD_MANIFEST.csv','PAYLOAD_MANIFEST.json','WRITE_STOPPED.json')
$sourceFiles=Get-ChildItem -LiteralPath $src -File -Recurse | Where-Object { $controls -notcontains $_.FullName.Substring($src.Length+1) }
if($sourceFiles.Count -ne 1052){throw "base count $($sourceFiles.Count)"}
foreach($f in $sourceFiles){
  $rel=$f.FullName.Substring($src.Length+1); $out=Join-Path $dst $rel
  $parent=Split-Path -Parent $out; if(!(Test-Path -LiteralPath $parent)){New-Item -ItemType Directory -Force -Path $parent | Out-Null}
  Copy-Item -LiteralPath $f.FullName -Destination $out -Force
  $ticks=$f.LastWriteTimeUtc.Ticks; [IO.File]::SetLastWriteTimeUtc($out,[DateTime]::new($ticks,[DateTimeKind]::Utc))
  $g=Get-Item -LiteralPath $out; $h=(Get-FileHash -LiteralPath $f.FullName -Algorithm SHA256).Hash
  if($g.Length -ne $f.Length -or (Get-FileHash -LiteralPath $out -Algorithm SHA256).Hash -ne $h -or $g.LastWriteTimeUtc.Ticks -ne $ticks){throw "copy mismatch $rel"}
}
$prov=[ordered]@{source_root=$src;target_root=$dst;round='R12_EVIDENCE_ONLY_CONTROL_RESEAL';created_at=[DateTime]::UtcNow.ToString('o')}
$provPath=Join-Path $dst 'R12_COPY_PROVENANCE.json'; $prov | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $provPath -Encoding UTF8
$raw=Get-Content -Raw -LiteralPath $provPath; if($raw -match '\$' ){throw 'provenance contains dollar'}
$check=$raw|ConvertFrom-Json; if($check.source_root -ne $src -or $check.target_root -ne $dst){throw 'provenance mismatch'}
$rows=foreach($f in $sourceFiles){$rel=$f.FullName.Substring($src.Length+1);$g=Get-Item (Join-Path $dst $rel);[ordered]@{relative_path=$rel;bytes=[int64]$g.Length;sha256=(Get-FileHash -LiteralPath $g.FullName -Algorithm SHA256).Hash.ToLowerInvariant();mtime_utc_ticks=$g.LastWriteTimeUtc.Ticks.ToString([Globalization.CultureInfo]::InvariantCulture);mtime_utc_7digit=$g.LastWriteTimeUtc.ToString('yyyy-MM-ddTHH:mm:ss.fffffffZ')}}
$rows | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $dst 'R12_BASE_COPY_IDENTITY.json') -Encoding UTF8
$rows | ConvertTo-Csv -NoTypeInformation | Set-Content -LiteralPath (Join-Path $dst 'R12_BASE_COPY_IDENTITY.csv') -Encoding UTF8
if((Get-Content (Join-Path $dst 'R12_BASE_COPY_IDENTITY.json') -Raw|ConvertFrom-Json).Count -ne 1052){throw 'identity json count'}
