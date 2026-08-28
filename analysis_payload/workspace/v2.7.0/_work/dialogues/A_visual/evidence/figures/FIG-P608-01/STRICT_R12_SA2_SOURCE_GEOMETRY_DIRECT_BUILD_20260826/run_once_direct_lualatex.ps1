$ErrorActionPreference = 'Stop'

$root = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P608-01\STRICT_R12_SA2_SOURCE_GEOMETRY_DIRECT_BUILD_20260826'
$source = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_A_visual\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C03\fig_v5_c03_trace_running_mean.tex'
$wrapper = Join-Path $root 'local_wrapper_r12_worktree.tex'
$engine = 'D:\texlive\2026\bin\windows\lualatex.exe'
$workingDirectory = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_A_visual\src\讲义源码\合并总册'
$build = Join-Path $root 'build'
$cache = Join-Path $root 'texcache'
$stdoutPath = Join-Path $root 'lualatex.stdout.txt'
$stderrPath = Join-Path $root 'lualatex.stderr.txt'
$startPath = Join-Path $root 'BUILD_START.json'
$resultPath = Join-Path $root 'BUILD_RESULT.json'
$expectedSourceSha = '49A683AEEC94AFD71AE33E95D4DF51BA3CC722F10B432B065FDBD2E45898635E'

if ((Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash -ne $expectedSourceSha) {
  throw 'Source SHA mismatch before the only invocation.'
}
$texBefore = @(Get-Process -ErrorAction SilentlyContinue | Where-Object {
  $_.ProcessName -match '^(latexmk|lualatex|luatex|luahbtex)$'
})
if ($texBefore.Count -ne 0) {
  throw 'TeX process already active before the only invocation.'
}
New-Item -ItemType Directory -Path $build,$cache -Force | Out-Null

$sourceBeforeSha = (Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash
$wrapperBeforeSha = (Get-FileHash -LiteralPath $wrapper -Algorithm SHA256).Hash
$engineSha = (Get-FileHash -LiteralPath $engine -Algorithm SHA256).Hash
$startedAt = [DateTime]::UtcNow.ToString('o')

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
  uid = 'FIG-P608-01'
  round = 'STRICT_R12_SA2_SOURCE_GEOMETRY_DIRECT_BUILD_20260826'
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
  pid = $pidValue
  started_at_utc = $startedAt
  tex_processes_before = 0
  latexmk_used = $false
}
$start | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $startPath -Encoding utf8NoBOM

$stdoutTask = $process.StandardOutput.ReadToEndAsync()
$stderrTask = $process.StandardError.ReadToEndAsync()
$process.WaitForExit()
$exitCode = $process.ExitCode
$stdoutTask.GetAwaiter().GetResult() | Set-Content -LiteralPath $stdoutPath -Encoding utf8NoBOM
$stderrTask.GetAwaiter().GetResult() | Set-Content -LiteralPath $stderrPath -Encoding utf8NoBOM
$endedAt = [DateTime]::UtcNow.ToString('o')

$pdfs = @(Get-ChildItem -LiteralPath $build -Filter '*.pdf' -File -ErrorAction SilentlyContinue)
$pdfIdentity = @()
foreach ($pdf in $pdfs) {
  $pdfIdentity += [ordered]@{
    path = $pdf.FullName
    bytes = $pdf.Length
    sha256 = (Get-FileHash -LiteralPath $pdf.FullName -Algorithm SHA256).Hash
    last_write_time_utc = $pdf.LastWriteTimeUtc.ToString('o')
  }
}
$sourceAfterSha = (Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash
$wrapperAfterSha = (Get-FileHash -LiteralPath $wrapper -Algorithm SHA256).Hash
$texAfter = @(Get-Process -ErrorAction SilentlyContinue | Where-Object {
  $_.ProcessName -match '^(latexmk|lualatex|luatex|luahbtex)$'
})
$result = [ordered]@{
  uid = 'FIG-P608-01'
  round = 'STRICT_R12_SA2_SOURCE_GEOMETRY_DIRECT_BUILD_20260826'
  invocation_count = 1
  pid = $pidValue
  exit_code = $exitCode
  natural_exit = $true
  started_at_utc = $startedAt
  ended_at_utc = $endedAt
  source_before_sha256 = $sourceBeforeSha
  source_after_sha256 = $sourceAfterSha
  wrapper_before_sha256 = $wrapperBeforeSha
  wrapper_after_sha256 = $wrapperAfterSha
  pdf_count = $pdfs.Count
  pdfs = $pdfIdentity
  tex_processes_after = $texAfter.Count
  latexmk_used = $false
  retry_count = 0
}
$result | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $resultPath -Encoding utf8NoBOM
exit $exitCode
