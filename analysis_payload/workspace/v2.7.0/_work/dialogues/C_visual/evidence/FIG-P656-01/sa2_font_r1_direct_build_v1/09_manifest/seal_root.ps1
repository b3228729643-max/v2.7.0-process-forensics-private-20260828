#requires -Version 7.4

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$Root = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P656-01\sa2_font_r1_direct_build_v1'
$Manifest = Join-Path $Root '09_manifest\MANIFEST.csv'
$Marker = Join-Path $Root 'WRITE_STOPPED.json'
if (Test-Path -LiteralPath $Manifest) { throw 'MANIFEST_ALREADY_EXISTS' }
if (Test-Path -LiteralPath $Marker) { throw 'WRITE_STOPPED_ALREADY_EXISTS' }

function Get-Sha256([string] $Path) {
    return (Get-FileHash -Algorithm SHA256 -LiteralPath $Path).Hash
}

function Escape-Csv([object] $Value) {
    $text = [string] $Value
    return '"' + $text.Replace('"', '""') + '"'
}

$rootFull = [IO.Path]::GetFullPath($Root)
$files = @(Get-ChildItem -LiteralPath $Root -File -Recurse | Where-Object {
    $_.FullName -cne $Manifest -and $_.FullName -cne $Marker
} | Sort-Object FullName)
$lines = [Collections.Generic.List[string]]::new()
$lines.Add('relative_path,resolved_path,bytes,sha256,last_write_utc,filetime_utc_ticks')
foreach ($file in $files) {
    $relative = [IO.Path]::GetRelativePath($rootFull, $file.FullName).Replace('\', '/')
    $values = @(
        $relative,
        [IO.Path]::GetFullPath($file.FullName),
        $file.Length,
        (Get-Sha256 $file.FullName),
        $file.LastWriteTimeUtc.ToString('o'),
        $file.LastWriteTimeUtc.ToFileTimeUtc()
    )
    $lines.Add(($values | ForEach-Object { Escape-Csv $_ }) -join ',')
}
[IO.File]::WriteAllLines($Manifest, $lines, [Text.UTF8Encoding]::new($false))

$payloadAndManifest = @($files + (Get-Item -LiteralPath $Manifest))
foreach ($file in $payloadAndManifest) { $file.IsReadOnly = $true }
if (@($payloadAndManifest | Where-Object { -not (Get-Item -LiteralPath $_.FullName).IsReadOnly }).Count -ne 0) {
    throw 'PAYLOAD_READONLY_FREEZE_FAILED'
}

$manifestIdentity = Get-Item -LiteralPath $Manifest
$markerData = [ordered]@{
    schema = 'P656_R1_WRITE_STOPPED_V1'
    handoff_id = 'C-FIG-P656-01-SA2-FONT-DIRECT-BUILD-R1-LOCAL-V1'
    status = 'LOCAL_SA2_PASS_READY_FOR_MAIN'
    recorded_utc = [DateTime]::UtcNow.ToString('o')
    root = $rootFull
    payload_count = $files.Count
    manifest_entry_count = $files.Count
    manifest_self_excluded = $true
    marker_self_excluded = $true
    final_ordinary_file_count = $files.Count + 2
    manifest = [ordered]@{
        path = [IO.Path]::GetFullPath($Manifest)
        bytes = $manifestIdentity.Length
        sha256 = Get-Sha256 $Manifest
    }
    source_sha256 = '9D404ED0694D575DE89038D3D6485C49AA4C60DCC3238AD8318CADACF810B381'
    wrapper_sha256 = '6092B8A09AC8AF8C0605599CA6C2583530EC2D5DE13F4F6847244015AAC0A3C9'
    pdf_sha256 = '1B01C9FFA6E80AEFB79107BFDAE2B7014893BFCAA76654F756DB49AEE7E6C869'
    denominators = [ordered]@{ glyphs = 90; drawings = 25; objects = 115; unordered_pairs = 6555; critical_pairs = 34; clip_rows = 115 }
    failures = [ordered]@{ empty_masks = 0; clip = 0; manual_objects = 0; critical_pairs = 0; views = 0; hard_gates = 0; unresolved = 0 }
    invocation_count = 1
    retry_count = 0
    post_tex_process_count = 0
    all_payload_and_manifest_readonly_before_marker = $true
    no_more_root_writes_authorized = $true
}
[IO.File]::WriteAllText($Marker, ($markerData | ConvertTo-Json -Depth 10), [Text.UTF8Encoding]::new($false))
(Get-Item -LiteralPath $Marker).IsReadOnly = $true
$rootItem = Get-Item -LiteralPath $Root -Force
$rootItem.Attributes = $rootItem.Attributes -bor [IO.FileAttributes]::ReadOnly
