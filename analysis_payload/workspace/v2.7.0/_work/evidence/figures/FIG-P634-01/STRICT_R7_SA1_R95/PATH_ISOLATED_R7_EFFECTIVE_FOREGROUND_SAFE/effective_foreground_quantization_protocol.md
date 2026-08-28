# Effective-foreground closure on the official 8-bit lattice

For each official CID and each native coordinate, the local background is the same-coordinate official knockout RGB `K` (the official page with only that CID changed to `Tr 3`).  The three gate supports are:

- `B = max_abs(crop-baseline RGB − K) >= 20`;
- `D = max_abs(direct full-page native RGB − K) >= 20`;
- `R = max_abs(round_8bit(alpha/255 × official_fill_RGB + (1−alpha/255) × K) − K) >= 20`.

`round_8bit` occurs before the threshold because the authoritative direct page is an 8-bit RGB lattice.  The audit requires coordinate-wise `B XOR D = 0`, `B XOR R = 0`, and `D XOR R = 0`; it does not compare totals alone.  The transparent replay alpha remains separately ledgered.

R7 quantization-boundary rows: 148; unexpected boundary rows: 4.  Each boundary coordinate is listed in `glyph_replay_integer_lattice_quantization_ledger.csv`.
