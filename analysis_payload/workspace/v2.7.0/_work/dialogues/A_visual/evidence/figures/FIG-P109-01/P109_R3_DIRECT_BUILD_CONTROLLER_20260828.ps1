$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$root = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P109-01\STRICT_R3_SA2_DOMAIN_LABEL_OPAQUE_PATCH_R114_DIRECT_BUILD_20260828'
$build = Join-Path $root 'build'
$texcache = Join-Path $root 'texcache'
$engine = 'D:\texlive\2026\bin\windows\lualatex.exe'
$wrapper = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_A_visual\src\讲义源码\合并总册\v260_FIG-P109-01_standalone.tex'
$source = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_A_visual\src\绘图源码\第01册_数学基础与统计学习基本理论\V1-C07\fig_v1_c07_convex_set.tex'
$expectedPdf = Join-Path $build 'v260_FIG-P109-01_standalone.pdf'
$utf8NoBom = [Text.UTF8Encoding]::new($false)

function Get-Identity([string]$Path) {
  $item = Get-Item -LiteralPath $Path
  [ordered]@{
    path=$item.FullName
    bytes=[int64]$item.Length
    sha256=(Get-FileHash -LiteralPath $item.FullName -Algorithm SHA256).Hash
  }
}

function Get-TexCounts {
  $result = [ordered]@{}
  foreach($name in @('latexmk','lualatex','luatex','luahbtex')) {
    $result[$name] = @(Get-Process -Name $name -ErrorAction SilentlyContinue).Count
  }
  $result
}

if((Test-Path -LiteralPath $root -PathType Leaf) -or (Test-Path -LiteralPath $root -PathType Container) -or (Test-Path -LiteralPath $root)){ throw 'BUILD_ROOT_NOT_ABSENT' }
$engineBefore = Get-Identity $engine
$wrapperBefore = Get-Identity $wrapper
$sourceBefore = Get-Identity $source
$controllerBefore = Get-Identity $PSCommandPath
if($engineBefore.bytes -ne 6656 -or $engineBefore.sha256 -cne 'CC944A1DB010B47FCF5CCB5D1B184CBA208FE7FEA9F18BEC414940E6FD3E24A6'){ throw 'ENGINE_IDENTITY_MISMATCH' }
if($wrapperBefore.bytes -ne 394 -or $wrapperBefore.sha256 -cne 'F2594687F563AB4A11FC5D0E08F913BD53ADFEA9CF97498DB686E5C11E8B30C7'){ throw 'WRAPPER_IDENTITY_MISMATCH' }
if($sourceBefore.bytes -ne 1922 -or $sourceBefore.sha256 -cne '887326D54E8DD97AA6D580EFA7CCD21FA371A94CACD36EB7029E80FC4D2D9355'){ throw 'SOURCE_IDENTITY_MISMATCH' }
$controllerTexCounts = Get-TexCounts
if((@($controllerTexCounts.Values | Measure-Object -Sum).Sum) -ne 0){ throw 'TEX_PROCESS_GATE_NONZERO' }

$null = New-Item -ItemType Directory -Path $root
$null = New-Item -ItemType Directory -Path $build
$null = New-Item -ItemType Directory -Path $texcache

$startUtc = [DateTime]::UtcNow
$psi = [Diagnostics.ProcessStartInfo]::new()
$psi.FileName = $engine
$psi.WorkingDirectory = [IO.Path]::GetDirectoryName($wrapper)
$psi.UseShellExecute = $false
$psi.CreateNoWindow = $true
$psi.RedirectStandardOutput = $true
$psi.RedirectStandardError = $true
foreach($argument in @('-interaction=nonstopmode','-halt-on-error','-file-line-error',"-output-directory=$build",$wrapper)) {
  $null = $psi.ArgumentList.Add($argument)
}
foreach($name in @('TEXMFVAR','TEXMFCACHE','TEXMFCONFIG','TEXMFHOME')) {
  $psi.Environment[$name] = $texcache
}

$process = [Diagnostics.Process]::new()
$process.StartInfo = $psi
if(-not $process.Start()){ throw 'LUALATEX_CHILD_START_FAILED' }
$childPid = $process.Id
$startRecord = [ordered]@{
  schema='P109_R3_DIRECT_BUILD_START_V1'
  handoff_id='A-R114-P109-SA2-DIRECT-BUILD-R3-20260828'
  controller_pid=$PID
  child_pid=$childPid
  start_utc=$startUtc.ToString('o')
  engine=$engineBefore
  wrapper_before=$wrapperBefore
  source_before=$sourceBefore
  controller_before=$controllerBefore
  working_directory=$psi.WorkingDirectory
  output_directory=$build
  texcache=$texcache
  tex_environment=[ordered]@{TEXMFVAR=$texcache;TEXMFCACHE=$texcache;TEXMFCONFIG=$texcache;TEXMFHOME=$texcache}
  controller_invocation_count=1
  typeset_invocation_count=1
  retry_count=0
  latexmk_count=0
  version_probe_count=0
}
[IO.File]::WriteAllText((Join-Path $root 'START.json'),($startRecord | ConvertTo-Json -Depth 7),$utf8NoBom)

$stdoutTask = $process.StandardOutput.ReadToEndAsync()
$stderrTask = $process.StandardError.ReadToEndAsync()
$process.WaitForExit()
$stdout = $stdoutTask.GetAwaiter().GetResult()
$stderr = $stderrTask.GetAwaiter().GetResult()
$exitCode = $process.ExitCode
$endUtc = [DateTime]::UtcNow
[IO.File]::WriteAllText((Join-Path $root 'lualatex.stdout.txt'),$stdout,$utf8NoBom)
[IO.File]::WriteAllText((Join-Path $root 'lualatex.stderr.txt'),$stderr,$utf8NoBom)

$engineAfter = Get-Identity $engine
$wrapperAfter = Get-Identity $wrapper
$sourceAfter = Get-Identity $source
$controllerAfter = Get-Identity $PSCommandPath
$pdfFiles = @(Get-ChildItem -LiteralPath $build -File -Filter '*.pdf')
$pdfIdentity = if($pdfFiles.Count -eq 1){Get-Identity $pdfFiles[0].FullName}else{$null}
$terminalTexCounts = Get-TexCounts
$result = [ordered]@{
  schema='P109_R3_DIRECT_BUILD_RESULT_V1'
  handoff_id='A-R114-P109-SA2-DIRECT-BUILD-R3-20260828'
  controller_pid=$PID
  child_pid=$childPid
  start_utc=$startUtc.ToString('o')
  end_utc=$endUtc.ToString('o')
  duration_ms=[Math]::Round(($endUtc-$startUtc).TotalMilliseconds,3)
  exit_code=$exitCode
  natural=$true
  interrupted=$false
  controller_invocation_count=1
  typeset_invocation_count=1
  retry_count=0
  latexmk_count=0
  version_probe_count=0
  pdf_count=$pdfFiles.Count
  pdf=$pdfIdentity
  expected_pdf_path=$expectedPdf
  source_before=$sourceBefore
  source_after=$sourceAfter
  wrapper_before=$wrapperBefore
  wrapper_after=$wrapperAfter
  controller_before=$controllerBefore
  controller_after=$controllerAfter
  engine_before=$engineBefore
  engine_after=$engineAfter
  terminal_tex_counts=$terminalTexCounts
}
[IO.File]::WriteAllText((Join-Path $root 'RESULT.json'),($result | ConvertTo-Json -Depth 8),$utf8NoBom)
$result | ConvertTo-Json -Depth 8

$identityStable = (
  $engineBefore.bytes -eq $engineAfter.bytes -and $engineBefore.sha256 -ceq $engineAfter.sha256 -and
  $wrapperBefore.bytes -eq $wrapperAfter.bytes -and $wrapperBefore.sha256 -ceq $wrapperAfter.sha256 -and
  $sourceBefore.bytes -eq $sourceAfter.bytes -and $sourceBefore.sha256 -ceq $sourceAfter.sha256 -and
  $controllerBefore.bytes -eq $controllerAfter.bytes -and $controllerBefore.sha256 -ceq $controllerAfter.sha256
)
$terminalSum = @($terminalTexCounts.Values | Measure-Object -Sum).Sum
if($exitCode -ne 0 -or $pdfFiles.Count -ne 1 -or -not $identityStable -or $terminalSum -ne 0){ exit 1 }
exit 0
