Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$handoffId = 'A-R113-P067-SA2-DIRECT-BUILD-R11-20260827'
$root = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P067-01\STRICT_R11_SA2_P4_COORDINATE_DIRECT_BUILD_R113_20260827'
$source = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_A_visual\src\绘图源码\第01册_数学基础与统计学习基本理论\V1-C04\fig_v1_c04_cdf.tex'
$wrapper = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_A_visual\src\讲义源码\合并总册\v260_FIG-P067-01_standalone.tex'
$engine = 'D:\texlive\2026\bin\windows\lualatex.exe'
$expectedSourceBytes = 4014L
$expectedSourceSha = '11BF3681D069F6A38C479B3074F39F93E8EB6144FF155AC543508E3589A51144'
$expectedWrapperBytes = 388L
$expectedWrapperSha = 'ADDF75D1C82DAB9AB4D5A76E6B241DA1CEB7AED9C2E536106ECFD7710B2D14BF'
$expectedEngineBytes = 6656L
$expectedEngineSha = 'CC944A1DB010B47FCF5CCB5D1B184CBA208FE7FEA9F18BEC414940E6FD3E24A6'

function Get-Identity([string]$Path) {
    $item = Get-Item -LiteralPath $Path
    return [ordered]@{
        path = $item.FullName
        bytes = [int64]$item.Length
        sha256 = (Get-FileHash -LiteralPath $item.FullName -Algorithm SHA256).Hash
    }
}

function Assert-Identity($Identity, [int64]$ExpectedBytes, [string]$ExpectedSha, [string]$Label) {
    if ($Identity.bytes -ne $ExpectedBytes) {
        throw "$Label bytes mismatch: $($Identity.bytes) != $ExpectedBytes"
    }
    if ($Identity.sha256 -ne $ExpectedSha) {
        throw "$Label SHA mismatch: $($Identity.sha256) != $ExpectedSha"
    }
}

if ([IO.File]::Exists($root) -or [IO.Directory]::Exists($root)) {
    throw "R11 build root must be absent before the sole controller invocation: $root"
}

$controllerBefore = Get-Identity -Path $PSCommandPath
$sourceBefore = Get-Identity -Path $source
$wrapperBefore = Get-Identity -Path $wrapper
$engineIdentity = Get-Identity -Path $engine
Assert-Identity $sourceBefore $expectedSourceBytes $expectedSourceSha 'source before'
Assert-Identity $wrapperBefore $expectedWrapperBytes $expectedWrapperSha 'wrapper before'
Assert-Identity $engineIdentity $expectedEngineBytes $expectedEngineSha 'engine'

$null = [IO.Directory]::CreateDirectory($root)
$build = Join-Path $root 'build'
$texcache = Join-Path $root 'texcache'
$null = [IO.Directory]::CreateDirectory($build)
$null = [IO.Directory]::CreateDirectory($texcache)

$env:TEXMFVAR = $texcache
$env:TEXMFCACHE = $texcache
$env:TEXMFCONFIG = $texcache
$env:LC_ALL = 'C.UTF-8'
$env:LANG = 'C.UTF-8'
[Console]::InputEncoding = [Text.UTF8Encoding]::new($false)
[Console]::OutputEncoding = [Text.UTF8Encoding]::new($false)

$stdoutPath = Join-Path $root 'lualatex.stdout.txt'
$stderrPath = Join-Path $root 'lualatex.stderr.txt'
$startPath = Join-Path $root 'START.json'
$resultPath = Join-Path $root 'RESULT.json'
$workingDirectory = Split-Path -LiteralPath $wrapper -Parent
$arguments = @(
    '-interaction=nonstopmode',
    '-halt-on-error',
    '-file-line-error',
    '-synctex=0',
    "-output-directory=$build",
    $wrapper
)

$controllerStartUtc = [DateTime]::UtcNow
$childStartUtc = [DateTime]::UtcNow
$process = Start-Process -FilePath $engine -ArgumentList $arguments -WorkingDirectory $workingDirectory -RedirectStandardOutput $stdoutPath -RedirectStandardError $stderrPath -WindowStyle Hidden -PassThru
$startRecord = [ordered]@{
    handoff_id = $handoffId
    controller_pid = $PID
    child_pid = $process.Id
    controller_start_utc = $controllerStartUtc.ToString('O')
    child_start_utc = $childStartUtc.ToString('O')
    typeset_invocation_count = 1
    retry_count = 0
    latexmk_count = 0
    version_probe_count = 0
    engine = $engineIdentity
    source_before = $sourceBefore
    wrapper_before = $wrapperBefore
    controller_before = $controllerBefore
    root = $root
    build_directory = $build
    texcache = $texcache
    TEXMFVAR = $env:TEXMFVAR
    TEXMFCACHE = $env:TEXMFCACHE
    TEXMFCONFIG = $env:TEXMFCONFIG
    arguments = $arguments
}
$startRecord | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $startPath -Encoding utf8NoBOM

$process.WaitForExit()
$childEndUtc = [DateTime]::UtcNow
$childExit = $process.ExitCode
$sourceAfter = Get-Identity -Path $source
$wrapperAfter = Get-Identity -Path $wrapper
$controllerAfter = Get-Identity -Path $PSCommandPath
$pdfs = @(Get-ChildItem -LiteralPath $build -File -Filter '*.pdf')
$pdfIdentity = $null
if ($pdfs.Count -eq 1) {
    $pdfIdentity = Get-Identity -Path $pdfs[0].FullName
}

$identityUnchanged = (
    $sourceAfter.bytes -eq $sourceBefore.bytes -and
    $sourceAfter.sha256 -eq $sourceBefore.sha256 -and
    $wrapperAfter.bytes -eq $wrapperBefore.bytes -and
    $wrapperAfter.sha256 -eq $wrapperBefore.sha256 -and
    $controllerAfter.bytes -eq $controllerBefore.bytes -and
    $controllerAfter.sha256 -eq $controllerBefore.sha256
)
$controllerEndUtc = [DateTime]::UtcNow
$result = [ordered]@{
    handoff_id = $handoffId
    controller_pid = $PID
    child_pid = $process.Id
    controller_start_utc = $controllerStartUtc.ToString('O')
    child_start_utc = $childStartUtc.ToString('O')
    child_end_utc = $childEndUtc.ToString('O')
    controller_end_utc = $controllerEndUtc.ToString('O')
    duration_seconds = [Math]::Round(($childEndUtc - $childStartUtc).TotalSeconds, 6)
    child_exit_code = $childExit
    natural_exit = $true
    interrupted = $false
    typeset_invocation_count = 1
    retry_count = 0
    latexmk_count = 0
    version_probe_count = 0
    pdf_count = $pdfs.Count
    pdf = $pdfIdentity
    source_before = $sourceBefore
    source_after = $sourceAfter
    wrapper_before = $wrapperBefore
    wrapper_after = $wrapperAfter
    controller_before = $controllerBefore
    controller_after = $controllerAfter
    identity_unchanged = $identityUnchanged
    stdout_path = $stdoutPath
    stderr_path = $stderrPath
    success_gate = ($childExit -eq 0 -and $pdfs.Count -eq 1 -and $identityUnchanged)
}
$result | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $resultPath -Encoding utf8NoBOM

if (-not $result.success_gate) {
    exit 12
}
exit 0
