$ErrorActionPreference = 'Stop'

$evidenceRoot = $PSScriptRoot
$manifestPath = Join-Path $evidenceRoot 'MANIFEST.csv'
$markerPath = Join-Path $evidenceRoot 'WRITE_STOPPED'
$recordsetPath = Join-Path $evidenceRoot 'RECORDSET_CONTENTS.sha256'
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)

foreach ($reservedPath in @($manifestPath, $markerPath, $recordsetPath)) {
    if (Test-Path -LiteralPath $reservedPath) {
        throw "Reserved sealing path already exists: $reservedPath"
    }
}

# The canonical recordset lists every payload/control file existing before the
# recordset itself. Its own SHA256 is recorded by both the manifest and marker.
$baseFiles = @(Get-ChildItem -LiteralPath $evidenceRoot -Recurse -File | Sort-Object FullName)
$recordLines = foreach ($file in $baseFiles) {
    $relative = $file.FullName.Substring($evidenceRoot.Length + 1).Replace('\', '/')
    $hash = (Get-FileHash -Algorithm SHA256 -LiteralPath $file.FullName).Hash.ToUpperInvariant()
    "$hash *$relative"
}
[System.IO.File]::WriteAllLines($recordsetPath, [string[]]$recordLines, $utf8NoBom)
$recordsetHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $recordsetPath).Hash.ToUpperInvariant()

# The non-self-referential manifest covers every ordinary file, including the
# recordset, but deliberately excludes MANIFEST.csv and WRITE_STOPPED.
$ordinaryFiles = @(Get-ChildItem -LiteralPath $evidenceRoot -Recurse -File |
    Where-Object { $_.FullName -ne $manifestPath -and $_.FullName -ne $markerPath } |
    Sort-Object FullName)
$manifestRows = foreach ($file in $ordinaryFiles) {
    [pscustomobject]@{
        RELATIVE_PATH = $file.FullName.Substring($evidenceRoot.Length + 1).Replace('\', '/')
        LENGTH_BYTES = $file.Length
        SHA256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $file.FullName).Hash.ToUpperInvariant()
    }
}
$manifestText = $manifestRows | ConvertTo-Csv -NoTypeInformation
[System.IO.File]::WriteAllLines($manifestPath, [string[]]$manifestText, $utf8NoBom)
$manifestHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $manifestPath).Hash.ToUpperInvariant()

# Make all existing files immutable before the final marker payload is created.
Get-ChildItem -LiteralPath $evidenceRoot -Recurse -File | ForEach-Object { $_.IsReadOnly = $true }
Start-Sleep -Milliseconds 1200

$markerLines = @(
    'HANDOFF_ID=C-FIG-P602-01-R103-SA1-FRESH-ISOLATED-V1'
    'REVIEWER_INSTANCE=/root/sa1_fig_p602_r103_fresh_isolated'
    'FIGURE_ID=FIG-P602-01'
    'RESULT=PASS'
    'HARD_FAILURE_IDS=NONE'
    'PHYSICAL_PAGE=653'
    'PRINTED_PAGE=640'
    'SEMANTIC_OBJECTS=32'
    'UNORDERED_PAIRS=496'
    'VISIBLE_GLYPHS=194'
    'CRITICAL_INTERSECTIONS=24'
    'PEER_GROUPS=25'
    'ROLE_GROUPS=9'
    'CLIP_CHECKS=32'
    'VIEWS=72'
    'HARD_GATES=20'
    "ORDINARY_FILES=$($ordinaryFiles.Count)"
    "MANIFEST_LISTED_FILES=$($ordinaryFiles.Count)"
    'EXPECTED_UNLISTED=MANIFEST.csv|WRITE_STOPPED'
    "RECORDSET_SHA256=$recordsetHash"
    "MANIFEST_SHA256=$manifestHash"
    'BUSINESS_SOURCE_WRITER_NEEDED=NO'
    'FUTURE_TEX_SLOT_NEEDED=NO'
    'NEXT_STEP=FRESH_ISOLATED_SA3_ONLY'
    'WRITES_AFTER_MARKER=0'
)
[System.IO.File]::WriteAllLines($markerPath, [string[]]$markerLines, $utf8NoBom)
(Get-Item -LiteralPath $markerPath).IsReadOnly = $true

"ordinary=$($ordinaryFiles.Count) manifest_sha256=$manifestHash recordset_sha256=$recordsetHash"
