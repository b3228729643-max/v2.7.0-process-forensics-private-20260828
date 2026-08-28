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
    @{ File = 'V5-C07.tex'; Label = 'exm:V5-C07-damped-four' },
    @{ File = 'V5-C07.tex'; Label = 'exm:V5-C07-power-three' },
    @{ File = 'V5-C08.tex'; Label = 'exm:V5-C08-two-candidate-selection' },
    @{ File = 'V5-C08.tex'; Label = 'exm:V5-C08-lsa-shape' },
    @{ File = 'V5-C08.tex'; Label = 'exm:V5-C08-holdout' }
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
    $displayOpen = [regex]::Matches($body, [regex]::Escape('\[')).Count
    $displayClose = [regex]::Matches($body, [regex]::Escape('\]')).Count
    if ($displayOpen -ne $displayClose) {
        throw "display math delimiter imbalance: $($target.Label) $displayOpen/$displayClose"
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

$combined = ($cache.Values -join "`n")
if ($combined -match '0\.3877,0\.2149,0\.3974' -or $combined -match '0\.3877897') {
    throw 'uncertified 36.4 approximate vector remains'
}
if (-not $combined.Contains('\mathbb E\!\left[\min_K\widehat R_K\mid\mathcal D_{\rm dev}\right]')) {
    throw '37.4 conditional minimum-risk check missing'
}
if (-not $combined.Contains('上述取等边界表明不能把它表述为无例外的严格不等式')) {
    throw '37.4 non-strict equality boundary missing'
}
if (-not $combined.Contains('K_\star\in\arg\min_K R(f_K)')) {
    throw '37.4 left equality boundary missing'
}
if (-not $combined.Contains('\mathbb P\!\left(\widehat K\in\arg\min_K R(f_K)\mid\mathcal D_{\rm dev}\right)=1')) {
    throw '37.4 right equality boundary missing'
}

if ($stageTotal -ne 35) {
    throw "stage total failure: $stageTotal"
}

Write-Output 'P08_STATIC=PASS'
Write-Output 'TARGET_SOLUTIONS=5'
Write-Output "STAGE_MACROS=$stageTotal/35"
Write-Output 'TARGET_LABELS_AND_HEADINGS=5/5'
Write-Output 'TARGET_NESTED_RUNNING_EXAMPLE=0'
Write-Output 'ENVIRONMENT_STACKS=BALANCED'
Write-Output 'HANDWRITTEN_CHECK_ANSWER_HEADINGS=0'
Write-Output 'TARGET_DISPLAY_MATH=BALANCED'
Write-Output 'UNCERTIFIED_36_4_APPROX=0'
Write-Output 'HOLDOUT_CONDITIONAL_BOUNDARY=PASS'
Write-Output 'HOLDOUT_EQUALITY_BOUNDARIES=PASS'
