$ErrorActionPreference = 'Stop'

$root = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P582-01\STRICT_R2_SA2_FONT_PATCH_R108_DIRECT_BUILD_20260826'
$source = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_A_visual\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C02\fig_v5_c02_running_mean.tex'
$wrapper = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_A_visual\src\讲义源码\合并总册\v260_FIG-P582-01_standalone.tex'
$engine = 'D:\texlive\2026\bin\windows\lualatex.exe'
$workingDirectory = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_A_visual\src\讲义源码\合并总册'
$build = Join-Path $root 'build'
$cache = Join-Path $root 'texcache'
$stdoutPath = Join-Path $root 'lualatex.stdout.txt'
$stderrPath = Join-Path $root 'lualatex.stderr.txt'
$startPath = Join-Path $root 'BUILD_START.json'
$resultPath = Join-Path $root 'BUILD_RESULT.json'
$expectedSourceSha = '4AB4E8D14252B20576F05BD1D5CB54BCB28F162B9E33EF439BD3ED6E01DBC65C'
$expectedWrapperSha = '831360DBDEFA9AF2A45ED120AF4F33E280C342D07DD1136E5FFA0E2BD592A21C'

$sourceBeforeSha = (Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash
$wrapperBeforeSha = (Get-FileHash -LiteralPath $wrapper -Algorithm SHA256).Hash
if ($sourceBeforeSha -ne $expectedSourceSha) {
  throw 'Source SHA mismatch before the only invocation.'
}
if ($wrapperBeforeSha -ne $expectedWrapperSha) {
  throw 'Wrapper SHA mismatch before the only invocation.'
}
$texBefore = @(Get-Process -ErrorAction SilentlyContinue | Where-Object {
  $_.ProcessName -match '^(latexmk|lualatex|luatex|luahbtex)$'
})
if ($texBefore.Count -ne 0) {
  throw 'TeX process already active before the only invocation.'
}
New-Item -ItemType Directory -Path $build,$cache -Force | Out-Null

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
$psi.ArgumentList.Add("-output-directory=$build")
$psi.ArgumentList.Add($wrapper)
$psi.Environment['TEXMFVAR'] = $cache
$psi.Environment['TEXMFCACHE'] = $cache
$psi.Environment['TEXMFCONFIG'] = $cache

$process = [Diagnostics.Process]::new()
$process.StartInfo = $psi
if (-not $process.Start()) { throw 'The only direct LuaLaTeX process did not start.' }
$pidValue = $process.Id
$start = [ordered]@{
  uid = 'FIG-P582-01'
  handoff_id = 'A-R108-P582-SA2-DIRECT-BUILD-20260826'
  round = 'STRICT_R2_SA2_FONT_PATCH_R108_DIRECT_BUILD_20260826'
  controller_pid = $PID
  child_pid = $pidValue
  invocation_ordinal = 1
  engine = $engine
  engine_sha256 = $engineSha
  wrapper = $wrapper
  wrapper_sha256 = $wrapperBeforeSha
  source = $source
  source_sha256 = $sourceBeforeSha
  working_directory = $workingDirectory
  output_directory = $build
  texmfvar = $cache
  texmfcache = $cache
  texmfconfig = $cache
  started_at_utc = $started.ToString('o')
  tex_processes_before = 0
  invocation_count = 1
  retry_count = 0
  latexmk_count = 0
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
$sourceAfterSha = (Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash
$wrapperAfterSha = (Get-FileHash -LiteralPath $wrapper -Algorithm SHA256).Hash
$texAfter = @(Get-Process -ErrorAction SilentlyContinue | Where-Object {
  $_.ProcessName -match '^(latexmk|lualatex|luatex|luahbtex)$'
})
$result = [ordered]@{
  uid = 'FIG-P582-01'
  handoff_id = 'A-R108-P582-SA2-DIRECT-BUILD-20260826'
  round = 'STRICT_R2_SA2_FONT_PATCH_R108_DIRECT_BUILD_20260826'
  controller_pid = $PID
  child_pid = $pidValue
  invocation_count = 1
  retry_count = 0
  latexmk_count = 0
  exit_code = $exitCode
  natural_exit = $true
  interrupted = $false
  started_at_utc = $started.ToString('o')
  ended_at_utc = $ended.ToString('o')
  duration_seconds = [Math]::Round(($ended - $started).TotalSeconds, 3)
  source_before_sha256 = $sourceBeforeSha
  source_after_sha256 = $sourceAfterSha
  wrapper_before_sha256 = $wrapperBeforeSha
  wrapper_after_sha256 = $wrapperAfterSha
  pdf_count = $pdfs.Count
  pdfs = $pdfIdentity
  tex_processes_after = $texAfter.Count
}
$result | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $resultPath -Encoding utf8NoBOM
exit $exitCode
