param(
    [Parameter(Mandatory = $true)][string]$ControllerPath,
    [Parameter(Mandatory = $true)][string]$AuditorPath,
    [Parameter(Mandatory = $true)][string]$OldRoot,
    [Parameter(Mandatory = $true)][string]$NewRoot,
    [Parameter(Mandatory = $true)][string]$OutputPath
)

$ErrorActionPreference = 'Stop'
$utf8NoBom = [System.Text.UTF8Encoding]::new($false)
$records = [System.Collections.Generic.List[object]]::new()
foreach ($path in @($ControllerPath, $AuditorPath, $PSCommandPath)) {
    $tokens = $null
    $errors = $null
    [System.Management.Automation.Language.Parser]::ParseFile($path, [ref]$tokens, [ref]$errors) | Out-Null
    $records.Add([pscustomobject][ordered]@{
        resolved_path = (Resolve-Path -LiteralPath $path).Path
        bytes = (Get-Item -LiteralPath $path).Length
        sha256 = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToUpperInvariant()
        ast_errors = $errors.Count
    }) | Out-Null
}
if (@($records | Where-Object { $_.ast_errors -ne 0 }).Count -ne 0) { throw 'AST parse gate failed' }
if (Test-Path -LiteralPath $NewRoot) { throw 'New root already exists' }
$oldManifest = Join-Path $OldRoot 'MANIFEST.json'
$oldWstop = Join-Path $OldRoot 'WRITE_STOPPED'
if ((Get-FileHash -LiteralPath $oldManifest -Algorithm SHA256).Hash -ne '1603663F3E6A0AEAC0AB570753100BCDF04F833A5BE04AA4BBA6CBDB85DF5B12') { throw 'Old manifest identity mismatch' }
if ((Get-FileHash -LiteralPath $oldWstop -Algorithm SHA256).Hash -ne '6EB000A064DA7D16D74E10FFA6A61A10B9E19E1EDE976348DDCF430A04BC6170') { throw 'Old WSTOP identity mismatch' }
$controllerText = Get-Content -LiteralPath $ControllerPath -Raw
$lint = [ordered]@{
    start_process_tokens = ([regex]::Matches($controllerText, 'Start-Process', 'IgnoreCase')).Count
    tex_tokens = ([regex]::Matches($controllerText, 'latexmk|lualatex|luatex|luahbtex', 'IgnoreCase')).Count
    retry_loop_tokens = ([regex]::Matches($controllerText, '\bwhile\b|\bdo\s*\{|\bfor\s*\(', 'IgnoreCase')).Count
    controller_invocation_record_exists = Test-Path -LiteralPath (Join-Path (Split-Path -Parent $ControllerPath) 'CONTROLLER_INVOCATION.json')
    controller_result_record_exists = Test-Path -LiteralPath (Join-Path (Split-Path -Parent $ControllerPath) 'CONTROLLER_RESULT.json')
}
if ($lint.start_process_tokens -ne 0 -or $lint.tex_tokens -ne 0 -or $lint.retry_loop_tokens -ne 0 -or $lint.controller_invocation_record_exists -or $lint.controller_result_record_exists) { throw 'Static no-retry/no-TeX/invocation lint failed' }
$report = [ordered]@{
    schema_version = '1.0'
    authorization = 'MAIN_R286_P632_SA1_ROOT_REJECT_ONE_CONTROL_RESEAL_AUTHORIZATION'
    preflight_utc = [DateTime]::UtcNow.ToString('o')
    pass = $true
    scripts = $records
    old_root = (Resolve-Path -LiteralPath $OldRoot).Path
    old_manifest_sha256 = (Get-FileHash -LiteralPath $oldManifest -Algorithm SHA256).Hash.ToUpperInvariant()
    old_wstop_sha256 = (Get-FileHash -LiteralPath $oldWstop -Algorithm SHA256).Hash.ToUpperInvariant()
    new_root = [IO.Path]::GetFullPath($NewRoot)
    new_root_existed = $false
    lint = $lint
    planned_controller_invocations = 1
    planned_retry_count = 0
}
$tmp = $OutputPath + '.tmp-' + [Guid]::NewGuid().ToString('N')
[IO.File]::WriteAllText($tmp, ($report | ConvertTo-Json -Depth 20), $utf8NoBom)
[IO.File]::Move($tmp, $OutputPath)
foreach ($path in @($ControllerPath, $AuditorPath, $PSCommandPath, $OutputPath)) { (Get-Item -LiteralPath $path).IsReadOnly = $true }
exit 0
