$ErrorActionPreference = 'Stop'

$preflightRoot = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P654-01\STRICT_R6_SA2_NARROW_R100_DIRECT_PREFLIGHT_20260825'
$texcachePath = [System.IO.Path]::GetFullPath((Join-Path $preflightRoot 'texcache')).TrimEnd('\', '/')
$texcacheBinding = $texcachePath.Replace('\', '/')
$childScript = Join-Path $preflightRoot 'child_env_kpse_probe.ps1'
$childJsonPath = Join-Path $preflightRoot 'CHILD_PREFLIGHT_ATTEMPT2.json'
$parentJsonPath = Join-Path $preflightRoot 'PARENT_PREFLIGHT_RESULT_ATTEMPT2.json'

if (-not (Test-Path -LiteralPath $texcachePath -PathType Container)) {
    throw "texcache missing: $texcachePath"
}
$entriesBefore = @(Get-ChildItem -LiteralPath $texcachePath -Force)
if ($entriesBefore.Count -ne 1 -or $entriesBefore[0].Name -cne 'P654_R6_CHILD_WRITE_PROBE.txt') {
    throw 'attempt-2 requires exactly the retained attempt-1 probe and no other cache entry'
}

# This is the exact parent-shell binding stanza reserved for a future explicitly
# authorized direct-lualatex controller.  R6 executes only an ordinary PowerShell
# child and kpsewhich; it never calls a TeX typesetter.
$env:TEXMFVAR = $texcacheBinding
$env:TEXMFCACHE = $texcacheBinding
$env:TEXMFCONFIG = $texcacheBinding

$childPowerShell = (Get-Command powershell.exe -ErrorAction Stop).Source
$childOutput = @(& $childPowerShell -NoProfile -ExecutionPolicy Bypass -File $childScript -RootPath $preflightRoot -CachePath $texcacheBinding -OutputJsonPath $childJsonPath 2>&1)
$childExit = $LASTEXITCODE
if (-not (Test-Path -LiteralPath $childJsonPath -PathType Leaf)) {
    throw 'child produced no JSON evidence file'
}
$child = Get-Content -LiteralPath $childJsonPath -Raw -Encoding UTF8 | ConvertFrom-Json -ErrorAction Stop

$parentVisible = [ordered]@{
    TEXMFVAR = [Environment]::GetEnvironmentVariable('TEXMFVAR', 'Process')
    TEXMFCACHE = [Environment]::GetEnvironmentVariable('TEXMFCACHE', 'Process')
    TEXMFCONFIG = [Environment]::GetEnvironmentVariable('TEXMFCONFIG', 'Process')
}
$parentPass = (
    $childExit -eq 0 -and
    $child.pass -eq $true -and
    $parentVisible.TEXMFVAR -ceq $texcacheBinding -and
    $parentVisible.TEXMFCACHE -ceq $texcacheBinding -and
    $parentVisible.TEXMFCONFIG -ceq $texcacheBinding -and
    $child.environment.TEXMFVAR -ceq $texcacheBinding -and
    $child.environment.TEXMFCACHE -ceq $texcacheBinding -and
    $child.environment.TEXMFCONFIG -ceq $texcacheBinding
)

$parentResult = [ordered]@{
    parent_pid = $PID
    parent_executable = (Get-Process -Id $PID).Path
    parent_powershell_version = $PSVersionTable.PSVersion.ToString()
    child_launch = [ordered]@{
        executable = $childPowerShell
        mode = 'ordinary PowerShell child; inherited process environment; no -Environment override'
        exit_code = $childExit
        stdout = (($childOutput | ForEach-Object { [string]$_ }) -join "`n").Trim()
    }
    expected_texcache = $texcachePath
    exact_environment_binding = $texcacheBinding
    diagnostic_attempt = 2
    attempt_1_retained = [ordered]@{
        child_json = (Join-Path $preflightRoot 'CHILD_PREFLIGHT.json')
        parent_json = (Join-Path $preflightRoot 'PARENT_PREFLIGHT_RESULT.json')
        failure = 'kpsewhich CP936 bytes decoded as UTF-8 by the first child harness'
    }
    parent_environment = $parentVisible
    child_pid = $child.child_process.pid
    child_environment = $child.environment
    child_kpsewhich = $child.kpsewhich
    child_probe = $child.probe
    texcache_entry_count = $child.texcache_entry_count_after_probe
    forbidden_tex_engines_invoked_by_parent = @()
    forbidden_tex_engines_invoked_by_child = $child.forbidden_tex_engines_invoked_by_script
    pass = $parentPass
}
[System.IO.File]::WriteAllText(
    $parentJsonPath,
    ($parentResult | ConvertTo-Json -Depth 14) + "`n",
    [System.Text.UTF8Encoding]::new($false)
)
$parentResult | ConvertTo-Json -Depth 14
if (-not $parentPass) {
    exit 3
}
