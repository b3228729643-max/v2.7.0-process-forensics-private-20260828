Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$HandoffId = 'C-FIG-P687-01-R115-SA2-R168-READONLY-ADJUDICATION-CONTROL-RESEAL-V1'
$Uid = 'FIG-P687-01'
$Operation = 'P687_R115_SA2_EVIDENCE_ONLY_CONTROL_RESEAL_V1'
$Verdict = 'SA2_NO_SOURCE_CHANGE_READY_FOR_FRESH_SA1'
$SourceRoot = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P687-01\sa2_r115_r168_readonly_adjudication_v1'
$NewRoot = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P687-01\sa2_r115_r168_readonly_adjudication_v1_control_reseal_v1'
$ControlRoot = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\control\P687_R115_SA2_CONTROL_RESEAL_V1'
$ArtifactRoot = Join-Path $ControlRoot 'artifacts'
$SourceBeforePath = Join-Path $ArtifactRoot 'SOURCE_ROOT_BEFORE.csv'
$PostMarkerStatePath = Join-Path $ArtifactRoot 'POSTMARKER_ROOT_STATE.csv'
$ControllerResultPath = Join-Path $ArtifactRoot 'CONTROLLER_RESULT.json'
$AuditorResultPath = Join-Path $ArtifactRoot 'AUDITOR_RESULT.json'
$OldControlNames = @('MANIFEST_CONTROL.txt', 'root_external_readonly_audit.txt', 'WSTOP')

function Write-Utf8NoBom {
    param([string]$LiteralPath, [string]$Text)
    $encoding = [System.Text.UTF8Encoding]::new($false)
    [System.IO.File]::WriteAllText($LiteralPath, $Text, $encoding)
}

function Get-Sha256 {
    param([string]$LiteralPath)
    return (Get-FileHash -LiteralPath $LiteralPath -Algorithm SHA256).Hash.ToUpperInvariant()
}

function Get-ResolvedFullPath {
    param([string]$LiteralPath)
    return [System.IO.Path]::GetFullPath($LiteralPath)
}

function ConvertTo-CanonicalRelativePath {
    param([string]$Value)
    if ([string]::IsNullOrWhiteSpace($Value)) { throw 'CANONICAL_EMPTY' }
    $canonical = $Value.Replace('\', '/')
    $canonical = [regex]::Replace($canonical, '^(?:\./)+', '')
    if ([string]::IsNullOrWhiteSpace($canonical)) { throw 'CANONICAL_EMPTY_AFTER_DOT_SLASH' }
    if ([System.IO.Path]::IsPathRooted($canonical) -or $canonical -match '^[A-Za-z]:') { throw "CANONICAL_ROOTED:$Value" }
    $segments = $canonical.Split('/')
    if ($segments.Count -eq 0) { throw "CANONICAL_NO_SEGMENTS:$Value" }
    foreach ($segment in $segments) {
        if ([string]::IsNullOrEmpty($segment)) { throw "CANONICAL_EMPTY_SEGMENT:$Value" }
        if ($segment -eq '.') { throw "CANONICAL_DOT_SEGMENT:$Value" }
        if ($segment -eq '..') { throw "CANONICAL_PARENT_SEGMENT:$Value" }
        if ($segment.Contains(':')) { throw "CANONICAL_COLON_SEGMENT:$Value" }
    }
    return [string]::Join('/', $segments)
}

function Resolve-ContainedPath {
    param([string]$Root, [string]$CanonicalRelativePath)
    $canonical = ConvertTo-CanonicalRelativePath -Value $CanonicalRelativePath
    $rootFull = [System.IO.Path]::GetFullPath($Root).TrimEnd('\', '/')
    $nativeRelative = $canonical.Replace('/', [System.IO.Path]::DirectorySeparatorChar)
    $candidate = [System.IO.Path]::GetFullPath([System.IO.Path]::Combine($rootFull, $nativeRelative))
    $prefix = $rootFull + [System.IO.Path]::DirectorySeparatorChar
    if (-not $candidate.StartsWith($prefix, [System.StringComparison]::OrdinalIgnoreCase)) { throw "PATH_ESCAPE:$canonical" }
    return $candidate
}

function Get-CanonicalRelativeFromRoot {
    param([string]$Root, [string]$LiteralPath)
    $relative = [System.IO.Path]::GetRelativePath([System.IO.Path]::GetFullPath($Root), [System.IO.Path]::GetFullPath($LiteralPath))
    return ConvertTo-CanonicalRelativePath -Value $relative
}

function Assert-CanonicalSelfTest {
    $left = @('.\top.txt', '.\nested\child.txt') | ForEach-Object { ConvertTo-CanonicalRelativePath -Value $_ }
    $right = @('top.txt', 'nested/child.txt') | ForEach-Object { ConvertTo-CanonicalRelativePath -Value $_ }
    $caseDiff = @(Compare-Object -ReferenceObject $left -DifferenceObject $right -CaseSensitive).Count
    if ($caseDiff -ne 0) { throw "CANONICAL_SELFTEST_DIFF:$caseDiff" }
    if ((ConvertTo-CanonicalRelativePath -Value '.\.\top.txt') -ne 'top.txt') { throw 'CANONICAL_MULTI_PREFIX_FAILED' }
    if ((ConvertTo-CanonicalRelativePath -Value 'Case.TXT') -ne 'Case.TXT') { throw 'CANONICAL_CASE_FAILED' }
    $invalid = @('', '/', '\rooted', 'C:\rooted', 'a//b', 'a/./b', 'a/../b', '../escape')
    $rejected = 0
    foreach ($value in $invalid) { try { $null = ConvertTo-CanonicalRelativePath -Value $value } catch { $rejected++ } }
    if ($rejected -ne $invalid.Count) { throw "CANONICAL_INVALID_REJECTED:$rejected" }
    return [ordered]@{ CASE_SENSITIVE_DIFF = $caseDiff; INVALID_REJECTED = $rejected }
}

function Get-TreeState {
    param([string]$RootPath)
    $rootItem = Get-Item -LiteralPath $RootPath -Force
    $rows = [System.Collections.Generic.List[object]]::new()
    $rows.Add([pscustomobject][ordered]@{ TYPE='ROOT'; RELATIVE_PATH='@ROOT'; RESOLVED_PATH=[System.IO.Path]::GetFullPath($rootItem.FullName); BYTES=''; SHA256=''; CREATION_FILETIME_UTC=[int64]$rootItem.CreationTimeUtc.ToFileTimeUtc(); LASTWRITE_FILETIME_UTC=[int64]$rootItem.LastWriteTimeUtc.ToFileTimeUtc(); ATTRIBUTES=[int64]$rootItem.Attributes; READONLY=(($rootItem.Attributes -band [System.IO.FileAttributes]::ReadOnly) -ne 0) })
    foreach ($directory in @(Get-ChildItem -LiteralPath $RootPath -Force -Recurse -Directory | Sort-Object FullName -CaseSensitive)) {
        $rows.Add([pscustomobject][ordered]@{ TYPE='DIRECTORY'; RELATIVE_PATH=(Get-CanonicalRelativeFromRoot -Root $RootPath -LiteralPath $directory.FullName); RESOLVED_PATH=[System.IO.Path]::GetFullPath($directory.FullName); BYTES=''; SHA256=''; CREATION_FILETIME_UTC=[int64]$directory.CreationTimeUtc.ToFileTimeUtc(); LASTWRITE_FILETIME_UTC=[int64]$directory.LastWriteTimeUtc.ToFileTimeUtc(); ATTRIBUTES=[int64]$directory.Attributes; READONLY=(($directory.Attributes -band [System.IO.FileAttributes]::ReadOnly) -ne 0) })
    }
    foreach ($file in @(Get-ChildItem -LiteralPath $RootPath -Force -Recurse -File | Sort-Object FullName -CaseSensitive)) {
        $rows.Add([pscustomobject][ordered]@{ TYPE='FILE'; RELATIVE_PATH=(Get-CanonicalRelativeFromRoot -Root $RootPath -LiteralPath $file.FullName); RESOLVED_PATH=[System.IO.Path]::GetFullPath($file.FullName); BYTES=[int64]$file.Length; SHA256=(Get-Sha256 -LiteralPath $file.FullName); CREATION_FILETIME_UTC=[int64]$file.CreationTimeUtc.ToFileTimeUtc(); LASTWRITE_FILETIME_UTC=[int64]$file.LastWriteTimeUtc.ToFileTimeUtc(); ATTRIBUTES=[int64]$file.Attributes; READONLY=$file.IsReadOnly })
    }
    return @($rows)
}

function Compare-StateRows {
    param([object[]]$Before, [object[]]$After)
    $fields = @('TYPE','RELATIVE_PATH','RESOLVED_PATH','BYTES','SHA256','CREATION_FILETIME_UTC','LASTWRITE_FILETIME_UTC','ATTRIBUTES','READONLY')
    $beforeMap = [System.Collections.Generic.Dictionary[string,string]]::new([System.StringComparer]::Ordinal)
    $afterMap = [System.Collections.Generic.Dictionary[string,string]]::new([System.StringComparer]::Ordinal)
    foreach ($row in $Before) { $key="$($row.TYPE)|$($row.RELATIVE_PATH)"; $beforeMap.Add($key,(($fields|ForEach-Object{[string]$row.$_})-join '|')) }
    foreach ($row in $After) { $key="$($row.TYPE)|$($row.RELATIVE_PATH)"; $afterMap.Add($key,(($fields|ForEach-Object{[string]$row.$_})-join '|')) }
    $mismatch=0
    foreach($key in $beforeMap.Keys){ if(-not $afterMap.ContainsKey($key)-or $beforeMap[$key]-cne $afterMap[$key]){$mismatch++} }
    foreach($key in $afterMap.Keys){ if(-not $beforeMap.ContainsKey($key)){$mismatch++} }
    return $mismatch
}

function Assert-ParseAndHygiene {
    param([string]$RootPath)
    $parseFailures=0
    foreach($csv in @(Get-ChildItem -LiteralPath $RootPath -Force -Recurse -File -Filter '*.csv')){try{$null=@(Import-Csv -LiteralPath $csv.FullName)}catch{$parseFailures++}}
    foreach($json in @(Get-ChildItem -LiteralPath $RootPath -Force -Recurse -File -Filter '*.json')){try{$null=(Get-Content -LiteralPath $json.FullName -Raw|ConvertFrom-Json)}catch{$parseFailures++}}
    if($parseFailures-ne0){throw "PARSE_FAILURES:$parseFailures"}
    $adsFailures=0
    foreach($file in @(Get-ChildItem -LiteralPath $RootPath -Force -Recurse -File)){$adsFailures+=@(Get-Item -LiteralPath $file.FullName -Stream * -ErrorAction Stop|Where-Object{$_.Stream-notin@(':$DATA','$DATA')}).Count}
    if($adsFailures-ne0){throw "ADS_FAILURES:$adsFailures"}
    $cachePyc=@(Get-ChildItem -LiteralPath $RootPath -Force -Recurse|Where-Object{$_.Name-eq'__pycache__'-or$_.Extension-eq'.pyc'-or$_.Name-match'(^|[._-])cache($|[._-])'})
    if($cachePyc.Count-ne0){throw "CACHE_PYC_FAILURES:$($cachePyc.Count)"}
    $reparse=@(Get-ChildItem -LiteralPath $RootPath -Force -Recurse|Where-Object{($_.Attributes-band[System.IO.FileAttributes]::ReparsePoint)-ne0})
    if($reparse.Count-ne0){throw "REPARSE_FAILURES:$($reparse.Count)"}
}

$selfTest=Assert-CanonicalSelfTest
if(Test-Path -LiteralPath $AuditorResultPath){throw'AUDITOR_RESULT_ALREADY_EXISTS'}
foreach($required in @($SourceBeforePath,$PostMarkerStatePath,$ControllerResultPath)){if(-not(Test-Path -LiteralPath $required -PathType Leaf)){throw "REQUIRED_EXTERNAL_ARTIFACT_MISSING:$required"}}
if(-not(Test-Path -LiteralPath $SourceRoot -PathType Container)){throw'SOURCE_ROOT_MISSING'}
if(-not(Test-Path -LiteralPath $NewRoot -PathType Container)){throw'NEW_ROOT_MISSING'}
$controllerResult=Get-Content -LiteralPath $ControllerResultPath -Raw|ConvertFrom-Json
if(-not[bool]$controllerResult.SUCCESS-or[int]$controllerResult.INVOCATION_COUNT-ne1){throw'CONTROLLER_RESULT_NOT_SUCCESS'}

$sourceBefore=@(Import-Csv -LiteralPath $SourceBeforePath)
$sourceCurrent=@(Get-TreeState -RootPath $SourceRoot)
$sourceMismatch=Compare-StateRows -Before $sourceBefore -After $sourceCurrent
if($sourceMismatch-ne0){throw "SOURCE_ROOT_MISMATCH:$sourceMismatch"}
$sourceFiles=@(Get-ChildItem -LiteralPath $SourceRoot -Force -Recurse -File)
$sourceDirs=@(Get-ChildItem -LiteralPath $SourceRoot -Force -Recurse -Directory)
if($sourceFiles.Count-ne40-or$sourceDirs.Count-ne0){throw'SOURCE_COUNT_MISMATCH'}
$controlSet=[System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::Ordinal)
foreach($name in $OldControlNames){$null=$controlSet.Add($name)}
$materialSet=[System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::Ordinal)
$controlSeen=[System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::Ordinal)
foreach($file in $sourceFiles){$rel=Get-CanonicalRelativeFromRoot -Root $SourceRoot -LiteralPath $file.FullName;if($controlSet.Contains($rel)){$null=$controlSeen.Add($rel)}else{if(-not$materialSet.Add($rel)){throw "SOURCE_MATERIAL_DUPLICATE:$rel"}}}
if($materialSet.Count-ne37-or$controlSeen.Count-ne3){throw'SOURCE_MATERIAL_CONTROL_COUNT_MISMATCH'}

$copyIdentityPath=Join-Path $NewRoot 'COPY_IDENTITY.csv'
$copyProvenancePath=Join-Path $NewRoot 'COPY_PROVENANCE.json'
$manifestPath=Join-Path $NewRoot 'PAYLOAD_MANIFEST.csv'
$sealAuditPath=Join-Path $NewRoot 'SEAL_AUDIT.json'
$markerPath=Join-Path $NewRoot 'WRITE_STOPPED'
$copyRows=@(Import-Csv -LiteralPath $copyIdentityPath)
if($copyRows.Count-ne37){throw "COPY_IDENTITY_ROWS:$($copyRows.Count)"}
$copySeen=[System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::Ordinal)
$copyMismatch=0
foreach($row in $copyRows){
    $rel=ConvertTo-CanonicalRelativePath -Value ([string]$row.RELATIVE_PATH)
    if(-not$copySeen.Add($rel)){$copyMismatch++;continue}
    if(-not$materialSet.Contains($rel)){$copyMismatch++}
    $source=Resolve-ContainedPath -Root $SourceRoot -CanonicalRelativePath $rel
    $destination=Resolve-ContainedPath -Root $NewRoot -CanonicalRelativePath $rel
    if([System.IO.Path]::GetFullPath($source)-cne[string]$row.SOURCE_RESOLVED_PATH-or[System.IO.Path]::GetFullPath($destination)-cne[string]$row.DESTINATION_RESOLVED_PATH){$copyMismatch++}
    $sourceItem=Get-Item -LiteralPath $source -Force;$destinationItem=Get-Item -LiteralPath $destination -Force
    if([int64]$sourceItem.Length-ne[int64]$row.SOURCE_BYTES-or[int64]$destinationItem.Length-ne[int64]$row.DESTINATION_BYTES-or(Get-Sha256 -LiteralPath $source)-cne[string]$row.SOURCE_SHA256-or(Get-Sha256 -LiteralPath $destination)-cne[string]$row.DESTINATION_SHA256-or[int64]$sourceItem.CreationTimeUtc.ToFileTimeUtc()-ne[int64]$row.SOURCE_CREATION_FILETIME_UTC-or[int64]$destinationItem.CreationTimeUtc.ToFileTimeUtc()-ne[int64]$row.DESTINATION_CREATION_FILETIME_UTC-or[int64]$sourceItem.LastWriteTimeUtc.ToFileTimeUtc()-ne[int64]$row.SOURCE_LASTWRITE_FILETIME_UTC-or[int64]$destinationItem.LastWriteTimeUtc.ToFileTimeUtc()-ne[int64]$row.DESTINATION_LASTWRITE_FILETIME_UTC){$copyMismatch++}
}
if($copyMismatch-ne0-or$copySeen.Count-ne37){throw "COPY_IDENTITY_MISMATCH:$copyMismatch"}

$provenance=Get-Content -LiteralPath $copyProvenancePath -Raw|ConvertFrom-Json
if([string]$provenance.HANDOFF_ID-cne$HandoffId-or[string]$provenance.OPERATION-cne$Operation-or[string]$provenance.SOURCE_ROOT-cne(Get-ResolvedFullPath -LiteralPath $SourceRoot)-or[string]$provenance.DESTINATION_ROOT-cne(Get-ResolvedFullPath -LiteralPath $NewRoot)-or[int]$provenance.MATERIAL_ROWS-ne37-or[int]$provenance.OLD_CONTROLS_COPIED-ne0-or-not[bool]$provenance.CONTROL_ONLY-or[bool]$provenance.BUSINESS_RERUN){throw'PROVENANCE_MISMATCH'}

$manifestRows=@(Import-Csv -LiteralPath $manifestPath)
if($manifestRows.Count-ne39){throw "MANIFEST_ROWS:$($manifestRows.Count)"}
$manifestSeen=[System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::Ordinal)
$manifestMismatch=0
foreach($row in $manifestRows){
    $rel=ConvertTo-CanonicalRelativePath -Value ([string]$row.RELATIVE_PATH)
    if(-not$manifestSeen.Add($rel)){$manifestMismatch++;continue}
    $path=Resolve-ContainedPath -Root $NewRoot -CanonicalRelativePath $rel
    if([System.IO.Path]::GetFullPath($path)-cne[string]$row.RESOLVED_PATH){$manifestMismatch++}
    $item=Get-Item -LiteralPath $path -Force
    if([int64]$item.Length-ne[int64]$row.BYTES-or(Get-Sha256 -LiteralPath $path)-cne[string]$row.SHA256-or[int64]$item.CreationTimeUtc.ToFileTimeUtc()-ne[int64]$row.CREATION_FILETIME_UTC-or[int64]$item.LastWriteTimeUtc.ToFileTimeUtc()-ne[int64]$row.LASTWRITE_FILETIME_UTC){$manifestMismatch++}
}
$actualPayload=@(Get-ChildItem -LiteralPath $NewRoot -Force -Recurse -File|Where-Object{$_.Name-notin@('PAYLOAD_MANIFEST.csv','SEAL_AUDIT.json','WRITE_STOPPED')}|ForEach-Object{Get-CanonicalRelativeFromRoot -Root $NewRoot -LiteralPath $_.FullName})
$setDiff=@(Compare-Object -ReferenceObject @($manifestSeen) -DifferenceObject $actualPayload -CaseSensitive).Count
if($manifestMismatch-ne0-or$manifestSeen.Count-ne39-or$setDiff-ne0){throw "MANIFEST_IDENTITY_MISMATCH:${manifestMismatch}:${setDiff}"}

$sealAudit=Get-Content -LiteralPath $sealAuditPath -Raw|ConvertFrom-Json
if([string]$sealAudit.HANDOFF_ID-cne$HandoffId-or[string]$sealAudit.OPERATION-cne$Operation-or[int]$sealAudit.MATERIAL_ROWS-ne37-or[int]$sealAudit.PAYLOAD_ROWS-ne39-or[int]$sealAudit.CONTROL_ROWS-ne3-or[int]$sealAudit.PROJECTED_ORDINARY_FILES-ne42-or[string]$sealAudit.PAYLOAD_MANIFEST_SHA256-cne(Get-Sha256 -LiteralPath $manifestPath)-or[string]$sealAudit.VERDICT-cne$Verdict){throw'SEAL_AUDIT_MISMATCH'}

$markerBytes=[System.IO.File]::ReadAllBytes($markerPath)
$bom=($markerBytes.Length-ge3-and$markerBytes[0]-eq0xEF-and$markerBytes[1]-eq0xBB-and$markerBytes[2]-eq0xBF)
if($bom){throw'MARKER_BOM_PRESENT'}
$markerLines=@(Get-Content -LiteralPath $markerPath)
$markerMap=[System.Collections.Generic.Dictionary[string,string]]::new([System.StringComparer]::Ordinal)
$badLines=0
foreach($line in $markerLines){if($line-notmatch'^([^=]+)=(.+)$'){$badLines++;continue};if($markerMap.ContainsKey($Matches[1])){$badLines++;continue};$markerMap.Add($Matches[1],$Matches[2])}
$required=[ordered]@{HANDOFF_ID=$HandoffId;UID=$Uid;OPERATION=$Operation;SEALED_ROOT=(Get-ResolvedFullPath -LiteralPath $NewRoot);ACTUAL_SOURCE_ROOT=(Get-ResolvedFullPath -LiteralPath $SourceRoot);MATERIAL_ROWS='37';COPY_IDENTITY_ROWS='37';PAYLOAD_ROWS='39';CONTROL_ROWS='3';ORDINARY_FILES='42';MANIFEST_ROWS='39';MANIFEST_SHA256=(Get-Sha256 -LiteralPath $manifestPath);SEAL_AUDIT_SHA256=(Get-Sha256 -LiteralPath $sealAuditPath);VERDICT=$Verdict;OLD_CONTROLS_COPIED='0';CONTROL_ONLY='true';BUSINESS_RERUN='false';POST_MARKER_ROOT_WRITES='0'}
$requiredMismatch=0
foreach($key in $required.Keys){if(-not$markerMap.ContainsKey($key)-or$markerMap[$key]-cne[string]$required[$key]){$requiredMismatch++}}
if($markerLines.Count-ne18-or$markerMap.Count-ne18-or$badLines-ne0-or$requiredMismatch-ne0){throw "MARKER_SCHEMA_MISMATCH:$($markerLines.Count):$($markerMap.Count):${badLines}:${requiredMismatch}"}

$files=@(Get-ChildItem -LiteralPath $NewRoot -Force -Recurse -File)
$directories=@((Get-Item -LiteralPath $NewRoot -Force))+@(Get-ChildItem -LiteralPath $NewRoot -Force -Recurse -Directory)
if($files.Count-ne42){throw "ORDINARY_FILES:$($files.Count)"}
$writableFiles=@($files|Where-Object{-not$_.IsReadOnly})
$writableDirectories=@($directories|Where-Object{($_.Attributes-band[System.IO.FileAttributes]::ReadOnly)-eq0})
if($writableFiles.Count-ne0-or$writableDirectories.Count-ne0){throw'READONLY_GATE_FAILED'}
$marker=Get-Item -LiteralPath $markerPath -Force
$otherItems=@($files|Where-Object{$_.FullName-cne$markerPath})+@($directories)
$maxOther=[int64](($otherItems|ForEach-Object{[int64]$_.LastWriteTimeUtc.ToFileTimeUtc()}|Measure-Object -Maximum).Maximum)
$margin=[int64]$marker.LastWriteTimeUtc.ToFileTimeUtc()-$maxOther
$atOrAfter=@($otherItems|Where-Object{[int64]$_.LastWriteTimeUtc.ToFileTimeUtc()-ge[int64]$marker.LastWriteTimeUtc.ToFileTimeUtc()}).Count
if($margin-le0-or$atOrAfter-ne0){throw "MARKER_ORDER_FAILED:${margin}:${atOrAfter}"}

$postMarkerRecorded=@(Import-Csv -LiteralPath $PostMarkerStatePath)
$postMarkerCurrent=@(Get-TreeState -RootPath $NewRoot)
$postMarkerMismatch=Compare-StateRows -Before $postMarkerRecorded -After $postMarkerCurrent
if($postMarkerMismatch-ne0){throw "POSTMARKER_MISMATCH:$postMarkerMismatch"}
Assert-ParseAndHygiene -RootPath $NewRoot

$result=[ordered]@{HANDOFF_ID=$HandoffId;UID=$Uid;OPERATION=$Operation;INVOCATION_COUNT=1;SECOND_INVOCATION_ALLOWED=$false;SUCCESS=$true;CANONICAL_SELFTEST_CASE_SENSITIVE_DIFF=$selfTest.CASE_SENSITIVE_DIFF;CANONICAL_SELFTEST_INVALID_REJECTED=$selfTest.INVALID_REJECTED;SOURCE_ROOT_MISMATCH=0;SOURCE_MATERIAL_ROWS=37;OLD_CONTROLS_COPIED=0;COPY_IDENTITY_ROWS=37;COPY_IDENTITY_MISMATCH=0;PAYLOAD_ROWS=39;MANIFEST_ROWS=39;MANIFEST_IDENTITY_MISMATCH=0;CONTROL_ROWS=3;ORDINARY_FILES=42;READONLY_FILES=$files.Count;READONLY_DIRECTORIES=$directories.Count;WRITE_STOPPED_PHYSICAL_LINES=$markerLines.Count;WRITE_STOPPED_UNIQUE_KEYS=$markerMap.Count;WRITE_STOPPED_BAD_LINES=$badLines;WRITE_STOPPED_SHA256=(Get-Sha256 -LiteralPath $markerPath);PAYLOAD_MANIFEST_SHA256=(Get-Sha256 -LiteralPath $manifestPath);STRICT_LATEST=$true;STRICT_LATEST_MARGIN_TICKS=$margin;AT_OR_AFTER_EXCLUDING_MARKER=0;POST_MARKER_STATE_MISMATCH=0;PARSE_FAILURES=0;ADS_FAILURES=0;CACHE_PYC_FAILURES=0;REPARSE_FAILURES=0;VERDICT=$Verdict}
Write-Utf8NoBom -LiteralPath $AuditorResultPath -Text (($result|ConvertTo-Json -Depth 8)+"`r`n")
$result|ConvertTo-Json -Compress
