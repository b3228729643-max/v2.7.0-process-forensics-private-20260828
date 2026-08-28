Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$paths=@(
'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\P126_R6_STATIC_SEAL_CONTROLLER_20260828.ps1',
'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\P126_R6_STATIC_SEAL_AUDITOR_20260828.ps1')
foreach($path in $paths){$tokens=$null;$errors=$null;[Management.Automation.Language.Parser]::ParseFile($path,[ref]$tokens,[ref]$errors)|Out-Null;[pscustomobject]@{path=$path;bytes=(Get-Item -LiteralPath $path).Length;sha256=(Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash;ast_errors=@($errors).Count;error_messages=@($errors|ForEach-Object{$_.Message});move_sites=@(Select-String -LiteralPath $path -Pattern 'Move-Item').Count;remove_sites=@(Select-String -LiteralPath $path -Pattern 'Remove-Item').Count;tex_sites=@(Select-String -LiteralPath $path -Pattern 'lualatex|latexmk|luatex|luahbtex').Count}|ConvertTo-Json -Depth 5}
