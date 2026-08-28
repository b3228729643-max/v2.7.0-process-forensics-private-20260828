# P126 R3A unsealed control failure report

HANDOFF_ID: `A-R115-P126-SA2-DIRECT-BUILD-R3A-20260828`

Classification: `UNSEALED_CONTROL_FAILURE_AFTER_PREMARKER_READONLY_FREEZE`.

## Preserved business direction

The non-TeX review completed before the control failure. Frozen denominator N=14 and all unordered pairs C=91 are closed. Genuine post-observation ledgers contain 14 objects, 91 pairs, 17 opened views, 10 math/semantic checks and 25 glyph/codepoint checks. The honest substantive verdict is `LOCAL_SA2_FAIL_RETURN_TO_MAIN_SOURCE_SCOPE`, with one unique hard defect: `HARD-LEGEND-GRAYSCALE-DASH-COLLAPSE`. The `更新 x_2` legend swatch renders as a continuous solid line rather than the requested multi-dash sample; native1x, nearest8x and pixel-run evidence agree. No additional TeX or source write followed the accepted R3A build.

## First control error

The intended static AST inspection used a nested PowerShell command whose trailing controller/auditor path arguments were interpreted by the nested host as commands instead of passive parser arguments. This unintentionally consumed the sole controller invocation. The controller completed both payload manifests and `SEAL_AUDIT.json`, then set all existing root files and directories ReadOnly. It stopped before marker staging/move at controller line 120:

`Measure-Object -Property @{ Expression = { $_.LastWriteTimeUtc.Ticks } } -Maximum`

PowerShell7 reported that the hashtable could not bind to `PSPropertyExpression`. No `WRITE_STOPPED`, external marker stage, controller result or auditor result was created. The auditor invocation count is 0. No retry, repair, rename, marker write or root mutation was attempted after the error.

## Frozen failure state

- Root ordinary files: 208; total bytes: 107,816,862.
- Directories including root: 12.
- ReadOnly: 208/208 files and 12/12 directories.
- Present controls: `PAYLOAD_MANIFEST.csv`, `PAYLOAD_MANIFEST.json`, `SEAL_AUDIT.json`.
- Missing control: `WRITE_STOPPED`.
- `PAYLOAD_MANIFEST.csv`: SHA-256 `405541B02D962FD75161DAEBB41C067955D7B99B992DD1F14A7399D3A6EB0D7E`.
- `PAYLOAD_MANIFEST.json`: SHA-256 `0F6072A10BE2D1F58B043190E741FCAEC69EACF98CFD5D0093C477A21D2125CD`.
- `SEAL_AUDIT.json`: SHA-256 `AC4386C51C81CF5450E8BA2F6E5765DD7CF52110D57F560AFCBCEF1D4C993993`.
- Controller: 12,295 bytes; SHA-256 `7C8E198CD641058C9F6CB53B406C0320393CEC3782B901260A7E06B3198B560D`; invocation1; retry0.
- Auditor: 9,439 bytes; SHA-256 `3A6C47F79068E4587E35BE5EFEC78B2A1D89EB13FE62AD87435A70FE39135F82`; invocation0.
- PDF unchanged: 33,952 bytes; SHA-256 `19F221487DB1930170608EAE0E09F019313791D808C724D05DBAC23465F746B2`.
- Source unchanged: 4,224 bytes; SHA-256 `366C905854F0F3952225600D5BD66AAB706B637A453FD23DDF9611E4C002AC20`.
- Terminal `latexmk/lualatex/luatex/luahbtex`: `0/0/0/0`.

The R3A root is not sealed and must not be presented as a sealed LOCAL_SA2 verdict. It is preserved exactly at the first error for Main adjudication. No sibling reseal or further source scope is implied or requested by this report.

