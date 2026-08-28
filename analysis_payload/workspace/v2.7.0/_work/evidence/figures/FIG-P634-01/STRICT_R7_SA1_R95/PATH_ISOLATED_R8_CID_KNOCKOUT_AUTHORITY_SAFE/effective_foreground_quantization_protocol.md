# Effective-foreground closure on the official 8-bit lattice

For each official CID and each native coordinate, the local background is the same-coordinate official knockout RGB `K` (the official page with only that CID changed to `Tr 3`).  The official supports are:

- `B = max_abs(crop-baseline RGB − K) >= 20`;
- `D = max_abs(direct full-page native RGB − K) >= 20`;
- `R = max_abs(round_8bit(alpha/255 × official_fill_RGB + (1−alpha/255) × K) − K) >= 20` (diagnostic only).

`B` and `D` are rendered by the same official PDF renderer and must have coordinate-wise `B XOR D = 0`; `D` is the final-visible raw mask. Every `D` pixel must be inside exactly the isolated official CID alpha support, and the raw mask must have zero foreign pixels. `B & ~D` is the only later-paint occlusion test and must be zero. The transparent CID replay proves actual path/source identity but is not a raw-mask authority: the 8-bit `R` diagnostic can overpredict a coloured-background threshold coordinate. Every such coordinate is enumerated and classified in `glyph_replay_integer_lattice_quantization_ledger.csv`; no coordinate has an unclassified status.

R8 transparency/integer diagnostic rows: 148; unexplained rows: 0.  The four `T020` alpha=23 overpredict coordinates retain B/D, background, float and integer values in that ledger.
