$ErrorActionPreference = 'Stop'

$R7ARoot = Split-Path -Parent $PSScriptRoot
$WorkRoot = (Resolve-Path -LiteralPath (Join-Path $R7ARoot '..\..\..\..\..\..')).Path
$Worktree = (Resolve-Path -LiteralPath (Join-Path $WorkRoot 'worktrees\dialogue_A_visual')).Path
$SourceMatches = @(Get-ChildItem -LiteralPath (Join-Path $Worktree 'src') -Recurse -File -Filter 'fig_v5_c05_dependency_graph.tex')
$WrapperMatches = @(Get-ChildItem -LiteralPath (Join-Path $Worktree 'src') -Recurse -File -Filter 'v260_FIG-P654-01_standalone.tex')
if ($SourceMatches.Count -ne 1) { throw "Expected one target source, found $($SourceMatches.Count)" }
if ($WrapperMatches.Count -ne 1) { throw "Expected one wrapper, found $($WrapperMatches.Count)" }
$SourcePath = $SourceMatches[0].FullName
$WrapperPath = $WrapperMatches[0].FullName
$StdoutPath = Join-Path $R7ARoot 'CURRENT_EXTERNAL_CHILD_STDOUT_R2.json'
$StderrPath = Join-Path $R7ARoot 'CURRENT_EXTERNAL_CHILD_STDERR_R2.txt'
$ResultPath = Join-Path $R7ARoot 'CURRENT_EXTERNAL_STATE_R2.json'
$env:P654_R7A_WORKTREE = $Worktree
$env:P654_R7A_SOURCE = $SourcePath
$env:P654_R7A_WRAPPER = $WrapperPath

$ChildScript = @'
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
$OutputEncoding = [Console]::OutputEncoding = [Text.UTF8Encoding]::new($false)
$Worktree = $env:P654_R7A_WORKTREE
$SourcePath = $env:P654_R7A_SOURCE
$WrapperPath = $env:P654_R7A_WRAPPER
$TexNames = @('latexmk','lualatex','luatex','luahbtex')
$Tex = @(Get-Process -ErrorAction SilentlyContinue | Where-Object { $_.ProcessName.ToLowerInvariant() -in $TexNames } | Select-Object Id,ProcessName,StartTime)
$GitStatus = @(& git -C $Worktree status --porcelain=v1)
$GitStatusExit = $LASTEXITCODE
$GitNames = @(& git -C $Worktree diff --name-only)
$GitNamesExit = $LASTEXITCODE
$GitNumstat = @(& git -C $Worktree diff --numstat)
$GitNumstatExit = $LASTEXITCODE
$GitDiffCheck = @(& git -C $Worktree diff --check)
$GitDiffCheckExit = $LASTEXITCODE
[ordered]@{
    observed_at_utc = (Get-Date).ToUniversalTime().ToString('o')
    observer_process_id = $PID
    tex_process_names_checked = $TexNames
    tex_process_count = $Tex.Count
    tex_processes = $Tex
    source_path = $SourcePath
    source_bytes = (Get-Item -LiteralPath $SourcePath).Length
    source_sha256 = (Get-FileHash -LiteralPath $SourcePath -Algorithm SHA256).Hash
    wrapper_path = $WrapperPath
    wrapper_bytes = (Get-Item -LiteralPath $WrapperPath).Length
    wrapper_sha256 = (Get-FileHash -LiteralPath $WrapperPath -Algorithm SHA256).Hash
    git_status_exit = $GitStatusExit
    git_status_porcelain = $GitStatus
    git_changed_name_exit = $GitNamesExit
    git_changed_name_count = $GitNames.Count
    git_changed_names = $GitNames
    git_numstat_exit = $GitNumstatExit
    git_numstat = $GitNumstat
    git_diff_check_exit = $GitDiffCheckExit
    git_diff_check_output = $GitDiffCheck
} | ConvertTo-Json -Depth 8
'@

$Encoded = [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($ChildScript))
$StartUtc = (Get-Date).ToUniversalTime().ToString('o')
$Child = Start-Process -FilePath 'powershell.exe' -ArgumentList @('-NoProfile','-NonInteractive','-EncodedCommand',$Encoded) -RedirectStandardOutput $StdoutPath -RedirectStandardError $StderrPath -PassThru -Wait
$ChildId = $Child.Id
$Child.Refresh()
$ChildExitCode = $Child.ExitCode
$EndUtc = (Get-Date).ToUniversalTime().ToString('o')
$Observed = Get-Content -LiteralPath $StdoutPath -Raw | ConvertFrom-Json
$StderrBytes = (Get-Item -LiteralPath $StderrPath).Length

$Envelope = [ordered]@{
    capture_kind = 'CURRENT_EXTERNAL_NON_TEX_READ_ONLY_OBSERVATION'
    historical_precheck_claimed = $false
    parent_process_id = $PID
    child_process_id = $ChildId
    child_exit_code = $ChildExitCode
    child_started_at_utc = $StartUtc
    child_finished_at_utc = $EndUtc
    child_stderr_bytes = $StderrBytes
    observed = $Observed
}
$Envelope | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $ResultPath -Encoding utf8

if ($ChildExitCode -ne 0) { throw "External child failed with exit $ChildExitCode" }
if ($StderrBytes -ne 0) { throw 'External child wrote stderr' }
if ($Observed.tex_process_count -ne 0) { throw 'Current TeX process observation is not NONE' }
if ($Observed.source_sha256 -ne 'EA4A19FF940A177D4D754C4277896A2F38B75C1E6F252D8A374F418B84E31E6D') { throw 'Current source SHA mismatch' }
if ($Observed.wrapper_sha256 -ne 'FE44F2E6005D884A6916A11C6EBCB89CF40BD523A64D8F8C6BC8124DBABC0CA1') { throw 'Current wrapper SHA mismatch' }
if ($Observed.git_changed_name_count -ne 1) { throw 'Git scope is not exactly one changed path' }
if ($Observed.git_diff_check_exit -ne 0) { throw 'git diff --check failed' }

Write-Output ($Envelope | ConvertTo-Json -Compress -Depth 10)
