[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$outputPath = Join-Path $projectRoot 'manifests\H1_content_sha256.txt'

if (Test-Path -LiteralPath $outputPath) {
    throw "H1 already exists and must not be regenerated: $outputPath"
}

$requiredEvidence = @(
    (Join-Path $projectRoot 'manifests\H0_input_sha256.txt'),
    (Join-Path $projectRoot 'qa\gate_a_structure_dependency.md'),
    (Join-Path $projectRoot 'qa\gate_b_math_teaching.md'),
    (Join-Path $projectRoot 'qa\source_cache\gate_b_ledger_verification.json')
)
foreach ($path in $requiredEvidence) {
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
        throw "Required H1 evidence is missing: $path"
    }
}

$gitStatus = @(& git -C $projectRoot status --porcelain --untracked-files=all)
if ($LASTEXITCODE -ne 0) {
    throw 'Unable to inspect the Git worktree before H1.'
}
if ($gitStatus.Count -ne 0) {
    throw "H1 requires a clean worktree. Dirty entries: $($gitStatus -join '; ')"
}
$sourceCommit = (& git -C $projectRoot rev-parse HEAD).Trim()
if ($LASTEXITCODE -ne 0 -or $sourceCommit -notmatch '^[0-9a-f]{40}$') {
    throw 'Unable to resolve the frozen source commit before H1.'
}

$sourceRoot = Join-Path $projectRoot 'src'
$sourceFiles = @(Get-ChildItem -LiteralPath $sourceRoot -Recurse -File | Where-Object {
    $_.Extension -in '.tex', '.sty', '.json' -and
    $_.FullName.Substring($projectRoot.Length + 1) -notmatch '^src\\(qa|tests|scripts)\\'
})
$qaFiles = @(Get-ChildItem -LiteralPath (Join-Path $projectRoot 'qa') -File | Where-Object {
    ($_.Extension -eq '.xlsx' -and $_.Name -notlike '*_v2.0.0_*') -or $_.Extension -eq '.csv'
})
$figureFiles = @(Get-ChildItem -LiteralPath (Join-Path $projectRoot 'figures') -File -Filter '*.csv')

$extensionCounts = @{}
foreach ($file in $sourceFiles) {
    $extensionCounts[$file.Extension] = 1 + [int]$extensionCounts[$file.Extension]
}
if ($extensionCounts['.tex'] -ne 147 -or $extensionCounts['.sty'] -ne 1 -or $extensionCounts['.json'] -ne 38) {
    throw "Unexpected content-source inventory: tex=$($extensionCounts['.tex']) sty=$($extensionCounts['.sty']) json=$($extensionCounts['.json'])."
}
if ($qaFiles.Count -ne 6 -or $figureFiles.Count -ne 1) {
    throw "Unexpected H1 matrix inventory: qa=$($qaFiles.Count) figure=$($figureFiles.Count)."
}

$paths = [string[]]@($sourceFiles.FullName + $qaFiles.FullName + $figureFiles.FullName)
[Array]::Sort($paths, [StringComparer]::Ordinal)
if ($paths.Count -ne 193 -or @($paths | Select-Object -Unique).Count -ne 193) {
    throw "Unexpected H1 content inventory total: $($paths.Count)."
}

function Get-ProjectRelativePath {
    param([Parameter(Mandatory = $true)][string]$Path)
    $rootUri = [Uri]($projectRoot.TrimEnd('\') + '\')
    $fileUri = [Uri]$Path
    return [Uri]::UnescapeDataString($rootUri.MakeRelativeUri($fileUri).ToString()).Replace('/', '\')
}

$timestamp = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
$lines = [System.Collections.Generic.List[string]]::new()
$lines.Add('# H1 content baseline freeze (SHA-256)')
$lines.Add("# event=H1 execution=1 generated_utc=$timestamp source_commit=$sourceCommit")
$lines.Add('# Scope: authoritative lecture/style/figure sources plus content-planning matrices; build products, caches, previews, logs, state, and the mutable issue ledger are excluded.')

foreach ($path in $paths) {
    $item = Get-Item -LiteralPath $path
    $relativePath = Get-ProjectRelativePath -Path $item.FullName
    if ($relativePath -like 'src\*') {
        $role = 'authoritative_source'
    }
    elseif ($relativePath -like 'figures\*') {
        $role = 'figure_manifest'
    }
    else {
        $role = 'content_planning_matrix'
    }
    $digest = (Get-FileHash -Algorithm SHA256 -LiteralPath $item.FullName).Hash.ToLowerInvariant()
    $lines.Add(('{0}  {1}  {2}  {3}' -f $digest, $item.Length, $role, $relativePath))
}

[System.IO.File]::WriteAllLines($outputPath, $lines, [System.Text.UTF8Encoding]::new($false))
Write-Output "H1_ENTRIES=$($paths.Count)"
Write-Output "H1_SOURCE_COMMIT=$sourceCommit"
Write-Output "H1_OUTPUT=$outputPath"
