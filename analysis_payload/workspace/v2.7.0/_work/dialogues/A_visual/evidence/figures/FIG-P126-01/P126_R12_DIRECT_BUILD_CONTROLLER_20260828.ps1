Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$handoff = 'A-R115-P126-SA2-DIRECT-BUILD-R12-20260828'
$root = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\STRICT_R12_SA2_LABEL6_REPOSITION_R115_DIRECT_BUILD_20260828'
$source = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_A_visual\src\绘图源码\第01册_数学基础与统计学习基本理论\V1-C08\fig_v1_c08_coordinate.tex'
$wrapper = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_A_visual\src\讲义源码\合并总册\v260_FIG-P126-01_standalone.tex'
$engine = 'D:\texlive\2026\bin\windows\lualatex.exe'
$controller = $MyInvocation.MyCommand.Path
$utf8 = [Text.UTF8Encoding]::new($false)

function Get-Identity([string]$Path) {
  $item = Get-Item -LiteralPath $Path
  [ordered]@{path=[IO.Path]::GetFullPath($Path);bytes=[long]$item.Length;sha256=(Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash}
}
function Get-TexCounts {
  $out = [ordered]@{}
  foreach ($name in @('latexmk','lualatex','luatex','luahbtex')) { $out[$name] = @(Get-Process -Name $name -ErrorAction SilentlyContinue).Count }
  $out
}

$preflight = Get-TexCounts
if (($preflight.Values | Measure-Object -Sum).Sum -ne 0) { throw 'TeX-family preflight is not zero' }
if (Test-Path -LiteralPath $root) { throw 'R12 root preexists' }

$sourceBefore = Get-Identity $source
$wrapperBefore = Get-Identity $wrapper
$engineBefore = Get-Identity $engine
$controllerBefore = Get-Identity $controller
if ($sourceBefore.bytes -ne 4373 -or $sourceBefore.sha256 -cne '81EFC188FA5E4827CAAB034C1EA3F7F4AFE25375DEE4046CD46F3FF49B0789BD') { throw 'source identity mismatch' }
if ($wrapperBefore.bytes -ne 395 -or $wrapperBefore.sha256 -cne '706312FAED4A825F61E1517AFFFC852369845F9DAEA051B6E8FEB99335998124') { throw 'wrapper identity mismatch' }
if ($engineBefore.bytes -ne 6656 -or $engineBefore.sha256 -cne 'CC944A1DB010B47FCF5CCB5D1B184CBA208FE7FEA9F18BEC414940E6FD3E24A6') { throw 'engine identity mismatch' }

$build = Join-Path $root 'build'
$texcache = Join-Path $root 'texcache'
[IO.Directory]::CreateDirectory($build) | Out-Null
[IO.Directory]::CreateDirectory($texcache) | Out-Null
$resolvedCache = [IO.Path]::GetFullPath($texcache)
$env:TEXMFVAR = $resolvedCache
$env:TEXMFCACHE = $resolvedCache
$env:TEXMFCONFIG = $resolvedCache
$env:TEXMFHOME = $resolvedCache

$stdout = Join-Path $root 'BUILD_STDOUT.log'
$stderr = Join-Path $root 'BUILD_STDERR.log'
$startPath = Join-Path $root 'BUILD_START.json'
$resultPath = Join-Path $root 'BUILD_RESULT.json'
$startUtc = [DateTime]::UtcNow
$start = [ordered]@{
  schema='P126_R12_BUILD_START_V1';handoff_id=$handoff;controller_pid=$PID;start_utc=$startUtc.ToString('O')
  controller_invocation_count=1;direct_lualatex_invocation_count=1;retry_count=0;latexmk_count=0;version_probe_count=0;second_invocation_count=0
  root=$root;build=$build;texcache=$resolvedCache;texmfvar=$env:TEXMFVAR;texmfcache=$env:TEXMFCACHE;texmfconfig=$env:TEXMFCONFIG;texmfhome=$env:TEXMFHOME
  source_before=$sourceBefore;wrapper_before=$wrapperBefore;engine_before=$engineBefore;controller_before=$controllerBefore;preflight_tex_counts=$preflight
}
[IO.File]::WriteAllText($startPath,($start | ConvertTo-Json -Depth 7)+"`n",$utf8)

$arguments = @('-interaction=nonstopmode','-halt-on-error','-file-line-error',"-output-directory=$build",$wrapper)
$workingDirectory = [IO.Path]::GetDirectoryName($wrapper)
$child = Start-Process -FilePath $engine -ArgumentList $arguments -WorkingDirectory $workingDirectory -NoNewWindow -PassThru -Wait -RedirectStandardOutput $stdout -RedirectStandardError $stderr
$endUtc = [DateTime]::UtcNow
$terminalCounts = Get-TexCounts
$pdfs = @(Get-ChildItem -LiteralPath $build -File -Filter '*.pdf' -Force)
$sourceAfter = Get-Identity $source
$wrapperAfter = Get-Identity $wrapper
$engineAfter = Get-Identity $engine
$controllerAfter = Get-Identity $controller
$identityStable = (($sourceBefore.sha256 -ceq $sourceAfter.sha256) -and ($wrapperBefore.sha256 -ceq $wrapperAfter.sha256) -and ($engineBefore.sha256 -ceq $engineAfter.sha256) -and ($controllerBefore.sha256 -ceq $controllerAfter.sha256))
$pdfIdentity = if ($pdfs.Count -eq 1) { Get-Identity $pdfs[0].FullName } else { $null }
$success = ($child.ExitCode -eq 0 -and $pdfs.Count -eq 1 -and $identityStable -and (($terminalCounts.Values | Measure-Object -Sum).Sum -eq 0))
$result = [ordered]@{
  schema='P126_R12_BUILD_RESULT_V1';handoff_id=$handoff;controller_pid=$PID;child_pid=$child.Id
  start_utc=$startUtc.ToString('O');end_utc=$endUtc.ToString('O');duration_seconds=[math]::Round(($endUtc-$startUtc).TotalSeconds,6)
  controller_exit_code=if($success){0}else{1};child_exit_code=$child.ExitCode;natural_exit=$true;interrupted=$false
  controller_invocation_count=1;direct_lualatex_invocation_count=1;retry_count=0;latexmk_count=0;version_probe_count=0;second_invocation_count=0
  texcache=$resolvedCache;texmfvar=$env:TEXMFVAR;texmfcache=$env:TEXMFCACHE;texmfconfig=$env:TEXMFCONFIG;texmfhome=$env:TEXMFHOME
  source_before=$sourceBefore;source_after=$sourceAfter;wrapper_before=$wrapperBefore;wrapper_after=$wrapperAfter
  engine_before=$engineBefore;engine_after=$engineAfter;controller_before=$controllerBefore;controller_after=$controllerAfter
  identity_stable=$identityStable;pdf_count=$pdfs.Count;pdf=$pdfIdentity;terminal_tex_counts=$terminalCounts;success=$success
}
[IO.File]::WriteAllText($resultPath,($result | ConvertTo-Json -Depth 8)+"`n",$utf8)
$result | ConvertTo-Json -Depth 8
if (-not $success) { throw 'BUILD_FAIL_NO_CANDIDATE_OR_GATE_FAILURE' }
