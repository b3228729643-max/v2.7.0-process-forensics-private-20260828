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
    @{ File = 'V4-C02.tex'; Label = 'exm:V4-C02-five-points' },
    @{ File = 'V4-C03.tex'; Label = 'exm:V4-C03-tall' },
    @{ File = 'V4-C04.tex'; Label = 'exm:V4-C04-pca-projection' },
    @{ File = 'V4-C05.tex'; Label = 'exm:V4-C05-one-nmf-step' },
    @{ File = 'V5-C01.tex'; Label = 'exm:V5-C01-stationary-reversible' },
    @{ File = 'V5-C01.tex'; Label = 'exm:V5-C01-two-state-audit' },
    @{ File = 'V5-C02.tex'; Label = 'exm:V5-C02-four-uniforms' },
    @{ File = 'V5-C02.tex'; Label = 'exm:V5-C02-mc-audit' },
    @{ File = 'V5-C03.tex'; Label = 'exm:V5-C03-asymmetric-proposal' },
    @{ File = 'V5-C03.tex'; Label = 'exm:V5-C03-three-state-kernel' }
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
    if ([regex]::Matches($text, '\\label\{' + $labelPattern + '\}').Count -ne 1) {
        throw "target label definition count failure: $($target.Label)"
    }
    $pattern = '(?s)\\SLExampleSolutionHeading\{' + $labelPattern + '\}\s*\\begin\{solution\}(?<body>.*?)\\end\{solution\}'
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
    if ($body -match '\\textbf\{(?:独立核验|结论)。\}') {
        throw "handwritten check/answer heading remains: $($target.Label)"
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

if ($stageTotal -ne 70) {
    throw "stage total failure: $stageTotal"
}

Write-Output 'P06_STATIC=PASS'
Write-Output 'TARGET_SOLUTIONS=10'
Write-Output "STAGE_MACROS=$stageTotal/70"
Write-Output 'TARGET_LABELS_AND_HEADINGS=10/10'
Write-Output 'TARGET_NESTED_RUNNING_EXAMPLE=0'
Write-Output 'ENVIRONMENT_STACKS=BALANCED'
Write-Output 'HANDWRITTEN_CHECK_ANSWER_HEADINGS=0'
