Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$handoff = 'A-R115-P126-SA2-DIRECT-BUILD-R16-20260828'
$root = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\STRICT_R16_SA2_FORGET_PLOT_PATCH_R115_DIRECT_BUILD_20260828'
$source = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_A_visual\src\绘图源码\第01册_数学基础与统计学习基本理论\V1-C08\fig_v1_c08_coordinate.tex'
$wrapper = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_A_visual\src\讲义源码\合并总册\v260_FIG-P126-01_standalone.tex'
$engine = 'D:\texlive\2026\bin\windows\lualatex.exe'
$controller = $PSCommandPath
$expectedSourceBytes = 4686L
$expectedSourceSha = '2887758F5CC94987BE750E1EC53B555FB88CE8F71B7260CABBE0A17DDF237405'
$expectedWrapperBytes = 395L
$expectedWrapperSha = '706312FAED4A825F61E1517AFFFC852369845F9DAEA051B6E8FEB99335998124'
$expectedEngineBytes = 6656L
$expectedEngineSha = 'CC944A1DB010B47FCF5CCB5D1B184CBA208FE7FEA9F18BEC414940E6FD3E24A6'

function Get-Identity([string]$LiteralPath) {
    $item = Get-Item -LiteralPath $LiteralPath -Force
    [ordered]@{
        path = $item.FullName
        bytes = [int64]$item.Length
        sha256 = (Get-FileHash -LiteralPath $LiteralPath -Algorithm SHA256).Hash
        last_write_time_utc_ticks = [int64]$item.LastWriteTimeUtc.Ticks
    }
}

function Assert-Identity([System.Collections.IDictionary]$Identity, [int64]$Bytes, [string]$Sha, [string]$Label) {
    if ([int64]$Identity['bytes'] -ne $Bytes) { throw "$Label bytes mismatch" }
    if ([string]$Identity['sha256'] -cne $Sha) { throw "$Label SHA256 mismatch" }
}

function Get-TexCounts {
    $result = [ordered]@{}
    foreach ($name in @('latexmk','lualatex','luatex','luahbtex')) {
        $result[$name] = @((Get-Process -Name $name -ErrorAction SilentlyContinue)).Count
    }
    $result
}

function Assert-ZeroTex([System.Collections.IDictionary]$Counts, [string]$Label) {
    foreach ($name in @('latexmk','lualatex','luatex','luahbtex')) {
        if ([int]$Counts[$name] -ne 0) { throw "$Label detected $name=$($Counts[$name])" }
    }
}

function Write-Utf8Json([string]$LiteralPath, [object]$Value) {
    $json = $Value | ConvertTo-Json -Depth 12
    [IO.File]::WriteAllText($LiteralPath, $json + [Environment]::NewLine, [Text.UTF8Encoding]::new($false))
}

if (Test-Path -LiteralPath $root) { throw 'R16 root must be absent before controller invocation' }
$sourceBefore = Get-Identity $source
$wrapperBefore = Get-Identity $wrapper
$engineBefore = Get-Identity $engine
$controllerBefore = Get-Identity $controller
Assert-Identity $sourceBefore $expectedSourceBytes $expectedSourceSha 'source'
Assert-Identity $wrapperBefore $expectedWrapperBytes $expectedWrapperSha 'wrapper'
Assert-Identity $engineBefore $expectedEngineBytes $expectedEngineSha 'engine'

$preflightCounts = Get-TexCounts
Assert-ZeroTex $preflightCounts 'preflight'

$null = New-Item -ItemType Directory -LiteralPath $root
$buildDir = Join-Path $root 'build'
$texcache = Join-Path $root 'texcache'
$null = New-Item -ItemType Directory -LiteralPath $buildDir
$null = New-Item -ItemType Directory -LiteralPath $texcache
$resolvedCache = (Get-Item -LiteralPath $texcache).FullName
$env:TEXMFVAR = $resolvedCache
$env:TEXMFCACHE = $resolvedCache
$env:TEXMFCONFIG = $resolvedCache
$env:TEXMFHOME = $resolvedCache

$controllerStartUtc = [DateTime]::UtcNow
$startRecord = [ordered]@{
    schema = 'P126_R16_DIRECT_BUILD_START_V1'
    handoff_id = $handoff
    controller_pid = $PID
    controller_start_utc = $controllerStartUtc.ToString('o')
    controller_invocation_count = 1
    direct_lualatex_invocation_count = 0
    retry_count = 0
    latexmk_count = 0
    version_probe_count = 0
    second_invocation_count = 0
    preflight_tex_counts = $preflightCounts
    texmfvar = $env:TEXMFVAR
    texmfcache = $env:TEXMFCACHE
    texmfconfig = $env:TEXMFCONFIG
    texmfhome = $env:TEXMFHOME
    source_before = $sourceBefore
    wrapper_before = $wrapperBefore
    engine_before = $engineBefore
    controller_before = $controllerBefore
}
Write-Utf8Json (Join-Path $root 'BUILD_START.json') $startRecord

$stdoutPath = Join-Path $root 'controller_stdout.txt'
$stderrPath = Join-Path $root 'controller_stderr.txt'
$workingDirectory = [IO.Path]::GetDirectoryName($wrapper)
$arguments = @(
    '-interaction=nonstopmode'
    '-halt-on-error'
    '-file-line-error'
    '-no-shell-escape'
    "-output-directory=$buildDir"
    $wrapper
)

$childStartUtc = [DateTime]::UtcNow
$child = Start-Process -FilePath $engine -ArgumentList $arguments -WorkingDirectory $workingDirectory -RedirectStandardOutput $stdoutPath -RedirectStandardError $stderrPath -PassThru
$childPid = $child.Id
$child.WaitForExit()
$childExit = $child.ExitCode
$childEndUtc = [DateTime]::UtcNow
$controllerEndUtc = [DateTime]::UtcNow

$sourceAfter = Get-Identity $source
$wrapperAfter = Get-Identity $wrapper
$engineAfter = Get-Identity $engine
$controllerAfter = Get-Identity $controller
Assert-Identity $sourceAfter $expectedSourceBytes $expectedSourceSha 'source-after'
Assert-Identity $wrapperAfter $expectedWrapperBytes $expectedWrapperSha 'wrapper-after'
Assert-Identity $engineAfter $expectedEngineBytes $expectedEngineSha 'engine-after'
if ([string]$controllerBefore['sha256'] -cne [string]$controllerAfter['sha256'] -or [int64]$controllerBefore['bytes'] -ne [int64]$controllerAfter['bytes']) { throw 'controller identity changed' }

$terminalCounts = Get-TexCounts
Assert-ZeroTex $terminalCounts 'terminal'
$pdfPath = Join-Path $buildDir 'v260_FIG-P126-01_standalone.pdf'
$pdfFiles = @(Get-ChildItem -LiteralPath $buildDir -File -Filter '*.pdf')
$pdfIdentity = $null
if ($pdfFiles.Count -eq 1 -and (Test-Path -LiteralPath $pdfPath -PathType Leaf)) {
    $pdfIdentity = Get-Identity $pdfPath
}
$success = ($childExit -eq 0 -and $pdfFiles.Count -eq 1 -and $null -ne $pdfIdentity)

$result = [ordered]@{
    schema = 'P126_R16_DIRECT_BUILD_RESULT_V1'
    handoff_id = $handoff
    success = $success
    controller_pid = $PID
    child_pid = $childPid
    controller_start_utc = $controllerStartUtc.ToString('o')
    child_start_utc = $childStartUtc.ToString('o')
    child_end_utc = $childEndUtc.ToString('o')
    controller_end_utc = $controllerEndUtc.ToString('o')
    duration_seconds = [math]::Round(($controllerEndUtc - $controllerStartUtc).TotalSeconds, 6)
    controller_exit_code = $(if ($success) { 0 } else { 1 })
    child_exit_code = $childExit
    natural = $true
    interrupted = $false
    controller_invocation_count = 1
    direct_lualatex_invocation_count = 1
    retry_count = 0
    latexmk_count = 0
    version_probe_count = 0
    second_invocation_count = 0
    pdf_count = $pdfFiles.Count
    pdf = $pdfIdentity
    source_before = $sourceBefore
    source_after = $sourceAfter
    wrapper_before = $wrapperBefore
    wrapper_after = $wrapperAfter
    engine_before = $engineBefore
    engine_after = $engineAfter
    controller_before = $controllerBefore
    controller_after = $controllerAfter
    preflight_tex_counts = $preflightCounts
    terminal_tex_counts = $terminalCounts
    texmfvar = $env:TEXMFVAR
    texmfcache = $env:TEXMFCACHE
    texmfconfig = $env:TEXMFCONFIG
    texmfhome = $env:TEXMFHOME
    stdout_path = $stdoutPath
    stderr_path = $stderrPath
}
Write-Utf8Json (Join-Path $root 'BUILD_RESULT.json') $result

if (-not $success) { exit 1 }
exit 0
