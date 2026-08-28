# NTFS ADS check

- scope: every regular file recursively under this exact evidence root
- command basis: PowerShell `Get-Item -Stream *` with default `:$DATA` excluded
- nondefault ADS count: `0`
- decision: `PASS`
