Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$root='D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\STRICT_R13_SA2_STATIC_DISCONNECTED_LEGEND_HANDLER_R115_20260828'
$parent=[IO.Path]::GetDirectoryName($root)
$controller=Join-Path $parent 'P126_R13_STATIC_SEAL_CONTROLLER_20260828.ps1'
$controllerResult=Join-Path $parent 'P126_R13_STATIC_SEAL_CONTROLLER_RESULT_20260828.json'
$result=Join-Path $parent 'P126_R13_STATIC_SEAL_AUDITOR_RESULT_20260828.json'
$stage=Join-Path $parent 'P126_R13_STATIC_WRITE_STOPPED_STAGE_20260828.tmp'
$utf8=[Text.UTF8Encoding]::new($false)
function Sha([string]$p){(Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash}
function Canon([string]$base,[string]$path){$b=[IO.Path]::GetFullPath($base).TrimEnd('\')+'\';$f=[IO.Path]::GetFullPath($path);if(-not$f.StartsWith($b,[StringComparison]::OrdinalIgnoreCase)){throw'PATH_ESCAPE'};$f.Substring($b.Length).Replace('\','/')}
function Row([string]$base,[string]$path){$i=Get-Item -LiteralPath $path -Force;[ordered]@{relative_path=Canon $base $path;bytes=[long]$i.Length;sha256=Sha $path;creation_time_utc_ticks=[long]$i.CreationTimeUtc.Ticks;last_write_time_utc_ticks=[long]$i.LastWriteTimeUtc.Ticks}}
function IsRO([string]$p){(((Get-Item -LiteralPath $p -Force).Attributes-band[IO.FileAttributes]::ReadOnly)-ne0)}
function Ads([string]$base){$r=Get-Item -LiteralPath $base -Force -ErrorAction Stop;$c=@(Get-ChildItem -LiteralPath $base -Recurse -Force -ErrorAction Stop);$items=@($r)+$c;$non=0;foreach($i in $items){$s=@(Get-Item -LiteralPath $i.FullName -Stream * -Force -ErrorAction Stop);$non+=@($s|Where-Object{$_.Stream-ne':$DATA'}).Count};[ordered]@{items=$items.Count;files=@($c|Where-Object{-not$_.PSIsContainer}).Count;child_dirs=@($c|Where-Object{$_.PSIsContainer}).Count;root=1;nondefault=$non}}
function Snap([string]$base){$r=Get-Item -LiteralPath $base -Force;$items=@($r)+@(Get-ChildItem -LiteralPath $base -Recurse -Force|Sort-Object FullName);$lines=@();foreach($i in $items){$rel=if($i.FullName-ceq$base){'.'}else{Canon $base $i.FullName};$sha=if($i.PSIsContainer){'-'}else{Sha $i.FullName};$bytes=if($i.PSIsContainer){0}else{[long]$i.Length};$lines+=('{0}`t{1}`t{2}`t{3}`t{4}`t{5}'-f$rel,$bytes,$sha,$i.CreationTimeUtc.Ticks,$i.LastWriteTimeUtc.Ticks,[int]$i.Attributes)};$data=$utf8.GetBytes(($lines-join"`n")+"`n");[ordered]@{entries=$items.Count;sha256=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($data))}}
foreach($p in @($root,$controller,$controllerResult)){if(-not(Test-Path -LiteralPath $p)){throw'MISSING'}}
foreach($p in @($result,$stage)){if(Test-Path -LiteralPath $p){throw'EXTERNAL_PREEXISTS'}}
$cr=Get-Content -LiteralPath $controllerResult -Raw|ConvertFrom-Json
if(-not$cr.success-or$cr.exit_code-ne0-or$cr.controller_invocation_count-ne1-or$cr.retry_count-ne0-or$cr.status-cne'STATIC_ONLY_NOT_RENDERED_NOT_PASS'){throw'CONTROLLER_RESULT'}
$manifest=Join-Path $root 'PAYLOAD_MANIFEST.csv';$audit=Join-Path $root 'SEAL_AUDIT.json';$marker=Join-Path $root 'WRITE_STOPPED'
$rows=@(Import-Csv -LiteralPath $manifest);if($rows.Count-ne10-or@($rows|Group-Object relative_path|Where-Object{$_.Count-ne1}).Count-ne0){throw'MANIFEST_ROWS'}
$controls=@('PAYLOAD_MANIFEST.csv','SEAL_AUDIT.json','WRITE_STOPPED')
$payload=@(Get-ChildItem -LiteralPath $root -Recurse -File -Force|Where-Object{$controls-notcontains(Canon $root $_.FullName)})
if($payload.Count-ne10){throw'PAYLOAD_COUNT'}
$map=[Collections.Generic.Dictionary[string,object]]::new([StringComparer]::Ordinal);foreach($r in $rows){if(-not$map.TryAdd([string]$r.relative_path,$r)){throw'DUP'}}
$mismatch=0;foreach($f in $payload){$x=Row $root $f.FullName;$k=[string]$x['relative_path'];if(-not$map.ContainsKey($k)){$mismatch++;continue};$r=$map[$k];foreach($field in @('bytes','sha256','creation_time_utc_ticks','last_write_time_utc_ticks')){if([string]$r.$field-cne[string]$x[$field]){$mismatch++}}};if($mismatch-ne0){throw'IDENTITY'}
$files=@(Get-ChildItem -LiteralPath $root -Recurse -File -Force);$dirs=@((Get-Item -LiteralPath $root -Force))+@(Get-ChildItem -LiteralPath $root -Recurse -Directory -Force)
if($files.Count-ne13-or$dirs.Count-ne1-or@($files|Where-Object{-not(IsRO $_.FullName)}).Count-ne0-or@($dirs|Where-Object{-not(IsRO $_.FullName)}).Count-ne0){throw'COUNT_RO'}
$lines=@([IO.File]::ReadAllLines($marker,$utf8));$keys=@($lines|ForEach-Object{$_.Split('=',2)[0]});if($lines.Count-ne19-or@($lines|Where-Object{$_-notmatch'^[A-Z0-9_]+=[^\r\n]+$'-or$_.Contains("`t")}).Count-ne0-or@($keys|Group-Object|Where-Object{$_.Count-ne1}).Count-ne0){throw'MARKER_SYNTAX'}
$markerItem=Get-Item -LiteralPath $marker;$others=@((Get-Item -LiteralPath $root -Force))+@(Get-ChildItem -LiteralPath $root -Recurse -Force|Where-Object{$_.FullName-cne$marker});$max=[long](($others|ForEach-Object{$_.LastWriteTimeUtc.Ticks}|Measure-Object -Maximum).Maximum);$at=@($others|Where-Object{$_.LastWriteTimeUtc.Ticks-ge$markerItem.LastWriteTimeUtc.Ticks}).Count;if($at-ne0-or$markerItem.LastWriteTimeUtc.Ticks-le$max){throw'MARKER_LATEST'}
$json=@(Get-ChildItem -LiteralPath $root -Recurse -File -Filter '*.json' -Force);$jsonFail=0;foreach($f in $json){try{$null=Get-Content -LiteralPath $f.FullName -Raw|ConvertFrom-Json}catch{$jsonFail++}}
$csv=@(Get-ChildItem -LiteralPath $root -Recurse -File -Filter '*.csv' -Force);$csvFail=0;foreach($f in $csv){try{$null=@(Import-Csv -LiteralPath $f.FullName)}catch{$csvFail++}}
$xmlFail=0;try{$null=[xml](Get-Content -LiteralPath (Join-Path $root 'STATIC_LEGEND_PROJECTION.svg')-Raw)}catch{$xmlFail++}
$ads=Ads $root;$cache=@(Get-ChildItem -LiteralPath $root -Recurse -Force|Where-Object{$_.Name-in@('__pycache__','.pytest_cache','.mypy_cache','.ruff_cache')}).Count;$pyc=@(Get-ChildItem -LiteralPath $root -Recurse -File -Filter '*.pyc' -Force).Count;$reparse=@((@((Get-Item -LiteralPath $root -Force))+@(Get-ChildItem -LiteralPath $root -Recurse -Force))|Where-Object{($_.Attributes-band[IO.FileAttributes]::ReparsePoint)-ne0}).Count
if($jsonFail-ne0-or$csvFail-ne0-or$xmlFail-ne0-or$ads.nondefault-ne0-or$cache-ne0-or$pyc-ne0-or$reparse-ne0){throw'HYGIENE'}
$snap=Snap $root;if($snap.sha256-cne$cr.snapshot_s1.sha256-or$snap.sha256-cne$cr.snapshot_s2.sha256){throw'POSTMARKER'}
$out=[ordered]@{schema='P126_R13_STATIC_AUDITOR_RESULT_V1';success=$true;exit_code=0;auditor_invocation_count=1;retry_count=0;root=$root;payload_count=10;control_count=3;ordinary_count=13;directory_count=1;manifest_rows=10;manifest_identity_mismatch=0;file_readonly_fail=0;directory_readonly_fail=0;marker_bytes=$markerItem.Length;marker_sha256=Sha $marker;marker_lines=$lines.Count;marker_keys=$keys.Count;marker_bad=0;marker_duplicate=0;marker_ticks=$markerItem.LastWriteTimeUtc.Ticks;strict_latest_margin_ticks=[long]($markerItem.LastWriteTimeUtc.Ticks-$max);at_or_after_excluding_marker=$at;postmarker_writes=0;snapshot=$snap;ads=$ads;json_files=$json.Count;json_parse_fail=$jsonFail;csv_files=$csv.Count;csv_parse_fail=$csvFail;xml_parse_fail=$xmlFail;cache_count=$cache;pyc_count=$pyc;reparse_count=$reparse;manifest_sha256=Sha $manifest;seal_audit_sha256=Sha $audit;controller_result_sha256=Sha $controllerResult;status='STATIC_ONLY_NOT_RENDERED_NOT_PASS'}
[IO.File]::WriteAllText($result,($out|ConvertTo-Json -Depth 8),$utf8);$i=Get-Item -LiteralPath $result;[IO.File]::SetAttributes($i.FullName,($i.Attributes-bor[IO.FileAttributes]::ReadOnly));$out|ConvertTo-Json -Depth 8
