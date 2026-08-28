[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$workspaceRoot = (Resolve-Path -LiteralPath (Join-Path $projectRoot '..')).Path
$outputPath = Join-Path $projectRoot 'manifests\H0_input_sha256.txt'

if (Test-Path -LiteralPath $outputPath) {
    throw "H0 already exists and must not be regenerated: $outputPath"
}

function Resolve-UniqueInput {
    param(
        [Parameter(Mandatory = $true)][string]$Directory,
        [Parameter(Mandatory = $true)][string]$Filter,
        [Parameter(Mandatory = $true)][long]$ExpectedLength
    )

    $matches = @(Get-ChildItem -LiteralPath $Directory -File -Filter $Filter |
        Where-Object { $_.Length -eq $ExpectedLength })
    if ($matches.Count -ne 1) {
        throw "Expected one H0 input in $Directory matching $Filter and $ExpectedLength bytes; found $($matches.Count)."
    }
    return $matches[0].FullName
}

# Keep this script ASCII-only so Windows PowerShell 5.1 cannot misdecode source
# literals.  The byte lengths are fixed identity selectors for the six inputs;
# the manifest still records the resolved Unicode paths and their SHA-256 values.
$inputs = @(
    [pscustomobject]@{ Role = 'baseline_pdf'; Path = Resolve-UniqueInput (Join-Path $workspaceRoot 'v1.9.0') '*.pdf' 10749343 }
    [pscustomobject]@{ Role = 'selected_source_archive'; Path = Join-Path $workspaceRoot 'v1.9.0\release\latex_source_v1.9.0.zip' }
    [pscustomobject]@{ Role = 'audit_report'; Path = Resolve-UniqueInput $workspaceRoot '*.md' 41214 }
    [pscustomobject]@{ Role = 'audit_workbook'; Path = Resolve-UniqueInput $workspaceRoot '*.xlsx' 254830 }
    [pscustomobject]@{ Role = 'visual_reference_pdf'; Path = Resolve-UniqueInput $workspaceRoot '*.pdf' 431726 }
    [pscustomobject]@{ Role = 'workbook_overview_png'; Path = Resolve-UniqueInput $workspaceRoot '*.png' 385924 }
)

foreach ($input in $inputs) {
    if (-not (Test-Path -LiteralPath $input.Path -PathType Leaf)) {
        throw "H0 input missing: $($input.Path)"
    }
}

$timestamp = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
$lines = [System.Collections.Generic.List[string]]::new()
$lines.Add('# H0 input freeze (SHA-256)')
$lines.Add("# event=H0 execution=1 generated_utc=$timestamp")
$lines.Add('# Do not regenerate unless an immutable input is proven corrupted or the user explicitly changes the input set.')

foreach ($input in $inputs) {
    $item = Get-Item -LiteralPath $input.Path
    $digest = (Get-FileHash -Algorithm SHA256 -LiteralPath $item.FullName).Hash.ToLowerInvariant()
    $lines.Add(('{0}  {1}  {2}  {3}' -f $digest, $item.Length, $input.Role, $item.FullName))
}

[System.IO.File]::WriteAllLines($outputPath, $lines, [System.Text.UTF8Encoding]::new($false))
Write-Output "H0_ENTRIES=$($inputs.Count)"
Write-Output "H0_OUTPUT=$outputPath"
