Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$root = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\STRICT_R15_SA2_STATIC_FORGET_PLOT_PATCH_R115_20260828'
$source = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_A_visual\src\绘图源码\第01册_数学基础与统计学习基本理论\V1-C08\fig_v1_c08_coordinate.tex'
$manifest = Join-Path $root 'PAYLOAD_MANIFEST.csv'
$sealAudit = Join-Path $root 'SEAL_AUDIT.json'
$marker = Join-Path $root 'WRITE_STOPPED'
$stage = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\P126_R15_STATIC_WSTOP_STAGE_20260828.tmp'
$resultPath = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\P126_R15_STATIC_SEAL_CONTROLLER_RESULT_20260828.json'
$controls = @('PAYLOAD_MANIFEST.csv','SEAL_AUDIT.json','WRITE_STOPPED')

function Sha([string]$path) { (Get-FileHash -LiteralPath $path -Algorithm SHA256 -ErrorAction Stop).Hash.ToUpperInvariant() }
function WriteUtf8([string]$path,[string]$text) { [IO.File]::WriteAllText($path,$text,[Text.UTF8Encoding]::new($false)) }
function Rel([string]$path) {
  $value = [IO.Path]::GetRelativePath($root,$path).Replace('\','/')
  if ([string]::IsNullOrWhiteSpace($value) -or [IO.Path]::IsPathRooted($value) -or $value.StartsWith('/')) { throw "BAD_REL:$value" }
  if (@($value.Split('/') | Where-Object { [string]::IsNullOrEmpty($_) -or $_ -eq '.' -or $_ -eq '..' }).Count -ne 0) { throw "BAD_SEGMENT:$value" }
  $rootFull = [IO.Path]::GetFullPath($root).TrimEnd('\')
  $pathFull = [IO.Path]::GetFullPath($path)
  if (-not $pathFull.StartsWith($rootFull+'\',[StringComparison]::OrdinalIgnoreCase)) { throw "ESCAPE:$value" }
  $value
}
function Snap {
  $rows=[Collections.Generic.List[string]]::new()
  foreach($f in @(Get-ChildItem -LiteralPath $root -File -Recurse -Force -ErrorAction Stop)){
    $rows.Add("F`t$(Rel $f.FullName)`t$($f.Length)`t$(Sha $f.FullName)`t$($f.CreationTimeUtc.Ticks)`t$($f.LastWriteTimeUtc.Ticks)`t$([int]$f.Attributes)")
  }
  foreach($d in @((Get-Item -LiteralPath $root -Force -ErrorAction Stop)) + @(Get-ChildItem -LiteralPath $root -Directory -Recurse -Force -ErrorAction Stop)){
    $r=if($d.FullName -eq $root){'.'}else{Rel $d.FullName}
    $rows.Add("D`t$r`t0`t-`t$($d.CreationTimeUtc.Ticks)`t$($d.LastWriteTimeUtc.Ticks)`t$([int]$d.Attributes)")
  }
  $array=$rows.ToArray();[Array]::Sort($array,[StringComparer]::Ordinal)
  $bytes=[Text.UTF8Encoding]::new($false).GetBytes(([string]::Join("`n",$array))+"`n")
  [ordered]@{entries=$array.Count;sha256=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($bytes))}
}
function Ads([string]$path){@((Get-Item -LiteralPath $path -Stream * -Force -ErrorAction Stop)|Where-Object{$_.Stream -ne ':$DATA'}).Count}

if (-not (Test-Path -LiteralPath $root -PathType Container)) { throw 'ROOT_MISSING' }
foreach($p in @($manifest,$sealAudit,$marker,$stage,$resultPath)){if(Test-Path -LiteralPath $p){throw "PREEXISTS:$p"}}
$src=Get-Item -LiteralPath $source -Force -ErrorAction Stop
if($src.Length -ne 4686 -or (Sha $source) -ne '2887758F5CC94987BE750E1EC53B555FB88CE8F71B7260CABBE0A17DDF237405'){throw 'SOURCE_IDENTITY'}

$payload=@(Get-ChildItem -LiteralPath $root -File -Recurse -Force -ErrorAction Stop)
$rows=@(foreach($f in $payload){[pscustomobject][ordered]@{relative_path=Rel $f.FullName;bytes=[long]$f.Length;sha256=Sha $f.FullName;creation_time_utc_ticks=[long]$f.CreationTimeUtc.Ticks;last_write_time_utc_ticks=[long]$f.LastWriteTimeUtc.Ticks}})
$rows=@($rows|Sort-Object -Property{[string]$_.relative_path}-CaseSensitive)
if(@($rows|Group-Object -Property{[string]$_.relative_path}|Where-Object{$_.Count-ne 1}).Count-ne 0){throw 'DUP_PAYLOAD'}
WriteUtf8 $manifest ((($rows|ConvertTo-Csv -NoTypeInformation -UseQuotes AsNeeded)-join"`r`n")+"`r`n")
$manifestHash=Sha $manifest
if(@(Import-Csv -LiteralPath $manifest -ErrorAction Stop).Count-ne $rows.Count){throw 'MANIFEST_PARSE'}
$audit=[ordered]@{schema='P126_R15_STATIC_SEAL_AUDIT_V1';handoff_id='A-R115-P126-SA2-STATIC-FORGET-PLOT-PATCH-20260828';status='STATIC_ONLY_NOT_RENDERED_NOT_PASS';payload_count=$rows.Count;control_count=3;ordinary_count=$rows.Count+3;source_before_bytes=4626;source_before_sha256='6CBAEBE50574E541A04B2FDCC74B432C49AF2590B579C6A85721EDF536912502';source_after_bytes=4686;source_after_sha256='2887758F5CC94987BE750E1EC53B555FB88CE8F71B7260CABBE0A17DDF237405';incremental_diff_additions=5;incremental_diff_deletions=5;ordinary_addplots=5;ordinary_addplots_with_forget_plot=5;manual_legend_images=2;legend_entries=2;render_validation_pending=$true;tex_build_count=0}
WriteUtf8 $sealAudit (($audit|ConvertTo-Json -Depth 5)+"`n")
$sealHash=Sha $sealAudit
$null=Get-Content -LiteralPath $sealAudit -Raw -ErrorAction Stop|ConvertFrom-Json -Depth 10 -ErrorAction Stop

$files=@(Get-ChildItem -LiteralPath $root -File -Recurse -Force -ErrorAction Stop)
$dirs=@((Get-Item -LiteralPath $root -Force -ErrorAction Stop))+@(Get-ChildItem -LiteralPath $root -Directory -Recurse -Force -ErrorAction Stop)
$ads=0;foreach($i in @($files+$dirs)){$ads+=Ads $i.FullName};if($ads-ne 0){throw 'ADS'}
$bad=@(Get-ChildItem -LiteralPath $root -Force -Recurse -ErrorAction Stop|Where-Object{$_.Name-eq'__pycache__'-or$_.Extension-in@('.pyc','.pyo')-or($_.Attributes-band[IO.FileAttributes]::ReparsePoint)-ne0}).Count;if($bad-ne0){throw 'HYGIENE'}
foreach($f in $files){[IO.File]::SetAttributes($f.FullName,([IO.File]::GetAttributes($f.FullName)-bor[IO.FileAttributes]::ReadOnly))}
foreach($d in @($dirs|Sort-Object{$_.FullName.Length}-Descending)){[IO.File]::SetAttributes($d.FullName,([IO.File]::GetAttributes($d.FullName)-bor[IO.FileAttributes]::ReadOnly))}
$files=@(Get-ChildItem -LiteralPath $root -File -Recurse -Force -ErrorAction Stop)
$dirs=@((Get-Item -LiteralPath $root -Force -ErrorAction Stop))+@(Get-ChildItem -LiteralPath $root -Directory -Recurse -Force -ErrorAction Stop)
if(@($files|Where-Object{-not$_.IsReadOnly}).Count-ne0-or@($dirs|Where-Object{($_.Attributes-band[IO.FileAttributes]::ReadOnly)-eq0}).Count-ne0){throw 'RO_GATE'}
$max=[long]0;foreach($i in @($files+$dirs)){if($i.LastWriteTimeUtc.Ticks-gt$max){$max=$i.LastWriteTimeUtc.Ticks}}
$ticks=[Math]::Max($max+3000000000L,[DateTime]::UtcNow.AddMinutes(5).Ticks)
$ordinary=$rows.Count+3
$lines=@('SCHEMA=P126_R15_STATIC_WRITE_STOPPED_V1','HANDOFF_ID=A-R115-P126-SA2-STATIC-FORGET-PLOT-PATCH-20260828','STATUS=STATIC_ONLY_NOT_RENDERED_NOT_PASS',"ROOT=$root","PAYLOAD_COUNT=$($rows.Count)",'CONTROL_COUNT=3',"ORDINARY_COUNT=$ordinary","MANIFEST_SHA256=$manifestHash","SEAL_AUDIT_SHA256=$sealHash",'SOURCE_BEFORE_BYTES=4626','SOURCE_BEFORE_SHA256=6CBAEBE50574E541A04B2FDCC74B432C49AF2590B579C6A85721EDF536912502','SOURCE_AFTER_BYTES=4686','SOURCE_AFTER_SHA256=2887758F5CC94987BE750E1EC53B555FB88CE8F71B7260CABBE0A17DDF237405','INCREMENTAL_DIFF_ADDITIONS=5','INCREMENTAL_DIFF_DELETIONS=5','ORDINARY_ADDPLOTS=5','ORDINARY_ADDPLOTS_WITH_FORGET_PLOT=5','MANUAL_LEGEND_IMAGES=2','LEGEND_ENTRIES=2','RENDER_VALIDATION_PENDING=TRUE','TEX_BUILD_COUNT=0','CONTROLLER_INVOCATION=1','RETRY_COUNT=0','PREMARKER_TREE_READONLY=TRUE',"MARKER_LAST_WRITE_UTC_TICKS=$ticks")
if(@($lines|Where-Object{$_-notmatch'^[A-Z0-9_]+=[^=].*$'}).Count-ne0-or@($lines|ForEach-Object{($_-split'=',2)[0]}|Group-Object|Where-Object{$_.Count-ne1}).Count-ne0){throw 'MARKER_PREWRITE'}
WriteUtf8 $stage (($lines-join"`n")+"`n")
[IO.File]::SetAttributes($stage,([IO.File]::GetAttributes($stage)-bor[IO.FileAttributes]::ReadOnly));[IO.File]::SetLastWriteTimeUtc($stage,[DateTime]::new($ticks,[DateTimeKind]::Utc))
if(-not(Get-Item -LiteralPath $stage -Force).IsReadOnly-or(Get-Item -LiteralPath $stage -Force).LastWriteTimeUtc.Ticks-ne$ticks){throw 'STAGE_GATE'}
Move-Item -LiteralPath $stage -Destination $marker -ErrorAction Stop
$s1=Snap;Start-Sleep -Milliseconds 300;$s2=Snap;if($s1.sha256-ne$s2.sha256){throw 'POSTMARKER_DRIFT'}
if((Get-Item -LiteralPath $source).Length-ne4686-or(Sha $source)-ne'2887758F5CC94987BE750E1EC53B555FB88CE8F71B7260CABBE0A17DDF237405'){throw 'SOURCE_AFTER'}
$result=[ordered]@{schema='P126_R15_STATIC_SEAL_CONTROLLER_RESULT_V1';success=$true;invocation_count=1;retry_count=0;payload_count=$rows.Count;control_count=3;ordinary_count=$ordinary;marker_lines=$lines.Count;marker_sha256=Sha $marker;marker_ticks=$ticks;snapshot_entries=$s1.entries;snapshot_sha256=$s1.sha256;postmarker_drift=0;source_identity_mismatch=0}
WriteUtf8 $resultPath (($result|ConvertTo-Json -Depth 5)+"`n")
