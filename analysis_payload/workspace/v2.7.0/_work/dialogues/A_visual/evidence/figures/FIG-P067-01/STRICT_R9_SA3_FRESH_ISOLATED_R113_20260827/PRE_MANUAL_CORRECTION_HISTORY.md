# Pre-manual correction history

All corrections below occurred before any manual reviewer boolean, decision, or note was authored. They are preserved to prevent an abandoned preliminary state from being mistaken for the final denominator.

1. The first PowerShell directory-creation syntax was unsupported (`New-Item -LiteralPath` in this environment). It created no content. The same exact root was then created with the .NET directory API.
2. A hardcoded `pdftotext.exe` path was absent. The installed read-only executable at `D:\texlive\2026\bin\windows\pdftotext.exe` was used instead.
3. One diagnostic Python stdout attempt encountered a GBK encoding error for mathematical Unicode. It was rerun with UTF-8 stdout; no evidence value was changed by that console-only failure.
4. An initial glyph-mask method added 2 px padding and imported neighboring antialias pixels. It was replaced, before manual decisions, by exact raw-dictionary character bounding boxes and all affected products were rebuilt.
5. PDF raw-dictionary spans split some visual formulas. Semantic parents were manually reconciled without changing the visible-glyph denominator.
6. A preliminary graphic enumeration used `Rect.intersects`, which excludes zero-width or zero-height line bounding boxes. That preliminary N=117/C=6,786 state is invalid and abandoned. Closed-interval geometry restored the missing visible line objects. The final frozen denominator is N=130 and C(130,2)=8,385. The obsolete pre-correction `critical_pair_contact_07_8x_nearest.png` was removed before validation/seal; the six final sheets cover all 71 final critical pairs.
7. The initial T021 fullwidth-colon mask included the adjacent G010 guide. Connected components were separated and the latest sheet 02 was reopened; T021 is a pure complete colon.
8. Five real high-opacity white node backgrounds were added as occlusion masks. Final-visible measurement correctly resolves P01217 and P05606 as occluded, while P01916 and P01917 remain real 34 px overlaps.

No seal attempt occurred before these corrections. The seal described by the external audit is the sole seal attempt.
