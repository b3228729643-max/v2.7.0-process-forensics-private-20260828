Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$Root = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\STRICT_R6_SA2_STATIC_ABSOLUTE_LEGEND_KEY_PATCH_R115_20260828'
$Manifest = Join-Path $Root 'PAYLOAD_MANIFEST.csv'
$Audit = Join-Path $Root 'SEAL_AUDIT.json'
$Marker = Join-Path $Root 'WRITE_STOPPED'
$Stage = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\P126_R6_STATIC_WRITE_STOPPED.stage'
$Result = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\P126_R6_STATIC_SEAL_CONTROLLER_RESULT_20260828.json'
$Source = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_A_visual\src\绘图源码\第01册_数学基础与统计学习基本理论\V1-C08\fig_v1_c08_coordinate.tex'
$Utf8 = [Text.UTF8Encoding]::new($false)
function Sha([string]$Path) { (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToUpperInvariant() }
function WriteUtf8([string]$Path,[string]$Text) { [IO.File]::WriteAllText($Path,$Text,$Utf8) }
function Rel([string]$Path) { [IO.Path]::GetRelativePath($Root,$Path).Replace('\','/') }
function IsRO([string]$Path) { (([IO.File]::GetAttributes($Path) -band [IO.FileAttributes]::ReadOnly) -ne 0) }
function MakeRO([string]$Path) { [IO.File]::SetAttributes($Path,([IO.File]::GetAttributes($Path) -bor [IO.FileAttributes]::ReadOnly)) }
function Snapshot {
    $rows=[Collections.Generic.List[string]]::new()
    $files=@(Get-ChildItem -LiteralPath $Root -File -Recurse | Sort-Object FullName)
    foreach($f in $files){$rows.Add("F`t$(Rel $f.FullName)`t$($f.Length)`t$(Sha $f.FullName)`t$($f.CreationTimeUtc.Ticks)`t$($f.LastWriteTimeUtc.Ticks)`t$([int][IO.File]::GetAttributes($f.FullName))")}
    $dirs=@((Get-Item -LiteralPath $Root))+@(Get-ChildItem -LiteralPath $Root -Directory -Recurse | Sort-Object FullName)
    foreach($d in $dirs){$rp=if($d.FullName -eq $Root){'.'}else{Rel $d.FullName};$rows.Add("D`t$rp`t$($d.CreationTimeUtc.Ticks)`t$($d.LastWriteTimeUtc.Ticks)`t$([int][IO.File]::GetAttributes($d.FullName))")}
    $text=(@($rows|Sort-Object -CaseSensitive)-join "`n")+"`n"
    [ordered]@{files=$files.Count;dirs=$dirs.Count;sha256=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($Utf8.GetBytes($text)))}
}
if(-not(Test-Path -LiteralPath $Root -PathType Container)){throw 'root absent'}
foreach($p in @($Manifest,$Audit,$Marker,$Stage,$Result)){if(Test-Path -LiteralPath $p){throw "preexisting $p"}}
if((Get-Item -LiteralPath $Source).Length -ne 4366 -or (Sha $Source) -ne '20671687B41E0DD6C8D36774A7E669B0ABC55C5BBE8955BE39FA69137F52F279'){throw 'source identity'}
$payload=@(Get-ChildItem -LiteralPath $Root -File -Recurse | Sort-Object FullName)
if($payload.Count -ne 8){throw "payload count $($payload.Count)"}
$rows=foreach($f in $payload){[pscustomobject][ordered]@{relative_path=Rel $f.FullName;bytes=$f.Length;sha256=Sha $f.FullName;creation_time_utc_ticks=$f.CreationTimeUtc.Ticks;last_write_time_utc_ticks=$f.LastWriteTimeUtc.Ticks}}
if(@($rows.relative_path|Group-Object|Where-Object{$_.Count-ne1}).Count-ne0){throw 'duplicate paths'}
WriteUtf8 $Manifest ((($rows|ConvertTo-Csv -NoTypeInformation)-join "`r`n")+"`r`n")
$manifestSha=Sha $Manifest
$auditObject=[ordered]@{schema='P126_R6_STATIC_SEAL_AUDIT_V1';handoff_id='A-R115-P126-SA2-STATIC-ABSOLUTE-LEGEND-KEY-PATCH-20260828';verdict='STATIC_ONLY_NOT_RENDERED_NOT_PASS';payload_count=8;controls=3;ordinary=11;manifest_sha256=$manifestSha;source_bytes=4366;source_sha256='20671687B41E0DD6C8D36774A7E669B0ABC55C5BBE8955BE39FA69137F52F279';tex_count=0;build_count=0;commit_count=0;premarker='CLEAR'}
WriteUtf8 $Audit (($auditObject|ConvertTo-Json -Depth 5)+"`n")
$auditSha=Sha $Audit
$files=@(Get-ChildItem -LiteralPath $Root -File -Recurse)
$dirs=@((Get-Item -LiteralPath $Root))+@(Get-ChildItem -LiteralPath $Root -Directory -Recurse)
foreach($f in $files){MakeRO $f.FullName}
foreach($d in @($dirs|Sort-Object{$_.FullName.Length}-Descending)){MakeRO $d.FullName}
if(@($files|Where-Object{-not(IsRO $_.FullName)}).Count-ne0 -or @($dirs|Where-Object{-not(IsRO $_.FullName)}).Count-ne0){throw 'readonly gate'}
$max=0L;foreach($i in @($files)+@($dirs)){if($i.LastWriteTimeUtc.Ticks-gt$max){$max=$i.LastWriteTimeUtc.Ticks}}
$ticks=[Math]::Max($max+3000000000L,[DateTime]::UtcNow.AddMinutes(5).Ticks)
$markerLines=@('SCHEMA=P126_R6_STATIC_WRITE_STOPPED_V1','HANDOFF_ID=A-R115-P126-SA2-STATIC-ABSOLUTE-LEGEND-KEY-PATCH-20260828','OPERATION=P126_R115_R6_STATIC_SINGLE_SEAL','UID=FIG-P126-01','ROLE=SA2','VERDICT=STATIC_ONLY_NOT_RENDERED_NOT_PASS',"ROOT=$Root",'SOURCE_BYTES=4366','SOURCE_SHA256=20671687B41E0DD6C8D36774A7E669B0ABC55C5BBE8955BE39FA69137F52F279','PAYLOAD_COUNT=8','CONTROL_COUNT=3','ORDINARY_COUNT=11',"PAYLOAD_MANIFEST_SHA256=$manifestSha","SEAL_AUDIT_SHA256=$auditSha",'CONTROLLER_INVOCATION_COUNT=1','RETRY_COUNT=0','TEX_COUNT=0','BUILD_COUNT=0','COMMIT_COUNT=0',"PREPARED_UTC=$([DateTime]::UtcNow.ToString('o'))","LAST_WRITE_TIME_UTC_TICKS=$ticks")
if($markerLines.Count-ne21 -or @($markerLines|Where-Object{$_-notmatch'^[^=\s]+=[^\r\n]+$'}).Count-ne0){throw 'marker syntax'}
WriteUtf8 $Stage (($markerLines-join"`r`n")+"`r`n")
[IO.File]::SetLastWriteTimeUtc($Stage,[DateTime]::new($ticks,[DateTimeKind]::Utc));MakeRO $Stage
Move-Item -LiteralPath $Stage -Destination $Marker
$s1=Snapshot;Start-Sleep -Milliseconds 200;$s2=Snapshot
if($s1.sha256-ne$s2.sha256){throw 'postmarker mutation'}
$resultObject=[ordered]@{schema='P126_R6_STATIC_SEAL_CONTROLLER_RESULT_V1';exit=0;natural=$true;invocation=1;retry=0;payload=8;controls=3;ordinary=11;dirs=$s2.dirs;manifest_sha256=$manifestSha;audit_sha256=$auditSha;marker_sha256=Sha $Marker;marker_ticks=(Get-Item -LiteralPath $Marker).LastWriteTimeUtc.Ticks;snapshot1=$s1.sha256;snapshot2=$s2.sha256;completed_utc=[DateTime]::UtcNow.ToString('o')}
WriteUtf8 $Result (($resultObject|ConvertTo-Json -Depth 5)+"`n");MakeRO $Result
$resultObject|ConvertTo-Json -Depth 5
