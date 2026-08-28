$ErrorActionPreference = 'Stop'

$root = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P049-01\STRICT_R4_SA2_R3_GUIDE1_DIRECT_BUILD_R110_20260827'
$source = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_A_visual\src\绘图源码\第01册_数学基础与统计学习基本理论\V1-C03\fig_v1_c03_gradient_contour.tex'
$wrapper = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_A_visual\src\讲义源码\合并总册\v260_FIG-P049-01_standalone.tex'
$engine = 'D:\texlive\2026\bin\windows\lualatex.exe'
$workingDirectory = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_A_visual\src\讲义源码\合并总册'
$build = Join-Path $root 'build'
$cache = Join-Path $root 'texcache'
$stdoutPath = Join-Path $root 'lualatex.stdout.txt'
$stderrPath = Join-Path $root 'lualatex.stderr.txt'
$startPath = Join-Path $root 'BUILD_START.json'
$resultPath = Join-Path $root 'BUILD_RESULT.json'
$expectedSourceSha = '27BF53A0673A2D57308A836827CC8F0463BE725A11D6826E6BB94CAA91A9BB7E'
$expectedWrapperSha = 'ABF070666B10C0FA5B492FFEF2228728108A2EBE85F6077E40615C9F37B67F61'

$controllerPath = $PSCommandPath
$controllerSha = (Get-FileHash -LiteralPath $controllerPath -Algorithm SHA256).Hash
$sourceBefore = Get-Item -LiteralPath $source
$wrapperBefore = Get-Item -LiteralPath $wrapper
$sourceBeforeSha = (Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash
$wrapperBeforeSha = (Get-FileHash -LiteralPath $wrapper -Algorithm SHA256).Hash
if ($sourceBeforeSha -ne $expectedSourceSha) { throw 'Source SHA mismatch before the only invocation.' }
if ($wrapperBeforeSha -ne $expectedWrapperSha) { throw 'Wrapper SHA mismatch before the only invocation.' }
$texBefore = @(Get-Process -ErrorAction SilentlyContinue | Where-Object {
  $_.ProcessName -match '^(latexmk|lualatex|luatex|luahbtex)$'
})
if ($texBefore.Count -ne 0) { throw 'TeX process already active before the only invocation.' }
if (Test-Path -LiteralPath $build) { throw 'Build directory already exists before the only invocation.' }
if (Test-Path -LiteralPath $cache) { throw 'TeX cache already exists before the only invocation.' }
New-Item -ItemType Directory -Path $build,$cache | Out-Null

$engineInfo = Get-Item -LiteralPath $engine
$engineSha = (Get-FileHash -LiteralPath $engine -Algorithm SHA256).Hash
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
if (-not $process.Start()) { throw 'The only direct LuaLaTeX process did not start.' }
$childPid = $process.Id
$start = [ordered]@{
  uid = 'FIG-P049-01'
  handoff_id = 'A-R110-P049-SA2-DIRECT-BUILD-R4-20260827'
  round = 'STRICT_R4_SA2_R3_GUIDE1_DIRECT_BUILD_R110_20260827'
  controller_pid = $PID
  controller_path = $controllerPath
  controller_sha256 = $controllerSha
  child_pid = $childPid
  invocation_ordinal = 1
  invocation_count = 1
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
$exitCode = $process.ExitCode
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
$result = [ordered]@{
  uid = 'FIG-P049-01'
  handoff_id = 'A-R110-P049-SA2-DIRECT-BUILD-R4-20260827'
  round = 'STRICT_R4_SA2_R3_GUIDE1_DIRECT_BUILD_R110_20260827'
  controller_pid = $PID
  controller_path = $controllerPath
  controller_sha256 = $controllerSha
  child_pid = $childPid
  invocation_count = 1
  retry_count = 0
  latexmk_count = 0
  exit_code = $exitCode
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
  pdf_count = $pdfs.Count
  pdfs = $pdfIdentity
  tex_processes_after = $texAfter.Count
}
$result | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $resultPath -Encoding utf8NoBOM
exit $exitCode
