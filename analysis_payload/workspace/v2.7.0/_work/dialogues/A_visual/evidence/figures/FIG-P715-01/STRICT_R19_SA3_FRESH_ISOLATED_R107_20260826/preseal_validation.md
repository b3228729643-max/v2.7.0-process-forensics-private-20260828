# Pre-seal machine/manual consistency validation

The final read-only cross-check was run after every manual ledger and decision file had been authored.

- Frozen PDF: 4,967,249 bytes; SHA256 `8811950621E2D64A3C2A8F0F7A52DD0FAC2BDB12018F3EA052C1F58C94EF8DF3`.
- Frozen source: 4,057 bytes; SHA256 `900C3A8F72A7A6434101FEE9914019150D3D5F655A23FC5BF41EDB853C25EE87`.
- Object count / unique object IDs: 298 / 298.
- Pair rows / unique pair IDs: 44,253 / 44,253.
- Pair membership violations / self-pairs: 0 / 0.
- Machine candidates / candidate pixels: 0 / 0.
- Glyph machine rows / manual rows / ID delta / manual non-PASS: 255 / 255 / 0 / 0.
- Drawing machine rows / manual rows / ID delta / manual non-PASS: 43 / 43 / 0 / 0.
- Relation machine rows / manual rows / ID delta / manual non-PASS: 8 / 8 / 0 / 0.
- Glyph masks / drawing masks: 255 / 43.
- Glyph sheets / drawing sheets / relationship images / final figure views: 8 / 2 / 8 / 4.

Because every pair row uses only a frozen object ID, no row is self-paired, every unordered key is unique, and the pair count equals `choose(298,2)`, the unordered-pair ledger is exhaustive. Machine counts, manually reviewed IDs, manual decisions, and `RESULT.txt` are mutually consistent.
