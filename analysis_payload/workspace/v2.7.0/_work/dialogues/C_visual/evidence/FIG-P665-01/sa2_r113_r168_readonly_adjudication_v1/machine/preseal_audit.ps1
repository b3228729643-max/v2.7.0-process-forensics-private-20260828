$ErrorActionPreference = 'Stop'
$Root = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P665-01\sa2_r113_r168_readonly_adjudication_v1'
$Output = Join-Path $Root 'machine\preseal_audit.json'

$Files = @(Get-ChildItem -LiteralPath $Root -Recurse -File)
$Directories = @((Get-Item -LiteralPath $Root)) + @(Get-ChildItem -LiteralPath $Root -Recurse -Directory)

$CsvParseErrors = 0
$JsonParseErrors = 0
$EmptyManualCells = 0
foreach ($File in $Files) {
    if ($File.Extension -ieq '.csv') {
        try {
            $Rows = @(Import-Csv -LiteralPath $File.FullName)
            if ($File.DirectoryName -eq (Join-Path $Root 'ledgers')) {
                foreach ($Row in $Rows) {
                    foreach ($Property in $Row.PSObject.Properties) {
                        if ([string]::IsNullOrWhiteSpace([string]$Property.Value)) { $EmptyManualCells++ }
                    }
                }
            }
        } catch { $CsvParseErrors++ }
    }
    if ($File.Extension -ieq '.json') {
        try { $null = Get-Content -LiteralPath $File.FullName -Raw | ConvertFrom-Json } catch { $JsonParseErrors++ }
    }
}

$ManualPairs = @(Import-Csv -LiteralPath (Join-Path $Root 'ledgers\pair_manual.csv'))
$MachinePairs = @(Import-Csv -LiteralPath (Join-Path $Root 'machine\all_unordered_object_pairs_machine.csv'))
$ManualPairIds = @($ManualPairs.pair_id | Sort-Object)
$MachinePairIds = @($MachinePairs.pair_id | Sort-Object)
$ManualPairKeys = @($ManualPairs | ForEach-Object { $_.object_a + '|' + $_.object_b } | Sort-Object)
$MachinePairKeys = @($MachinePairs | ForEach-Object { $_.object_a + '|' + $_.object_b } | Sort-Object)

$AdditionalAds = 0
foreach ($File in $Files) {
    $Streams = @(Get-Item -LiteralPath $File.FullName -Stream * -ErrorAction SilentlyContinue)
    $AdditionalAds += @($Streams | Where-Object { $_.Stream -ne ':$DATA' }).Count
}
$CachePyc = @($Files | Where-Object { $_.FullName -match '(^|[\\/])(__pycache__|\.cache)([\\/]|$)|\.(pyc|pyo)$|\.tmp$|~$' }).Count
$Reparse = @($Files + $Directories | Where-Object { ($_.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0 }).Count

$TextPayloads = @($Files | Where-Object { $_.Extension -in '.md', '.csv', '.json', '.txt' })
$PlaceholderHits = 0
foreach ($File in $TextPayloads) {
    $PlaceholderHits += @(Select-String -LiteralPath $File.FullName -Pattern '\bTODO\b|\bTBD\b|\bPLACEHOLDER\b|\bUNKNOWN\b' -AllMatches -ErrorAction Stop).Matches.Count
}

$Fingerprint = Get-Content -LiteralPath (Join-Path $Root 'machine\page_713_text_fingerprint.json') -Raw | ConvertFrom-Json
$Result = [ordered]@{
    root = $Root
    file_count_before_audit_output = $Files.Count
    directory_count = $Directories.Count
    csv_parse_errors = $CsvParseErrors
    json_parse_errors = $JsonParseErrors
    empty_manual_cells = $EmptyManualCells
    object_manual_rows = @(Import-Csv -LiteralPath (Join-Path $Root 'ledgers\object_manual.csv')).Count
    pair_manual_rows = $ManualPairs.Count
    pair_manual_unique_ids = @($ManualPairIds | Select-Object -Unique).Count
    pair_id_set_differences = @(Compare-Object $ManualPairIds $MachinePairIds).Count
    pair_object_set_differences = @(Compare-Object $ManualPairKeys $MachinePairKeys).Count
    text_glyph_manual_rows = @(Import-Csv -LiteralPath (Join-Path $Root 'ledgers\text_glyph_manual.csv')).Count
    geometry_manual_rows = @(Import-Csv -LiteralPath (Join-Path $Root 'ledgers\geometry_manual.csv')).Count
    view_manual_rows = @(Import-Csv -LiteralPath (Join-Path $Root 'ledgers\view_manual.csv')).Count
    hard_gate_manual_rows = @(Import-Csv -LiteralPath (Join-Path $Root 'ledgers\hard_gate_manual.csv')).Count
    mathematics_manual_rows = @(Import-Csv -LiteralPath (Join-Path $Root 'ledgers\mathematics_manual.csv')).Count
    semantic_manual_rows = @(Import-Csv -LiteralPath (Join-Path $Root 'ledgers\semantic_reading_order_manual.csv')).Count
    replacement_character_count = [int]$Fingerprint.replacement_character_count
    placeholder_hits = $PlaceholderHits
    additional_ads_count = $AdditionalAds
    cache_pyc_count = $CachePyc
    reparse_point_count = $Reparse
}
[IO.File]::WriteAllText($Output, (($Result | ConvertTo-Json -Depth 4) + "`n"), [Text.UTF8Encoding]::new($false))
$Result | ConvertTo-Json -Depth 4
