# R95 authority and native-pixel identity check

## Authority

- Current official candidate: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r95_fullbook\main_full.pdf`.
- Candidate file size: `4,934,184` bytes.
- Candidate SHA-256: `24CC8BE127D00435CC544E4E9142D45272675DA0D9967C89ADAC294D08910496`.
- Target: physical PDF page `625`, printed page `612`, FIG-P577-01.

## Native identity method

Both R94 and R95 were rendered directly with the identical command form:

```text
pdftoppm.exe -f 625 -l 625 -r 300 -png -singlefile <candidate.pdf> <output-base>
```

The resulting normal RGB rasters have shape `3508 × 2481 × 3` (height × width × channels). A direct channelwise NumPy comparison used no scaling, recolouring, crop re-render, or tolerance.

| Comparison scope | Pixel rectangle `[x0,y0,x1,y1]` | changed pixels | changed channels | max absolute channel delta |
|---|---:|---:|---:|---:|
| Full physical page | `[0,0,2481,3508]` | 0 | 0 | 0 |
| Defined figure scope | `[229,229,2251,1850]` | 0 | 0 | 0 |

Rendered artifacts:

- R94 bridge raster: `raw/official_page_625_300dpi.png`
- R95 official raster: `raw/r95_page_625_300dpi.png`

Each raster's SHA-256 is `a0a9ae288c82f724fc2bd433ed37df393e587be36b28a842e349597eeaf86583`.

## Consequence

R95 is the only current authority. The pre-existing R94-labelled raw raster was used solely as an exact-byte identity bridge; all glyph masks, overlays, and 8× nearest-neighbour views made from that raster are pixel-identical to R95 page 625 and are therefore reusable R95-pixel evidence. No old SA1/SA2 evidence has been read or reused.
