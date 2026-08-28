$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$root = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P067-01\STRICT_R3_SA2_TICK_LABEL_PATCH_R111_DIRECT_BUILD_20260827'
$source = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_A_visual\src\绘图源码\第01册_数学基础与统计学习基本理论\V1-C04\fig_v1_c04_cdf.tex'
$wrapper = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_A_visual\src\讲义源码\合并总册\v260_FIG-P067-01_standalone.tex'
$engine = 'D:\texlive\2026\bin\windows\lualatex.exe'
$workingDirectory = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_A_visual\src\讲义源码\合并总册'
$build = Join-Path $root 'build'
$cache = Join-Path $root 'texcache'
$stdoutPath = Join-Path $root 'lualatex.stdout.txt'
$stderrPath = Join-Path $root 'lualatex.stderr.txt'
$startPath = Join-Path $root 'BUILD_START.json'
$resultPath = Join-Path $root 'BUILD_RESULT.json'
$expectedSourceSha = 'C570597B72EEA4610380359A84EA078B24C810EC89039215BC9B42AB0F8AFFA0'
$expectedWrapperSha = 'ADDF75D1C82DAB9AB4D5A76E6B241DA1CEB7AED9C2E536106ECFD7710B2D14BF'
$expectedEngineSha = 'CC944A1DB010B47FCF5CCB5D1B184CBA208FE7FEA9F18BEC414940E6FD3E24A6'

$controllerPath = $PSCommandPath
$controllerSha = (Get-FileHash -LiteralPath $controllerPath -Algorithm SHA256).Hash
if ([IO.File]::Exists($root) -or [IO.Directory]::Exists($root)) { throw 'Authorized R3 root must be absent before the only controller invocation.' }

$sourceBefore = Get-Item -LiteralPath $source
$wrapperBefore = Get-Item -LiteralPath $wrapper
$engineInfo = Get-Item -LiteralPath $engine
$sourceBeforeSha = (Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash
$wrapperBeforeSha = (Get-FileHash -LiteralPath $wrapper -Algorithm SHA256).Hash
$engineSha = (Get-FileHash -LiteralPath $engine -Algorithm SHA256).Hash
if ($sourceBeforeSha -ne $expectedSourceSha) { throw 'Source SHA mismatch before the only typeset invocation.' }
if ($wrapperBeforeSha -ne $expectedWrapperSha) { throw 'Wrapper SHA mismatch before the only typeset invocation.' }
if ($engineSha -ne $expectedEngineSha) { throw 'Engine SHA mismatch before the only typeset invocation.' }
$texBefore = @(Get-Process -ErrorAction SilentlyContinue | Where-Object {
  $_.ProcessName -match '^(latexmk|lualatex|luatex|luahbtex)$'
})
if ($texBefore.Count -ne 0) { throw 'TeX process already active before the only typeset invocation.' }

New-Item -ItemType Directory -Path $root | Out-Null
New-Item -ItemType Directory -Path $build,$cache | Out-Null
$started = [DateTime]::UtcNow

$psi = [Diagnostics.ProcessStartInfo]::new()
$psi.FileName = $engine
$psi.WorkingDirectory = $workingDirectory
$psi.UseShellExecute = $false
$psi.CreateNoWindow = $true
$psi.RedirectStandardOutput = $true
$psi.RedirectStandardError = $true
$psi.StandardOutputEncoding = [Text.UTF8Encoding]::new($false)
$psi.StandardErrorEncoding = [Text.UTF8Encoding]::new($false)
$psi.ArgumentList.Add('-interaction=nonstopmode')
$psi.ArgumentList.Add('-halt-on-error')
$psi.ArgumentList.Add('-file-line-error')
$psi.ArgumentList.Add('-synctex=0')
$psi.ArgumentList.Add("-output-directory=$build")
$psi.ArgumentList.Add($wrapper)
$psi.Environment['TEXMFVAR'] = $cache
$psi.Environment['TEXMFCACHE'] = $cache
$psi.Environment['TEXMFCONFIG'] = $cache

$process = [Diagnostics.Process]::new()
$process.StartInfo = $psi
if (-not $process.Start()) { throw 'The only direct LuaLaTeX typeset process did not start.' }
$childPid = $process.Id
$start = [ordered]@{
  uid = 'FIG-P067-01'
  handoff_id = 'A-R111-P067-SA2-DIRECT-BUILD-R3-20260827'
  round = 'STRICT_R3_SA2_TICK_LABEL_PATCH_R111_DIRECT_BUILD_20260827'
  controller_pid = $PID
  controller_path = $controllerPath
  controller_sha256 = $controllerSha
  child_pid = $childPid
  engine_version_probe_count = 1
  typeset_invocation_ordinal = 1
  typeset_invocation_count = 1
  retry_count = 0
  latexmk_count = 0
  engine = $engine
  engine_bytes = $engineInfo.Length
  engine_sha256 = $engineSha
  wrapper = $wrapper
  wrapper_bytes = $wrapperBefore.Length
  wrapper_sha256 = $wrapperBeforeSha
  source = $source
  source_bytes = $sourceBefore.Length
  source_sha256 = $sourceBeforeSha
  working_directory = $workingDirectory
  output_directory = $build
  texmfvar = $psi.Environment['TEXMFVAR']
  texmfcache = $psi.Environment['TEXMFCACHE']
  texmfconfig = $psi.Environment['TEXMFCONFIG']
  started_at_utc = $started.ToString('o')
  tex_processes_before = 0
}
$start | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $startPath -Encoding utf8NoBOM

$stdoutTask = $process.StandardOutput.ReadToEndAsync()
$stderrTask = $process.StandardError.ReadToEndAsync()
$process.WaitForExit()
$childExitCode = $process.ExitCode
$stdoutTask.GetAwaiter().GetResult() | Set-Content -LiteralPath $stdoutPath -Encoding utf8NoBOM
$stderrTask.GetAwaiter().GetResult() | Set-Content -LiteralPath $stderrPath -Encoding utf8NoBOM
$ended = [DateTime]::UtcNow

$pdfs = @(Get-ChildItem -LiteralPath $build -Filter '*.pdf' -File -ErrorAction SilentlyContinue)
$pdfIdentity = @()
foreach ($pdf in $pdfs) {
  $pdfIdentity += [ordered]@{
    path = $pdf.FullName
    bytes = $pdf.Length
    sha256 = (Get-FileHash -LiteralPath $pdf.FullName -Algorithm SHA256).Hash
    last_write_time_utc = $pdf.LastWriteTimeUtc.ToString('o')
    last_write_time_utc_ticks = $pdf.LastWriteTimeUtc.Ticks.ToString()
  }
}
$sourceAfter = Get-Item -LiteralPath $source
$wrapperAfter = Get-Item -LiteralPath $wrapper
$sourceAfterSha = (Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash
$wrapperAfterSha = (Get-FileHash -LiteralPath $wrapper -Algorithm SHA256).Hash
$texAfter = @(Get-Process -ErrorAction SilentlyContinue | Where-Object {
  $_.ProcessName -match '^(latexmk|lualatex|luatex|luahbtex)$'
})
$identityStable = ($sourceAfterSha -eq $sourceBeforeSha) -and ($wrapperAfterSha -eq $wrapperBeforeSha) -and ($sourceAfter.Length -eq $sourceBefore.Length) -and ($wrapperAfter.Length -eq $wrapperBefore.Length)
$hardGatePass = ($childExitCode -eq 0) -and ($pdfs.Count -eq 1) -and $identityStable -and ($texAfter.Count -eq 0)
$controllerExitCode = if ($hardGatePass) { 0 } elseif ($childExitCode -ne 0) { $childExitCode } else { 97 }
$result = [ordered]@{
  uid = 'FIG-P067-01'
  handoff_id = 'A-R111-P067-SA2-DIRECT-BUILD-R3-20260827'
  round = 'STRICT_R3_SA2_TICK_LABEL_PATCH_R111_DIRECT_BUILD_20260827'
  controller_pid = $PID
  controller_path = $controllerPath
  controller_sha256 = $controllerSha
  child_pid = $childPid
  engine_version_probe_count = 1
  typeset_invocation_count = 1
  retry_count = 0
  latexmk_count = 0
  child_exit_code = $childExitCode
  controller_exit_code = $controllerExitCode
  natural_exit = $true
  interrupted = $false
  started_at_utc = $started.ToString('o')
  ended_at_utc = $ended.ToString('o')
  duration_seconds = [Math]::Round(($ended - $started).TotalSeconds, 3)
  source_before_bytes = $sourceBefore.Length
  source_after_bytes = $sourceAfter.Length
  source_before_sha256 = $sourceBeforeSha
  source_after_sha256 = $sourceAfterSha
  wrapper_before_bytes = $wrapperBefore.Length
  wrapper_after_bytes = $wrapperAfter.Length
  wrapper_before_sha256 = $wrapperBeforeSha
  wrapper_after_sha256 = $wrapperAfterSha
  identity_stable = $identityStable
  pdf_count = $pdfs.Count
  pdfs = $pdfIdentity
  tex_processes_after = $texAfter.Count
  hard_gate_pass = $hardGatePass
}
$result | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $resultPath -Encoding utf8NoBOM
exit $controllerExitCode
