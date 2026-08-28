[CmdletBinding()]
param(
    [ValidateSet('template-contract', 'stage07-full')]
    [string]$Stage = 'template-contract',
    [switch]$WriteResults
)

$ErrorActionPreference = 'Stop'
$root = [System.IO.Path]::GetFullPath($PSScriptRoot)
$pythonCommand = Get-Command python.exe -ErrorAction SilentlyContinue
if (-not $pythonCommand) {
    $pythonCommand = Get-Command python -ErrorAction SilentlyContinue
}
if (-not $pythonCommand) {
    throw 'Python was not found on PATH.'
}
$python = $pythonCommand.Source
$generatorMatches = @(Get-ChildItem -LiteralPath $root -Recurse -File -Filter 'stage07_generate_latex_skeleton.py' | Sort-Object { $_.FullName.Length })
$checklistMatches = @(Get-ChildItem -LiteralPath $root -Recurse -File -Filter 'build_chapter_template_checklist.py' | Sort-Object { $_.FullName.Length })
$validatorMatches = @(Get-ChildItem -LiteralPath $root -Recurse -File -Filter 'validate_stage07.py' | Sort-Object { $_.FullName.Length })
if ($generatorMatches.Count -lt 1 -or $checklistMatches.Count -lt 1 -or $validatorMatches.Count -lt 1) {
    throw 'Stage-07 generator, checklist builder, or validator is missing.'
}
$generator = $generatorMatches[0].FullName
$checklist = $checklistMatches[0].FullName
$validator = $validatorMatches[0].FullName

function Invoke-CheckedPython {
    param([Parameter(Mandatory = $true)][string[]]$Arguments)
    & $python @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Validation command failed ($LASTEXITCODE): python $($Arguments -join ' ')"
    }
}

Push-Location -LiteralPath $root
try {
    if ($Stage -eq 'template-contract') {
        # This default route only reads public LaTeX/schema/checklist artifacts.
        # It intentionally never scans or hashes the original textbook PDF.
        Invoke-CheckedPython -Arguments @($generator, '--self-test')
        Invoke-CheckedPython -Arguments @($generator, '--verify-contracts-only')
        Invoke-CheckedPython -Arguments @($checklist, '--self-test')
        Invoke-CheckedPython -Arguments @($checklist, '--check')
        $validatorArgs = @($validator, '--contract-only')
        if (-not $WriteResults) { $validatorArgs += '--no-write' }
        Invoke-CheckedPython $validatorArgs
        [ordered]@{
            result = 'PASS'
            stage = 'template-contract'
            writes_results = [bool]$WriteResults
            original_pdf_access = $false
        } | ConvertTo-Json
        exit 0
    }

    # The full historical gate is opt-in because it revalidates upstream
    # artifacts and may read the original PDF.  It still never regenerates it.
    $fullArgs = @($validator)
    if (-not $WriteResults) { $fullArgs += '--no-write' }
    Invoke-CheckedPython $fullArgs
    [ordered]@{
        result = 'PASS'
        stage = 'stage07-full'
        writes_results = [bool]$WriteResults
        original_pdf_access = 'read-only verification may occur'
    } | ConvertTo-Json
} finally {
    Pop-Location
}
