$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$handoff = 'A-R115-P126-SA2-DIRECT-BUILD-R5-20260828'
$root = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\STRICT_R5_SA2_LEGEND_SEGMENT_PATCH_R115_DIRECT_BUILD_20260828'
$source = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_A_visual\src\绘图源码\第01册_数学基础与统计学习基本理论\V1-C08\fig_v1_c08_coordinate.tex'
$wrapper = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_A_visual\src\讲义源码\合并总册\v260_FIG-P126-01_standalone.tex'
$engine = 'D:\texlive\2026\bin\windows\lualatex.exe'
$expectedSourceBytes = 4356L
$expectedSourceSha = '3185834A7D4DEAC1595C244DA626FF52B5308E733AFD851E8FF508037C51ED75'
$expectedWrapperBytes = 395L
$expectedWrapperSha = '706312FAED4A825F61E1517AFFFC852369845F9DAEA051B6E8FEB99335998124'
$expectedEngineBytes = 6656L
$expectedEngineSha = 'CC944A1DB010B47FCF5CCB5D1B184CBA208FE7FEA9F18BEC414940E6FD3E24A6'
$utf8NoBom = [Text.UTF8Encoding]::new($false)
$controllerStartUtc = [DateTime]::UtcNow

function Get-Sha256([string]$Path) {
  return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToUpperInvariant()
}

function Get-Identity([string]$Path) {
  $item = Get-Item -LiteralPath $Path
  return [ordered]@{ path=$Path; bytes=[long]$item.Length; sha256=Get-Sha256 $Path }
}

function Get-TexCounts {
  return [ordered]@{
    latexmk = @(Get-Process -Name 'latexmk' -ErrorAction SilentlyContinue).Count
    lualatex = @(Get-Process -Name 'lualatex' -ErrorAction SilentlyContinue).Count
    luatex = @(Get-Process -Name 'luatex' -ErrorAction SilentlyContinue).Count
    luahbtex = @(Get-Process -Name 'luahbtex' -ErrorAction SilentlyContinue).Count
  }
}

function Assert-Identity([Collections.IDictionary]$Identity, [long]$Bytes, [string]$Sha, [string]$Label) {
  if ([long]$Identity.bytes -ne $Bytes -or [string]$Identity.sha256 -cne $Sha) { throw "$Label identity mismatch" }
}

$preflightCounts = Get-TexCounts
if (($preflightCounts.latexmk + $preflightCounts.lualatex + $preflightCounts.luatex + $preflightCounts.luahbtex) -ne 0) {
  throw ('HOLD_TEX_PROCESS_COUNTS_NONZERO: ' + ($preflightCounts | ConvertTo-Json -Compress))
}
if (Test-Path -LiteralPath $root) { throw 'R5 root must be absent at controller start' }
if (-not (Test-Path -LiteralPath (Split-Path -Parent $root) -PathType Container)) { throw 'R5 parent missing' }

$controllerBefore = Get-Identity $PSCommandPath
$sourceBefore = Get-Identity $source
$wrapperBefore = Get-Identity $wrapper
$engineBefore = Get-Identity $engine
Assert-Identity $sourceBefore $expectedSourceBytes $expectedSourceSha 'source'
Assert-Identity $wrapperBefore $expectedWrapperBytes $expectedWrapperSha 'wrapper'
Assert-Identity $engineBefore $expectedEngineBytes $expectedEngineSha 'engine'

$buildDir = Join-Path $root 'build'
$texcache = Join-Path $root 'texcache'
[IO.Directory]::CreateDirectory($buildDir) | Out-Null
[IO.Directory]::CreateDirectory($texcache) | Out-Null
$buildDir = [IO.Path]::GetFullPath($buildDir)
$texcache = [IO.Path]::GetFullPath($texcache)
$startPath = Join-Path $root 'BUILD_START.json'
$resultPath = Join-Path $root 'BUILD_RESULT.json'
$stdoutPath = Join-Path $root 'lualatex.stdout.txt'
$stderrPath = Join-Path $root 'lualatex.stderr.txt'
$expectedPdf = Join-Path $buildDir 'v260_FIG-P126-01_standalone.pdf'

$startRecord = [ordered]@{
  schema = 'P126_R5_DIRECT_BUILD_START_V1'
  handoff_id = $handoff
  controller_pid = $PID
  controller_start_utc = $controllerStartUtc.ToString('o')
  root = $root
  build_dir = $buildDir
  texcache = $texcache
  preflight_tex_counts = $preflightCounts
  controller_identity = $controllerBefore
  source_identity = $sourceBefore
  wrapper_identity = $wrapperBefore
  engine_identity = $engineBefore
  controller_invocation_count = 1
  planned_typeset_invocation_count = 1
  retry_count = 0
  latexmk_count = 0
  version_probe_count = 0
  texmfvar = $texcache
  texmfcache = $texcache
  texmfconfig = $texcache
  texmfhome = $texcache
}
[IO.File]::WriteAllText($startPath, ($startRecord | ConvertTo-Json -Depth 7) + "`n", $utf8NoBom)

$psi = [Diagnostics.ProcessStartInfo]::new()
$psi.FileName = $engine
$psi.WorkingDirectory = [IO.Path]::GetDirectoryName($wrapper)
$psi.UseShellExecute = $false
$psi.CreateNoWindow = $true
$psi.RedirectStandardOutput = $true
$psi.RedirectStandardError = $true
$psi.ArgumentList.Add('--interaction=nonstopmode')
$psi.ArgumentList.Add('--halt-on-error')
$psi.ArgumentList.Add('--file-line-error')
$psi.ArgumentList.Add("--output-directory=$buildDir")
$psi.ArgumentList.Add($wrapper)
foreach ($name in @('TEXMFVAR','TEXMFCACHE','TEXMFCONFIG','TEXMFHOME')) { $psi.Environment[$name] = $texcache }

$child = [Diagnostics.Process]::new()
$child.StartInfo = $psi
$typesetInvocationCount = 0
$childStarted = $false
$childStartUtc = [DateTime]::MinValue
$childEndUtc = [DateTime]::MinValue
$childPid = 0
$childExit = -1
$stdout = ''
$stderr = ''

if (-not $child.Start()) { throw 'direct LuaLaTeX child failed to start' }
$typesetInvocationCount = 1
$childStarted = $true
$childStartUtc = [DateTime]::UtcNow
$childPid = $child.Id
$stdoutTask = $child.StandardOutput.ReadToEndAsync()
$stderrTask = $child.StandardError.ReadToEndAsync()
$child.WaitForExit()
$stdout = $stdoutTask.GetAwaiter().GetResult()
$stderr = $stderrTask.GetAwaiter().GetResult()
$childExit = $child.ExitCode
$childEndUtc = [DateTime]::UtcNow
[IO.File]::WriteAllText($stdoutPath, $stdout, $utf8NoBom)
[IO.File]::WriteAllText($stderrPath, $stderr, $utf8NoBom)

$terminalCounts = Get-TexCounts
$sourceAfter = Get-Identity $source
$wrapperAfter = Get-Identity $wrapper
$engineAfter = Get-Identity $engine
$controllerAfter = Get-Identity $PSCommandPath
$pdfFiles = @(Get-ChildItem -LiteralPath $buildDir -File -Filter '*.pdf' -Force)
$pdfIdentity = $null
if ($pdfFiles.Count -eq 1) { $pdfIdentity = Get-Identity $pdfFiles[0].FullName }
$identityUnchanged = (
  $sourceBefore.bytes -eq $sourceAfter.bytes -and $sourceBefore.sha256 -ceq $sourceAfter.sha256 -and
  $wrapperBefore.bytes -eq $wrapperAfter.bytes -and $wrapperBefore.sha256 -ceq $wrapperAfter.sha256 -and
  $engineBefore.bytes -eq $engineAfter.bytes -and $engineBefore.sha256 -ceq $engineAfter.sha256 -and
  $controllerBefore.bytes -eq $controllerAfter.bytes -and $controllerBefore.sha256 -ceq $controllerAfter.sha256
)
$terminalTotal = $terminalCounts.latexmk + $terminalCounts.lualatex + $terminalCounts.luatex + $terminalCounts.luahbtex
$success = ($childStarted -and $childExit -eq 0 -and $typesetInvocationCount -eq 1 -and $pdfFiles.Count -eq 1 -and $pdfFiles[0].FullName -ceq $expectedPdf -and $identityUnchanged -and $terminalTotal -eq 0)
$controllerEndUtc = [DateTime]::UtcNow
$result = [ordered]@{
  schema = 'P126_R5_DIRECT_BUILD_RESULT_V1'
  handoff_id = $handoff
  controller_pid = $PID
  child_pid = $childPid
  controller_start_utc = $controllerStartUtc.ToString('o')
  controller_end_utc = $controllerEndUtc.ToString('o')
  child_start_utc = $childStartUtc.ToString('o')
  child_end_utc = $childEndUtc.ToString('o')
  controller_exit_code = if ($success) { 0 } else { 1 }
  child_exit_code = $childExit
  natural_exit = $childStarted
  interrupted = $false
  controller_invocation_count = 1
  typeset_invocation_count = $typesetInvocationCount
  retry_count = 0
  latexmk_count = 0
  version_probe_count = 0
  second_invocation_count = 0
  texmfvar = $texcache
  texmfcache = $texcache
  texmfconfig = $texcache
  texmfhome = $texcache
  preflight_tex_counts = $preflightCounts
  terminal_tex_counts = $terminalCounts
  source_before = $sourceBefore
  source_after = $sourceAfter
  wrapper_before = $wrapperBefore
  wrapper_after = $wrapperAfter
  engine_before = $engineBefore
  engine_after = $engineAfter
  controller_before = $controllerBefore
  controller_after = $controllerAfter
  identities_unchanged = $identityUnchanged
  pdf_count = $pdfFiles.Count
  pdf = $pdfIdentity
  success = $success
}
[IO.File]::WriteAllText($resultPath, ($result | ConvertTo-Json -Depth 8) + "`n", $utf8NoBom)
$result | ConvertTo-Json -Depth 8
if (-not $success) { exit 1 }
