[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$Worktree,
    [Parameter(Mandatory = $true)][string]$OutputDir,
    [Parameter(Mandatory = $true)][string]$ControlDir,
    [switch]$Resume
)

$ErrorActionPreference = 'Stop'
$resolvedWorktree = [System.IO.Path]::GetFullPath($Worktree)
$resolvedControl = [System.IO.Path]::GetFullPath($ControlDir)
$worktreePrefix = $resolvedWorktree.TrimEnd('\') + '\'
if (-not $resolvedControl.StartsWith($worktreePrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "Control directory must remain inside worktree: $resolvedControl"
}

New-Item -ItemType Directory -Path $resolvedControl -Force | Out-Null
$stdoutPath = Join-Path $resolvedControl 'stdout.log'
$stderrPath = Join-Path $resolvedControl 'stderr.log'
$exitPath = Join-Path $resolvedControl 'exit_code.txt'
$startedPath = Join-Path $resolvedControl 'started_at.txt'
$finishedPath = Join-Path $resolvedControl 'finished_at.txt'

Set-Content -LiteralPath $startedPath -Value ([DateTimeOffset]::Now.ToString('o')) -Encoding UTF8
Push-Location -LiteralPath $resolvedWorktree
try {
    $buildArguments = @(
        '-ExecutionPolicy', 'Bypass',
        '-File', '.\build_v2.7.0.ps1',
        '-Engine', 'lualatex',
        '-OutputDir', $OutputDir,
        '-NoPublish'
    )
    if ($Resume) {
        $buildArguments += '-Resume'
    }
    # Windows PowerShell promotes native stderr (for example Perl locale
    # warnings emitted by latexmk) to a non-terminating NativeCommandError.
    # Keep the diagnostic in stderr.log but use the child process exit code as
    # the build result.
    $savedErrorActionPreference = $ErrorActionPreference
    try {
        $ErrorActionPreference = 'Continue'
        & powershell.exe @buildArguments 1> $stdoutPath 2> $stderrPath
        $buildExitCode = $LASTEXITCODE
    } finally {
        $ErrorActionPreference = $savedErrorActionPreference
    }
} catch {
    $_ | Out-File -LiteralPath $stderrPath -Append -Encoding UTF8
    $buildExitCode = 1
} finally {
    Pop-Location
}

Set-Content -LiteralPath $exitPath -Value $buildExitCode -Encoding ASCII
Set-Content -LiteralPath $finishedPath -Value ([DateTimeOffset]::Now.ToString('o')) -Encoding UTF8
exit $buildExitCode
