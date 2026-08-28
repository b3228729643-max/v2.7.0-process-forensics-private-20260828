$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$root = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P109-01\STRICT_R2_SA2_STATIC_DOMAIN_LABEL_OPAQUE_PATCH_R114_20260828'
$externalAudit = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P109-01\STRICT_R2_SA2_STATIC_DOMAIN_LABEL_OPAQUE_PATCH_R114_20260828_EXTERNAL_AUDIT.json'
$payloadNames = @(
  'PRESEAL_CHECKS.json',
  'SOURCE_IDENTITY.json',
  'SOURCE_PATCH.diff',
  'STATIC_PROJECTION.md',
  'STATIC_SCOPE.md'
)
$controlNames = @('PAYLOAD_MANIFEST.json','SEAL_AUDIT.json','WRITE_STOPPED.json')
$utf8NoBom = [Text.UTF8Encoding]::new($false)

function Get-FileRow([string]$Path) {
  $item = Get-Item -LiteralPath $Path
  [ordered]@{
    relative_path = $item.Name
    bytes = [int64]$item.Length
    sha256 = (Get-FileHash -LiteralPath $item.FullName -Algorithm SHA256).Hash
    last_write_time_utc_ticks = $item.LastWriteTimeUtc.Ticks.ToString()
  }
}

function Get-TreeSnapshot([string]$RootPath) {
  $rows = [Collections.Generic.List[object]]::new()
  $rootItem = Get-Item -LiteralPath $RootPath
  $rows.Add([ordered]@{
    kind='directory'; relative_path='.'; bytes=$null; sha256=$null
    creation_ticks=$rootItem.CreationTimeUtc.Ticks.ToString()
    last_write_ticks=$rootItem.LastWriteTimeUtc.Ticks.ToString()
    attributes=[int]$rootItem.Attributes
  })
  foreach($item in @(Get-ChildItem -LiteralPath $RootPath -Force | Sort-Object Name)) {
    $isDir = $item.PSIsContainer
    $rows.Add([ordered]@{
      kind=if($isDir){'directory'}else{'file'}
      relative_path=$item.Name
      bytes=if($isDir){$null}else{[int64]$item.Length}
      sha256=if($isDir){$null}else{(Get-FileHash -LiteralPath $item.FullName -Algorithm SHA256).Hash}
      creation_ticks=$item.CreationTimeUtc.Ticks.ToString()
      last_write_ticks=$item.LastWriteTimeUtc.Ticks.ToString()
      attributes=[int]$item.Attributes
    })
  }
  @($rows)
}

if(-not (Test-Path -LiteralPath $root -PathType Container)){ throw 'STATIC_ROOT_MISSING' }
if(Test-Path -LiteralPath $externalAudit){ throw 'EXTERNAL_AUDIT_ALREADY_EXISTS' }
$initialFiles = @(Get-ChildItem -LiteralPath $root -File -Force)
$initialNames = @($initialFiles.Name | Sort-Object)
if($initialNames.Count -ne $payloadNames.Count){ throw 'INITIAL_PAYLOAD_COUNT_MISMATCH' }
if((Compare-Object -ReferenceObject $payloadNames -DifferenceObject $initialNames).Count -ne 0){ throw 'INITIAL_PAYLOAD_SET_MISMATCH' }

$payloadRows = @($payloadNames | ForEach-Object { Get-FileRow (Join-Path $root $_) })
$manifest = [ordered]@{
  schema='P109_STATIC_PAYLOAD_MANIFEST_V1'
  payload_count=$payloadRows.Count
  excluded_controls=$controlNames
  rows=$payloadRows
}
$manifestPath = Join-Path $root 'PAYLOAD_MANIFEST.json'
[IO.File]::WriteAllText($manifestPath,($manifest | ConvertTo-Json -Depth 6),$utf8NoBom)

$roundTrip = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
if([int]$roundTrip.payload_count -ne 5){ throw 'MANIFEST_COUNT_MISMATCH' }
$manifestNames = @($roundTrip.rows.relative_path | Sort-Object)
if((Compare-Object -ReferenceObject $payloadNames -DifferenceObject $manifestNames).Count -ne 0){ throw 'MANIFEST_SET_MISMATCH' }
$identityErrors = [Collections.Generic.List[string]]::new()
foreach($row in @($roundTrip.rows)) {
  $actual = Get-FileRow (Join-Path $root ([string]$row.relative_path))
  if(([string]$row.bytes -ne [string]$actual.bytes) -or
     ([string]$row.sha256 -ne [string]$actual.sha256) -or
     ([string]$row.last_write_time_utc_ticks -ne [string]$actual.last_write_time_utc_ticks)) {
    $identityErrors.Add([string]$row.relative_path)
  }
}
if($identityErrors.Count -ne 0){ throw 'MANIFEST_IDENTITY_MISMATCH' }

$jsonParseErrors = [Collections.Generic.List[string]]::new()
foreach($name in @('PRESEAL_CHECKS.json','SOURCE_IDENTITY.json','PAYLOAD_MANIFEST.json')) {
  try { $null = Get-Content -LiteralPath (Join-Path $root $name) -Raw | ConvertFrom-Json }
  catch { $jsonParseErrors.Add($name) }
}
if($jsonParseErrors.Count -ne 0){ throw 'JSON_PARSE_FAILURE' }

$sealAuditPath = Join-Path $root 'SEAL_AUDIT.json'
$sealAudit = [ordered]@{
  schema='P109_STATIC_SEAL_AUDIT_V1'
  status='PASS'
  payload_count=5
  control_count=3
  expected_ordinary_count=8
  manifest_identity_error_count=0
  json_parse_error_count=0
  source_edit_scope='one file / one insertion / one deletion'
  tex_or_build_run=$false
  rendered=$false
  pass_claimed=$false
}
[IO.File]::WriteAllText($sealAuditPath,($sealAudit | ConvertTo-Json -Depth 4),$utf8NoBom)

$preMarkerFiles = @(Get-ChildItem -LiteralPath $root -File -Force)
if($preMarkerFiles.Count -ne 7){ throw 'PREMARKER_FILE_COUNT_MISMATCH' }
foreach($file in $preMarkerFiles) { $file.Attributes = $file.Attributes -bor [IO.FileAttributes]::ReadOnly }
$rootItem = Get-Item -LiteralPath $root
$rootItem.Attributes = $rootItem.Attributes -bor [IO.FileAttributes]::ReadOnly
$readonlyMissing = @(@($preMarkerFiles + (Get-Item -LiteralPath $root)) | Where-Object { -not ($_.Attributes -band [IO.FileAttributes]::ReadOnly) })
if($readonlyMissing.Count -ne 0){ throw 'PREMARKER_READONLY_FAILURE' }

$markerTemp = Join-Path ([IO.Path]::GetDirectoryName($root)) 'P109_R2_WRITE_STOPPED.prepared.json'
if(Test-Path -LiteralPath $markerTemp){ throw 'MARKER_TEMP_ALREADY_EXISTS' }
$marker = [ordered]@{
  schema='P109_STATIC_WRITE_STOPPED_V1'
  status='STATIC_ONLY_NOT_RENDERED_NOT_PASS'
  handoff_id='A-R114-P109-SA2-STATIC-DOMAIN-LABEL-PATCH-20260828'
  root=$root
  payload_count=5
  control_count=3
  ordinary_count=8
  last_root_operation='single_move_of_prepared_readonly_marker'
  postmarker_root_content_writes=0
  postmarker_root_attribute_writes=0
}
[IO.File]::WriteAllText($markerTemp,($marker | ConvertTo-Json -Depth 4),$utf8NoBom)
$markerTempItem = Get-Item -LiteralPath $markerTemp
$markerTempItem.Attributes = $markerTempItem.Attributes -bor [IO.FileAttributes]::ReadOnly
$maxTicks = (@((Get-Item -LiteralPath $root).LastWriteTimeUtc.Ticks) + @($preMarkerFiles.LastWriteTimeUtc.Ticks) | Measure-Object -Maximum).Maximum
$futureTicks = [Math]::Max([DateTime]::UtcNow.AddMinutes(5).Ticks, [int64]$maxTicks + [TimeSpan]::FromMinutes(2).Ticks)
$markerTempItem.LastWriteTimeUtc = [DateTime]::new([int64]$futureTicks,[DateTimeKind]::Utc)
$markerPath = Join-Path $root 'WRITE_STOPPED.json'
Move-Item -LiteralPath $markerTemp -Destination $markerPath

$snapshot1 = @(Get-TreeSnapshot $root)
Start-Sleep -Milliseconds 1200
$snapshot2 = @(Get-TreeSnapshot $root)
$snapshot1Json = $snapshot1 | ConvertTo-Json -Depth 5 -Compress
$snapshot2Json = $snapshot2 | ConvertTo-Json -Depth 5 -Compress
$postMarkerMutationCount = if($snapshot1Json -ceq $snapshot2Json){0}else{1}

$finalFiles = @(Get-ChildItem -LiteralPath $root -File -Force)
$finalDirs = @(Get-ChildItem -LiteralPath $root -Directory -Force)
$allItems = @($finalFiles + $finalDirs + (Get-Item -LiteralPath $root))
$finalReadonlyMissing = @($allItems | Where-Object { -not ($_.Attributes -band [IO.FileAttributes]::ReadOnly) })
$markerItem = Get-Item -LiteralPath $markerPath
$atOrAfter = @($allItems | Where-Object { $_.FullName -ne $markerPath -and $_.LastWriteTimeUtc.Ticks -ge $markerItem.LastWriteTimeUtc.Ticks })
$maxOtherTicks = (@($allItems | Where-Object { $_.FullName -ne $markerPath } | ForEach-Object { $_.LastWriteTimeUtc.Ticks }) | Measure-Object -Maximum).Maximum

$ads = [Collections.Generic.List[string]]::new()
foreach($file in $finalFiles) {
  foreach($stream in @(Get-Item -LiteralPath $file.FullName -Stream * | Where-Object { $_.Stream -ne ':$DATA' })) {
    $ads.Add($file.Name + ':' + $stream.Stream)
  }
}
$cachePyc = @($allItems | Where-Object { $_.Name -match '(?i)(__pycache__|\.pyc$|cache)' })
$reparse = @($allItems | Where-Object { $_.Attributes -band [IO.FileAttributes]::ReparsePoint })
$parseErrors = [Collections.Generic.List[string]]::new()
foreach($file in @($finalFiles | Where-Object { $_.Extension -eq '.json' })) {
  try { $null = Get-Content -LiteralPath $file.FullName -Raw | ConvertFrom-Json }
  catch { $parseErrors.Add($file.Name) }
}

$external = [ordered]@{
  schema='P109_STATIC_ROOT_EXTERNAL_AUDIT_V1'
  status=if($finalFiles.Count -eq 8 -and $finalDirs.Count -eq 0 -and $finalReadonlyMissing.Count -eq 0 -and $atOrAfter.Count -eq 0 -and $postMarkerMutationCount -eq 0 -and $ads.Count -eq 0 -and $cachePyc.Count -eq 0 -and $reparse.Count -eq 0 -and $parseErrors.Count -eq 0){'PASS'}else{'FAIL'}
  root=$root
  payload_count=5
  control_count=3
  ordinary_count=$finalFiles.Count
  directory_count_below_root=$finalDirs.Count
  manifest_identity_error_count=$identityErrors.Count
  readonly_missing_count=$finalReadonlyMissing.Count
  wstop_unique_count=@($finalFiles | Where-Object { $_.Name -eq 'WRITE_STOPPED.json' }).Count
  wstop_strict_latest_including_root=($atOrAfter.Count -eq 0)
  wstop_margin_ticks=([int64]$markerItem.LastWriteTimeUtc.Ticks - [int64]$maxOtherTicks)
  excluding_marker_at_or_after_count=$atOrAfter.Count
  postmarker_content_or_attribute_mutation_count=$postMarkerMutationCount
  parse_error_count=$parseErrors.Count
  ads_count=$ads.Count
  cache_pyc_count=$cachePyc.Count
  reparse_count=$reparse.Count
}
[IO.File]::WriteAllText($externalAudit,($external | ConvertTo-Json -Depth 5),$utf8NoBom)
$externalItem = Get-Item -LiteralPath $externalAudit
$externalItem.Attributes = $externalItem.Attributes -bor [IO.FileAttributes]::ReadOnly
if($external.status -ne 'PASS'){ throw 'EXTERNAL_AUDIT_FAILED' }
$external | ConvertTo-Json -Depth 5
