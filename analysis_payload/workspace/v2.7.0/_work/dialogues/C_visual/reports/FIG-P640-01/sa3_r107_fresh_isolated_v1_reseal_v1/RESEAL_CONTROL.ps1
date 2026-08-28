$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'

$OriginalRoot = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P640-01\sa3_r107_fresh_isolated_v1'
$NewRoot = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P640-01\sa3_r107_fresh_isolated_v1_reseal_v1'
$MaterialRoot = Join-Path $NewRoot 'material'
$ReportRoot = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\reports\FIG-P640-01\sa3_r107_fresh_isolated_v1_reseal_v1'
$AuditPath = Join-Path $ReportRoot 'ROOT_AUDIT.md'
$HandoffPath = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\handoff\C\P640_R107_SA3_RESEAL_V1_HANDOFF.md'
$ControllerPath = $PSCommandPath

$OriginalHandoffId = 'C-FIG-P640-01-R107-SA3-FRESH-ISOLATED-V1'
$ResealHandoffId = 'C-FIG-P640-01-R107-SA3-EVIDENCE-ONLY-RESEAL-V1'
$OriginalInstance = '/root/sa3_fig_p640_r107_fresh_isolated_v1'
$OriginalModel = 'gpt-5.6-sol'
$OriginalEffort = 'xhigh'
$OriginalForkTurns = 'none'

function Get-RelativePath {
    param([string]$Base, [string]$Full)
    return $Full.Substring($Base.Length + 1)
}

function Get-Sha256 {
    param([string]$Path)
    return (Get-FileHash -Algorithm SHA256 -LiteralPath $Path).Hash.ToUpperInvariant()
}

function Assert-True {
    param([bool]$Condition, [string]$Message)
    if (-not $Condition) { throw $Message }
}

Assert-True (Test-Path -LiteralPath $OriginalRoot -PathType Container) 'Original root missing.'
Assert-True (-not (Test-Path -LiteralPath $NewRoot)) 'New reseal root already exists.'
Assert-True (-not (Test-Path -LiteralPath $AuditPath)) 'External audit path already exists.'
Assert-True (-not (Test-Path -LiteralPath $HandoffPath)) 'External handoff path already exists.'

$OriginalFiles = @(Get-ChildItem -LiteralPath $OriginalRoot -Recurse -File | Sort-Object FullName)
Assert-True ($OriginalFiles.Count -eq 621) "Expected 621 original files; found $($OriginalFiles.Count)."
$OriginalWstop = Get-Item -LiteralPath (Join-Path $OriginalRoot 'WRITE_STOPPED')
$OriginalLater = @($OriginalFiles | Where-Object { $_.LastWriteTimeUtc -gt $OriginalWstop.LastWriteTimeUtc })
Assert-True ($OriginalLater.Count -eq 0) 'Original root has writes later than its WRITE_STOPPED.'

New-Item -ItemType Directory -Path $MaterialRoot -Force | Out-Null

$CopyRows = [System.Collections.Generic.List[object]]::new()
foreach ($SourceFile in $OriginalFiles) {
    $RelativePath = Get-RelativePath -Base $OriginalRoot -Full $SourceFile.FullName
    $DestinationPath = Join-Path $MaterialRoot $RelativePath
    $DestinationParent = Split-Path -Parent $DestinationPath
    if (-not (Test-Path -LiteralPath $DestinationParent)) {
        New-Item -ItemType Directory -Path $DestinationParent -Force | Out-Null
    }
    Copy-Item -LiteralPath $SourceFile.FullName -Destination $DestinationPath
    $DestinationFile = Get-Item -LiteralPath $DestinationPath
    $SourceSha = Get-Sha256 -Path $SourceFile.FullName
    $DestinationSha = Get-Sha256 -Path $DestinationPath
    $IdentityMatch = (
        ($SourceFile.Length -eq $DestinationFile.Length) -and
        ($SourceSha -eq $DestinationSha)
    )
    Assert-True $IdentityMatch "Copy identity mismatch: $RelativePath"
    $CopyRows.Add([pscustomobject]@{
        relative_path = ($RelativePath -replace '\\', '/')
        source_resolved_path = $SourceFile.FullName
        destination_resolved_path = $DestinationFile.FullName
        source_bytes = $SourceFile.Length
        destination_bytes = $DestinationFile.Length
        source_sha256 = $SourceSha
        destination_sha256 = $DestinationSha
        source_mtime_utc = $SourceFile.LastWriteTimeUtc.ToString('O')
        destination_mtime_utc = $DestinationFile.LastWriteTimeUtc.ToString('O')
        bytes_sha_identity_match = 'true'
    })
}

$CopyIdentityPath = Join-Path $NewRoot 'COPY_IDENTITY.csv'
$CopyRows | Export-Csv -LiteralPath $CopyIdentityPath -NoTypeInformation -Encoding utf8NoBOM

$Provenance = [ordered]@{
    reseal_handoff_id = $ResealHandoffId
    operation = 'EVIDENCE_ONLY_CONTROL_RESEAL_READONLY_FREEZE'
    content_readjudicated = $false
    original_handoff_id = $OriginalHandoffId
    original_instance = $OriginalInstance
    original_model = $OriginalModel
    original_reasoning_effort = $OriginalEffort
    original_fork_turns = $OriginalForkTurns
    original_root = $OriginalRoot
    new_root = $NewRoot
    material_root = $MaterialRoot
    copied_material_file_count = 621
    copy_identity_file = 'COPY_IDENTITY.csv'
    manifest_file = 'MANIFEST.sha256'
    self_excluded_files = @('MANIFEST.sha256', 'WRITE_STOPPED')
    expected_payload_count = 623
    expected_final_ordinary_count = 625
    authority_files_modified = $false
    tex_invoked = $false
    source_modified = $false
    second_role_started = $false
    original_root_modified = $false
    original_sa3_outcome_preserved = 'CANDIDATE_PASS_PENDING_MAIN_ACCEPTANCE'
    local_pass_counted = $false
    global_pass_counted = $false
}
$ProvenancePath = Join-Path $NewRoot 'RESEAL_PROVENANCE.json'
$Provenance | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $ProvenancePath -Encoding utf8NoBOM

$PayloadFiles = @(Get-ChildItem -LiteralPath $MaterialRoot -Recurse -File | Sort-Object FullName)
Assert-True ($PayloadFiles.Count -eq 621) "Expected 621 material files; found $($PayloadFiles.Count)."
$PayloadFiles += Get-Item -LiteralPath $CopyIdentityPath
$PayloadFiles += Get-Item -LiteralPath $ProvenancePath
Assert-True ($PayloadFiles.Count -eq 623) "Expected 623 manifest payload files; found $($PayloadFiles.Count)."

$ManifestLines = foreach ($PayloadFile in ($PayloadFiles | Sort-Object FullName)) {
    $RelativePath = Get-RelativePath -Base $NewRoot -Full $PayloadFile.FullName
    '{0}  {1}' -f (Get-Sha256 -Path $PayloadFile.FullName), ($RelativePath -replace '\\', '/')
}
$ManifestPath = Join-Path $NewRoot 'MANIFEST.sha256'
$ManifestLines | Set-Content -LiteralPath $ManifestPath -Encoding utf8NoBOM
Assert-True (@(Get-Content -LiteralPath $ManifestPath).Count -eq 623) 'Manifest line count is not 623.'

$CopyIdentitySha = Get-Sha256 -Path $CopyIdentityPath
$ProvenanceSha = Get-Sha256 -Path $ProvenancePath
$ManifestSha = Get-Sha256 -Path $ManifestPath
Start-Sleep -Milliseconds 80
$WriteStoppedPath = Join-Path $NewRoot 'WRITE_STOPPED'
@(
    "RESEAL_HANDOFF_ID=$ResealHandoffId"
    "ORIGINAL_HANDOFF_ID=$OriginalHandoffId"
    "ORIGINAL_INSTANCE=$OriginalInstance"
    "ORIGINAL_MODEL=$OriginalModel"
    "ORIGINAL_REASONING_EFFORT=$OriginalEffort"
    "ORIGINAL_FORK_TURNS=$OriginalForkTurns"
    'CONTENT_READJUDICATED=false'
    'MATERIAL_FILE_COUNT=621'
    'MANIFEST_PAYLOAD_COUNT=623'
    'FINAL_ORDINARY_FILE_COUNT=625'
    'SELF_EXCLUDED_COUNT=2'
    'SELF_EXCLUDED_FILES=MANIFEST.sha256|WRITE_STOPPED'
    "COPY_IDENTITY_SHA256=$CopyIdentitySha"
    "RESEAL_PROVENANCE_SHA256=$ProvenanceSha"
    "MANIFEST_SHA256=$ManifestSha"
    'ROOT_AND_ALL_FILES_READONLY=true'
    'ADS_COUNT=0'
    'CACHE_PYC_COUNT=0'
    'REPARSE_POINT_COUNT=0'
    'WRITE_STOPPED_UNIQUE_LATEST=true'
    'POST_MARKER_WRITES=0'
    'LOCAL_PASS_COUNTED=false'
    'GLOBAL_PASS_COUNTED=false'
) | Set-Content -LiteralPath $WriteStoppedPath -Encoding utf8NoBOM

$PreFreezeFiles = @(Get-ChildItem -LiteralPath $NewRoot -Recurse -File)
Assert-True ($PreFreezeFiles.Count -eq 625) "Expected 625 final files before freeze; found $($PreFreezeFiles.Count)."
$WstopItem = Get-Item -LiteralPath $WriteStoppedPath
$PreFreezeNewer = @($PreFreezeFiles | Where-Object { $_.LastWriteTimeUtc -gt $WstopItem.LastWriteTimeUtc })
$PreFreezeSameLatest = @($PreFreezeFiles | Where-Object { $_.LastWriteTimeUtc -eq $WstopItem.LastWriteTimeUtc })
Assert-True ($PreFreezeNewer.Count -eq 0) 'A file is later than WRITE_STOPPED before freeze.'
Assert-True (($PreFreezeSameLatest.Count -eq 1) -and ($PreFreezeSameLatest[0].FullName -eq $WriteStoppedPath)) 'WRITE_STOPPED is not uniquely latest before freeze.'

foreach ($File in $PreFreezeFiles) { $File.IsReadOnly = $true }
foreach ($Directory in @(Get-ChildItem -LiteralPath $NewRoot -Recurse -Directory)) {
    $Directory.Attributes = $Directory.Attributes -bor [System.IO.FileAttributes]::ReadOnly
}
$NewRootItem = Get-Item -LiteralPath $NewRoot
$NewRootItem.Attributes = $NewRootItem.Attributes -bor [System.IO.FileAttributes]::ReadOnly

$FinalFiles = @(Get-ChildItem -LiteralPath $NewRoot -Recurse -File)
$ReadonlyFiles = @($FinalFiles | Where-Object { $_.IsReadOnly })
$MaterialFinal = @(Get-ChildItem -LiteralPath $MaterialRoot -Recurse -File)
$CopyAuditRows = @(Import-Csv -LiteralPath $CopyIdentityPath)
$CopyUniquePaths = @($CopyAuditRows.relative_path | Sort-Object -Unique)
$CopyBad = @($CopyAuditRows | Where-Object {
    ($_.bytes_sha_identity_match -ne 'true') -or
    ([int64]$_.source_bytes -ne [int64]$_.destination_bytes) -or
    ($_.source_sha256 -ne $_.destination_sha256) -or
    (-not (Test-Path -LiteralPath $_.source_resolved_path -PathType Leaf)) -or
    (-not (Test-Path -LiteralPath $_.destination_resolved_path -PathType Leaf))
})

$ManifestAuditLines = @(Get-Content -LiteralPath $ManifestPath)
$ManifestBadLines = @($ManifestAuditLines | Where-Object { $_ -notmatch '^[0-9A-F]{64}  .+' })
$ManifestPaths = [System.Collections.Generic.List[string]]::new()
$ManifestMissing = 0
$ManifestHashMismatch = 0
foreach ($Line in $ManifestAuditLines) {
    if ($Line -notmatch '^[0-9A-F]{64}  .+') { continue }
    $ExpectedHash = $Line.Substring(0, 64)
    $RelativePath = $Line.Substring(66)
    $ManifestPaths.Add($RelativePath)
    $Path = Join-Path $NewRoot ($RelativePath -replace '/', '\\')
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        $ManifestMissing++
    } elseif ((Get-Sha256 -Path $Path) -ne $ExpectedHash) {
        $ManifestHashMismatch++
    }
}
$ManifestDuplicatePaths = @($ManifestPaths | Group-Object | Where-Object { $_.Count -gt 1 })
$ManifestPathSet = @($ManifestPaths | ForEach-Object { $_ -replace '/', '\\' })
$ManifestExtraFiles = @($FinalFiles | Where-Object {
    $RelativePath = Get-RelativePath -Base $NewRoot -Full $_.FullName
    $RelativePath -notin $ManifestPathSet
} | ForEach-Object { Get-RelativePath -Base $NewRoot -Full $_.FullName } | Sort-Object)

$FinalWstop = Get-Item -LiteralPath $WriteStoppedPath
$FilesLaterThanMarker = @($FinalFiles | Where-Object { $_.LastWriteTimeUtc -gt $FinalWstop.LastWriteTimeUtc })
$FilesAtLatestMarkerTime = @($FinalFiles | Where-Object { $_.LastWriteTimeUtc -eq $FinalWstop.LastWriteTimeUtc })
$CachePyc = @($FinalFiles | Where-Object {
    $_.Name -match '\.py[co]$' -or
    $_.FullName -match '(^|[\\/])(__pycache__|\.pytest_cache|\.mypy_cache|\.ruff_cache|texmf-cache|texmf-var)([\\/]|$)'
})
$ReparsePoints = @(Get-ChildItem -LiteralPath $NewRoot -Recurse -Force | Where-Object {
    ($_.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0
})
$AdsCount = 0
foreach ($File in $FinalFiles) {
    $AdsCount += @(Get-Item -LiteralPath $File.FullName -Stream * -ErrorAction SilentlyContinue | Where-Object { $_.Stream -ne ':$DATA' }).Count
}

$RootReadonly = (((Get-Item -LiteralPath $NewRoot).Attributes -band [System.IO.FileAttributes]::ReadOnly) -ne 0)
$ExpectedExtras = @('MANIFEST.sha256', 'WRITE_STOPPED')
$ExtrasMatch = (($ManifestExtraFiles.Count -eq 2) -and (@($ManifestExtraFiles | Where-Object { $_ -notin $ExpectedExtras }).Count -eq 0))

$AuditPassed = (
    ($FinalFiles.Count -eq 625) -and
    ($MaterialFinal.Count -eq 621) -and
    ($ReadonlyFiles.Count -eq 625) -and
    $RootReadonly -and
    ($CopyAuditRows.Count -eq 621) -and
    ($CopyUniquePaths.Count -eq 621) -and
    ($CopyBad.Count -eq 0) -and
    ($ManifestAuditLines.Count -eq 623) -and
    ($ManifestBadLines.Count -eq 0) -and
    ($ManifestDuplicatePaths.Count -eq 0) -and
    ($ManifestMissing -eq 0) -and
    ($ManifestHashMismatch -eq 0) -and
    $ExtrasMatch -and
    ($FilesLaterThanMarker.Count -eq 0) -and
    ($FilesAtLatestMarkerTime.Count -eq 1) -and
    ($FilesAtLatestMarkerTime[0].FullName -eq $WriteStoppedPath) -and
    ($AdsCount -eq 0) -and
    ($CachePyc.Count -eq 0) -and
    ($ReparsePoints.Count -eq 0)
)
Assert-True $AuditPassed 'External root audit failed.'

$AuditLines = @(
    '# P640 R107 SA3 evidence-only reseal root audit'
    ''
    "- Reseal handoff: $ResealHandoffId"
    "- Original SA3 instance: $OriginalInstance"
    "- Original model/effort/fork: $OriginalModel / $OriginalEffort / $OriginalForkTurns"
    "- Original handoff: $OriginalHandoffId"
    "- Original root: $OriginalRoot"
    "- New root: $NewRoot"
    '- Content readjudicated: false'
    '- Original SA3 candidate outcome preserved; local/global pass counted: false/false'
    ''
    '## Mechanical result'
    ''
    '- ROOT_AUDIT_RESULT: PASS'
    '- Original material copied: 621/621 files'
    '- COPY_IDENTITY rows/unique/mismatch: 621/621/0'
    '- Final ordinary files: 625'
    '- Read-only ordinary files: 625/625'
    '- Root read-only: true'
    '- Manifest payload rows: 623'
    '- Manifest bad/missing/duplicate/hash mismatch: 0/0/0/0'
    '- Manifest self-excluded files: MANIFEST.sha256, WRITE_STOPPED'
    '- WRITE_STOPPED unique latest: true'
    '- Post-marker writes: 0'
    '- ADS/cache-pyc/reparse: 0/0/0'
    ''
    '## Immutable identities'
    ''
    "- COPY_IDENTITY.csv: $CopyIdentitySha"
    "- RESEAL_PROVENANCE.json: $ProvenanceSha"
    "- MANIFEST.sha256: $ManifestSha"
    "- WRITE_STOPPED: $(Get-Sha256 -Path $WriteStoppedPath)"
)
$AuditLines | Set-Content -LiteralPath $AuditPath -Encoding utf8NoBOM

$AuditSha = Get-Sha256 -Path $AuditPath
$HandoffLines = @(
    '# Immutable handoff: P640 R107 SA3 evidence-only reseal V1'
    ''
    "RESEAL_HANDOFF_ID: $ResealHandoffId  "
    "ORIGINAL_HANDOFF_ID: $OriginalHandoffId  "
    "ORIGINAL_INSTANCE: $OriginalInstance  "
    "MODEL_EFFORT_FORK: $OriginalModel / $OriginalEffort / $OriginalForkTurns  "
    "ORIGINAL_ROOT: $OriginalRoot  "
    "NEW_ROOT: $NewRoot  "
    'CONTENT_READJUDICATED: false  '
    'SA3_REVIEW_OUTCOME: CANDIDATE_PASS_PENDING_MAIN_ACCEPTANCE  '
    'LOCAL_PASS_COUNTED: false  '
    'GLOBAL_PASS_COUNTED: false  '
    ''
    'Mechanical reseal result: PASS. The original 621 ordinary files were copied byte-for-byte and SHA-for-SHA under material/. COPY_IDENTITY.csv contains 621 unique rows with zero identity mismatch. MANIFEST.sha256 covers exactly 623 payload files. The final root contains 625 ordinary files; all 625 files and the root are read-only. WRITE_STOPPED is uniquely latest with zero post-marker writes. Missing, extra beyond the two declared self-exclusions, duplicate, SHA mismatch, ADS, cache/pyc, and reparse counts are all zero.'
    ''
    "ROOT_AUDIT.md SHA256: $AuditSha  "
    "COPY_IDENTITY.csv SHA256: $CopyIdentitySha  "
    "RESEAL_PROVENANCE.json SHA256: $ProvenanceSha  "
    "MANIFEST.sha256 SHA256: $ManifestSha  "
    "WRITE_STOPPED SHA256: $(Get-Sha256 -Path $WriteStoppedPath)  "
    ''
    'No TeX, source modification, Git commit, second SA3, or second UID was started.'
)
$HandoffLines | Set-Content -LiteralPath $HandoffPath -Encoding utf8NoBOM

(Get-Item -LiteralPath $AuditPath).IsReadOnly = $true
(Get-Item -LiteralPath $HandoffPath).IsReadOnly = $true
(Get-Item -LiteralPath $ControllerPath).IsReadOnly = $true

Write-Output "RESEAL_RESULT=PASS"
Write-Output "ORIGINAL_FILES=621"
Write-Output "FINAL_FILES=625"
Write-Output "READONLY_FILES=625"
Write-Output "ROOT_READONLY=true"
Write-Output "MANIFEST_PAYLOAD=623"
Write-Output "COPY_IDENTITY_SHA256=$CopyIdentitySha"
Write-Output "RESEAL_PROVENANCE_SHA256=$ProvenanceSha"
Write-Output "MANIFEST_SHA256=$ManifestSha"
Write-Output "WRITE_STOPPED_SHA256=$(Get-Sha256 -Path $WriteStoppedPath)"
Write-Output "ROOT_AUDIT_SHA256=$AuditSha"
Write-Output "HANDOFF_SHA256=$(Get-Sha256 -Path $HandoffPath)"
