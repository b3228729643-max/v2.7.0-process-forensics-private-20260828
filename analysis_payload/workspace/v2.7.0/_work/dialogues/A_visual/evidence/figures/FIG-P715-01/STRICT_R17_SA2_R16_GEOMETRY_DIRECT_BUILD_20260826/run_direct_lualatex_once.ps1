$ErrorActionPreference = 'Stop'

[Console]::InputEncoding = [System.Text.UTF8Encoding]::new($false)
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$OutputEncoding = [System.Text.UTF8Encoding]::new($false)

$evidenceRoot = Split-Path -Parent $PSCommandPath
$cachePath = Join-Path $evidenceRoot 'texcache'
$buildPath = Join-Path $evidenceRoot 'build'
New-Item -ItemType Directory -Path $cachePath -Force | Out-Null
New-Item -ItemType Directory -Path $buildPath -Force | Out-Null
$cacheBinding = $cachePath.Replace('\', '/')
$buildBinding = $buildPath.Replace('\', '/')

$env:TEXMFVAR = $cacheBinding
$env:TEXMFCACHE = $cacheBinding
$env:TEXMFCONFIG = $cacheBinding

$engine = 'D:\texlive\2026\bin\windows\lualatex.exe'
$wrapperDirectory = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_A_visual\src\讲义源码\合并总册'
$entry = 'v260_FIG-P715-01_standalone.tex'
$sourcePath = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_A_visual\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C07\web_random_walk.tex'
$wrapperPath = Join-Path $wrapperDirectory $entry
$stdoutPath = Join-Path $buildPath 'lualatex.stdout.log'
$stderrPath = Join-Path $buildPath 'lualatex.stderr.log'
$expectedSourceSha = '900C3A8F72A7A6434101FEE9914019150D3D5F655A23FC5BF41EDB853C25EE87'
$expectedWrapperSha = '7710147ECF4D7F048ACE5C213916FCD67EA5066D0F77ED3A4278ABEADB75CBEE'
$argumentList = @(
    '-interaction=nonstopmode'
    '-halt-on-error'
    '-file-line-error'
    '-recorder'
    "-output-directory=$buildBinding"
    $entry
)

$sourceBefore = [ordered]@{
    path = $sourcePath
    bytes = (Get-Item -LiteralPath $sourcePath).Length
    sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $sourcePath).Hash
}
$wrapperBefore = [ordered]@{
    path = $wrapperPath
    bytes = (Get-Item -LiteralPath $wrapperPath).Length
    sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $wrapperPath).Hash
}
$engineIdentity = [ordered]@{
    path = $engine
    bytes = (Get-Item -LiteralPath $engine).Length
    sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $engine).Hash
}

if ($sourceBefore.sha256 -ne $expectedSourceSha) { throw "Source SHA mismatch: $($sourceBefore.sha256)" }
if ($wrapperBefore.sha256 -ne $expectedWrapperSha) { throw "Wrapper SHA mismatch: $($wrapperBefore.sha256)" }

$texBefore = @(Get-Process -Name latexmk,lualatex,luatex,luahbtex -ErrorAction SilentlyContinue)
$preflight = [ordered]@{
    round = 'STRICT_R17_SA2_R16_GEOMETRY_DIRECT_BUILD_20260826'
    controller_pid = $PID
    controller_executable = (Get-Process -Id $PID).Path
    invocation_limit = 1
    automatic_retry = $false
    source = $sourceBefore
    wrapper = $wrapperBefore
    engine = $engineIdentity
    tex_processes_before_count = $texBefore.Count
    environment = [ordered]@{
        TEXMFVAR = $env:TEXMFVAR
        TEXMFCACHE = $env:TEXMFCACHE
        TEXMFCONFIG = $env:TEXMFCONFIG
    }
    recorded_utc = [DateTime]::UtcNow.ToString('o')
}
$preflight | ConvertTo-Json -Depth 7 | Set-Content -LiteralPath (Join-Path $evidenceRoot 'BUILD_PREFLIGHT.json') -Encoding utf8
if ($texBefore.Count -ne 0) { throw "TeX process table not empty: $($texBefore.Count)" }

$startUtc = [DateTime]::UtcNow
$child = Start-Process -FilePath $engine -ArgumentList $argumentList -WorkingDirectory $wrapperDirectory -RedirectStandardOutput $stdoutPath -RedirectStandardError $stderrPath -WindowStyle Hidden -PassThru

$startRecord = [ordered]@{
    parent_pid = $PID
    parent_executable = (Get-Process -Id $PID).Path
    lualatex_pid = $child.Id
    engine = $engineIdentity
    working_directory = $wrapperDirectory
    entry = $entry
    arguments = $argumentList
    invocation_count = 1
    latexmk_invoked = $false
    retry_enabled = $false
    start_utc = $startUtc.ToString('o')
    source_before = $sourceBefore
    wrapper_before = $wrapperBefore
    environment = $preflight.environment
}
$startRecord | ConvertTo-Json -Depth 7 | Set-Content -LiteralPath (Join-Path $evidenceRoot 'DIRECT_INVOCATION_START.json') -Encoding utf8

$child.WaitForExit()
$child.Refresh()
$endUtc = [DateTime]::UtcNow
$exitCode = $child.ExitCode
$pdfs = @(
    Get-ChildItem -LiteralPath $buildPath -Filter '*.pdf' -File -ErrorAction SilentlyContinue | ForEach-Object {
        [ordered]@{
            absolute_path = $_.FullName
            bytes = $_.Length
            mtime_utc = $_.LastWriteTimeUtc.ToString('o')
            sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $_.FullName).Hash
        }
    }
)
$sourceAfter = [ordered]@{
    path = $sourcePath
    bytes = (Get-Item -LiteralPath $sourcePath).Length
    sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $sourcePath).Hash
}
$wrapperAfter = [ordered]@{
    path = $wrapperPath
    bytes = (Get-Item -LiteralPath $wrapperPath).Length
    sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $wrapperPath).Hash
}
$texAfter = @(Get-Process -Name latexmk,lualatex,luatex,luahbtex -ErrorAction SilentlyContinue)

$result = [ordered]@{
    parent_pid = $PID
    lualatex_pid = $child.Id
    lualatex_exit_code = $exitCode
    invocation_count = 1
    natural_exit = $true
    interrupted_or_terminated = $false
    latexmk_invoked = $false
    automatic_retry_count = 0
    start_utc = $startUtc.ToString('o')
    end_utc = $endUtc.ToString('o')
    duration_seconds = [Math]::Round(($endUtc - $startUtc).TotalSeconds, 3)
    source_after = $sourceAfter
    wrapper_after = $wrapperAfter
    source_identity_unchanged = ($sourceAfter.sha256 -eq $sourceBefore.sha256 -and $sourceAfter.bytes -eq $sourceBefore.bytes)
    wrapper_identity_unchanged = ($wrapperAfter.sha256 -eq $wrapperBefore.sha256 -and $wrapperAfter.bytes -eq $wrapperBefore.bytes)
    environment = $preflight.environment
    stdout = $stdoutPath
    stderr = $stderrPath
    pdf_count = $pdfs.Count
    pdfs = $pdfs
    tex_processes_after_count = $texAfter.Count
}
$result | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $evidenceRoot 'DIRECT_INVOCATION_RESULT.json') -Encoding utf8
$result | ConvertTo-Json -Depth 8
exit $exitCode
