[CmdletBinding()]
param(
    [ValidateSet('demo', 'volume1', 'volume2', 'volume3', 'volume4', 'volume5', 'merged', 'merged_student', 'merged_full')]
    [string]$Target = 'demo',
    [ValidateSet('lualatex', 'xelatex')]
    [string]$Engine = 'lualatex',
    [string]$Source,
    [string]$OutputDir,
    [switch]$Resume,
    [switch]$DryRun
)

$ErrorActionPreference = 'Stop'
$root = [System.IO.Path]::GetFullPath($PSScriptRoot)
$rootPrefix = $root.TrimEnd('\') + '\'
$projectRoot = [System.IO.Directory]::GetParent($root).FullName
$releaseVersionPath = Join-Path $projectRoot 'manifests\release_version.tex'
if (-not (Test-Path -LiteralPath $releaseVersionPath -PathType Leaf)) {
    throw "Missing authoritative release-version file: $releaseVersionPath"
}
$releaseVersionSource = Get-Content -LiteralPath $releaseVersionPath -Raw -Encoding UTF8
$releaseVersionMatch = [regex]::Match($releaseVersionSource, '\\newcommand\{\\SLReleaseVersion\}\{(?<version>v\d+\.\d+\.\d+)\}')
if (-not $releaseVersionMatch.Success) {
    throw 'release_version.tex must define \newcommand{\SLReleaseVersion}{vX.Y.Z}.'
}
$releaseVersion = $releaseVersionMatch.Groups['version'].Value

function Resolve-WorkspacePath {
    param([Parameter(Mandatory = $true)][string]$PathValue)
    $candidate = if ([System.IO.Path]::IsPathRooted($PathValue)) {
        [System.IO.Path]::GetFullPath($PathValue)
    } else {
        [System.IO.Path]::GetFullPath((Join-Path $root $PathValue))
    }
    if (-not $candidate.StartsWith($rootPrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing path outside workspace: $candidate"
    }
    return $candidate
}

$sourceRoots = @(Get-ChildItem -LiteralPath $root -Directory | Where-Object {
    Test-Path -LiteralPath (Join-Path $_.FullName 'common\statlearnbook.sty') -PathType Leaf
})
if ($sourceRoots.Count -ne 1) {
    throw "Expected one LaTeX source root, found $($sourceRoots.Count)."
}
$sourceRoot = $sourceRoots[0].FullName

function Find-VolumeMain {
    param([Parameter(Mandatory = $true)][string]$TwoDigitNumber)
    $matches = @(Get-ChildItem -LiteralPath $sourceRoot -Directory | Where-Object {
        $_.Name -match $TwoDigitNumber -and (Test-Path -LiteralPath (Join-Path $_.FullName 'main.tex') -PathType Leaf)
    })
    if ($matches.Count -ne 1) {
        throw "Expected one volume $TwoDigitNumber main.tex, found $($matches.Count)."
    }
    return (Join-Path $matches[0].FullName 'main.tex')
}

$volumeMains = @{}
1..5 | ForEach-Object {
    $key = "volume$_"
    $volumeMains[$key] = Find-VolumeMain -TwoDigitNumber ('{0:D2}' -f $_)
}
$mergedMatches = @(Get-ChildItem -LiteralPath $sourceRoot -Directory | Where-Object {
    $_.Name -notmatch '0[1-5]' -and (Test-Path -LiteralPath (Join-Path $_.FullName 'main.tex') -PathType Leaf)
})
if ($mergedMatches.Count -ne 1) {
    throw "Expected one merged main.tex, found $($mergedMatches.Count)."
}
$mergedRoot = $mergedMatches[0].FullName
$targets = @{
    demo    = (Join-Path $sourceRoot 'common\template_demo.tex')
    volume1 = $volumeMains['volume1']
    volume2 = $volumeMains['volume2']
    volume3 = $volumeMains['volume3']
    volume4 = $volumeMains['volume4']
    volume5 = $volumeMains['volume5']
    merged         = (Join-Path $mergedRoot 'main.tex')
    merged_student = (Join-Path $mergedRoot 'main_student.tex')
    merged_full    = (Join-Path $mergedRoot 'main_full.tex')
}

$sourceValue = if ($Source) { $Source } else { $targets[$Target] }
$sourcePath = Resolve-WorkspacePath -PathValue $sourceValue
if (-not $sourcePath.EndsWith('.tex', [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "Build source must be a .tex file: $sourcePath"
}
if (-not (Test-Path -LiteralPath $sourcePath -PathType Leaf)) {
    throw "Build source does not exist: $sourcePath"
}

$defaultDemoMatches = @(Get-ChildItem -LiteralPath $root -Recurse -Directory -Filter 'stage07_demo' -ErrorAction SilentlyContinue)
$defaultOutput = if ($Target -eq 'demo' -and -not $Source -and $defaultDemoMatches.Count -eq 1) {
    $defaultDemoMatches[0].FullName
} else {
    Join-Path $root "build-output\$Target"
}
$outputPath = Resolve-WorkspacePath -PathValue $(if ($OutputDir) { $OutputDir } else { $defaultOutput })
if ($outputPath.Equals($root, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw 'Refusing to use workspace root as a build output directory.'
}

function Get-IncludeOutputDirectories {
    param(
        [Parameter(Mandatory = $true)][string]$SourcePath,
        [Parameter(Mandatory = $true)][string]$OutputPath
    )
    $sourceText = Get-Content -LiteralPath $SourcePath -Raw -Encoding UTF8
    $outputPrefix = $OutputPath.TrimEnd('\') + '\'
    $directories = @()
    foreach ($match in [regex]::Matches($sourceText, '\\include\s*\{([^{}]+)\}')) {
        $includeValue = $match.Groups[1].Value.Trim().Replace('/', '\')
        if ([System.IO.Path]::IsPathRooted($includeValue)) {
            throw "Refusing rooted include path: $includeValue"
        }
        $relativeDirectory = [System.IO.Path]::GetDirectoryName($includeValue)
        if ([string]::IsNullOrWhiteSpace($relativeDirectory)) {
            continue
        }
        $candidate = [System.IO.Path]::GetFullPath((Join-Path $OutputPath $relativeDirectory))
        if (-not $candidate.StartsWith($outputPrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
            throw "Refusing include output directory outside build output: $candidate"
        }
        $directories += $candidate
    }
    return @($directories | Sort-Object -Unique)
}

$includeOutputDirs = @(Get-IncludeOutputDirectories -SourcePath $sourcePath -OutputPath $outputPath)

$onPath = Get-Command latexmk.exe -ErrorAction SilentlyContinue
$latexmk = if ($onPath) { $onPath.Source } else { $null }
if (-not $latexmk) {
    throw 'latexmk.exe was not found on PATH. Add the selected TeX distribution bin directory to PATH.'
}

$sourceItem = Get-Item -LiteralPath $sourcePath
$stagingName = '.slbuild-' + $Target + '-' + $Engine
$stagingPath = Join-Path $sourceItem.Directory.FullName $stagingName
$latexArgs = @("-$Engine")
if (-not $Resume) {
    $latexArgs += '-g'
}
$latexArgs += @(
    '-interaction=nonstopmode',
    '-halt-on-error',
    '-file-line-error',
    "-outdir=$stagingName",
    $sourceItem.Name
)
$plan = [ordered]@{
    target = $Target
    release_version = $releaseVersion
    source = $sourcePath
    working_directory = $sourceItem.Directory.FullName
    output_directory = $outputPath
    latex_staging_directory = $stagingPath
    latexmk = $latexmk
    tex_engine = $Engine
    arguments = $latexArgs
    output_include_directories = $includeOutputDirs
    original_pdf_access = $false
    destructive_clean = $false
    resume_existing_staging = [bool]$Resume
}

if ($DryRun) {
    $plan | ConvertTo-Json -Depth 4
    exit 0
}

New-Item -ItemType Directory -Path $outputPath -Force | Out-Null
New-Item -ItemType Directory -Path $stagingPath -Force | Out-Null
foreach ($includeOutputDir in $includeOutputDirs) {
    New-Item -ItemType Directory -Path $includeOutputDir -Force | Out-Null
}
$previousTexmfCache = $env:TEXMFCACHE
$previousTexmfVar = $env:TEXMFVAR
if ($Engine -eq 'lualatex') {
    # luaotfload requires a writable cache.  Use a disposable ASCII-only temp
    # path instead of a possibly read-only user-profile cache.
    # Kpathsea on this Windows host cannot round-trip the workspace's CJK
    # path through its legacy code page.  An ASCII-named temporary cache is
    # therefore used; all actual source, logs and PDFs remain in the current
    # workspace and the cache is not part of the release package.
    $portableTexmfCache = Join-Path ([System.IO.Path]::GetTempPath()) "statlearn-$releaseVersion-texmf-cache"
    New-Item -ItemType Directory -Path $portableTexmfCache -Force | Out-Null
    $env:TEXMFCACHE = $portableTexmfCache
    $env:TEXMFVAR = $portableTexmfCache
}
Push-Location -LiteralPath $sourceItem.Directory.FullName
try {
    & $latexmk @latexArgs
    if ($LASTEXITCODE -ne 0) {
        throw "$Engine build failed with exit code $LASTEXITCODE."
    }
} finally {
    Pop-Location
    if ($Engine -eq 'lualatex') {
        if ($null -eq $previousTexmfCache) {
            Remove-Item Env:TEXMFCACHE -ErrorAction SilentlyContinue
        } else {
            $env:TEXMFCACHE = $previousTexmfCache
        }
        if ($null -eq $previousTexmfVar) {
            Remove-Item Env:TEXMFVAR -ErrorAction SilentlyContinue
        } else {
            $env:TEXMFVAR = $previousTexmfVar
        }
    }
}

$stagedOutputs = @(Get-ChildItem -LiteralPath $stagingPath -File)
foreach ($stagedOutput in $stagedOutputs) {
    Copy-Item -LiteralPath $stagedOutput.FullName -Destination $outputPath -Force
}
$pdfPath = Join-Path $outputPath ($sourceItem.BaseName + '.pdf')
if (-not (Test-Path -LiteralPath $pdfPath -PathType Leaf)) {
    throw "Build reported success but PDF is missing: $pdfPath"
}
[ordered]@{
    result = 'PASS'
    pdf = $pdfPath
    bytes = (Get-Item -LiteralPath $pdfPath).Length
    original_pdf_access = $false
} | ConvertTo-Json
