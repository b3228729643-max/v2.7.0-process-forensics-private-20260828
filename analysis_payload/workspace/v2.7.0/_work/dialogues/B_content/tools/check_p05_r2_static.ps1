param(
    [Parameter(Mandatory = $true)]
    [string]$Worktree
)

$ErrorActionPreference = 'Stop'

function Resolve-SourceFile {
    param([string]$LeafName)
    $matches = @(Get-ChildItem -LiteralPath (Join-Path $Worktree 'src') -Recurse -File -Filter $LeafName)
    if ($matches.Count -ne 1) {
        throw "source file match count $($matches.Count): $LeafName"
    }
    return $matches[0].FullName
}

$targets = @(
    @{ File = 'V1-C08.tex'; Label = 'exm:V1-C08-preconditioning' },
    @{ File = 'V1-C09.tex'; Label = 'exm:V1-C09-finite-class' },
    @{ File = 'V1-C10.tex'; Label = 'exm:V1-C10-generalization-gap' },
    @{ File = 'V2-C01.tex'; Label = 'exm:V2-C01-update' },
    @{ File = 'V2-C01.tex'; Label = 'exm:V2-C01-xor' },
    @{ File = 'V2-C02.tex'; Label = 'exm:V2-C02-original-distance' },
    @{ File = 'V2-C04.tex'; Label = 'exm:V2-C04-split-choice' },
    @{ File = 'V3-C01.tex'; Label = 'exm:V3-C01-two-groups' },
    @{ File = 'V3-C02.tex'; Label = 'exm:V3-C02-kkt-state' },
    @{ File = 'V3-C07.tex'; Label = 'exm:V3-C07-selection' }
)

$stages = @(
    '\SLReadTranslation',
    '\SolGiven',
    '\SLMethodTrigger',
    '\SolPlan',
    '\SolDerive',
    '\SolCheck',
    '\SolAnswer'
)

$cache = @{}
$stageTotal = 0
foreach ($target in $targets) {
    $path = Resolve-SourceFile $target.File
    if (-not $cache.ContainsKey($path)) {
        $cache[$path] = Get-Content -LiteralPath $path -Raw -Encoding UTF8
    }
    $text = $cache[$path]
    $labelPattern = [regex]::Escape($target.Label)
    $pattern = '(?s)\\SLExampleSolutionHeading\{' + $labelPattern + '\}\}?\s*\\begin\{solution\}(?<body>.*?)\\end\{solution\}'
    $matches = [regex]::Matches($text, $pattern)
    if ($matches.Count -ne 1) {
        throw "target solution match count $($matches.Count): $($target.Label)"
    }
    $body = $matches[0].Groups['body'].Value
    $lastIndex = -1
    foreach ($stage in $stages) {
        $stageMatches = [regex]::Matches($body, [regex]::Escape($stage) + '\b')
        if ($stageMatches.Count -ne 1) {
            throw "stage count $($stageMatches.Count): $($target.Label) $stage"
        }
        if ($stageMatches[0].Index -le $lastIndex) {
            throw "stage order failure: $($target.Label) $stage"
        }
        $lastIndex = $stageMatches[0].Index
        $stageTotal++
    }
    if ($body -match '\\begin\{SLRunningExample\}') {
        throw "nested SLRunningExample in target solution: $($target.Label)"
    }
}

foreach ($path in $cache.Keys) {
    $text = [regex]::Replace($cache[$path], '(?m)(?<!\\)%.*$', '')
    $depth = @{ solution = 0; SLRunningExample = 0 }
    $envMatches = [regex]::Matches($text, '\\(?<kind>begin|end)\{(?<name>solution|SLRunningExample)\}')
    foreach ($match in $envMatches) {
        $name = $match.Groups['name'].Value
        if ($match.Groups['kind'].Value -eq 'begin') {
            $depth[$name]++
        } else {
            $depth[$name]--
        }
        if ($depth[$name] -lt 0) {
            throw "environment stack underflow: $path $name"
        }
    }
    foreach ($name in @('solution', 'SLRunningExample')) {
        if ($depth[$name] -ne 0) {
            throw "environment stack unbalanced: $path $name depth=$($depth[$name])"
        }
    }
}

foreach ($file in @(
    'V2-C01.tex',
    'V2-C02.tex'
)) {
    $text = Get-Content -LiteralPath (Resolve-SourceFile $file) -Raw -Encoding UTF8
    $newOrder = [regex]::Matches($text, '\\Needspace\{6\\baselineskip\}\s*\\SLSourceBookExercises').Count
    $oldOrder = [regex]::Matches($text, '\\SLSourceBookExercises\s*\\Needspace\{6\\baselineskip\}').Count
    if ($newOrder -ne 1 -or $oldOrder -ne 0) {
        throw "source-book heading guard order failure: $file new=$newOrder old=$oldOrder"
    }
}

foreach ($item in @(
    @{ File = 'V3-C02.tex'; Label = 'exm:V3-C02-kkt-state' },
    @{ File = 'V3-C07.tex'; Label = 'exm:V3-C07-selection' }
)) {
    $text = Get-Content -LiteralPath (Resolve-SourceFile $item.File) -Raw -Encoding UTF8
    $linePattern = '(?m)^\{\\let\\needspace\\Needspace\\SLExampleSolutionHeading\{' + [regex]::Escape($item.Label) + '\}\}\r?$'
    if ([regex]::Matches($text, $linePattern).Count -ne 1) {
        throw "local Needspace wrapper failure: $($item.File) $($item.Label)"
    }
}

if ($stageTotal -ne 70) {
    throw "stage total failure: $stageTotal"
}

Write-Output 'P05_R2_STATIC=PASS'
Write-Output 'TARGET_SOLUTIONS=10'
Write-Output "STAGE_MACROS=$stageTotal/70"
Write-Output 'TARGET_NESTED_RUNNING_EXAMPLE=0'
Write-Output 'ENVIRONMENT_STACKS=BALANCED'
Write-Output 'SOURCE_BOOK_HEADING_GUARDS=2/2'
Write-Output 'LOCAL_NEEDSPACE_WRAPPERS=2/2'
