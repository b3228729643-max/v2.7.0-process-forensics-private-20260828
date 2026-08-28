param(
    [Parameter(Mandatory = $true)] [string] $Path1,
    [Parameter(Mandatory = $true)] [string] $Path2
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$results = [System.Collections.Generic.List[object]]::new()
$totalErrors = 0
foreach ($path in @($Path1, $Path2)) {
    $tokens = $null
    $errors = $null
    $null = [System.Management.Automation.Language.Parser]::ParseFile($path, [ref]$tokens, [ref]$errors)
    $totalErrors += @($errors).Count
    $results.Add([pscustomobject]@{
        path = [System.IO.Path]::GetFullPath($path)
        ast_error_count = @($errors).Count
        ast_errors = @($errors | ForEach-Object {
            [pscustomobject]@{
                message = $_.Message
                line = $_.Extent.StartLineNumber
                column = $_.Extent.StartColumnNumber
                text = $_.Extent.Text
            }
        })
        token_count = @($tokens).Count
        bytes = (Get-Item -LiteralPath $path -Force).Length
        sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $path).Hash
    })
}
$results | ConvertTo-Json -Depth 8
if ($totalErrors -ne 0) { exit 1 }
