# Final deterministic build commands

All commands used only the read-only local wrappers and wrote build/cache output under the dedicated SA2 evidence root. No official full-book build or official `strict_current_r95_fullbook` location was used.

## Page wrapper

Working directory:
`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\讲义源码\合并总册`

```powershell
$env:TEXMFVAR='D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\evidence\figures\FIG-P580-01\STRICT_R2_SA2_R95_LOCAL_20260824\build\texmf-var'
$env:TEXMFCACHE=$env:TEXMFVAR
& 'C:\Users\ASUS\AppData\Local\Programs\MiKTeX\miktex\bin\x64\latexmk.exe' -g -lualatex -interaction=nonstopmode -halt-on-error -file-line-error -outdir='D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\evidence\figures\FIG-P580-01\STRICT_R2_SA2_R95_LOCAL_20260824\build\page' 'v260_FIG-P580-01_page.tex'
```

Exit code: `0`. Final PDF: `build/page/v260_FIG-P580-01_page.pdf` (69,542 bytes). Final log: `build/page/v260_FIG-P580-01_page.log`.

## Standalone wrapper

Working directory:
`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\讲义源码\合并总册`

```powershell
$env:TEXMFVAR='D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\evidence\figures\FIG-P580-01\STRICT_R2_SA2_R95_LOCAL_20260824\build\texmf-var'
$env:TEXMFCACHE=$env:TEXMFVAR
& 'C:\Users\ASUS\AppData\Local\Programs\MiKTeX\miktex\bin\x64\latexmk.exe' -g -lualatex -interaction=nonstopmode -halt-on-error -file-line-error -outdir='D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\evidence\figures\FIG-P580-01\STRICT_R2_SA2_R95_LOCAL_20260824\build\standalone' 'v260_FIG-P580-01_standalone.tex'
```

Exit code: `0`. Final PDF: `build/standalone/v260_FIG-P580-01_standalone.pdf` (40,522 bytes). Final log: `build/standalone/v260_FIG-P580-01_standalone.log`.

## Revision-111 low-profile punctuation calibration

Working directory: dedicated SA2 evidence root.

```powershell
$env:TEXMFVAR='D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\evidence\figures\FIG-P580-01\STRICT_R2_SA2_R95_LOCAL_20260824\build\texmf-var'
$env:TEXMFCACHE=$env:TEXMFVAR
& 'C:\Users\ASUS\AppData\Local\Programs\MiKTeX\miktex\bin\x64\latexmk.exe' -g -lualatex -interaction=nonstopmode -halt-on-error -file-line-error -outdir='D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\evidence\figures\FIG-P580-01\STRICT_R2_SA2_R95_LOCAL_20260824\build\calibration' 'calibration_low_profile_punctuation.tex'
```

Exit code: `0`. Final calibration PDF: `build/calibration/calibration_low_profile_punctuation.pdf`.

## Native evidence reconstruction

```powershell
python audit_sa2_core.py
```

Exit code: `0`. The audit renders directly at native 300 dpi, uses integer cropping only, and records `resize_after_render=false` in `render_manifest.json`. The final run completed after both final wrapper builds.
