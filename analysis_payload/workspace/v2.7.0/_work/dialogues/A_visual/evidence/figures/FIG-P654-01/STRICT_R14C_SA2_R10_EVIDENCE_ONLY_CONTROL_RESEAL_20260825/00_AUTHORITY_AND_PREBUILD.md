# P654 R10 controlled direct build

- Authority: P654_R10_BUILD_SLOT_GRANTED.
- Build mode: exactly one controller and one direct lualatex standalone invocation.
- Controller host: D:\PowerShell7\pwsh.exe, version 7.6.4.500 as independently verified by mainline.
- Forbidden: latexmk, concurrent TeX, automatic retry, second invocation.
- Source identity: 3,122 bytes; SHA-256 EA4A19FF940A177D4D754C4277896A2F38B75C1E6F252D8A374F418B84E31E6D.
- Wrapper identity: 397 bytes; SHA-256 FE44F2E6005D884A6916A11C6EBCB89CF40BD523A64D8F8C6BC8124DBABC0CA1.
- Controller content must remain byte-identical to the frozen R9 controller; only the external execution host and dynamic new-root path differ.
- R8 taxonomy is frozen and read-only. R7/R7A conclusions are not inherited.
- TEXMFVAR, TEXMFCACHE and TEXMFCONFIG must all bind to this R10 root's one writable texcache.
- Natural exit must be followed immediately by P654_R10_BUILD_SLOT_RELEASED and a TeX-process NONE check.
