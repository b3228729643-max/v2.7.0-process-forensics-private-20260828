#requires -Version 7.0
[CmdletBinding()]
param()
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$handoff = 'A-R115-P126-SA2-DIRECT-BUILD-R3-20260828'
$root = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\STRICT_R3_SA2_COORDINATE_QUADRATIC_PATCH_R115_DIRECT_BUILD_20260828'
$source = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_A_visual\src\绘图源码\第01册_数学基础与统计学习基本理论\V1-C08\fig_v1_c08_coordinate.tex'
$wrapper = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_A_visual\src\讲义源码\合并总册\v260_FIG-P126-01_standalone.tex'
$engine = 'D:\texlive\2026\bin\windows\lualatex.exe'
$build = [IO.Path]::Combine($root,'build')
$texcache = [IO.Path]::Combine($root,'texcache')
$utf8 = [Text.UTF8Encoding]::new($false)
function Sha([string]$Path) { (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToUpperInvariant() }
function Identity([string]$Path) { $i=Get-Item -LiteralPath $Path -Force; [ordered]@{path=$i.FullName;bytes=[int64]$i.Length;sha256=Sha $i.FullName;last_write_time_utc_ticks=[int64]$i.LastWriteTimeUtc.Ticks} }
function Write-Json([string]$Path,$Value) { [IO.File]::WriteAllText($Path,(($Value|ConvertTo-Json -Depth 10)+"`n"),$utf8) }
function Assert-Identity($Identity,[int64]$Bytes,[string]$Hash,[string]$Name) { if ($Identity.bytes -ne $Bytes -or $Identity.sha256 -cne $Hash) { throw "$Name identity mismatch." } }
function Process-Counts { $names=@('latexmk','lualatex','luatex','luahbtex');$o=[ordered]@{};foreach($name in $names){$o[$name]=@(Get-Process -Name $name -ErrorAction SilentlyContinue).Count};$o }

$controllerStart = [DateTime]::UtcNow
$controllerBefore = Identity $PSCommandPath
if (Test-Path -LiteralPath $root) { throw 'Build root already exists.' }
$sourceBefore = Identity $source
$wrapperBefore = Identity $wrapper
$engineBefore = Identity $engine
Assert-Identity $sourceBefore 4224 '366C905854F0F3952225600D5BD66AAB706B637A453FD23DDF9611E4C002AC20' 'source'
Assert-Identity $wrapperBefore 395 '706312FAED4A825F61E1517AFFFC852369845F9DAEA051B6E8FEB99335998124' 'wrapper'
Assert-Identity $engineBefore 6656 'CC944A1DB010B47FCF5CCB5D1B184CBA208FE7FEA9F18BEC414940E6FD3E24A6' 'engine'
$preCounts = Process-Counts
if (($preCounts['latexmk'] + $preCounts['lualatex'] + $preCounts['luatex'] + $preCounts['luahbtex']) -ne 0) { throw 'TeX preflight is nonzero.' }

[void](New-Item -ItemType Directory -Path $root)
[void](New-Item -ItemType Directory -Path $build)
foreach($name in @('var','cache','config','home')) { [void](New-Item -ItemType Directory -Path ([IO.Path]::Combine($texcache,$name)) -Force) }

$psi = [Diagnostics.ProcessStartInfo]::new()
$psi.FileName = $engine
$psi.WorkingDirectory = [IO.Path]::GetDirectoryName($wrapper)
$psi.UseShellExecute = $false
$psi.CreateNoWindow = $true
$psi.RedirectStandardOutput = $true
$psi.RedirectStandardError = $true
$psi.StandardOutputEncoding = $utf8
$psi.StandardErrorEncoding = $utf8
$psi.ArgumentList.Add('-interaction=nonstopmode')
$psi.ArgumentList.Add('-halt-on-error')
$psi.ArgumentList.Add('-file-line-error')
$psi.ArgumentList.Add('-no-shell-escape')
$psi.ArgumentList.Add("-output-directory=$build")
$psi.ArgumentList.Add($wrapper)
$psi.Environment['TEXMFVAR'] = [IO.Path]::Combine($texcache,'var')
$psi.Environment['TEXMFCACHE'] = [IO.Path]::Combine($texcache,'cache')
$psi.Environment['TEXMFCONFIG'] = [IO.Path]::Combine($texcache,'config')
$psi.Environment['TEXMFHOME'] = [IO.Path]::Combine($texcache,'home')

$childStart = [DateTime]::UtcNow
$process = [Diagnostics.Process]::new()
$process.StartInfo = $psi
$started = $process.Start()
if (-not $started) { throw 'LuaLaTeX child did not start.' }
$childPid = $process.Id
$startRecord = [ordered]@{handoff_id=$handoff;controller_pid=$PID;child_pid=$childPid;controller_start_utc=$controllerStart.ToString('o');child_start_utc=$childStart.ToString('o');controller_invocation_count=1;typeset_invocation_count=1;retry_count=0;latexmk_count=0;version_probe_count=0;source_before=$sourceBefore;wrapper_before=$wrapperBefore;engine_before=$engineBefore;preflight_process_counts=$preCounts;working_directory=$psi.WorkingDirectory;output_directory=$build;texmfvar=$psi.Environment['TEXMFVAR'];texmfcache=$psi.Environment['TEXMFCACHE'];texmfconfig=$psi.Environment['TEXMFCONFIG'];texmfhome=$psi.Environment['TEXMFHOME']}
Write-Json ([IO.Path]::Combine($root,'START.json')) $startRecord
$stdoutTask = $process.StandardOutput.ReadToEndAsync()
$stderrTask = $process.StandardError.ReadToEndAsync()
$process.WaitForExit()
$process.WaitForExit()
$childEnd = [DateTime]::UtcNow
$exitCode = $process.ExitCode
$stdout = $stdoutTask.GetAwaiter().GetResult()
$stderr = $stderrTask.GetAwaiter().GetResult()
[IO.File]::WriteAllText([IO.Path]::Combine($root,'lualatex.stdout.txt'),$stdout,$utf8)
[IO.File]::WriteAllText([IO.Path]::Combine($root,'lualatex.stderr.txt'),$stderr,$utf8)

$sourceAfter = Identity $source
$wrapperAfter = Identity $wrapper
$engineAfter = Identity $engine
$controllerAfter = Identity $PSCommandPath
$pdfs = @(Get-ChildItem -LiteralPath $build -File -Filter '*.pdf' -Force)
$expectedPdf = [IO.Path]::Combine($build,'v260_FIG-P126-01_standalone.pdf')
$pdfIdentity = $null
if ($pdfs.Count -eq 1) { $pdfIdentity = Identity $pdfs[0].FullName }
$postCounts = Process-Counts
$controllerEnd = [DateTime]::UtcNow
$success = ($exitCode -eq 0 -and $pdfs.Count -eq 1 -and $pdfs[0].FullName -ceq $expectedPdf -and $sourceAfter.sha256 -ceq $sourceBefore.sha256 -and $wrapperAfter.sha256 -ceq $wrapperBefore.sha256 -and $engineAfter.sha256 -ceq $engineBefore.sha256 -and $controllerAfter.sha256 -ceq $controllerBefore.sha256 -and ($postCounts['latexmk'] + $postCounts['lualatex'] + $postCounts['luatex'] + $postCounts['luahbtex']) -eq 0)
$result = [ordered]@{handoff_id=$handoff;status=if($success){'BUILD_SUCCESS_SLOT_RELEASED'}else{'BUILD_FAIL_NO_CANDIDATE'};controller_pid=$PID;child_pid=$childPid;controller_start_utc=$controllerStart.ToString('o');child_start_utc=$childStart.ToString('o');child_end_utc=$childEnd.ToString('o');controller_end_utc=$controllerEnd.ToString('o');duration_seconds=[Math]::Round(($childEnd-$childStart).TotalSeconds,6);controller_exit=if($success){0}else{1};child_exit=$exitCode;natural_exit=$true;interrupted=$false;controller_invocation_count=1;typeset_invocation_count=1;retry_count=0;latexmk_count=0;version_probe_count=0;pdf_count=$pdfs.Count;pdf=$pdfIdentity;expected_pdf=$expectedPdf;source_before=$sourceBefore;source_after=$sourceAfter;wrapper_before=$wrapperBefore;wrapper_after=$wrapperAfter;engine_before=$engineBefore;engine_after=$engineAfter;controller_before=$controllerBefore;controller_after=$controllerAfter;postexit_process_counts=$postCounts}
Write-Json ([IO.Path]::Combine($root,'RESULT.json')) $result
$result | ConvertTo-Json -Depth 10 -Compress
if (-not $success) { exit 1 }
exit 0
