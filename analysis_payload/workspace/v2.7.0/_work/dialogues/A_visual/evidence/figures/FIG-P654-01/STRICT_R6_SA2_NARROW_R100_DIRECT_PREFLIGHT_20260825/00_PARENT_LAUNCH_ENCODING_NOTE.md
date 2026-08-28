# Preliminary parent-launch encoding note

An initial attempt to run `run_direct_parent_preflight.ps1` itself under Windows PowerShell 5.1 stopped before child creation because that host interpreted the UTF-8-without-BOM script literal as CP936 and corrupted the Chinese absolute path. The failure occurred at the parent's `texcache` existence check.

- Ordinary child PowerShell started: no
- `kpsewhich` started: no
- Probe written: no
- TeX typesetter started: no
- Cache entries after this stop: zero

The actual R6 preflight therefore uses UTF-8-native PowerShell 7 as the planned direct-call parent. That parent launches an ordinary Windows PowerShell child, whose stdout encoding is explicitly UTF-8 so the captured absolute environment and `kpsewhich` values remain lossless. This is an encoding correction to the diagnostic harness, not a source or TeX-build retry.
