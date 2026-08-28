[CmdletBinding()]
param(
    [ValidateSet('lualatex', 'xelatex')]
    [string]$Engine = 'lualatex',
    [string]$OutputDir = 'build\final',
    [switch]$Clean,
    [switch]$Resume,
    [switch]$NoPublish,
    [switch]$DryRun
)

$ErrorActionPreference = 'Stop'
$projectRoot = [System.IO.Path]::GetFullPath($PSScriptRoot)
$projectPrefix = $projectRoot.TrimEnd('\') + '\'

function Resolve-ProjectPath {
    param([Parameter(Mandatory = $true)][string]$PathValue)
    $candidate = if ([System.IO.Path]::IsPathRooted($PathValue)) {
        [System.IO.Path]::GetFullPath($PathValue)
    } else {
        [System.IO.Path]::GetFullPath((Join-Path $projectRoot $PathValue))
    }
    if (-not $candidate.StartsWith($projectPrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing path outside project: $candidate"
    }
    if ($candidate.Equals($projectRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing project root as a generated output: $candidate"
    }
    return $candidate
}

$sourceRoot = Join-Path $projectRoot 'src'
$mainMatches = @(Get-ChildItem -LiteralPath $sourceRoot -Recurse -File -Filter 'main_full.tex')
if ($mainMatches.Count -ne 1) {
    throw "Expected one main_full.tex below src; found $($mainMatches.Count)."
}
$sourcePath = $mainMatches[0].FullName
$sourceDirectory = $mainMatches[0].Directory.FullName
$outputPath = Resolve-ProjectPath -PathValue $OutputDir

$releaseVersionPath = Join-Path $projectRoot 'manifests\release_version.tex'
if (-not (Test-Path -LiteralPath $releaseVersionPath -PathType Leaf)) {
    throw "Missing authoritative release-version file: $releaseVersionPath"
}
$releaseVersionSource = Get-Content -LiteralPath $releaseVersionPath -Raw -Encoding UTF8
$releaseVersionMatch = [regex]::Match($releaseVersionSource, '\\newcommand\{\\SLReleaseVersion\}\{(?<version>v\d+\.\d+\.\d+)\}')
if (-not $releaseVersionMatch.Success) {
    throw 'release_version.tex must define exactly one semantic version with \newcommand{\SLReleaseVersion}{vX.Y.Z}.'
}
$releaseVersion = $releaseVersionMatch.Groups['version'].Value
# Keep the script ASCII-only so Windows PowerShell 5.1 does not misdecode an
# UTF-8-without-BOM source file before it reaches the explicit UTF-8 reads.
$releasePrefix = [System.Text.Encoding]::UTF8.GetString(
    [System.Convert]::FromBase64String('57uf6K6h5a2m5Lmg5pa55rOV5Yid5a2m6ICF6K6y5LmJX+WQiOW5tuaAu+WGjA==')
)
$releaseSuffix = [System.Text.Encoding]::UTF8.GetString(
    [System.Convert]::FromBase64String('X+WujOaVtOino+aekOeJiC5wZGY=')
)
$releaseName = "${releasePrefix}${releaseVersion}${releaseSuffix}"
if ($releaseName.IndexOfAny([System.IO.Path]::GetInvalidFileNameChars()) -ge 0) {
    throw 'Derived release filename contains invalid filename characters.'
}
$releasePath = Join-Path $projectRoot $releaseName

$latexmkCommand = Get-Command latexmk.exe -ErrorAction SilentlyContinue
if (-not $latexmkCommand) {
    throw 'latexmk.exe was not found on PATH. Installations are intentionally not performed by this script.'
}
$engineCommand = Get-Command ($Engine + '.exe') -ErrorAction SilentlyContinue
if (-not $engineCommand) {
    throw "$Engine.exe was not found on PATH. Installations are intentionally not performed by this script."
}
$makeindexCommand = Get-Command makeindex.exe -ErrorAction SilentlyContinue
if (-not $makeindexCommand) {
    throw 'makeindex.exe was not found on PATH. Installations are intentionally not performed by this script.'
}

$arguments = @("-$Engine")
if (-not $Resume) {
    $arguments += '-g'
}
$arguments += @(
    '-interaction=nonstopmode',
    '-file-line-error',
    '-halt-on-error',
    "-outdir=$outputPath",
    $mainMatches[0].Name
)
$plan = [ordered]@{
    target = 'merged_full'
    release_version = $releaseVersion
    engine = $Engine
    source = $sourcePath
    working_directory = $sourceDirectory
    output_directory = $outputPath
    output_pdf = (Join-Path $outputPath 'main_full.pdf')
    release_pdf = $releasePath
    clean_generated_output = [bool]$Clean
    resume_existing_output = [bool]$Resume
    publish_release_pdf = -not [bool]$NoPublish
    latexmk = $latexmkCommand.Source
    makeindex = $makeindexCommand.Source
    arguments = $arguments
    network_required = $false
    automatic_install = $false
}

if ($DryRun) {
    $plan | ConvertTo-Json -Depth 4
    exit 0
}

if ($Clean -and (Test-Path -LiteralPath $outputPath)) {
    $resolvedOutput = [System.IO.Path]::GetFullPath($outputPath)
    $requiredPrefix = (Join-Path $projectRoot 'build').TrimEnd('\') + '\'
    if (-not $resolvedOutput.StartsWith($requiredPrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Clean is restricted to the project build directory: $resolvedOutput"
    }
    Remove-Item -LiteralPath $resolvedOutput -Recurse -Force
}
New-Item -ItemType Directory -Path $outputPath -Force | Out-Null

$previousTexmfCache = $env:TEXMFCACHE
$previousTexmfVar = $env:TEXMFVAR
if ($Engine -eq 'lualatex') {
    $portableTexmfCache = Join-Path ([System.IO.Path]::GetTempPath()) "statlearn-$releaseVersion-texmf-cache"
    New-Item -ItemType Directory -Path $portableTexmfCache -Force | Out-Null
    $env:TEXMFCACHE = $portableTexmfCache
    $env:TEXMFVAR = $portableTexmfCache
}

Push-Location -LiteralPath $sourceDirectory
try {
    & $latexmkCommand.Source @arguments
    if ($LASTEXITCODE -ne 0) {
        throw "$Engine build failed with exit code $LASTEXITCODE."
    }
} finally {
    Pop-Location
    if ($Engine -eq 'lualatex') {
        if ($null -eq $previousTexmfCache) { Remove-Item Env:TEXMFCACHE -ErrorAction SilentlyContinue } else { $env:TEXMFCACHE = $previousTexmfCache }
        if ($null -eq $previousTexmfVar) { Remove-Item Env:TEXMFVAR -ErrorAction SilentlyContinue } else { $env:TEXMFVAR = $previousTexmfVar }
    }
}

$builtPdf = Join-Path $outputPath 'main_full.pdf'
if (-not (Test-Path -LiteralPath $builtPdf -PathType Leaf)) {
    throw "latexmk returned success but the merged PDF is missing: $builtPdf"
}
if (-not $NoPublish) {
    [System.IO.File]::Copy($builtPdf, $releasePath, $true)
}

[ordered]@{
    result = 'PASS'
    release_version = $releaseVersion
    engine = $Engine
    pdf = $builtPdf
    bytes = (Get-Item -LiteralPath $builtPdf).Length
    release_pdf = $(if ($NoPublish) { $null } else { $releasePath })
    automatic_install = $false
} | ConvertTo-Json -Depth 3
