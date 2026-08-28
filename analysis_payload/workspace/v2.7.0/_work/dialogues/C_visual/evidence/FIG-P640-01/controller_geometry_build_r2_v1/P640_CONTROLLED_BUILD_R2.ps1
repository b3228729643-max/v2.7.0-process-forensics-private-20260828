param(
  [Parameter(Mandatory = $true)]
  [string]$AuthorizationToken
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$expectedToken = 'P640_R2_BUILD_SLOT_GRANTED'
$source = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_C_visual\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C04\fig_v5_c04_mixing_rho_comparison.tex'
$wrapper = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_C_visual\src\讲义源码\合并总册\v260_FIG-P640-01_standalone.tex'
$engine = 'D:\texlive\2026\bin\windows\lualatex.exe'
$kpsewhich = 'D:\texlive\2026\bin\windows\kpsewhich.exe'
$buildRoot = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P640-01\sa2_geometry_direct_build_r2'
$outputDir = Join-Path $buildRoot '01_build'
$cacheRoot = 'C:\Users\ASUS\AppData\Local\Temp\codex_v270_p640_geometry_r2'
$texmfVar = Join-Path $cacheRoot 'texmf-var'
$texmfCache = Join-Path $cacheRoot 'texmf-cache'
$texmfConfig = Join-Path $cacheRoot 'texmf-config'
$wrapperDir = Split-Path -Parent $wrapper
$expectedSourceSha = '044431D3E6B2ABAFE786EB151B7F4B01585F8E83F158EADEF736E005F6161F38'
$expectedWrapperSha = '495C5D0D36BE60B82BDB44AF4E352960680416785F991F8F0A15F0E495ABDC5C'
$expectedEngineSha = 'CC944A1DB010B47FCF5CCB5D1B184CBA208FE7FEA9F18BEC414940E6FD3E24A6'
$expectedKpseSha = '90E5BD3477FB1AF7F9D1F8C858DE31137AAB4DF57B29928BA82B7D00B2DD85DB'

function Get-Sha256([string]$Path) {
  return (Get-FileHash -Algorithm SHA256 -LiteralPath $Path).Hash
}

function Write-JsonAtomic([string]$Path, [object]$Value) {
  $temporary = "$Path.tmp"
  $Value | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $temporary -Encoding utf8NoBOM
  Move-Item -LiteralPath $temporary -Destination $Path -Force
}

function New-ChildStartInfo([string]$FileName) {
  $psi = [Diagnostics.ProcessStartInfo]::new()
  $psi.FileName = $FileName
  $psi.WorkingDirectory = $wrapperDir
  $psi.UseShellExecute = $false
  $psi.CreateNoWindow = $true
  $psi.RedirectStandardOutput = $true
  $psi.RedirectStandardError = $true
  $psi.Environment['TEXMFOUTPUT'] = $cacheRoot
  $psi.Environment['TEXMFVAR'] = $texmfVar
  $psi.Environment['TEXMFCACHE'] = $texmfCache
  $psi.Environment['TEXMFCONFIG'] = $texmfConfig
  return $psi
}

function Invoke-KpseValue([string]$Variable) {
  $psi = New-ChildStartInfo $kpsewhich
  $psi.ArgumentList.Add("--var-value=$Variable")
  $process = [Diagnostics.Process]::Start($psi)
  $stdoutTask = $process.StandardOutput.ReadToEndAsync()
  $stderrTask = $process.StandardError.ReadToEndAsync()
  $process.WaitForExit()
  return [ordered]@{
    variable = $Variable
    exit_code = $process.ExitCode
    stdout = $stdoutTask.GetAwaiter().GetResult().Trim()
    stderr = $stderrTask.GetAwaiter().GetResult()
  }
}

if ($AuthorizationToken -cne $expectedToken) { throw 'Authorization token mismatch.' }
if (Test-Path -LiteralPath $buildRoot) { throw 'Fresh build root already exists.' }
if (Test-Path -LiteralPath $cacheRoot) { throw 'Fresh cache root already exists.' }

$identity = [ordered]@{
  authorization_token = $expectedToken
  source = [ordered]@{ path=$source; bytes=(Get-Item -LiteralPath $source).Length; sha256=(Get-Sha256 $source) }
  wrapper = [ordered]@{ path=$wrapper; bytes=(Get-Item -LiteralPath $wrapper).Length; sha256=(Get-Sha256 $wrapper) }
  engine = [ordered]@{ path=$engine; bytes=(Get-Item -LiteralPath $engine).Length; sha256=(Get-Sha256 $engine) }
  kpsewhich = [ordered]@{ path=$kpsewhich; bytes=(Get-Item -LiteralPath $kpsewhich).Length; sha256=(Get-Sha256 $kpsewhich) }
  invocation_ordinal = 1
  invocation_limit = 1
  retry_forbidden = $true
  latexmk_forbidden = $true
}
if ($identity.source.sha256 -cne $expectedSourceSha -or
    $identity.wrapper.sha256 -cne $expectedWrapperSha -or
    $identity.engine.sha256 -cne $expectedEngineSha -or
    $identity.kpsewhich.sha256 -cne $expectedKpseSha) {
  throw 'Frozen identity gate failed.'
}

New-Item -ItemType Directory -Path $outputDir -Force | Out-Null
New-Item -ItemType Directory -Path $texmfVar,$texmfCache,$texmfConfig -Force | Out-Null
Write-JsonAtomic (Join-Path $buildRoot 'SOURCE_WRAPPER_ENGINE_IDENTITY.json') $identity

$preProcesses = @(Get-Process -ErrorAction SilentlyContinue | Where-Object { $_.ProcessName -in @('latexmk','lualatex','luatex','luahbtex') })
Write-JsonAtomic (Join-Path $buildRoot 'PREBUILD_PROCESS_GATE.json') ([ordered]@{
  checked_utc = [DateTime]::UtcNow.ToString('o')
  process_count = $preProcesses.Count
  processes = @($preProcesses | ForEach-Object { [ordered]@{ name=$_.ProcessName; pid=$_.Id } })
  pass = ($preProcesses.Count -eq 0)
})
if ($preProcesses.Count -ne 0) { throw 'Prebuild TeX process gate failed.' }

$probes = @()
foreach ($directory in @($cacheRoot,$texmfVar,$texmfCache,$texmfConfig)) {
  $probePath = Join-Path $directory 'p640-r2-write-probe.tmp'
  'probe' | Set-Content -LiteralPath $probePath -Encoding ascii
  $readback = Get-Content -LiteralPath $probePath -Raw
  Remove-Item -LiteralPath $probePath -Force
  $probes += [ordered]@{ path=$directory; write_read_delete_pass=($readback.Trim() -ceq 'probe') }
}
Write-JsonAtomic (Join-Path $buildRoot 'CACHE_WRITE_PROBE.json') ([ordered]@{
  results = $probes
  pass = (-not ($probes.write_read_delete_pass -contains $false))
})
if ($probes.write_read_delete_pass -contains $false) { throw 'Cache write probe failed.' }

$kpseResults = @(
  Invoke-KpseValue 'openout_any'
  Invoke-KpseValue 'TEXMFOUTPUT'
  Invoke-KpseValue 'TEXMFVAR'
  Invoke-KpseValue 'TEXMFCACHE'
  Invoke-KpseValue 'TEXMFCONFIG'
)
$expectedValues = @{
  openout_any = 'p'
  TEXMFOUTPUT = $cacheRoot
  TEXMFVAR = $texmfVar
  TEXMFCACHE = $texmfCache
  TEXMFCONFIG = $texmfConfig
}
$kpseFailures = @()
foreach ($item in $kpseResults) {
  $actual = ($item.stdout -replace '\\','/').TrimEnd('/')
  $expected = ($expectedValues[$item.variable] -replace '\\','/').TrimEnd('/')
  $nonAscii = ([regex]::Matches($item.stdout, '[^\x00-\x7F]')).Count
  if ($item.exit_code -ne 0 -or $nonAscii -ne 0 -or $actual -cne $expected) { $kpseFailures += $item.variable }
}
Write-JsonAtomic (Join-Path $buildRoot 'PREBUILD_KPSE_GATE.json') ([ordered]@{
  results = $kpseResults
  failure_count = $kpseFailures.Count
  failures = $kpseFailures
  pass = ($kpseFailures.Count -eq 0)
})
if ($kpseFailures.Count -ne 0) { throw 'kpsewhich environment gate failed.' }

$psi = New-ChildStartInfo $engine
$psi.ArgumentList.Add('--interaction=nonstopmode')
$psi.ArgumentList.Add('--halt-on-error')
$psi.ArgumentList.Add('--file-line-error')
$psi.ArgumentList.Add("--output-directory=$outputDir")
$psi.ArgumentList.Add((Split-Path -Leaf $wrapper))

$startedUtc = [DateTime]::UtcNow
$started = $false
$naturalExit = $false
$pidValue = $null
$exitCode = $null
$startException = $null
$runtimeException = $null
$outputPersistenceException = $null
$pdfIdentityException = $null
$controllerException = $null
$stdout = ''
$stderr = ''
$process = $null

try {
  try {
    $process = [Diagnostics.Process]::Start($psi)
    $started = $true
    $pidValue = $process.Id
    Write-JsonAtomic (Join-Path $buildRoot 'DIRECT_INVOCATION_START.json') ([ordered]@{
      pid = $pidValue
      started_utc = $startedUtc.ToString('o')
      source = $identity.source
      wrapper = $identity.wrapper
      engine = $identity.engine
      working_directory = $wrapperDir
      environment = [ordered]@{ TEXMFOUTPUT=$cacheRoot; TEXMFVAR=$texmfVar; TEXMFCACHE=$texmfCache; TEXMFCONFIG=$texmfConfig }
      arguments = @($psi.ArgumentList)
      invocation_ordinal = 1
      invocation_limit = 1
    })
  } catch {
    $startException = $_.Exception.ToString()
  }
  if ($started) {
    try {
      $stdoutTask = $process.StandardOutput.ReadToEndAsync()
      $stderrTask = $process.StandardError.ReadToEndAsync()
      $process.WaitForExit()
      $stdout = $stdoutTask.GetAwaiter().GetResult()
      $stderr = $stderrTask.GetAwaiter().GetResult()
      $exitCode = $process.ExitCode
      $naturalExit = $true
    } catch {
      $runtimeException = $_.Exception.ToString()
    }
  }
} catch {
  $controllerException = $_.Exception.ToString()
}

$stdoutPath = Join-Path $outputDir 'lualatex.stdout.txt'
$stderrPath = Join-Path $outputDir 'lualatex.stderr.txt'
try {
  $stdout | Set-Content -LiteralPath $stdoutPath -Encoding utf8NoBOM
  $stderr | Set-Content -LiteralPath $stderrPath -Encoding utf8NoBOM
} catch {
  $outputPersistenceException = $_.Exception.ToString()
}

$pdfFiles = @(Get-ChildItem -LiteralPath $outputDir -Filter '*.pdf' -File -ErrorAction SilentlyContinue)
$pdfIdentity = $null
try {
  if ($pdfFiles.Count -eq 1) {
    $pdfIdentity = [ordered]@{ path=$pdfFiles[0].FullName; bytes=$pdfFiles[0].Length; sha256=(Get-Sha256 $pdfFiles[0].FullName) }
  }
} catch {
  $pdfIdentityException = $_.Exception.ToString()
}

$stdoutIdentity = $null
$stderrIdentity = $null
if (Test-Path -LiteralPath $stdoutPath) { $stdoutIdentity = [ordered]@{ path=$stdoutPath; bytes=(Get-Item -LiteralPath $stdoutPath).Length; sha256=(Get-Sha256 $stdoutPath) } }
if (Test-Path -LiteralPath $stderrPath) { $stderrIdentity = [ordered]@{ path=$stderrPath; bytes=(Get-Item -LiteralPath $stderrPath).Length; sha256=(Get-Sha256 $stderrPath) } }
$postProcesses = @(Get-Process -ErrorAction SilentlyContinue | Where-Object { $_.ProcessName -in @('latexmk','lualatex','luatex','luahbtex') })
$finishedUtc = [DateTime]::UtcNow
$exceptionsEmpty = [string]::IsNullOrEmpty($startException) -and [string]::IsNullOrEmpty($runtimeException) -and [string]::IsNullOrEmpty($outputPersistenceException) -and [string]::IsNullOrEmpty($pdfIdentityException) -and [string]::IsNullOrEmpty($controllerException)
$success = (1 -eq 1 -and $started -and $naturalExit -and $exitCode -eq 0 -and $pdfFiles.Count -eq 1 -and $null -ne $pdfIdentity -and $pdfIdentity.bytes -gt 0 -and $postProcesses.Count -eq 0 -and $exceptionsEmpty -and $null -ne $stdoutIdentity -and $null -ne $stderrIdentity)

Write-JsonAtomic (Join-Path $buildRoot 'DIRECT_INVOCATION_RESULT.json') ([ordered]@{
  invocation_count = 1
  retry_count = 0
  started = $started
  natural_exit = $naturalExit
  pid = $pidValue
  started_utc = $startedUtc.ToString('o')
  finished_utc = $finishedUtc.ToString('o')
  duration_seconds = ($finishedUtc - $startedUtc).TotalSeconds
  exit_code = $exitCode
  pdf_count = $pdfFiles.Count
  pdf = $pdfIdentity
  stdout = $stdoutIdentity
  stderr = $stderrIdentity
  post_tex_process_count = $postProcesses.Count
  post_tex_processes = @($postProcesses | ForEach-Object { [ordered]@{ name=$_.ProcessName; pid=$_.Id } })
  start_record_exception = $startException
  runtime_exception = $runtimeException
  output_persistence_exception = $outputPersistenceException
  pdf_identity_exception = $pdfIdentityException
  controller_exception = $controllerException
  success_hard_gate = $success
})

if (-not $success) { throw 'Controlled direct LuaLaTeX build failed; no retry is permitted.' }
