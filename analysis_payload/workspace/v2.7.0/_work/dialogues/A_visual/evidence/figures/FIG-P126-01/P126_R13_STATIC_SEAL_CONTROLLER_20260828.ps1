Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$root='D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\STRICT_R13_SA2_STATIC_DISCONNECTED_LEGEND_HANDLER_R115_20260828'
$parent=[IO.Path]::GetDirectoryName($root)
$stage=Join-Path $parent 'P126_R13_STATIC_WRITE_STOPPED_STAGE_20260828.tmp'
$result=Join-Path $parent 'P126_R13_STATIC_SEAL_CONTROLLER_RESULT_20260828.json'
$source='D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_A_visual\src\绘图源码\第01册_数学基础与统计学习基本理论\V1-C08\fig_v1_c08_coordinate.tex'
$utf8=[Text.UTF8Encoding]::new($false)
function Sha([string]$p){(Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash}
function Canon([string]$base,[string]$path){$b=[IO.Path]::GetFullPath($base).TrimEnd('\')+'\';$f=[IO.Path]::GetFullPath($path);if(-not $f.StartsWith($b,[StringComparison]::OrdinalIgnoreCase)){throw 'PATH_ESCAPE'};$f.Substring($b.Length).Replace('\','/')}
function Row([string]$base,[string]$path){$i=Get-Item -LiteralPath $path -Force;[ordered]@{relative_path=Canon $base $path;bytes=[long]$i.Length;sha256=Sha $path;creation_time_utc_ticks=[long]$i.CreationTimeUtc.Ticks;last_write_time_utc_ticks=[long]$i.LastWriteTimeUtc.Ticks}}
function SetRO([string]$p){$i=Get-Item -LiteralPath $p -Force;[IO.File]::SetAttributes($i.FullName,($i.Attributes -bor [IO.FileAttributes]::ReadOnly))}
function IsRO([string]$p){(((Get-Item -LiteralPath $p -Force).Attributes -band [IO.FileAttributes]::ReadOnly)-ne0)}
function Ads([string]$base){$rootItem=Get-Item -LiteralPath $base -Force -ErrorAction Stop;$children=@(Get-ChildItem -LiteralPath $base -Recurse -Force -ErrorAction Stop);$items=@($rootItem)+$children;$non=0;foreach($item in $items){$streams=@(Get-Item -LiteralPath $item.FullName -Stream * -Force -ErrorAction Stop);$non+=@($streams|Where-Object{$_.Stream-ne':$DATA'}).Count};[ordered]@{items=$items.Count;files=@($children|Where-Object{-not$_.PSIsContainer}).Count;child_dirs=@($children|Where-Object{$_.PSIsContainer}).Count;root=1;nondefault=$non}}
function Snap([string]$base){$rootItem=Get-Item -LiteralPath $base -Force;$items=@($rootItem)+@(Get-ChildItem -LiteralPath $base -Recurse -Force|Sort-Object FullName);$lines=@();foreach($i in $items){$rel=if($i.FullName-ceq$base){'.'}else{Canon $base $i.FullName};$sha=if($i.PSIsContainer){'-'}else{Sha $i.FullName};$bytes=if($i.PSIsContainer){0}else{[long]$i.Length};$lines+=('{0}`t{1}`t{2}`t{3}`t{4}`t{5}'-f$rel,$bytes,$sha,$i.CreationTimeUtc.Ticks,$i.LastWriteTimeUtc.Ticks,[int]$i.Attributes)};$data=$utf8.GetBytes(($lines-join"`n")+"`n");[ordered]@{entries=$items.Count;sha256=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($data))}}
if(-not(Test-Path -LiteralPath $root -PathType Container)){throw 'ROOT_MISSING'}
foreach($p in @($stage,$result)){if(Test-Path -LiteralPath $p){throw 'EXTERNAL_PREEXISTS'}}
$expected=@('GIT_SCOPE.txt','INCREMENTAL_DIFF.patch','PGFPLOTS_HANDLER_CAUSALITY.md','REVERSE_RECONSTRUCTION.json','SOURCE_IDENTITY.json','STATIC_GAP_PROJECTION.json','STATIC_HANDOFF.md','STATIC_LEGEND_PROJECTION.svg','STATIC_REPORT.md','STATIC_SCOPE.md')
$files=@(Get-ChildItem -LiteralPath $root -Recurse -File -Force)
$dirs=@(Get-ChildItem -LiteralPath $root -Recurse -Directory -Force)
if($dirs.Count-ne0-or$files.Count-ne10){throw 'PAYLOAD_COUNT'}
$names=@($files|ForEach-Object{Canon $root $_.FullName}|Sort-Object)
if(@(Compare-Object -ReferenceObject @($expected|Sort-Object) -DifferenceObject $names -CaseSensitive).Count-ne0){throw 'PAYLOAD_SET'}
$si=Get-Item -LiteralPath $source
if($si.Length-ne4626-or(Sha $source)-cne'6CBAEBE50574E541A04B2FDCC74B432C49AF2590B579C6A85721EDF536912502'){throw 'SOURCE_IDENTITY'}
foreach($j in @('SOURCE_IDENTITY.json','REVERSE_RECONSTRUCTION.json','STATIC_GAP_PROJECTION.json')){$null=Get-Content -LiteralPath (Join-Path $root $j)-Raw|ConvertFrom-Json}
$null=[xml](Get-Content -LiteralPath (Join-Path $root 'STATIC_LEGEND_PROJECTION.svg')-Raw)
$adsPayload=Ads $root;if($adsPayload.nondefault-ne0){throw 'PAYLOAD_ADS'}
$rows=@($files|ForEach-Object{Row $root $_.FullName}|Sort-Object -Property{[string]$_['relative_path']})
if(@($rows|Group-Object -Property{[string]$_['relative_path']}|Where-Object{$_.Count-ne1}).Count-ne0){throw 'DUPLICATE'}
$manifest=Join-Path $root 'PAYLOAD_MANIFEST.csv'
[IO.File]::WriteAllLines($manifest,@($rows|ForEach-Object{[pscustomobject]$_}|ConvertTo-Csv -NoTypeInformation),$utf8)
$manifestSha=Sha $manifest
$audit=Join-Path $root 'SEAL_AUDIT.json'
$auditObject=[ordered]@{schema='P126_R13_STATIC_SEAL_AUDIT_V1';handoff_id='A-R115-P126-SA2-STATIC-DISCONNECTED-LEGEND-HANDLER-20260828';status='STATIC_ONLY_NOT_RENDERED_NOT_PASS';payload_count=10;control_count=3;ordinary_count=13;manifest_rows=10;manifest_sha256=$manifestSha;source_bytes=4626;source_sha256='6CBAEBE50574E541A04B2FDCC74B432C49AF2590B579C6A85721EDF536912502';reverse_bytes=4373;reverse_sha256='81EFC188FA5E4827CAAB034C1EA3F7F4AFE25375DEE4046CD46F3FF49B0789BD';payload_ads_nondefault=0;tex_build_commit=@{tex=0;build=0;commit=0};preseal_errors=0}
[IO.File]::WriteAllText($audit,($auditObject|ConvertTo-Json -Depth 6),$utf8)
$auditSha=Sha $audit
$premarker=@(Get-ChildItem -LiteralPath $root -Recurse -File -Force);if($premarker.Count-ne12){throw 'PREMARKER_COUNT'}
$adsPre=Ads $root;if($adsPre.nondefault-ne0){throw 'PREMARKER_ADS'}
foreach($f in $premarker){SetRO $f.FullName};SetRO $root
if(@($premarker|Where-Object{-not(IsRO $_.FullName)}).Count-ne0-or-not(IsRO $root)){throw 'RO_GATE'}
$markerLines=@('SCHEMA=P126_R13_STATIC_WRITE_STOPPED_V1','HANDOFF_ID=A-R115-P126-SA2-STATIC-DISCONNECTED-LEGEND-HANDLER-20260828','STATUS=STATIC_ONLY_NOT_RENDERED_NOT_PASS','SOURCE_BYTES=4626','SOURCE_SHA256=6CBAEBE50574E541A04B2FDCC74B432C49AF2590B579C6A85721EDF536912502','PAYLOAD_COUNT=10','CONTROL_COUNT=3','ORDINARY_COUNT=13',"PAYLOAD_MANIFEST_SHA256=$manifestSha","SEAL_AUDIT_SHA256=$auditSha",'PREMARKER_FILES_READONLY=12','PREMARKER_DIRS_READONLY=1','PREMARKER_ADS_NONDEFAULT=0','TEX_COUNT=0','BUILD_COUNT=0','COMMIT_COUNT=0','CONTROLLER_INVOCATION_COUNT=1','RETRY_COUNT=0',"PREPARED_UTC=$([DateTime]::UtcNow.ToString('o'))")
if($markerLines.Count-ne19-or@($markerLines|Where-Object{$_-notmatch'^[A-Z0-9_]+=[^\r\n]+$'-or$_.Contains("`t")}).Count-ne0){throw 'MARKER_SYNTAX'}
[IO.File]::WriteAllLines($stage,$markerLines,$utf8);SetRO $stage
$allPre=@((Get-Item -LiteralPath $root -Force))+@(Get-ChildItem -LiteralPath $root -Recurse -Force)
$max=[long](($allPre|ForEach-Object{$_.LastWriteTimeUtc.Ticks}|Measure-Object -Maximum).Maximum)
$future=[Math]::Max($max+3000000000,[DateTime]::UtcNow.AddMinutes(5).Ticks)
[IO.File]::SetLastWriteTimeUtc($stage,[DateTime]::new($future,[DateTimeKind]::Utc));if(-not(IsRO $stage)){throw 'STAGE_RO'}
$marker=Join-Path $root 'WRITE_STOPPED';Move-Item -LiteralPath $stage -Destination $marker
$s1=Snap $root;Start-Sleep -Milliseconds 100;$s2=Snap $root
if($s1.sha256-cne$s2.sha256-or$s1.entries-ne$s2.entries){throw 'POSTMARKER_CHANGE'}
$markerItem=Get-Item -LiteralPath $marker;$others=@((Get-Item -LiteralPath $root -Force))+@(Get-ChildItem -LiteralPath $root -Recurse -Force|Where-Object{$_.FullName-cne$marker});$maxOther=[long](($others|ForEach-Object{$_.LastWriteTimeUtc.Ticks}|Measure-Object -Maximum).Maximum);$at=@($others|Where-Object{$_.LastWriteTimeUtc.Ticks-ge$markerItem.LastWriteTimeUtc.Ticks}).Count
if($at-ne0-or$markerItem.LastWriteTimeUtc.Ticks-le$maxOther){throw 'MARKER_LATEST'}
$out=[ordered]@{schema='P126_R13_STATIC_CONTROLLER_RESULT_V1';success=$true;exit_code=0;natural_exit=$true;controller_invocation_count=1;retry_count=0;root=$root;payload_count=10;control_count=3;ordinary_count=13;directory_count=1;manifest_sha256=$manifestSha;seal_audit_sha256=$auditSha;marker_bytes=$markerItem.Length;marker_sha256=Sha $marker;marker_lines=19;marker_keys=19;marker_ticks=$markerItem.LastWriteTimeUtc.Ticks;strict_latest_margin_ticks=[long]($markerItem.LastWriteTimeUtc.Ticks-$maxOther);at_or_after_excluding_marker=$at;payload_ads=$adsPayload;premarker_ads=$adsPre;snapshot_s1=$s1;snapshot_s2=$s2;source_bytes=$si.Length;source_sha256=Sha $source;status='STATIC_ONLY_NOT_RENDERED_NOT_PASS'}
[IO.File]::WriteAllText($result,($out|ConvertTo-Json -Depth 8),$utf8);SetRO $result
$out|ConvertTo-Json -Depth 8
