# FIG-P580-01 R2C final local build record

Both final wrappers were rebuilt after the business-source freeze. All cache and output paths were evidence-local. No official full-book build, central inventory/state update, public-style edit, or wrapper edit was performed.

## Page wrapper

Working directory: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\讲义源码\合并总册`

```powershell
$env:TEXMFVAR='D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\evidence\figures\FIG-P580-01\STRICT_R2C_SA2_GRAPHIC_PAIR_REPAIR_R95_LOCAL_20260824\build\texmf-var'
$env:TEXMFCACHE=$env:TEXMFVAR
& 'C:\Users\ASUS\AppData\Local\Programs\MiKTeX\miktex\bin\x64\latexmk.exe' -g -lualatex -interaction=nonstopmode -halt-on-error -file-line-error -outdir='D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\evidence\figures\FIG-P580-01\STRICT_R2C_SA2_GRAPHIC_PAIR_REPAIR_R95_LOCAL_20260824\build\page' 'v260_FIG-P580-01_page.tex'
```

Exit code: `0`. Final PDF: `build/page/v260_FIG-P580-01_page.pdf` (69,568 bytes). Its final log records one page and 69,568 bytes.

## Standalone wrapper

Working directory: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\讲义源码\合并总册`

```powershell
$env:TEXMFVAR='D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\evidence\figures\FIG-P580-01\STRICT_R2C_SA2_GRAPHIC_PAIR_REPAIR_R95_LOCAL_20260824\build\texmf-var'
$env:TEXMFCACHE=$env:TEXMFVAR
& 'C:\Users\ASUS\AppData\Local\Programs\MiKTeX\miktex\bin\x64\latexmk.exe' -g -lualatex -interaction=nonstopmode -halt-on-error -file-line-error -outdir='D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\evidence\figures\FIG-P580-01\STRICT_R2C_SA2_GRAPHIC_PAIR_REPAIR_R95_LOCAL_20260824\build\standalone' 'v260_FIG-P580-01_standalone.tex'
```

Exit code: `0`. Final PDF: `build/standalone/v260_FIG-P580-01_standalone.pdf` (40,556 bytes). Its final log records one page and 40,556 bytes.

## Native revision-111 reconstruction

```powershell
python audit_sa2_core.py
```

Exit code: `0`. The final reconstruction followed both wrapper builds, rendered directly at native 300 dpi with `resize_after_render=false`, regenerated every mask/package/view in this R2C directory, and did not reuse an R2B screenshot or mask.

No official full-book build was run. This record supports only `SA2_LOCAL_PASS_AWAIT_ROOT_OFFICIAL_BUILD`.
