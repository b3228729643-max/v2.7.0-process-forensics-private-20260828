#requires -Version 7.4

[CmdletBinding()]
param(
    [string] $AuthorizationToken = ''
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# Frozen static proposal. Main has not authorized or executed this controller.
$ExpectedAuthorizationToken = 'P602_V3B_ONE_DIRECT_LUALATEX_SLOT_GRANTED'
if ($AuthorizationToken -cne $ExpectedAuthorizationToken) {
    throw 'STATIC_CONTROLLER_NOT_AUTHORIZED'
}

$Worktree = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_C_visual'
$Source = Join-Path $Worktree 'src\绘图源码\第05册_采样方法主题模型与图排序\V5-C03\fig_v5_c03_mh_accept_reject.tex'
$WrapperDirectory = Join-Path $Worktree 'src\讲义源码\合并总册'
$WrapperName = 'v260_FIG-P602-01_standalone.tex'
$Wrapper = Join-Path $WrapperDirectory $WrapperName
$Engine = 'D:\texlive\2026\bin\windows\lualatex.exe'
$Kpsewhich = 'D:\texlive\2026\bin\windows\kpsewhich.exe'
$EvidenceParent = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P602-01'
$FutureEvidenceRoot = Join-Path $EvidenceParent 'sa2_r2_controlled_build_v3b'
$ControlDirectory = Join-Path $FutureEvidenceRoot '00_control'
$BuildDirectory = Join-Path $FutureEvidenceRoot '01_build'
$CandidatePdf = Join-Path $BuildDirectory 'v260_FIG-P602-01_standalone.pdf'

$CacheRoot = 'C:\Users\ASUS\AppData\Local\Temp\codex_v270_p602_texcache_v3b'
$PreclaimKpseGate = Join-Path $CacheRoot 'PREBUILD_KPSE_GATE.json'
$ChildEnvironment = [ordered]@{
    TEXMFOUTPUT = $CacheRoot
    TEXMFVAR = Join-Path $CacheRoot 'texmf-var'
    TEXMFCACHE = Join-Path $CacheRoot 'texmf-cache'
    TEXMFCONFIG = Join-Path $CacheRoot 'texmf-config'
}

$ExpectedSourceSha256 = '2B15B4BEEA7A922FEE24259678DBAE2A54915955915E6714A350122A6251E349'
$ExpectedWrapperSha256 = 'AFE3464AEA950331908CD3C56DD0392A6D5010138C4EE9341B78F7FD3E9F7279'
$ExpectedEngineSha256 = 'CC944A1DB010B47FCF5CCB5D1B184CBA208FE7FEA9F18BEC414940E6FD3E24A6'
$ExpectedKpsewhichSha256 = '90E5BD3477FB1AF7F9D1F8C858DE31137AAB4DF57B29928BA82B7D00B2DD85DB'
$InvocationLimit = 1
$BuildState = [ordered]@{ InvocationCount = 0 }

function Get-NormalizedAbsolutePath {
    param([Parameter(Mandatory)][string] $Path)
    return [IO.Path]::TrimEndingDirectorySeparator([IO.Path]::GetFullPath($Path))
}

function Get-SlashNormalizedPath {
    param([Parameter(Mandatory)][string] $Path)
    return (Get-NormalizedAbsolutePath $Path).Replace('\', '/').TrimEnd('/')
}

function Assert-ExactPath {
    param([string] $Actual, [string] $Expected, [string] $Label)
    if (-not [string]::Equals((Get-NormalizedAbsolutePath $Actual), (Get-NormalizedAbsolutePath $Expected), [StringComparison]::OrdinalIgnoreCase)) {
        throw "PATH_IDENTITY_GATE_FAILED:$Label"
    }
}

function Assert-StrictDescendant {
    param([string] $Child, [string] $Parent, [string] $Label)
    $childFull = Get-NormalizedAbsolutePath $Child
    $parentFull = Get-NormalizedAbsolutePath $Parent
    if (-not $childFull.StartsWith(($parentFull + [IO.Path]::DirectorySeparatorChar), [StringComparison]::OrdinalIgnoreCase)) {
        throw "PATH_CONTAINMENT_GATE_FAILED:$Label"
    }
}

function Assert-AsciiPath {
    param([string] $Path, [string] $Label)
    if ([regex]::Matches($Path, '[^\x00-\x7F]').Count -ne 0) { throw "ASCII_PATH_GATE_FAILED:$Label" }
}

function Assert-NoReparsePoint {
    param([string] $Path, [string] $Label)
    $item = Get-Item -LiteralPath $Path -Force
    if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) { throw "REPARSE_POINT_GATE_FAILED:$Label" }
}

function Write-AtomicBytesNew {
    param([string] $Path, [byte[]] $Bytes)
    $directory = Split-Path -Parent $Path
    if (-not (Test-Path -LiteralPath $directory -PathType Container)) { throw 'ATOMIC_WRITE_PARENT_MISSING' }
    if (Test-Path -LiteralPath $Path) { throw 'ATOMIC_WRITE_TARGET_EXISTS' }
    $temporary = Join-Path $directory ('.atomic_' + [Guid]::NewGuid().ToString('N') + '.tmp')
    $stream = [IO.File]::Open($temporary, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write, [IO.FileShare]::None)
    try {
        $stream.Write($Bytes, 0, $Bytes.Length)
        $stream.Flush($true)
    } finally {
        $stream.Dispose()
    }
    [IO.File]::Move($temporary, $Path, $false)
}

function Write-AtomicJsonNew {
    param([string] $Path, [object] $Data)
    $json = ($Data | ConvertTo-Json -Depth 12)
    Write-AtomicBytesNew -Path $Path -Bytes ([Text.UTF8Encoding]::new($false).GetBytes($json))
}

function Invoke-WriteReadDeleteProbe {
    param([string] $Directory, [string] $Label)
    $probe = Join-Path $Directory ('.p602_v3b_probe_' + [Guid]::NewGuid().ToString('N') + '.txt')
    $payload = 'P602_V3B_CACHE_PROBE_' + $Label
    [IO.File]::WriteAllText($probe, $payload, [Text.UTF8Encoding]::new($false))
    $readback = [IO.File]::ReadAllText($probe, [Text.UTF8Encoding]::new($false))
    $readPass = $readback -ceq $payload
    [IO.File]::Delete($probe)
    $deletePass = -not (Test-Path -LiteralPath $probe)
    return [ordered]@{ name = $Label; path = $Directory; write_read_pass = $readPass; delete_pass = $deletePass; pass = ($readPass -and $deletePass) }
}

function New-ControlledProcessStartInfo {
    param([string] $FileName, [string[]] $Arguments)
    $info = [Diagnostics.ProcessStartInfo]::new()
    $info.FileName = $FileName
    $info.WorkingDirectory = $WrapperDirectory
    $info.UseShellExecute = $false
    $info.CreateNoWindow = $true
    $info.RedirectStandardOutput = $true
    $info.RedirectStandardError = $true
    foreach ($argument in $Arguments) { [void] $info.ArgumentList.Add($argument) }
    foreach ($entry in $ChildEnvironment.GetEnumerator()) { $info.Environment[$entry.Key] = $entry.Value }
    return $info
}

# Sole syntactic Process.Start site for both preflight helpers and the one build invocation.
function Invoke-ControlledProcessOnce {
    param(
        [Parameter(Mandatory)][Diagnostics.ProcessStartInfo] $StartInfo,
        [scriptblock] $OnStarted = $null
    )
    $process = [Diagnostics.Process]::new()
    $process.StartInfo = $StartInfo
    $attemptedUtc = [DateTime]::UtcNow
    $started = $false
    $pidValue = $null
    $startedUtc = $null
    $finishedUtc = $null
    $naturalExit = $false
    $interrupted = $false
    $exitCode = $null
    $startException = $null
    $callbackException = $null
    $runtimeException = $null
    $stdout = ''
    $stderr = ''
    $stdoutTask = $null
    $stderrTask = $null
    try {
        try {
            $started = $process.Start()
            if (-not $started) { $startException = 'Process.Start returned false.' }
        } catch {
            $startException = $_.Exception.ToString()
        }
        if ($started) {
            $pidValue = $process.Id
            $startedUtc = [DateTime]::UtcNow
            if ($null -ne $OnStarted) {
                try { & $OnStarted $pidValue $startedUtc } catch { $callbackException = $_.Exception.ToString() }
            }
            try {
                $stdoutTask = $process.StandardOutput.ReadToEndAsync()
                $stderrTask = $process.StandardError.ReadToEndAsync()
                $process.WaitForExit()
                $naturalExit = $true
                $exitCode = $process.ExitCode
                [Threading.Tasks.Task]::WaitAll(@($stdoutTask, $stderrTask))
                $stdout = $stdoutTask.Result
                $stderr = $stderrTask.Result
            } catch {
                $runtimeException = $_.Exception.ToString()
                $interrupted = -not $naturalExit
            }
        }
    } finally {
        $finishedUtc = [DateTime]::UtcNow
        $process.Dispose()
    }
    return [pscustomobject]@{
        AttemptedUtc = $attemptedUtc
        Started = $started
        Pid = $pidValue
        StartedUtc = $startedUtc
        FinishedUtc = $finishedUtc
        DurationSeconds = [Math]::Round(($finishedUtc - $attemptedUtc).TotalSeconds, 3)
        NaturalExit = $naturalExit
        Interrupted = $interrupted
        ExitCode = $exitCode
        StartException = $startException
        CallbackException = $callbackException
        RuntimeException = $runtimeException
        Stdout = $stdout
        Stderr = $stderr
    }
}

# Immutable identity, path, and one-invocation gates. No candidate/cache root exists before these pass.
Assert-ExactPath -Actual (Split-Path -Parent $Wrapper) -Expected $WrapperDirectory -Label 'WRAPPER_CWD'
Assert-StrictDescendant -Child $FutureEvidenceRoot -Parent $EvidenceParent -Label 'FUTURE_EVIDENCE_ROOT'
Assert-StrictDescendant -Child $BuildDirectory -Parent $FutureEvidenceRoot -Label 'BUILD_DIRECTORY'
Assert-StrictDescendant -Child $CacheRoot -Parent 'C:\Users\ASUS\AppData\Local\Temp' -Label 'CACHE_ROOT'
Assert-ExactPath -Actual $ChildEnvironment.TEXMFOUTPUT -Expected $CacheRoot -Label 'TEXMFOUTPUT'
Assert-StrictDescendant -Child $ChildEnvironment.TEXMFVAR -Parent $ChildEnvironment.TEXMFOUTPUT -Label 'TEXMFVAR_IN_TEXMFOUTPUT'
Assert-StrictDescendant -Child $ChildEnvironment.TEXMFCACHE -Parent $ChildEnvironment.TEXMFOUTPUT -Label 'TEXMFCACHE_IN_TEXMFOUTPUT'
Assert-StrictDescendant -Child $ChildEnvironment.TEXMFCONFIG -Parent $ChildEnvironment.TEXMFOUTPUT -Label 'TEXMFCONFIG_IN_TEXMFOUTPUT'
foreach ($entry in $ChildEnvironment.GetEnumerator()) { Assert-AsciiPath -Path $entry.Value -Label $entry.Key }
if ((Get-FileHash -Algorithm SHA256 -LiteralPath $Source).Hash -cne $ExpectedSourceSha256) { throw 'SOURCE_SHA_GATE_FAILED' }
if ((Get-FileHash -Algorithm SHA256 -LiteralPath $Wrapper).Hash -cne $ExpectedWrapperSha256) { throw 'WRAPPER_SHA_GATE_FAILED' }
if ((Get-FileHash -Algorithm SHA256 -LiteralPath $Engine).Hash -cne $ExpectedEngineSha256) { throw 'ENGINE_SHA_GATE_FAILED' }
if ((Get-FileHash -Algorithm SHA256 -LiteralPath $Kpsewhich).Hash -cne $ExpectedKpsewhichSha256) { throw 'KPSEWHICH_SHA_GATE_FAILED' }
if (Test-Path -LiteralPath $FutureEvidenceRoot) { throw 'FUTURE_EVIDENCE_ROOT_MUST_BE_ABSENT' }
if (Test-Path -LiteralPath $CacheRoot) { throw 'CACHE_ROOT_MUST_BE_FRESH_AND_ABSENT' }
if ($InvocationLimit -ne 1 -or $BuildState.InvocationCount -ne 0) { throw 'INVOCATION_COUNT_GATE_FAILED' }
$forbiddenNames = @('latexmk', 'lualatex', 'luatex', 'luahbtex')
if (@(Get-Process -ErrorAction SilentlyContinue | Where-Object { $forbiddenNames -contains $_.ProcessName }).Count -ne 0) { throw 'TEX_CONCURRENCY_GATE_FAILED' }

# Create only the fresh ASCII cache tree; candidate root is still absent.
[IO.Directory]::CreateDirectory($CacheRoot) | Out-Null
$probeResults = @()
foreach ($entry in $ChildEnvironment.GetEnumerator()) {
    [IO.Directory]::CreateDirectory($entry.Value) | Out-Null
    Assert-NoReparsePoint -Path $entry.Value -Label $entry.Key
    $probeResults += Invoke-WriteReadDeleteProbe -Directory $entry.Value -Label $entry.Key
}

# Independent kpsewhich ProcessStartInfo calls use the exact future child environment and wrapper cwd.
$expectedValues = [ordered]@{
    openout_any = 'p'
    TEXMFOUTPUT = $ChildEnvironment.TEXMFOUTPUT
    TEXMFVAR = $ChildEnvironment.TEXMFVAR
    TEXMFCACHE = $ChildEnvironment.TEXMFCACHE
    TEXMFCONFIG = $ChildEnvironment.TEXMFCONFIG
}
$kpseResults = @()
foreach ($entry in $expectedValues.GetEnumerator()) {
    $kpseInfo = New-ControlledProcessStartInfo -FileName $Kpsewhich -Arguments @(('--var-value=' + $entry.Key))
    $outcome = Invoke-ControlledProcessOnce -StartInfo $kpseInfo
    $resolved = $outcome.Stdout.Trim()
    $nonAscii = [regex]::Matches($resolved, '[^\x00-\x7F]').Count
    if ($entry.Key -ceq 'openout_any') {
        $exact = $resolved -ceq 'p'
    } else {
        $exact = [string]::Equals(($resolved.Replace('\', '/').TrimEnd('/')), (Get-SlashNormalizedPath $entry.Value), [StringComparison]::OrdinalIgnoreCase)
    }
    $pass = $outcome.Started -and $outcome.NaturalExit -and $outcome.ExitCode -eq 0 -and $nonAscii -eq 0 -and $exact
    $kpseResults += [ordered]@{
        name = $entry.Key
        requested = $entry.Value
        resolved = $resolved
        exit_code = $outcome.ExitCode
        started = $outcome.Started
        natural_exit = $outcome.NaturalExit
        non_ascii_count = $nonAscii
        exact_after_slash_normalization = $exact
        start_exception = $outcome.StartException
        runtime_exception = $outcome.RuntimeException
        pass = $pass
    }
}
$kpseGatePass = @($kpseResults | Where-Object { -not $_.pass }).Count -eq 0
$probeGatePass = @($probeResults | Where-Object { -not $_.pass }).Count -eq 0
$kpseGate = [ordered]@{
    schema = 'P602_V3B_PREBUILD_KPSE_GATE_V1'
    recorded_utc = [DateTime]::UtcNow.ToString('o')
    candidate_root_exists_when_gate_recorded = Test-Path -LiteralPath $FutureEvidenceRoot
    working_directory = $WrapperDirectory
    kpsewhich_path = $Kpsewhich
    kpsewhich_sha256 = $ExpectedKpsewhichSha256
    child_environment = $ChildEnvironment
    probes = $probeResults
    resolutions = $kpseResults
    probe_gate_pass = $probeGatePass
    kpse_gate_pass = $kpseGatePass
    gate_pass = ($probeGatePass -and $kpseGatePass)
}
Write-AtomicJsonNew -Path $PreclaimKpseGate -Data $kpseGate
if (-not $kpseGate.gate_pass) { throw 'PREBUILD_KPSE_GATE_FAILED_NO_LUALATEX' }

# Gate passed and is durable outside the still-absent candidate root. Now create root, copy gate bytes, then claim ordinal 1.
[IO.Directory]::CreateDirectory($ControlDirectory) | Out-Null
[IO.Directory]::CreateDirectory($BuildDirectory) | Out-Null
Write-AtomicBytesNew -Path (Join-Path $ControlDirectory 'PREBUILD_KPSE_GATE.json') -Bytes ([IO.File]::ReadAllBytes($PreclaimKpseGate))
$claim = [ordered]@{
    schema = 'P602_V3B_INVOCATION_CLAIM_V1'
    recorded_utc = [DateTime]::UtcNow.ToString('o')
    ordinal = 1
    invocation_limit = $InvocationLimit
    invocation_count_before_start = $BuildState.InvocationCount
    source_sha256 = $ExpectedSourceSha256
    wrapper_sha256 = $ExpectedWrapperSha256
    engine_sha256 = $ExpectedEngineSha256
    prebuild_kpse_gate_pass = $true
    retry_count = 0
}
Write-AtomicJsonNew -Path (Join-Path $ControlDirectory 'INVOCATION_CLAIM.json') -Data $claim

$buildArguments = @(
    '-interaction=nonstopmode',
    '-halt-on-error',
    '-file-line-error',
    '-recorder',
    ('-output-directory=' + $BuildDirectory),
    $WrapperName
)
$buildInfo = New-ControlledProcessStartInfo -FileName $Engine -Arguments $buildArguments
$onBuildStarted = {
    param($PidValue, $StartedUtc)
    if ($BuildState.InvocationCount -ne 0) { throw 'SECOND_BUILD_INVOCATION_BLOCKED' }
    $BuildState.InvocationCount = 1
    $startRecord = [ordered]@{
        schema = 'P602_V3B_DIRECT_INVOCATION_START_V1'
        pid = $PidValue
        started_utc = $StartedUtc.ToString('o')
        ordinal = 1
        invocation_limit = $InvocationLimit
        source = [ordered]@{ path = $Source; sha256 = $ExpectedSourceSha256 }
        wrapper = [ordered]@{ path = $Wrapper; sha256 = $ExpectedWrapperSha256 }
        engine = [ordered]@{ path = $Engine; sha256 = $ExpectedEngineSha256 }
        working_directory = $WrapperDirectory
        child_environment = $ChildEnvironment
        arguments = $buildArguments
        retry_count = 0
    }
    Write-AtomicJsonNew -Path (Join-Path $ControlDirectory 'DIRECT_INVOCATION_START.json') -Data $startRecord
}.GetNewClosure()

$buildOutcome = $null
$controllerException = $null
$postProcesses = @()
try {
    if ($BuildState.InvocationCount -ne 0) { throw 'SECOND_BUILD_INVOCATION_BLOCKED' }
    $buildOutcome = Invoke-ControlledProcessOnce -StartInfo $buildInfo -OnStarted $onBuildStarted
} catch {
    $controllerException = $_.Exception.ToString()
} finally {
    $postProcesses = @(Get-Process -ErrorAction SilentlyContinue | Where-Object { $forbiddenNames -contains $_.ProcessName } | Select-Object ProcessName, Id)
    $pdfExists = $false
    $pdfBytes = $null
    $pdfSha256 = $null
    $pdfIdentityException = $null
    try {
        $pdfExists = Test-Path -LiteralPath $CandidatePdf -PathType Leaf
        if ($pdfExists) {
            $pdfBytes = (Get-Item -LiteralPath $CandidatePdf).Length
            $pdfSha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $CandidatePdf).Hash
        }
    } catch {
        $pdfIdentityException = $_.Exception.ToString()
    }
    $resultRecord = [ordered]@{
        schema = 'P602_V3B_DIRECT_INVOCATION_RESULT_V1'
        ordinal = 1
        invocation_limit = $InvocationLimit
        invocation_count = $BuildState.InvocationCount
        started = if ($null -ne $buildOutcome) { $buildOutcome.Started } else { $false }
        pid = if ($null -ne $buildOutcome) { $buildOutcome.Pid } else { $null }
        attempted_utc = if ($null -ne $buildOutcome) { $buildOutcome.AttemptedUtc.ToString('o') } else { $null }
        started_utc = if ($null -ne $buildOutcome -and $null -ne $buildOutcome.StartedUtc) { $buildOutcome.StartedUtc.ToString('o') } else { $null }
        finished_utc = if ($null -ne $buildOutcome) { $buildOutcome.FinishedUtc.ToString('o') } else { [DateTime]::UtcNow.ToString('o') }
        duration_seconds = if ($null -ne $buildOutcome) { $buildOutcome.DurationSeconds } else { $null }
        natural_exit = if ($null -ne $buildOutcome) { $buildOutcome.NaturalExit } else { $false }
        interrupted = if ($null -ne $buildOutcome) { $buildOutcome.Interrupted } else { $false }
        exit_code = if ($null -ne $buildOutcome) { $buildOutcome.ExitCode } else { $null }
        start_exception = if ($null -ne $buildOutcome) { $buildOutcome.StartException } else { $controllerException }
        start_record_exception = if ($null -ne $buildOutcome) { $buildOutcome.CallbackException } else { $null }
        runtime_exception = if ($null -ne $buildOutcome) { $buildOutcome.RuntimeException } else { $controllerException }
        candidate_pdf = [ordered]@{ path = $CandidatePdf; exists = $pdfExists; bytes = $pdfBytes; sha256 = $pdfSha256; identity_exception = $pdfIdentityException }
        post_tex_process_count = $postProcesses.Count
        post_tex_processes = $postProcesses
        retry_count = 0
        second_start_attempted = $false
    }
    Write-AtomicJsonNew -Path (Join-Path $ControlDirectory 'DIRECT_INVOCATION_RESULT.json') -Data $resultRecord
}

# Every stop below occurs only after DIRECT_INVOCATION_RESULT.json is durable.
if ($null -ne $controllerException) { throw 'BUILD_CONTROLLER_EXCEPTION_RESULT_RECORDED' }
if (-not $buildOutcome.Started) { throw 'BUILD_START_EXCEPTION_RESULT_RECORDED' }
if ($null -ne $buildOutcome.CallbackException) { throw 'BUILD_START_RECORD_EXCEPTION_RESULT_RECORDED' }
if (-not $buildOutcome.NaturalExit) { throw 'BUILD_INTERRUPTED_RESULT_RECORDED' }
if ($buildOutcome.ExitCode -ne 0 -or -not (Test-Path -LiteralPath $CandidatePdf -PathType Leaf)) { throw 'BUILD_FAIL_NO_CANDIDATE_RESULT_RECORDED' }

[ordered]@{
    status = 'CANDIDATE_PDF_CREATED_PENDING_NON_TEX_REVIEW'
    invocation_count = $BuildState.InvocationCount
    retry_count = 0
    candidate_pdf = $CandidatePdf
}
