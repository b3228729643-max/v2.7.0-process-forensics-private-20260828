#requires -Version 7.4

[CmdletBinding()]
param([string] $AuthorizationToken = '')

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# Frozen static proposal. Main has not authorized or executed this controller.
$ExpectedAuthorizationToken = 'P602_R3_V1_ONE_DIRECT_LUALATEX_SLOT_GRANTED'
if ($AuthorizationToken -cne $ExpectedAuthorizationToken) { throw 'STATIC_CONTROLLER_NOT_AUTHORIZED' }

$Worktree = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_C_visual'
$Source = Join-Path $Worktree 'src\绘图源码\第05册_采样方法主题模型与图排序\V5-C03\fig_v5_c03_mh_accept_reject.tex'
$WrapperDirectory = Join-Path $Worktree 'src\讲义源码\合并总册'
$WrapperName = 'v260_FIG-P602-01_standalone.tex'
$Wrapper = Join-Path $WrapperDirectory $WrapperName
$Engine = 'D:\texlive\2026\bin\windows\lualatex.exe'
$Kpsewhich = 'D:\texlive\2026\bin\windows\kpsewhich.exe'
$EvidenceParent = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P602-01'
$FutureEvidenceRoot = Join-Path $EvidenceParent 'sa2_r3_controlled_build_v1'
$ControlDirectory = Join-Path $FutureEvidenceRoot '00_control'
$BuildDirectory = Join-Path $FutureEvidenceRoot '01_build'
$CandidatePdf = Join-Path $BuildDirectory 'v260_FIG-P602-01_standalone.pdf'
$StdoutPath = Join-Path $BuildDirectory 'lualatex.stdout.txt'
$StderrPath = Join-Path $BuildDirectory 'lualatex.stderr.txt'

$CacheRoot = 'C:\Users\ASUS\AppData\Local\Temp\codex_v270_p602_texcache_r3_v1'
$PreclaimKpseGate = Join-Path $CacheRoot 'PREBUILD_KPSE_GATE.json'
$ChildEnvironment = [ordered]@{
    TEXMFOUTPUT = $CacheRoot
    TEXMFVAR = Join-Path $CacheRoot 'texmf-var'
    TEXMFCACHE = Join-Path $CacheRoot 'texmf-cache'
    TEXMFCONFIG = Join-Path $CacheRoot 'texmf-config'
}

$ExpectedSourceSha256 = '6C4E8F156709C0FF384F9E7B7F2BD5D9CB586E24206BF0BCD2E58933ED3DB47D'
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

function Write-AtomicTextNew {
    param([string] $Path, [AllowEmptyString()][string] $Text)
    Write-AtomicBytesNew -Path $Path -Bytes ([Text.UTF8Encoding]::new($false).GetBytes($Text))
}

function Write-AtomicJsonNew {
    param([string] $Path, [object] $Data)
    Write-AtomicTextNew -Path $Path -Text ($Data | ConvertTo-Json -Depth 14)
}

function Get-FileIdentity {
    param([string] $Path)
    $resolved = [IO.Path]::GetFullPath($Path)
    $exists = Test-Path -LiteralPath $resolved -PathType Leaf
    return [ordered]@{
        resolved_path = $resolved
        exists = $exists
        bytes = if ($exists) { (Get-Item -LiteralPath $resolved).Length } else { $null }
        sha256 = if ($exists) { (Get-FileHash -Algorithm SHA256 -LiteralPath $resolved).Hash } else { $null }
    }
}

function Test-RecomputedIdentity {
    param([object] $Identity)
    if ($null -eq $Identity -or -not $Identity.exists) { return $false }
    $again = Get-FileIdentity -Path $Identity.resolved_path
    return ($again.exists -and $again.bytes -eq $Identity.bytes -and $again.sha256 -ceq $Identity.sha256)
}

function Add-ExceptionText {
    param([string] $Existing, [string] $Additional)
    if ([string]::IsNullOrEmpty($Existing)) { return $Additional }
    return ($Existing + [Environment]::NewLine + $Additional)
}

function Invoke-WriteReadDeleteProbe {
    param([string] $Directory, [string] $Label)
    $probe = Join-Path $Directory ('.p602_r3_v1_probe_' + [Guid]::NewGuid().ToString('N') + '.txt')
    $payload = 'P602_R3_V1_CACHE_PROBE_' + $Label
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
    $info.StandardOutputEncoding = [Text.UTF8Encoding]::new($false)
    $info.StandardErrorEncoding = [Text.UTF8Encoding]::new($false)
    foreach ($argument in $Arguments) { [void] $info.ArgumentList.Add($argument) }
    foreach ($entry in $ChildEnvironment.GetEnumerator()) { $info.Environment[$entry.Key] = $entry.Value }
    return $info
}

# Sole syntactic Process.Start site. It is never called from a retry loop or an exception branch.
function Invoke-ControlledProcessOnce {
    param([Diagnostics.ProcessStartInfo] $StartInfo, [scriptblock] $OnStarted = $null)
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
                # START callback has completed or recorded its exception before output waiting begins.
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

# Pre-cache immutable gates.
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

# Fresh cache and same-child-environment kpse gate, before candidate root or claim.
[IO.Directory]::CreateDirectory($CacheRoot) | Out-Null
$probeResults = @()
foreach ($entry in $ChildEnvironment.GetEnumerator()) {
    [IO.Directory]::CreateDirectory($entry.Value) | Out-Null
    Assert-NoReparsePoint -Path $entry.Value -Label $entry.Key
    $probeResults += Invoke-WriteReadDeleteProbe -Directory $entry.Value -Label $entry.Key
}
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
    $exact = if ($entry.Key -ceq 'openout_any') {
        $resolved -ceq 'p'
    } else {
        [string]::Equals($resolved.Replace('\', '/').TrimEnd('/'), (Get-SlashNormalizedPath $entry.Value), [StringComparison]::OrdinalIgnoreCase)
    }
    $pass = $outcome.Started -and $outcome.NaturalExit -and $outcome.ExitCode -eq 0 -and $nonAscii -eq 0 -and $exact
    $kpseResults += [ordered]@{
        name = $entry.Key; requested = $entry.Value; resolved = $resolved; stderr = $outcome.Stderr
        exit_code = $outcome.ExitCode; started = $outcome.Started; natural_exit = $outcome.NaturalExit
        non_ascii_count = $nonAscii; exact_after_slash_normalization = $exact
        start_exception = $outcome.StartException; runtime_exception = $outcome.RuntimeException; pass = $pass
    }
}
$kpseGatePass = @($kpseResults | Where-Object { -not $_.pass }).Count -eq 0
$probeGatePass = @($probeResults | Where-Object { -not $_.pass }).Count -eq 0
$kpseGate = [ordered]@{
    schema = 'P602_R3_V1_PREBUILD_KPSE_GATE_V1'
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

# PASS-only candidate root, gate copy, and ordinal claim.
[IO.Directory]::CreateDirectory($ControlDirectory) | Out-Null
[IO.Directory]::CreateDirectory($BuildDirectory) | Out-Null
Write-AtomicBytesNew -Path (Join-Path $ControlDirectory 'PREBUILD_KPSE_GATE.json') -Bytes ([IO.File]::ReadAllBytes($PreclaimKpseGate))
Write-AtomicJsonNew -Path (Join-Path $ControlDirectory 'INVOCATION_CLAIM.json') -Data ([ordered]@{
    schema = 'P602_R3_V1_INVOCATION_CLAIM_V1'; recorded_utc = [DateTime]::UtcNow.ToString('o')
    ordinal = 1; invocation_limit = $InvocationLimit; invocation_count_before_start = $BuildState.InvocationCount
    source_sha256 = $ExpectedSourceSha256; wrapper_sha256 = $ExpectedWrapperSha256
    engine_sha256 = $ExpectedEngineSha256; prebuild_kpse_gate_pass = $true; retry_count = 0
})

$buildArguments = @(
    '-interaction=nonstopmode', '-halt-on-error', '-file-line-error', '-recorder',
    ('-output-directory=' + $BuildDirectory), $WrapperName
)
$buildInfo = New-ControlledProcessStartInfo -FileName $Engine -Arguments $buildArguments
$onBuildStarted = {
    param($PidValue, $StartedUtc)
    if ($BuildState.InvocationCount -ne 0) { throw 'SECOND_BUILD_INVOCATION_BLOCKED' }
    $BuildState.InvocationCount = 1
    Write-AtomicJsonNew -Path (Join-Path $ControlDirectory 'DIRECT_INVOCATION_START.json') -Data ([ordered]@{
        schema = 'P602_R3_V1_DIRECT_INVOCATION_START_V1'; pid = $PidValue; started_utc = $StartedUtc.ToString('o')
        ordinal = 1; invocation_limit = $InvocationLimit
        source = [ordered]@{ path = $Source; sha256 = $ExpectedSourceSha256 }
        wrapper = [ordered]@{ path = $Wrapper; sha256 = $ExpectedWrapperSha256 }
        engine = [ordered]@{ path = $Engine; sha256 = $ExpectedEngineSha256 }
        working_directory = $WrapperDirectory; child_environment = $ChildEnvironment; arguments = $buildArguments; retry_count = 0
    })
}.GetNewClosure()

$buildOutcome = $null
$controllerException = $null
$outputPersistenceException = $null
$pdfIdentityException = $null
$stdoutIdentity = [ordered]@{ resolved_path = [IO.Path]::GetFullPath($StdoutPath); exists = $false; bytes = $null; sha256 = $null }
$stderrIdentity = [ordered]@{ resolved_path = [IO.Path]::GetFullPath($StderrPath); exists = $false; bytes = $null; sha256 = $null }
$stdoutIdentityRecomputed = $false
$stderrIdentityRecomputed = $false
$pdfIdentity = $null
$pdfCount = 0
$postProcesses = @()
$successHardGatePass = $false
$resultPersisted = $false
try {
    if ($BuildState.InvocationCount -ne 0) { throw 'SECOND_BUILD_INVOCATION_BLOCKED' }
    $buildOutcome = Invoke-ControlledProcessOnce -StartInfo $buildInfo -OnStarted $onBuildStarted
} catch {
    $controllerException = $_.Exception.ToString()
} finally {
    # Read-only post-process scan is part of RESULT and is a mandatory success gate.
    $postProcesses = @(Get-Process -ErrorAction SilentlyContinue | Where-Object { $forbiddenNames -contains $_.ProcessName } | Select-Object ProcessName, Id)

    # Persist complete redirected output before RESULT for success, nonzero exit, missing PDF, start exception, or controller exception.
    $stdoutText = if ($null -ne $buildOutcome) { [string] $buildOutcome.Stdout } else { '' }
    $stderrText = if ($null -ne $buildOutcome) { [string] $buildOutcome.Stderr } else { '' }
    try {
        Write-AtomicTextNew -Path $StdoutPath -Text $stdoutText
        Write-AtomicTextNew -Path $StderrPath -Text $stderrText
    } catch {
        $outputPersistenceException = Add-ExceptionText -Existing $outputPersistenceException -Additional $_.Exception.ToString()
    }
    try {
        $stdoutIdentity = Get-FileIdentity -Path $StdoutPath
        $stderrIdentity = Get-FileIdentity -Path $StderrPath
        $stdoutIdentityRecomputed = Test-RecomputedIdentity -Identity $stdoutIdentity
        $stderrIdentityRecomputed = Test-RecomputedIdentity -Identity $stderrIdentity
    } catch {
        $outputPersistenceException = Add-ExceptionText -Existing $outputPersistenceException -Additional $_.Exception.ToString()
    }

    try {
        $pdfFiles = @(Get-ChildItem -LiteralPath $BuildDirectory -File -Filter '*.pdf' -ErrorAction Stop)
        $pdfCount = $pdfFiles.Count
        $pdfIdentity = Get-FileIdentity -Path $CandidatePdf
    } catch {
        $pdfIdentityException = $_.Exception.ToString()
        $pdfIdentity = [ordered]@{ resolved_path = [IO.Path]::GetFullPath($CandidatePdf); exists = $false; bytes = $null; sha256 = $null }
    }

    $started = $null -ne $buildOutcome -and $buildOutcome.Started
    $naturalExit = $null -ne $buildOutcome -and $buildOutcome.NaturalExit
    $exitZero = $null -ne $buildOutcome -and $buildOutcome.ExitCode -eq 0
    $startException = if ($null -ne $buildOutcome) { $buildOutcome.StartException } else { $null }
    $startRecordException = if ($null -ne $buildOutcome) { $buildOutcome.CallbackException } else { $null }
    $runtimeException = if ($null -ne $buildOutcome) { $buildOutcome.RuntimeException } else { $null }
    $exceptionsEmpty = [string]::IsNullOrEmpty($startException) -and
        [string]::IsNullOrEmpty($startRecordException) -and
        [string]::IsNullOrEmpty($runtimeException) -and
        [string]::IsNullOrEmpty($controllerException) -and
        [string]::IsNullOrEmpty($pdfIdentityException) -and
        [string]::IsNullOrEmpty($outputPersistenceException)
    $pdfExactlyOneNonempty = $pdfCount -eq 1 -and $pdfIdentity.exists -and $pdfIdentity.bytes -gt 0 -and -not [string]::IsNullOrEmpty($pdfIdentity.sha256)
    $outputsRecomputable = $stdoutIdentityRecomputed -and $stderrIdentityRecomputed
    $startRecordExists = Test-Path -LiteralPath (Join-Path $ControlDirectory 'DIRECT_INVOCATION_START.json') -PathType Leaf
    $successHardGatePass = $BuildState.InvocationCount -eq 1 -and $started -and $startRecordExists -and
        $naturalExit -and $exitZero -and $pdfExactlyOneNonempty -and $postProcesses.Count -eq 0 -and
        $exceptionsEmpty -and $outputsRecomputable

    $successGate = [ordered]@{
        invocation_count_is_one = $BuildState.InvocationCount -eq 1
        started_true = $started
        start_record_exists = $startRecordExists
        natural_exit_true = $naturalExit
        exit_code_zero = $exitZero
        pdf_count_exactly_one = $pdfCount -eq 1
        expected_pdf_exists = $pdfIdentity.exists
        expected_pdf_bytes_positive = $pdfIdentity.exists -and $pdfIdentity.bytes -gt 0
        post_tex_process_count_zero = $postProcesses.Count -eq 0
        all_exception_fields_empty = $exceptionsEmpty
        stdout_identity_recomputed = $stdoutIdentityRecomputed
        stderr_identity_recomputed = $stderrIdentityRecomputed
        all_pass = $successHardGatePass
    }
    $resultRecord = [ordered]@{
        schema = 'P602_R3_V1_DIRECT_INVOCATION_RESULT_V1'
        ordinal = 1; invocation_limit = $InvocationLimit; invocation_count = $BuildState.InvocationCount
        started = $started
        pid = if ($null -ne $buildOutcome) { $buildOutcome.Pid } else { $null }
        attempted_utc = if ($null -ne $buildOutcome) { $buildOutcome.AttemptedUtc.ToString('o') } else { $null }
        started_utc = if ($null -ne $buildOutcome -and $null -ne $buildOutcome.StartedUtc) { $buildOutcome.StartedUtc.ToString('o') } else { $null }
        finished_utc = if ($null -ne $buildOutcome) { $buildOutcome.FinishedUtc.ToString('o') } else { [DateTime]::UtcNow.ToString('o') }
        duration_seconds = if ($null -ne $buildOutcome) { $buildOutcome.DurationSeconds } else { $null }
        natural_exit = $naturalExit
        interrupted = if ($null -ne $buildOutcome) { $buildOutcome.Interrupted } else { $false }
        exit_code = if ($null -ne $buildOutcome) { $buildOutcome.ExitCode } else { $null }
        start_exception = $startException
        start_record_exception = $startRecordException
        runtime_exception = $runtimeException
        controller_exception = $controllerException
        pdf_identity_exception = $pdfIdentityException
        output_persistence_exception = $outputPersistenceException
        stdout = [ordered]@{ resolved_path = $stdoutIdentity.resolved_path; exists = $stdoutIdentity.exists; bytes = $stdoutIdentity.bytes; sha256 = $stdoutIdentity.sha256; identity_recomputed = $stdoutIdentityRecomputed }
        stderr = [ordered]@{ resolved_path = $stderrIdentity.resolved_path; exists = $stderrIdentity.exists; bytes = $stderrIdentity.bytes; sha256 = $stderrIdentity.sha256; identity_recomputed = $stderrIdentityRecomputed }
        candidate_pdf = [ordered]@{ resolved_path = $pdfIdentity.resolved_path; count_in_build_directory = $pdfCount; exists = $pdfIdentity.exists; bytes = $pdfIdentity.bytes; sha256 = $pdfIdentity.sha256 }
        post_tex_process_count = $postProcesses.Count
        post_tex_processes = $postProcesses
        retry_count = 0
        second_start_attempted = $false
        success_hard_gate = $successGate
    }
    Write-AtomicJsonNew -Path (Join-Path $ControlDirectory 'DIRECT_INVOCATION_RESULT.json') -Data $resultRecord
    $resultPersisted = $true
}

# RESULT is durable before this sole final build-status throw/return decision.
if (-not $resultPersisted) { throw 'RESULT_PERSISTENCE_FAILED' }
if (-not $successHardGatePass) { throw 'BUILD_NOT_SUCCESS_RESULT_RECORDED' }
return [ordered]@{ status = 'CANDIDATE_PDF_CREATED_PENDING_NON_TEX_REVIEW'; invocation_count = $BuildState.InvocationCount; retry_count = 0; candidate_pdf = $CandidatePdf }
