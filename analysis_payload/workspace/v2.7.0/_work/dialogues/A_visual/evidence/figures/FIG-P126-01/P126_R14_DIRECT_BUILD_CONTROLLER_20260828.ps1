Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$handoff='A-R115-P126-SA2-DIRECT-BUILD-R14-20260828'
$root='D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\STRICT_R14_SA2_DISCONNECTED_LEGEND_HANDLER_R115_DIRECT_BUILD_20260828'
$parent=[IO.Path]::GetDirectoryName($root)
$result=Join-Path $parent 'P126_R14_DIRECT_BUILD_RESULT_20260828.json'
$source='D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_A_visual\src\绘图源码\第01册_数学基础与统计学习基本理论\V1-C08\fig_v1_c08_coordinate.tex'
$wrapper='D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_A_visual\src\讲义源码\合并总册\v260_FIG-P126-01_standalone.tex'
$engine='D:\texlive\2026\bin\windows\lualatex.exe'
$utf8=[Text.UTF8Encoding]::new($false)
function Sha([string]$p){(Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash}
function Identity([string]$p){$i=Get-Item -LiteralPath $p -Force;[ordered]@{path=$i.FullName;bytes=[long]$i.Length;sha256=Sha $p}}
function Counts(){[ordered]@{latexmk=@(Get-Process -Name latexmk -ErrorAction SilentlyContinue).Count;lualatex=@(Get-Process -Name lualatex -ErrorAction SilentlyContinue).Count;luatex=@(Get-Process -Name luatex -ErrorAction SilentlyContinue).Count;luahbtex=@(Get-Process -Name luahbtex -ErrorAction SilentlyContinue).Count}}
if(Test-Path -LiteralPath $root){throw 'ROOT_PREEXISTS'}
if(Test-Path -LiteralPath $result){throw 'RESULT_PREEXISTS'}
$sourceBefore=Identity $source;$wrapperBefore=Identity $wrapper;$engineBefore=Identity $engine;$controllerBefore=Identity $PSCommandPath
if($sourceBefore.bytes-ne4626-or$sourceBefore.sha256-cne'6CBAEBE50574E541A04B2FDCC74B432C49AF2590B579C6A85721EDF536912502'){throw 'SOURCE_IDENTITY'}
if($wrapperBefore.bytes-ne395-or$wrapperBefore.sha256-cne'706312FAED4A825F61E1517AFFFC852369845F9DAEA051B6E8FEB99335998124'){throw 'WRAPPER_IDENTITY'}
if($engineBefore.bytes-ne6656-or$engineBefore.sha256-cne'CC944A1DB010B47FCF5CCB5D1B184CBA208FE7FEA9F18BEC414940E6FD3E24A6'){throw 'ENGINE_IDENTITY'}
$pre=Counts;if(($pre.Values|Measure-Object -Sum).Sum-ne0){throw 'TEX_PREFLIGHT_NONZERO'}
[void][IO.Directory]::CreateDirectory($root)
$build=Join-Path $root 'build';$cache=Join-Path $root 'texcache';[void][IO.Directory]::CreateDirectory($build);[void][IO.Directory]::CreateDirectory($cache)
$resolvedCache=[IO.Path]::GetFullPath($cache)
$env:TEXMFVAR=$resolvedCache;$env:TEXMFCACHE=$resolvedCache;$env:TEXMFCONFIG=$resolvedCache;$env:TEXMFHOME=$resolvedCache
$stdout=Join-Path $root 'controller_stdout.txt';$stderr=Join-Path $root 'controller_stderr.txt'
$args=@('-interaction=nonstopmode','-halt-on-error','-file-line-error',('-output-directory='+$build),$wrapper)
$controllerPid=$PID;$start=[DateTime]::UtcNow
$child=Start-Process -FilePath $engine -ArgumentList $args -WorkingDirectory ([IO.Path]::GetDirectoryName($wrapper)) -Wait -PassThru -WindowStyle Hidden -RedirectStandardOutput $stdout -RedirectStandardError $stderr
$end=[DateTime]::UtcNow
$sourceAfter=Identity $source;$wrapperAfter=Identity $wrapper;$engineAfter=Identity $engine;$controllerAfter=Identity $PSCommandPath
$terminal=Counts
$pdfs=@(Get-ChildItem -LiteralPath $build -File -Filter '*.pdf' -Force)
$expectedPdf=Join-Path $build 'v260_FIG-P126-01_standalone.pdf'
$success=($child.ExitCode-eq0-and$pdfs.Count-eq1-and$pdfs[0].FullName-ceq$expectedPdf-and(($terminal.Values|Measure-Object -Sum).Sum-eq0)-and$sourceBefore.sha256-ceq$sourceAfter.sha256-and$wrapperBefore.sha256-ceq$wrapperAfter.sha256-and$engineBefore.sha256-ceq$engineAfter.sha256-and$controllerBefore.sha256-ceq$controllerAfter.sha256)
$out=[ordered]@{schema='P126_R14_DIRECT_BUILD_RESULT_V1';handoff_id=$handoff;controller_pid=$controllerPid;child_pid=$child.Id;controller_invocation_count=1;direct_lualatex_invocation_count=1;retry_count=0;latexmk_count=0;version_probe_count=0;second_invocation_count=0;start_utc=$start.ToString('o');end_utc=$end.ToString('o');duration_seconds=($end-$start).TotalSeconds;child_exit_code=$child.ExitCode;controller_exit_code=if($success){0}else{1};natural_exit=$true;interrupted=$false;success=$success;root=$root;build_dir=$build;texcache=$resolvedCache;texmfvar=$env:TEXMFVAR;texmfcache=$env:TEXMFCACHE;texmfconfig=$env:TEXMFCONFIG;texmfhome=$env:TEXMFHOME;source_before=$sourceBefore;source_after=$sourceAfter;wrapper_before=$wrapperBefore;wrapper_after=$wrapperAfter;engine_before=$engineBefore;engine_after=$engineAfter;controller_before=$controllerBefore;controller_after=$controllerAfter;pdf_count=$pdfs.Count;pdf=if($pdfs.Count-eq1){Identity $pdfs[0].FullName}else{$null};terminal_tex_counts=$terminal;stdout=[ordered]@{path=$stdout;bytes=(Get-Item -LiteralPath $stdout).Length;sha256=Sha $stdout};stderr=[ordered]@{path=$stderr;bytes=(Get-Item -LiteralPath $stderr).Length;sha256=Sha $stderr}}
[IO.File]::WriteAllText($result,($out|ConvertTo-Json -Depth 8),$utf8);$ri=Get-Item -LiteralPath $result;[IO.File]::SetAttributes($ri.FullName,($ri.Attributes-bor[IO.FileAttributes]::ReadOnly));$out|ConvertTo-Json -Depth 8
if(-not$success){exit 1}
