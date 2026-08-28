$ErrorActionPreference='Stop'
$root=[IO.Path]::GetFullPath((Split-Path -Parent $MyInvocation.MyCommand.Path)); $src=[IO.Path]::GetFullPath('D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P654-01\STRICT_R10_SA2_TAXONOMY_R100_DIRECT_BUILD_20260825'); $controls=@('PAYLOAD_MANIFEST.csv','PAYLOAD_MANIFEST.json','WRITE_STOPPED.json')
$base=Get-Content (Join-Path $root 'R12_BASE_COPY_IDENTITY.json') -Raw|ConvertFrom-Json; if(@($base).Count -ne 1052){throw 'base identity count'}
$prov=Get-Content (Join-Path $root 'R12_COPY_PROVENANCE.json') -Raw|ConvertFrom-Json; if($prov.source_root -ne $src -or $prov.target_root -ne $root){throw 'provenance'}
$all=Get-ChildItem -LiteralPath $root -File -Recurse | Where-Object {$controls -notcontains $_.FullName.Substring($root.Length+1)}
$reportRel='R12_PRESEAL_VALIDATION.json'; $expected=$all.Count+1
$report=[ordered]@{status='PASS';source_to_dest_base_count=1052;identity_json_count=@($base).Count;identity_csv_rows=(Get-Content (Join-Path $root 'R12_BASE_COPY_IDENTITY.csv')).Count-1;current_payload_count=$all.Count;expected_payload_after_report=$expected;preseal_report_relative_path=$reportRel;provenance_status='PASS';source_root=$prov.source_root;target_root=$prov.target_root;ordinary_extension_denominator=[ordered]@{json=(@($all|Where-Object {$_.Extension -eq '.json'}).Count+1);csv=(@($all|Where-Object {$_.Extension -eq '.csv'}).Count+1);png=(@($all|Where-Object {$_.Extension -eq '.png'}).Count);pdf=(@($all|Where-Object {$_.Extension -eq '.pdf'}).Count)}}
$report|ConvertTo-Json -Depth 8|Set-Content (Join-Path $root $reportRel) -Encoding UTF8
$after=Get-ChildItem -LiteralPath $root -File -Recurse | Where-Object {$controls -notcontains $_.FullName.Substring($root.Length+1)}
if($after.Count -ne $expected -or !(Test-Path (Join-Path $root $reportRel))){throw 'payload expected count'}
