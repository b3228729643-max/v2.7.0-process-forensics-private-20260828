#requires -Version 7.4

[CmdletBinding()]
param(
    [string] $AuthorizationToken = ''
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# This file is frozen for main review. It was not executed while the package was built.
$ExpectedAuthorizationToken = 'P602_V3_ONE_DIRECT_LUALATEX_SLOT_GRANTED'
if ($AuthorizationToken -cne $ExpectedAuthorizationToken) {
    throw 'STATIC_CONTROLLER_NOT_AUTHORIZED: an explicit future main grant is required.'
}

$Worktree = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_C_visual'
$Source = Join-Path $Worktree 'src\绘图源码\第05册_采样方法主题模型与图排序\V5-C03\fig_v5_c03_mh_accept_reject.tex'
$WrapperDirectory = Join-Path $Worktree 'src\讲义源码\合并总册'
$WrapperName = 'v260_FIG-P602-01_standalone.tex'
$Wrapper = Join-Path $WrapperDirectory $WrapperName
$Engine = 'D:\texlive\2026\bin\windows\lualatex.exe'
$FutureEvidenceRoot = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P602-01\sa2_r2_controlled_build_v3'
$BuildDirectory = Join-Path $FutureEvidenceRoot '01_build'
$ControlDirectory = Join-Path $FutureEvidenceRoot '00_control'
$CandidatePdf = Join-Path $BuildDirectory 'v260_FIG-P602-01_standalone.pdf'

$CacheRoot = 'C:\Users\ASUS\AppData\Local\Temp\codex_v270_p602_texcache_v3'
$ChildEnvironment = [ordered]@{
    TEXMFOUTPUT = $CacheRoot
    TEXMFVAR = Join-Path $CacheRoot 'texmf-var'
    TEXMFCACHE = Join-Path $CacheRoot 'texmf-cache'
    TEXMFCONFIG = Join-Path $CacheRoot 'texmf-config'
}

$ExpectedSourceSha256 = '2B15B4BEEA7A922FEE24259678DBAE2A54915955915E6714A350122A6251E349'
$ExpectedWrapperSha256 = 'AFE3464AEA950331908CD3C56DD0392A6D5010138C4EE9341B78F7FD3E9F7279'
$ExpectedEngineSha256 = 'CC944A1DB010B47FCF5CCB5D1B184CBA208FE7FEA9F18BEC414940E6FD3E24A6'
$InvocationLimit = 1
$InvocationCount = 0

function Get-NormalizedAbsolutePath {
    param([Parameter(Mandatory)][string] $Path)
    return [System.IO.Path]::TrimEndingDirectorySeparator([System.IO.Path]::GetFullPath($Path))
}

function Assert-ExactPath {
    param(
        [Parameter(Mandatory)][string] $Actual,
        [Parameter(Mandatory)][string] $Expected,
        [Parameter(Mandatory)][string] $Label
    )
    $actualFull = Get-NormalizedAbsolutePath $Actual
    $expectedFull = Get-NormalizedAbsolutePath $Expected
    if (-not [string]::Equals($actualFull, $expectedFull, [StringComparison]::OrdinalIgnoreCase)) {
        throw "PATH_IDENTITY_GATE_FAILED:$Label"
    }
}

function Assert-StrictDescendant {
    param(
        [Parameter(Mandatory)][string] $Child,
        [Parameter(Mandatory)][string] $Parent,
        [Parameter(Mandatory)][string] $Label
    )
    $childFull = Get-NormalizedAbsolutePath $Child
    $parentFull = Get-NormalizedAbsolutePath $Parent
    $prefix = $parentFull + [System.IO.Path]::DirectorySeparatorChar
    if (-not $childFull.StartsWith($prefix, [StringComparison]::OrdinalIgnoreCase)) {
        throw "PATH_CONTAINMENT_GATE_FAILED:$Label"
    }
}

function Assert-AsciiPath {
    param(
        [Parameter(Mandatory)][string] $Path,
        [Parameter(Mandatory)][string] $Label
    )
    if ([regex]::Matches($Path, '[^\x00-\x7F]').Count -ne 0) {
        throw "ASCII_PATH_GATE_FAILED:$Label"
    }
}

function Assert-NoReparsePoint {
    param(
        [Parameter(Mandatory)][string] $Path,
        [Parameter(Mandatory)][string] $Label
    )
    $item = Get-Item -LiteralPath $Path -Force
    if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
        throw "REPARSE_POINT_GATE_FAILED:$Label"
    }
}

function Invoke-WriteReadDeleteProbe {
    param(
        [Parameter(Mandatory)][string] $Directory,
        [Parameter(Mandatory)][string] $Label
    )
    $probe = Join-Path $Directory ('.p602_v3_probe_' + [Guid]::NewGuid().ToString('N') + '.txt')
    $payload = 'P602_V3_CACHE_PROBE_' + $Label
    [IO.File]::WriteAllText($probe, $payload, [Text.UTF8Encoding]::new($false))
    $readback = [IO.File]::ReadAllText($probe, [Text.UTF8Encoding]::new($false))
    if ($readback -cne $payload) {
        throw "CACHE_READBACK_GATE_FAILED:$Label"
    }
    [IO.File]::Delete($probe)
    if (Test-Path -LiteralPath $probe) {
        throw "CACHE_DELETE_GATE_FAILED:$Label"
    }
}

# Static identity and scope gates. Any failure stops before a candidate root or engine process exists.
Assert-ExactPath -Actual (Split-Path -Parent $Wrapper) -Expected $WrapperDirectory -Label 'WRAPPER_CWD'
Assert-StrictDescendant -Child $FutureEvidenceRoot -Parent 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P602-01' -Label 'FUTURE_ROOT'
Assert-StrictDescendant -Child $BuildDirectory -Parent $FutureEvidenceRoot -Label 'BUILD_DIRECTORY'
Assert-StrictDescendant -Child $CacheRoot -Parent 'C:\Users\ASUS\AppData\Local\Temp' -Label 'CACHE_ROOT'
Assert-ExactPath -Actual $ChildEnvironment.TEXMFOUTPUT -Expected $CacheRoot -Label 'TEXMFOUTPUT'
Assert-StrictDescendant -Child $ChildEnvironment.TEXMFVAR -Parent $ChildEnvironment.TEXMFOUTPUT -Label 'TEXMFVAR_IN_TEXMFOUTPUT'
Assert-StrictDescendant -Child $ChildEnvironment.TEXMFCACHE -Parent $ChildEnvironment.TEXMFOUTPUT -Label 'TEXMFCACHE_IN_TEXMFOUTPUT'
Assert-StrictDescendant -Child $ChildEnvironment.TEXMFCONFIG -Parent $ChildEnvironment.TEXMFOUTPUT -Label 'TEXMFCONFIG_IN_TEXMFOUTPUT'

foreach ($entry in $ChildEnvironment.GetEnumerator()) {
    Assert-AsciiPath -Path $entry.Value -Label $entry.Key
}

if ($WrapperName.IndexOfAny([IO.Path]::GetInvalidFileNameChars()) -ge 0 -or
    $WrapperName.Contains([IO.Path]::DirectorySeparatorChar) -or
    $WrapperName.Contains([IO.Path]::AltDirectorySeparatorChar)) {
    throw 'WRAPPER_LEAF_NAME_GATE_FAILED'
}
if (-not (Test-Path -LiteralPath $Source -PathType Leaf)) { throw 'SOURCE_MISSING' }
if (-not (Test-Path -LiteralPath $Wrapper -PathType Leaf)) { throw 'WRAPPER_MISSING' }
if (-not (Test-Path -LiteralPath $Engine -PathType Leaf)) { throw 'ENGINE_MISSING' }
if ((Get-FileHash -Algorithm SHA256 -LiteralPath $Source).Hash -cne $ExpectedSourceSha256) { throw 'SOURCE_SHA_GATE_FAILED' }
if ((Get-FileHash -Algorithm SHA256 -LiteralPath $Wrapper).Hash -cne $ExpectedWrapperSha256) { throw 'WRAPPER_SHA_GATE_FAILED' }
if ((Get-FileHash -Algorithm SHA256 -LiteralPath $Engine).Hash -cne $ExpectedEngineSha256) { throw 'ENGINE_SHA_GATE_FAILED' }
if (Test-Path -LiteralPath $FutureEvidenceRoot) { throw 'FUTURE_EVIDENCE_ROOT_MUST_BE_ABSENT' }
if (Test-Path -LiteralPath $CacheRoot) { throw 'CACHE_ROOT_MUST_BE_FRESH_AND_ABSENT' }
if ($InvocationCount -ne 0 -or $InvocationLimit -ne 1) { throw 'INVOCATION_COUNT_GATE_FAILED' }

$forbiddenProcesses = @('latexmk', 'lualatex', 'luatex', 'luahbtex')
$active = @(Get-Process -ErrorAction SilentlyContinue | Where-Object { $forbiddenProcesses -contains $_.ProcessName })
if ($active.Count -ne 0) { throw 'TEX_CONCURRENCY_GATE_FAILED' }

# Runtime cache gates. They create only the task-specific ASCII cache tree, not the candidate root.
[IO.Directory]::CreateDirectory($CacheRoot) | Out-Null
foreach ($entry in $ChildEnvironment.GetEnumerator()) {
    [IO.Directory]::CreateDirectory($entry.Value) | Out-Null
    Assert-NoReparsePoint -Path $entry.Value -Label $entry.Key
    Invoke-WriteReadDeleteProbe -Directory $entry.Value -Label $entry.Key
}

# Candidate-root claim is atomic and occurs only after every preceding gate passes.
[IO.Directory]::CreateDirectory($ControlDirectory) | Out-Null
[IO.Directory]::CreateDirectory($BuildDirectory) | Out-Null
$claimPath = Join-Path $ControlDirectory 'INVOCATION_CLAIM.json'
$claim = [ordered]@{
    schema = 'P602_V3_INVOCATION_CLAIM_V1'
    invocation_limit = $InvocationLimit
    invocation_count_before_start = $InvocationCount
    status = 'CLAIMED_NOT_STARTED'
    source_sha256 = $ExpectedSourceSha256
    wrapper_sha256 = $ExpectedWrapperSha256
    engine_sha256 = $ExpectedEngineSha256
}
$claimBytes = [Text.UTF8Encoding]::new($false).GetBytes(($claim | ConvertTo-Json -Depth 4))
$claimStream = [IO.File]::Open($claimPath, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write, [IO.FileShare]::None)
try { $claimStream.Write($claimBytes, 0, $claimBytes.Length) } finally { $claimStream.Dispose() }

$Arguments = @(
    '-interaction=nonstopmode',
    '-halt-on-error',
    '-file-line-error',
    '-recorder',
    ('-output-directory=' + $BuildDirectory),
    $WrapperName
)

$startInfo = [Diagnostics.ProcessStartInfo]::new()
$startInfo.FileName = $Engine
$startInfo.WorkingDirectory = $WrapperDirectory
$startInfo.UseShellExecute = $false
$startInfo.CreateNoWindow = $true
$startInfo.RedirectStandardOutput = $true
$startInfo.RedirectStandardError = $true
foreach ($argument in $Arguments) { [void] $startInfo.ArgumentList.Add($argument) }
foreach ($entry in $ChildEnvironment.GetEnumerator()) { $startInfo.Environment[$entry.Key] = $entry.Value }

# Preserve paranoid output policy. A non-p value is never installed by this controller.
if ($startInfo.Environment.ContainsKey('openout_any') -and
    -not [string]::IsNullOrEmpty($startInfo.Environment['openout_any']) -and
    $startInfo.Environment['openout_any'] -cne 'p') {
    throw 'OPENOUT_ANY_POLICY_GATE_FAILED'
}

$process = [Diagnostics.Process]::new()
$process.StartInfo = $startInfo
$started = $false
$exitCode = $null
try {
    if ($InvocationCount -ne 0) { throw 'SECOND_INVOCATION_BLOCKED' }
    $started = $process.Start()
    if (-not $started) { throw 'PROCESS_START_RETURNED_FALSE' }
    $InvocationCount++
    if ($InvocationCount -ne 1) { throw 'INVOCATION_COUNT_POSTSTART_GATE_FAILED' }
    $stdoutTask = $process.StandardOutput.ReadToEndAsync()
    $stderrTask = $process.StandardError.ReadToEndAsync()
    $process.WaitForExit()
    $exitCode = $process.ExitCode
    [Threading.Tasks.Task]::WaitAll(@($stdoutTask, $stderrTask))
    [IO.File]::WriteAllText((Join-Path $BuildDirectory 'lualatex.stdout.txt'), $stdoutTask.Result, [Text.UTF8Encoding]::new($false))
    [IO.File]::WriteAllText((Join-Path $BuildDirectory 'lualatex.stderr.txt'), $stderrTask.Result, [Text.UTF8Encoding]::new($false))
} finally {
    if ($null -ne $process) { $process.Dispose() }
}

if (-not $started) { throw 'BUILD_FAIL_NO_PROCESS_START' }
if ($InvocationCount -ne 1) { throw 'INVOCATION_COUNT_FINAL_GATE_FAILED' }
if ($exitCode -ne 0 -or -not (Test-Path -LiteralPath $CandidatePdf -PathType Leaf)) {
    throw 'BUILD_FAIL_NO_CANDIDATE'
}

# Success stops here. Native evidence, another TeX call, commit, state changes, and next-figure work require separate authorization.
[ordered]@{
    status = 'CANDIDATE_PDF_CREATED_PENDING_NON_TEX_REVIEW'
    invocation_count = $InvocationCount
    candidate_pdf = $CandidatePdf
}
