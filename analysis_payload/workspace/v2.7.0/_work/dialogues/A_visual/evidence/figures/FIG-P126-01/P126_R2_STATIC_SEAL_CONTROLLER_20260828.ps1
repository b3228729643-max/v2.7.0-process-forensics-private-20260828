#requires -Version 7.0
[CmdletBinding()]
param()
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$root='D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\STRICT_R2_SA2_STATIC_COORDINATE_QUADRATIC_PATCH_R115_20260828'
$base=[IO.Path]::GetDirectoryName($root)
$stage=[IO.Path]::Combine($base,'P126_R2_STATIC_WRITE_STOPPED_STAGE_20260828')
$result=[IO.Path]::Combine($base,'P126_R2_STATIC_SEAL_RESULT_20260828.json')
$payloadNames=@('CLEARANCE_PROJECTION.json','MATHEMATICAL_PROOF.json','SCOPE_AUDIT.json','SOURCE_EXACT_DIFF.md','SOURCE_IDENTITY.json','STATIC_RESULT.json')
$utf8=[Text.UTF8Encoding]::new($false)
function Assert-True([bool]$Value,[string]$Message){if(-not$Value){throw$Message}}
function Sha([string]$Path){(Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToUpperInvariant()}
function Write-Text([string]$Path,[string]$Text){[IO.File]::WriteAllText($Path,$Text,$utf8)}
function ReadOnly([string]$Path){$i=Get-Item -LiteralPath $Path -Force;[IO.File]::SetAttributes($i.FullName,($i.Attributes-bor[IO.FileAttributes]::ReadOnly))}
function IsReadOnly($Item){(($Item.Attributes-band[IO.FileAttributes]::ReadOnly)-ne0)}
Assert-True (Test-Path -LiteralPath $root -PathType Container) 'Static root missing.'
Assert-True (-not(Test-Path -LiteralPath $stage)) 'Stage exists.'
Assert-True (-not(Test-Path -LiteralPath $result)) 'Result exists.'
$existing=@(Get-ChildItem -LiteralPath $root -Recurse -File -Force)
Assert-True ($existing.Count-eq6) 'Payload count mismatch.'
$actual=@($existing|ForEach-Object{[IO.Path]::GetRelativePath($root,$_.FullName).Replace('\','/')}|Sort-Object -CaseSensitive)
$diff=@((Compare-Object -ReferenceObject @($payloadNames|Sort-Object -CaseSensitive)-DifferenceObject $actual -CaseSensitive))
Assert-True ($diff.Count-eq0) 'Payload set mismatch.'
$rows=@();foreach($name in $payloadNames){$p=[IO.Path]::Combine($root,$name);$i=Get-Item -LiteralPath $p -Force;$rows+=[pscustomobject]@{relative_path=$name;bytes=[int64]$i.Length;sha256=Sha $p;creation_time_utc_ticks=[int64]$i.CreationTimeUtc.Ticks;last_write_time_utc_ticks=[int64]$i.LastWriteTimeUtc.Ticks}}
$manifest=[IO.Path]::Combine($root,'PAYLOAD_MANIFEST.csv');$rows|Export-Csv -LiteralPath $manifest -NoTypeInformation -UseQuotes AsNeeded -Encoding utf8
$manifestSha=Sha $manifest
$audit=[ordered]@{format_version=1;handoff_id='A-R115-P126-SA2-STATIC-COORDINATE-QUADRATIC-PATCH-20260828';status='STATIC_ONLY_NOT_RENDERED_NOT_PASS';payload_count=6;control_count=3;ordinary_count=9;manifest_sha256=$manifestSha;tex_invocations=0;build_invocations=0;commit_count=0;premarker_complete=$true;postmarker_write_policy='ZERO'}
$auditPath=[IO.Path]::Combine($root,'SEAL_AUDIT.json');Write-Text $auditPath (($audit|ConvertTo-Json -Depth 6)+"`n");$auditSha=Sha $auditPath
$files=@(Get-ChildItem -LiteralPath $root -Recurse -File -Force);Assert-True ($files.Count-eq8) 'Premarker ordinary count mismatch.';foreach($f in $files){ReadOnly $f.FullName}
$dirs=@((Get-Item -LiteralPath $root -Force))+@(Get-ChildItem -LiteralPath $root -Recurse -Directory -Force);foreach($d in @($dirs|Sort-Object{$_.FullName.Length}-Descending)){ReadOnly $d.FullName}
Assert-True (@($files|ForEach-Object{Get-Item -LiteralPath $_.FullName -Force}|Where-Object{-not(IsReadOnly $_)}).Count-eq0) 'Writable premarker file.'
Assert-True (@($dirs|ForEach-Object{Get-Item -LiteralPath $_.FullName -Force}|Where-Object{-not(IsReadOnly $_)}).Count-eq0) 'Writable premarker directory.'
$items=@((Get-Item -LiteralPath $root -Force))+@(Get-ChildItem -LiteralPath $root -Recurse -Force);$max=(@($items|ForEach-Object{$_.LastWriteTimeUtc.Ticks})|Measure-Object -Maximum).Maximum;$future=[Math]::Max([DateTime]::UtcNow.AddMinutes(5).Ticks,[int64]$max+[TimeSpan]::FromMinutes(3).Ticks)
$lines=@('FORMAT_VERSION=1','HANDOFF_ID=A-R115-P126-SA2-STATIC-COORDINATE-QUADRATIC-PATCH-20260828','STATUS=STATIC_ONLY_NOT_RENDERED_NOT_PASS','PAYLOAD_COUNT=6','CONTROL_COUNT=3','ORDINARY_COUNT=9',"PAYLOAD_MANIFEST_SHA256=$manifestSha","SEAL_AUDIT_SHA256=$auditSha",'TEX_INVOCATIONS=0','BUILD_INVOCATIONS=0','COMMIT_COUNT=0','PREMARKER_READONLY_VERIFIED=true','FINAL_MOVE_COUNT=1','POSTMARKER_WRITES=0',"MARKER_TARGET_TICKS=$future")
Assert-True (@($lines|Where-Object{$_-notmatch'^[^=\s]+=[^=\r\n\t]+$'}).Count-eq0) 'Marker syntax.'
Assert-True (@($lines|ForEach-Object{($_-split'=',2)[0]}|Group-Object -Property{[string]$_}|Where-Object{$_.Count-ne1}).Count-eq0) 'Marker duplicate key.'
Write-Text $stage (($lines-join"`n")+"`n");[IO.File]::SetLastWriteTimeUtc($stage,[DateTime]::new($future,[DateTimeKind]::Utc));ReadOnly $stage
$marker=[IO.Path]::Combine($root,'WRITE_STOPPED');Move-Item -LiteralPath $stage -Destination $marker
$finalFiles=@(Get-ChildItem -LiteralPath $root -Recurse -File -Force);$finalDirs=@((Get-Item -LiteralPath $root -Force))+@(Get-ChildItem -LiteralPath $root -Recurse -Directory -Force);$m=Get-Item -LiteralPath $marker -Force;$other=@((Get-Item -LiteralPath $root -Force))+@(Get-ChildItem -LiteralPath $root -Recurse -Force|Where-Object{$_.FullName-ne$m.FullName});$at=@($other|Where-Object{$_.LastWriteTimeUtc.Ticks-ge$m.LastWriteTimeUtc.Ticks});$otherMax=(@($other|ForEach-Object{$_.LastWriteTimeUtc.Ticks})|Measure-Object -Maximum).Maximum;$margin=$m.LastWriteTimeUtc.Ticks-[int64]$otherMax
Assert-True ($finalFiles.Count -eq 9 -and @($finalFiles|Where-Object{-not(IsReadOnly $_)}).Count -eq 0 -and @($finalDirs|ForEach-Object{Get-Item -LiteralPath $_.FullName -Force}|Where-Object{-not(IsReadOnly $_)}).Count -eq 0 -and $at.Count -eq 0 -and $margin -gt 0) 'Final seal gate.'
$out=[ordered]@{status='SEALED_STATIC_ONLY_NOT_RENDERED_NOT_PASS';payload_count=6;control_count=3;ordinary_count=9;directory_count=$finalDirs.Count;readonly_files=9;readonly_directories=$finalDirs.Count;manifest_sha256=$manifestSha;seal_audit_sha256=$auditSha;write_stopped_sha256=Sha $marker;marker_margin_ticks=$margin;at_or_after_excluding_marker=0;postmarker_writes=0}
Write-Text $result (($out|ConvertTo-Json -Depth 6)+"`n");$out|ConvertTo-Json -Compress
