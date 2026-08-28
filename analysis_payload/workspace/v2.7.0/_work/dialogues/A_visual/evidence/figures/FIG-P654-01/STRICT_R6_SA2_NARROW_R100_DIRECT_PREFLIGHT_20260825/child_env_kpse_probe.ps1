param(
    [Parameter(Mandatory = $true)][string]$RootPath,
    [Parameter(Mandatory = $true)][string]$CachePath,
    [Parameter(Mandatory = $true)][string]$OutputJsonPath
)

$ErrorActionPreference = 'Stop'
$nativeOutputEncoding = [System.Text.Encoding]::GetEncoding(936)
[Console]::OutputEncoding = $nativeOutputEncoding
$OutputEncoding = $nativeOutputEncoding
$kpseCommand = Get-Command kpsewhich.exe -ErrorAction Stop
$expectedEnvValue = $CachePath.TrimEnd('\', '/')
$expectedPath = [System.IO.Path]::GetFullPath($CachePath).TrimEnd('\', '/')

function Invoke-KpseValue {
    param(
        [Parameter(Mandatory = $true)][string]$VariableName
    )
    $valueOutput = @(& $kpseCommand.Source ('--var-value=' + $VariableName) 2>&1)
    $valueExit = $LASTEXITCODE
    $expandArgument = '--expand-var=$' + $VariableName
    $expandOutput = @(& $kpseCommand.Source $expandArgument 2>&1)
    $expandExit = $LASTEXITCODE
    $valueText = (($valueOutput | ForEach-Object { [string]$_ }) -join "`n").Trim()
    $expandText = (($expandOutput | ForEach-Object { [string]$_ }) -join "`n").Trim()
    $valueCanonical = if ($valueText) { [System.IO.Path]::GetFullPath($valueText).TrimEnd('\', '/') } else { '' }
    $expandCanonical = if ($expandText) { [System.IO.Path]::GetFullPath($expandText).TrimEnd('\', '/') } else { '' }
    [ordered]@{
        variable = $VariableName
        env_visible_value = [Environment]::GetEnvironmentVariable($VariableName, 'Process')
        kpsewhich_executable = $kpseCommand.Source
        var_value_exit = $valueExit
        var_value_raw = $valueText
        var_value_canonical = $valueCanonical
        var_value_exact_expected = ($valueText -ceq $expectedEnvValue)
        var_value_canonical_expected = ($valueCanonical -ceq $expectedPath)
        expand_exit = $expandExit
        expand_raw = $expandText
        expand_canonical = $expandCanonical
        expand_exact_expected = ($expandText -ceq $expectedEnvValue)
        expand_canonical_expected = ($expandCanonical -ceq $expectedPath)
    }
}

$probePath = Join-Path $expectedPath 'P654_R6_CHILD_WRITE_PROBE.txt'
$probeExistedBefore = Test-Path -LiteralPath $probePath
$probeContent = "P654_R6_CHILD_WRITE_PROBE`nCHILD_PID=$PID`n"
[System.IO.File]::WriteAllText($probePath, $probeContent, [System.Text.UTF8Encoding]::new($false))
$probeItem = Get-Item -LiteralPath $probePath
$probeHash = Get-FileHash -Algorithm SHA256 -LiteralPath $probePath

$kpseRows = @(
    Invoke-KpseValue -VariableName 'TEXMFVAR'
    Invoke-KpseValue -VariableName 'TEXMFCACHE'
    Invoke-KpseValue -VariableName 'TEXMFCONFIG'
)
$cacheEntries = @(Get-ChildItem -LiteralPath $expectedPath -Force)
$allPass = (
    $kpseRows.Count -eq 3 -and
    @($kpseRows | Where-Object {
        $_.env_visible_value -cne $expectedEnvValue -or
        $_.var_value_exit -ne 0 -or -not $_.var_value_exact_expected -or
        $_.expand_exit -ne 0 -or -not $_.expand_exact_expected
    }).Count -eq 0 -and
    $cacheEntries.Count -eq 1 -and
    $cacheEntries[0].FullName -ceq $probeItem.FullName
)

$result = [ordered]@{
    child_process = [ordered]@{
        pid = $PID
        executable = (Get-Process -Id $PID).Path
        powershell_version = $PSVersionTable.PSVersion.ToString()
        process_architecture = if ([Environment]::Is64BitProcess) { '64-bit' } else { '32-bit' }
    }
    root_path = [System.IO.Path]::GetFullPath($RootPath)
    expected_environment_value = $expectedEnvValue
    expected_texcache = $expectedPath
    environment = [ordered]@{
        TEXMFVAR = [Environment]::GetEnvironmentVariable('TEXMFVAR', 'Process')
        TEXMFCACHE = [Environment]::GetEnvironmentVariable('TEXMFCACHE', 'Process')
        TEXMFCONFIG = [Environment]::GetEnvironmentVariable('TEXMFCONFIG', 'Process')
    }
    kpsewhich = $kpseRows
    probe = [ordered]@{
        absolute_path = $probeItem.FullName
        bytes = $probeItem.Length
        mtime_utc = $probeItem.LastWriteTimeUtc.ToString('o')
        mtime_ticks_utc = $probeItem.LastWriteTimeUtc.Ticks
        sha256 = $probeHash.Hash
        existed_before_this_attempt = $probeExistedBefore
    }
    texcache_entry_count_after_probe = $cacheEntries.Count
    texcache_entries = @($cacheEntries | ForEach-Object { $_.FullName })
    forbidden_tex_engines_invoked_by_script = @()
    pass = $allPass
}

[System.IO.File]::WriteAllText(
    $OutputJsonPath,
    ($result | ConvertTo-Json -Depth 12) + "`n",
    [System.Text.UTF8Encoding]::new($false)
)
'CHILD_PREFLIGHT_JSON_WRITTEN'
if (-not $allPass) {
    exit 2
}
