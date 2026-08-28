#requires -Version 7.0
[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
$HandoffId = 'C-FIG-P662-01-R112-SA3-FRESH-ISOLATED-CONTROL-RESEAL-V1'
$Uid = 'FIG-P662-01'
$Verdict = 'SA3_PASS_AWAIT_MAIN_C_LOCAL_PASS_ACCEPTANCE'
$OldRoot = [IO.Path]::GetFullPath('D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P662-01\sa3_r112_fresh_isolated_v1')
$NewRoot = [IO.Path]::GetFullPath('D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P662-01\sa3_r112_fresh_isolated_v1_control_reseal_v1')
$OldManifest = [IO.Path]::Combine($OldRoot, 'MANIFEST.csv')
$ExternalResult = [IO.Path]::GetFullPath('D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\reports\P662_SA3_CONTROL_RESEAL_V1_RESULT.json')
$ExternalMarker = [IO.Path]::GetFullPath('D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\reports\P662_SA3_CONTROL_RESEAL_V1_WRITE_STOPPED.precreated')
$Utf8 = [Text.UTF8Encoding]::new($false)
$StartedUtc = [DateTime]::UtcNow
$MarkerMoved = $false

function Sha([string]$Path) { (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToUpperInvariant() }
function Rel([string]$Root, [string]$Path) { [IO.Path]::GetRelativePath($Root, $Path).Replace('\', '/') }
function SetRO([string]$Path) { [IO.File]::SetAttributes($Path, ([IO.File]::GetAttributes($Path) -bor [IO.FileAttributes]::ReadOnly)) }

function FileId([string]$Root, [string]$Path) {
    $item = Get-Item -LiteralPath $Path -Force
    [pscustomobject]@{
        relative_path = Rel $Root $item.FullName
        bytes = [int64]$item.Length
        sha256 = Sha $item.FullName
        creation_filetime_utc_ticks = [int64]$item.CreationTimeUtc.ToFileTimeUtc()
        last_write_filetime_utc_ticks = [int64]$item.LastWriteTimeUtc.ToFileTimeUtc()
        attributes = $item.Attributes.ToString()
    }
}

function FileSnapshot([string]$Root) {
    $map = [ordered]@{}
    foreach ($file in @(Get-ChildItem -LiteralPath $Root -Recurse -File -Force | Sort-Object FullName)) {
        $id = FileId $Root $file.FullName
        $map[$id.relative_path] = $id
    }
    $map
}

function DirectorySnapshot([string]$Root) {
    $map = [ordered]@{}
    $dirs = @((Get-Item -LiteralPath $Root -Force)) + @(Get-ChildItem -LiteralPath $Root -Recurse -Directory -Force | Sort-Object FullName)
    foreach ($dir in $dirs) {
        $relative = if ($dir.FullName -ceq $Root) { '.' } else { Rel $Root $dir.FullName }
        $map[$relative] = [pscustomobject]@{
            relative_path = $relative
            creation_filetime_utc_ticks = [int64]$dir.CreationTimeUtc.ToFileTimeUtc()
            last_write_filetime_utc_ticks = [int64]$dir.LastWriteTimeUtc.ToFileTimeUtc()
            attributes = $dir.Attributes.ToString()
        }
    }
    $map
}

function MapDiff($A, $B) {
    $errors = [Collections.Generic.List[string]]::new()
    foreach ($key in $A.Keys) {
        if (-not $B.Contains($key)) { $errors.Add("missing:$key"); continue }
        foreach ($field in @('bytes','sha256','creation_filetime_utc_ticks','last_write_filetime_utc_ticks','attributes')) {
            if (($A[$key].PSObject.Properties.Name -contains $field) -and ($B[$key].PSObject.Properties.Name -contains $field)) {
                if ([string]$A[$key].$field -cne [string]$B[$key].$field) { $errors.Add("${key}:$field") }
            }
        }
    }
    foreach ($key in $B.Keys) { if (-not $A.Contains($key)) { $errors.Add("extra:$key") } }
    @($errors)
}

function Hygiene([string]$Root) {
    $files = @(Get-ChildItem -LiteralPath $Root -Recurse -File -Force)
    $dirs = @((Get-Item -LiteralPath $Root -Force)) + @(Get-ChildItem -LiteralPath $Root -Recurse -Directory -Force)
    $ads = @($files | ForEach-Object { Get-Item -LiteralPath $_.FullName -Stream * -ErrorAction SilentlyContinue | Where-Object Stream -NotIn @(':$DATA','$DATA') })
    $cache = @($files | Where-Object { $_.FullName -match '(?i)(^|[\\/])(__pycache__|\.pytest_cache|\.mypy_cache|\.cache)([\\/]|$)|\.(pyc|pyo)$' })
    $reparse = @($files + $dirs | Where-Object { ([IO.File]::GetAttributes($_.FullName) -band [IO.FileAttributes]::ReparsePoint) -ne 0 })
    [pscustomobject]@{ ads=$ads.Count; cache_pyc=$cache.Count; reparse=$reparse.Count }
}

function ParseGate([string]$Root) {
    $bad = [Collections.Generic.List[string]]::new()
    foreach ($file in @(Get-ChildItem -LiteralPath $Root -Recurse -File -Force)) {
        try {
            if ($file.Extension -ieq '.json') { Get-Content -LiteralPath $file.FullName -Raw | ConvertFrom-Json | Out-Null }
            elseif ($file.Extension -ieq '.csv') { Import-Csv -LiteralPath $file.FullName | Out-Null }
        } catch { $bad.Add((Rel $Root $file.FullName)) }
    }
    if ($bad.Count -ne 0) { throw "Parse failures: $($bad -join ',')" }
}

function ManifestGate([string]$Root, [string]$Path, [int]$ExpectedRows) {
    $rows = @(Import-Csv -LiteralPath $Path)
    if ($rows.Count -ne $ExpectedRows) { throw "Manifest rows $($rows.Count), expected $ExpectedRows" }
    if (@($rows | Group-Object relative_path | Where-Object Count -gt 1).Count -ne 0) { throw 'Manifest duplicate paths' }
    $mismatch = 0
    foreach ($row in $rows) {
        $file = [IO.Path]::Combine($Root, $row.relative_path.Replace('/', '\'))
        if (-not [IO.File]::Exists($file)) { $mismatch++; continue }
        $id = FileId $Root $file
        if ($id.bytes -ne [int64]$row.bytes -or $id.sha256 -cne [string]$row.sha256 -or
            $id.creation_filetime_utc_ticks -ne [int64]$row.creation_filetime_utc_ticks -or
            $id.last_write_filetime_utc_ticks -ne [int64]$row.last_write_filetime_utc_ticks) { $mismatch++ }
    }
    $all = @(Get-ChildItem -LiteralPath $Root -Recurse -File -Force | ForEach-Object { Rel $Root $_.FullName })
    $payload = @($all | Where-Object { $_ -notin @('PAYLOAD_MANIFEST.csv','SEAL_AUDIT.json','WRITE_STOPPED') })
    $extra = @($payload | Where-Object { $_ -notin $rows.relative_path })
    $unlisted = @($rows.relative_path | Where-Object { $_ -notin $payload })
    if ($mismatch -ne 0 -or $extra.Count -ne 0 -or $unlisted.Count -ne 0) { throw "Manifest mismatch=$mismatch extra=$($extra.Count) unlisted=$($unlisted.Count)" }
    [pscustomobject]@{ rows=$rows.Count; mismatch=$mismatch; extra=$extra.Count; unlisted=$unlisted.Count }
}

function ExternalResult($Value) {
    [IO.File]::WriteAllText($ExternalResult, (($Value | ConvertTo-Json -Depth 12) + [Environment]::NewLine), $Utf8)
    SetRO $ExternalResult
}

try {
    if (-not [IO.Directory]::Exists($OldRoot)) { throw 'Old root missing' }
    if ([IO.Directory]::Exists($NewRoot) -or [IO.File]::Exists($NewRoot)) { throw 'New root already exists' }
    if ([IO.File]::Exists($ExternalResult) -or [IO.File]::Exists($ExternalMarker)) { throw 'External result or marker exists' }

    $tokens=$null; $astErrors=$null
    $null=[Management.Automation.Language.Parser]::ParseFile($PSCommandPath,[ref]$tokens,[ref]$astErrors)
    if ($astErrors.Count -ne 0) { throw "AST errors $($astErrors.Count)" }
    $controller = FileId ([IO.Path]::GetDirectoryName($PSCommandPath)) $PSCommandPath
    $oldBefore = FileSnapshot $OldRoot

    $rawRows = @(Import-Csv -LiteralPath $OldManifest)
    if ($rawRows.Count -ne 37) { throw "Old manifest rows $($rawRows.Count), expected 37" }
    if (@($rawRows | Group-Object RELATIVE_PATH | Where-Object Count -gt 1).Count -ne 0) { throw 'Old manifest duplicates' }
    if (@($rawRows | Where-Object { $_.RELATIVE_PATH -in @('MANIFEST.csv','WSTOP.txt') }).Count -ne 0) { throw 'Old control bound as material' }
    $oldRows = @($rawRows | ForEach-Object {
        [pscustomobject]@{
            relative_path=[string]$_.RELATIVE_PATH
            bytes=[int64]$_.BYTES
            sha256=[string]$_.SHA256
            creation_filetime_utc_ticks=[int64]$_.CREATION_FILETIME_TICKS
            last_write_filetime_utc_ticks=[int64]$_.LASTWRITE_FILETIME_TICKS
        }
    })

    [IO.Directory]::CreateDirectory($NewRoot) | Out-Null
    $copyRows = [Collections.Generic.List[object]]::new()
    foreach ($row in $oldRows) {
        $source = [IO.Path]::Combine($OldRoot, $row.relative_path.Replace('/', '\'))
        $dest = [IO.Path]::Combine($NewRoot, $row.relative_path.Replace('/', '\'))
        if (-not [IO.File]::Exists($source)) { throw "Missing old material $($row.relative_path)" }
        $sid = FileId $OldRoot $source
        if ($sid.bytes -ne $row.bytes -or $sid.sha256 -cne $row.sha256 -or $sid.creation_filetime_utc_ticks -ne $row.creation_filetime_utc_ticks -or $sid.last_write_filetime_utc_ticks -ne $row.last_write_filetime_utc_ticks) { throw "Old identity mismatch $($row.relative_path)" }
        [IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($dest)) | Out-Null
        [IO.File]::Copy($source,$dest,$false)
        [IO.File]::SetCreationTimeUtc($dest,[DateTime]::FromFileTimeUtc($row.creation_filetime_utc_ticks))
        [IO.File]::SetLastWriteTimeUtc($dest,[DateTime]::FromFileTimeUtc($row.last_write_filetime_utc_ticks))
        $did = FileId $NewRoot $dest
        if ($sid.bytes -ne $did.bytes -or $sid.sha256 -cne $did.sha256 -or $sid.creation_filetime_utc_ticks -ne $did.creation_filetime_utc_ticks -or $sid.last_write_filetime_utc_ticks -ne $did.last_write_filetime_utc_ticks) { throw "Copy mismatch $($row.relative_path)" }
        $copyRows.Add([pscustomobject]@{
            relative_path=$row.relative_path
            source_resolved_path=$source
            destination_resolved_path=$dest
            source_bytes=$sid.bytes
            destination_bytes=$did.bytes
            source_sha256=$sid.sha256
            destination_sha256=$did.sha256
            source_creation_filetime_utc_ticks=$sid.creation_filetime_utc_ticks
            destination_creation_filetime_utc_ticks=$did.creation_filetime_utc_ticks
            source_last_write_filetime_utc_ticks=$sid.last_write_filetime_utc_ticks
            destination_last_write_filetime_utc_ticks=$did.last_write_filetime_utc_ticks
            mismatch_count=0
        })
    }

    $copyIdentity = [IO.Path]::Combine($NewRoot,'COPY_IDENTITY.csv')
    $copyRows | Export-Csv -LiteralPath $copyIdentity -NoTypeInformation -Encoding utf8
    $oldManifestItem=Get-Item -LiteralPath $OldManifest -Force
    $provenance=[ordered]@{
        handoff_id=$HandoffId;uid=$Uid;operation='evidence-only sibling control reseal'
        source_root_resolved=$OldRoot;destination_root_resolved=$NewRoot
        source_manifest_resolved=$OldManifest;source_manifest_bytes=[int64]$oldManifestItem.Length;source_manifest_sha256=Sha $OldManifest
        copied_material_count=37;excluded_old_manifest_count=1;excluded_old_wstop_count=1;old_controls_copied=0
        copy_identity_relative_path='COPY_IDENTITY.csv';copy_identity_rows=37;material_identity_mismatch_count=0
        pdf_render_visual_object_pair_manual_math_semantic_rerun=0;tex_source_git_central_writes=0
        verdict_preserved=$Verdict;controller_resolved_path=$PSCommandPath;controller_bytes=$controller.bytes;controller_sha256=$controller.sha256
        invocation_ordinal=1;retry_count=0
    }
    $copyProvenance=[IO.Path]::Combine($NewRoot,'COPY_PROVENANCE.json')
    [IO.File]::WriteAllText($copyProvenance,(($provenance|ConvertTo-Json -Depth 8)+[Environment]::NewLine),$Utf8)

    $payloadRel=[Collections.Generic.List[string]]::new()
    foreach($row in $oldRows){$payloadRel.Add($row.relative_path)}
    $payloadRel.Add('COPY_IDENTITY.csv');$payloadRel.Add('COPY_PROVENANCE.json')
    if($payloadRel.Count -ne 39 -or @($payloadRel|Sort-Object -Unique).Count -ne 39){throw 'Payload count/unique failed'}
    $manifestRows=[Collections.Generic.List[object]]::new()
    foreach($relative in @($payloadRel|Sort-Object)){
        $id=FileId $NewRoot ([IO.Path]::Combine($NewRoot,$relative.Replace('/','\')))
        $manifestRows.Add([pscustomobject]@{relative_path=$relative;bytes=$id.bytes;sha256=$id.sha256;creation_filetime_utc_ticks=$id.creation_filetime_utc_ticks;last_write_filetime_utc_ticks=$id.last_write_filetime_utc_ticks})
    }
    $manifest=[IO.Path]::Combine($NewRoot,'PAYLOAD_MANIFEST.csv')
    $manifestRows|Export-Csv -LiteralPath $manifest -NoTypeInformation -Encoding utf8
    $manifestHash=Sha $manifest
    $manifestCheck=ManifestGate $NewRoot $manifest 39
    ParseGate $NewRoot
    $h=Hygiene $NewRoot
    if($h.ads-ne0-or$h.cache_pyc-ne0-or$h.reparse-ne0){throw 'Premarker hygiene failed'}

    $sealAudit=[IO.Path]::Combine($NewRoot,'SEAL_AUDIT.json')
    $audit=[ordered]@{
        handoff_id=$HandoffId;uid=$Uid;source_root_resolved=$OldRoot;sealed_root_resolved=$NewRoot
        old_manifest_bound_material_count=37;old_controls_copied=0;copy_identity_rows=37;copy_identity_mismatch_count=0
        payload_count=39;manifest_rows=$manifestCheck.rows;manifest_identity_mismatch=$manifestCheck.mismatch;manifest_extra=$manifestCheck.extra;manifest_unlisted=$manifestCheck.unlisted
        payload_manifest_relative_path='PAYLOAD_MANIFEST.csv';payload_manifest_sha256=$manifestHash
        json_csv_parse_failures=0;ads_count=$h.ads;cache_pyc_count=$h.cache_pyc;reparse_count=$h.reparse
        projected_controls=@('PAYLOAD_MANIFEST.csv','SEAL_AUDIT.json','WRITE_STOPPED');projected_ordinary_count=42
        marker_contract='multiline one KEY=VALUE per physical line; precreated outside root after all premarker operations; ReadOnly; single move final'
        verdict=$Verdict
    }
    [IO.File]::WriteAllText($sealAudit,(($audit|ConvertTo-Json -Depth 8)+[Environment]::NewLine),$Utf8)
    ParseGate $NewRoot
    $h=Hygiene $NewRoot
    if($h.ads-ne0-or$h.cache_pyc-ne0-or$h.reparse-ne0){throw 'Final premarker hygiene failed'}

    $premarkerFiles=@(Get-ChildItem -LiteralPath $NewRoot -Recurse -File -Force)
    if($premarkerFiles.Count-ne41){throw "Premarker files $($premarkerFiles.Count), expected 41"}
    foreach($file in $premarkerFiles){SetRO $file.FullName}
    $premarkerDirs=@((Get-Item -LiteralPath $NewRoot -Force))+@(Get-ChildItem -LiteralPath $NewRoot -Recurse -Directory -Force|Sort-Object {$_.FullName.Length} -Descending)
    foreach($dir in $premarkerDirs){SetRO $dir.FullName}
    $premarkerFiles=@(Get-ChildItem -LiteralPath $NewRoot -Recurse -File -Force)
    $premarkerDirs=@((Get-Item -LiteralPath $NewRoot -Force))+@(Get-ChildItem -LiteralPath $NewRoot -Recurse -Directory -Force)
    if(@($premarkerFiles|Where-Object{([IO.File]::GetAttributes($_.FullName)-band[IO.FileAttributes]::ReadOnly)-eq0}).Count-ne0){throw 'Writable premarker file'}
    if(@($premarkerDirs|Where-Object{([IO.File]::GetAttributes($_.FullName)-band[IO.FileAttributes]::ReadOnly)-eq0}).Count-ne0){throw 'Writable premarker directory'}

    $sealHash=Sha $sealAudit
    $maxPremarker=($premarkerFiles|ForEach-Object{$_.LastWriteTimeUtc.ToFileTimeUtc()}|Measure-Object -Maximum).Maximum
    $markerFiletime=[int64]$maxPremarker+10000000
    $markerLines=@(
        'WRITE_STOPPED=CONTROL_RESEAL_COMPLETE',
        "HANDOFF_ID=$HandoffId",
        "UID=$Uid",
        'ROLE=FRESH_ISOLATED_SA3_CONTROL_RESEAL',
        "SOURCE_ROOT=$OldRoot",
        "SEALED_ROOT=$NewRoot",
        'MATERIAL_COUNT=37',
        'COPY_IDENTITY_ROWS=37',
        'PAYLOAD_COUNT=39',
        'MANIFEST_ROWS=39',
        "MANIFEST_SHA256=$manifestHash",
        "SEAL_AUDIT_SHA256=$sealHash",
        'CONTROL_COUNT=3',
        'ORDINARY_COUNT=42',
        "DIRECTORY_COUNT_INCLUDING_ROOT=$($premarkerDirs.Count)",
        'ROOT_READONLY_PREMARKER=PASS',
        'ALL_PREMARKER_FILES_READONLY=PASS',
        'FINAL_ROOT_CONTENT_OPERATION=SINGLE_ATOMIC_MOVE_OF_THIS_PRECREATED_MARKER',
        'POST_MARKER_CONTENT_WRITES=0',
        'POST_MARKER_ATTRIBUTE_CHANGES=0',
        "VERDICT=$Verdict"
    )
    [IO.File]::WriteAllLines($ExternalMarker,$markerLines,$Utf8)
    $markerTime=[DateTime]::FromFileTimeUtc($markerFiletime)
    [IO.File]::SetCreationTimeUtc($ExternalMarker,$markerTime);[IO.File]::SetLastWriteTimeUtc($ExternalMarker,$markerTime);SetRO $ExternalMarker

    $physical=@([IO.File]::ReadAllLines($ExternalMarker,$Utf8))
    if($physical.Count-ne21){throw "Marker physical lines $($physical.Count), expected 21"}
    $raw=[IO.File]::ReadAllText($ExternalMarker,$Utf8)
    if($raw.Contains("`t")-or$raw-match'(?i)<[^>]+>|TBD|PLACEHOLDER|(^|[^A-Za-z])rue([^A-Za-z]|$)'){throw 'Marker placeholder/tab/rue'}
    $parsed=[ordered]@{}
    foreach($line in $physical){
        if($line-notmatch'^[^=\t]+=[^=\t]+$'){throw "Malformed marker line: $line"}
        $parts=$line.Split('=',2)
        if([string]::IsNullOrWhiteSpace($parts[0])-or[string]::IsNullOrWhiteSpace($parts[1])){throw 'Empty marker key/value'}
        if($parsed.Contains($parts[0])){throw "Duplicate marker key $($parts[0])"}
        $parsed[$parts[0]]=$parts[1]
    }
    $required=[ordered]@{HANDOFF_ID=$HandoffId;UID=$Uid;SEALED_ROOT=$NewRoot;MANIFEST_ROWS='39';MANIFEST_SHA256=$manifestHash;VERDICT=$Verdict}
    foreach($key in $required.Keys){if(-not$parsed.Contains($key)-or[string]$parsed[$key]-cne[string]$required[$key]){throw "Marker exact key failed $key"}}

    $markerDest=[IO.Path]::Combine($NewRoot,'WRITE_STOPPED')
    [IO.File]::Move($ExternalMarker,$markerDest);$MarkerMoved=$true
    $filesBefore=FileSnapshot $NewRoot;$dirsBefore=DirectorySnapshot $NewRoot

    $finalFiles=@(Get-ChildItem -LiteralPath $NewRoot -Recurse -File -Force)
    $finalDirs=@((Get-Item -LiteralPath $NewRoot -Force))+@(Get-ChildItem -LiteralPath $NewRoot -Recurse -Directory -Force)
    if($finalFiles.Count-ne42){throw "Final files $($finalFiles.Count), expected 42"}
    $roFiles=@($finalFiles|Where-Object{([IO.File]::GetAttributes($_.FullName)-band[IO.FileAttributes]::ReadOnly)-ne0})
    $roDirs=@($finalDirs|Where-Object{([IO.File]::GetAttributes($_.FullName)-band[IO.FileAttributes]::ReadOnly)-ne0})
    if($roFiles.Count-ne42-or$roDirs.Count-ne$finalDirs.Count){throw 'Final ReadOnly failed'}
    $markers=@($finalFiles|Where-Object Name -CEQ 'WRITE_STOPPED');if($markers.Count-ne1){throw 'Marker count failed'}
    $marker=$markers[0];$others=@($finalFiles|Where-Object FullName -CNE $marker.FullName)
    $at=@($others|Where-Object{$_.LastWriteTimeUtc.ToFileTimeUtc()-ge$marker.LastWriteTimeUtc.ToFileTimeUtc()});if($at.Count-ne0){throw 'At/after marker failed'}
    $manifestCheck=ManifestGate $NewRoot $manifest 39;ParseGate $NewRoot;$h=Hygiene $NewRoot
    if($h.ads-ne0-or$h.cache_pyc-ne0-or$h.reparse-ne0){throw 'Final hygiene failed'}
    $copyMismatch=0
    foreach($row in $copyRows){$did=FileId $NewRoot $row.destination_resolved_path;if($did.bytes-ne$row.source_bytes-or$did.sha256-cne$row.source_sha256-or$did.creation_filetime_utc_ticks-ne$row.source_creation_filetime_utc_ticks-or$did.last_write_filetime_utc_ticks-ne$row.source_last_write_filetime_utc_ticks){$copyMismatch++}}
    if($copyMismatch-ne0){throw "Final copy mismatch $copyMismatch"}
    $oldAfter=FileSnapshot $OldRoot;$oldDiff=MapDiff $oldBefore $oldAfter;if($oldDiff.Count-ne0){throw "Old root changed $($oldDiff.Count)"}
    $filesAfter=FileSnapshot $NewRoot;$dirsAfter=DirectorySnapshot $NewRoot
    $postFile=MapDiff $filesBefore $filesAfter;$postDir=MapDiff $dirsBefore $dirsAfter
    if($postFile.Count-ne0-or$postDir.Count-ne0){throw 'Postmarker changes detected'}

    $result=[ordered]@{
        status='PASS';handoff_id=$HandoffId;uid=$Uid;verdict=$Verdict
        controller_resolved_path=$PSCommandPath;controller_bytes=$controller.bytes;controller_sha256=$controller.sha256;controller_ast_parse_errors=0
        invocation_count=1;retry_count=0;started_utc=$StartedUtc.ToString('o');finished_utc=[DateTime]::UtcNow.ToString('o')
        source_root_resolved=$OldRoot;sealed_root_resolved=$NewRoot;old_root_ordinary=$oldBefore.Count;old_root_identity_mismatch_after=$oldDiff.Count
        old_manifest_material_rows=37;copied_old_controls=0;copy_identity_rows=$copyRows.Count;source_destination_identity_mismatch=$copyMismatch
        payload_count=39;manifest_rows=$manifestCheck.rows;manifest_identity_mismatch=$manifestCheck.mismatch;manifest_extra=$manifestCheck.extra;manifest_unlisted=$manifestCheck.unlisted
        manifest_resolved_path=$manifest;manifest_bytes=(Get-Item -LiteralPath $manifest).Length;manifest_sha256=Sha $manifest
        seal_audit_resolved_path=$sealAudit;seal_audit_bytes=(Get-Item -LiteralPath $sealAudit).Length;seal_audit_sha256=Sha $sealAudit
        write_stopped_resolved_path=$markerDest;write_stopped_bytes=(Get-Item -LiteralPath $markerDest).Length;write_stopped_sha256=Sha $markerDest
        write_stopped_filetime_utc_ticks=$marker.LastWriteTimeUtc.ToFileTimeUtc();max_other_filetime_utc_ticks=[int64](($others|ForEach-Object{$_.LastWriteTimeUtc.ToFileTimeUtc()}|Measure-Object -Maximum).Maximum)
        at_or_after_excluding_marker=$at.Count;ordinary_count=$finalFiles.Count;readonly_files=$roFiles.Count;directory_count_including_root=$finalDirs.Count;readonly_directories=$roDirs.Count
        marker_physical_lines=$physical.Count;marker_unique_keys=$parsed.Count;marker_required_exact_matches=6;marker_bad_or_orphan_lines=0;placeholder_tab_rue_count=0
        json_csv_parse_failures=0;ads_count=$h.ads;cache_pyc_count=$h.cache_pyc;reparse_count=$h.reparse
        postmarker_file_content_or_attribute_changes=$postFile.Count;postmarker_directory_attribute_changes=$postDir.Count
    }
    ExternalResult $result
    $result|ConvertTo-Json -Depth 12
}
catch{
    $message=$_.Exception.Message
    if(-not$MarkerMoved-and[IO.Directory]::Exists($NewRoot)){
        foreach($file in @(Get-ChildItem -LiteralPath $NewRoot -Recurse -File -Force)){try{SetRO $file.FullName}catch{}}
        foreach($dir in @((Get-Item -LiteralPath $NewRoot -Force))+@(Get-ChildItem -LiteralPath $NewRoot -Recurse -Directory -Force)){try{SetRO $dir.FullName}catch{}}
    }
    if(-not[IO.File]::Exists($ExternalResult)){
        ExternalResult ([ordered]@{status='FAIL';handoff_id=$HandoffId;invocation_count=1;retry_count=0;marker_moved=$MarkerMoved;started_utc=$StartedUtc.ToString('o');finished_utc=[DateTime]::UtcNow.ToString('o');error=$message;source_root_resolved=$OldRoot;attempted_root_resolved=$NewRoot})
    }
    throw
}
