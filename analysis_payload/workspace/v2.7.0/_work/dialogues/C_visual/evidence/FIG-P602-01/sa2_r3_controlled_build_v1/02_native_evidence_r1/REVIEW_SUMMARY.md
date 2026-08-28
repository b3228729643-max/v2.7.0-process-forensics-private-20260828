# FIG-P602-01 R3 native evidence review summary

Outcome: `C_LOCAL_PASS_CANDIDATE_PENDING_MAIN_ACCEPTANCE`.

This is a fresh review of the R3 v1 PDF. No R101 or R2 manual decision was copied or migrated. The candidate remains pending main acceptance and this file does not authorize a central inventory write or a commit.

## Frozen identities

- PDF: 41,653 bytes; SHA256 `68188DAAAF9B3C4233D5A032C3D8BE20A73B51D5E6058D0E1C12FDE6471093E7`.
- Source: 2,869 bytes; SHA256 `6C4E8F156709C0FF384F9E7B7F2BD5D9CB586E24206BF0BCD2E58933ED3DB47D`.
- Build START: SHA256 `4079A8BA4C6054A6693C6052578BED3056EA9AAD5DA3626477001C7245EDAF57`.
- Build RESULT: SHA256 `4746B6DA9D3F1F6DAA03DFBC31A8EBA6BFB6FC1A9A6048CBB8F878BEAB765D17`.
- Validator result before sealing: 8,397 bytes; SHA256 `04D0AF98D3DD4A311ED2D6E1A7B3BF00CFEA3D3969588CA9A686953A35602AA1`; outcome PASS with zero failures.

## Fresh denominators and decisions

| Family | Denominator | Machine failures | Manual failures |
|---|---:|---:|---:|
| objects | 30 | 0 | 0 |
| glyphs | 154 | 0 | 0 |
| unordered pairs | 435 = C(30,2) | 0 | 0 |
| critical pairs | 16 | 0 | 0 |
| peer rows | 28 | 0 | 0 |
| role rows | 3 | 0 | 0 |
| clip rows | 30 | 0 | 0 |
| views | 4 | 0 | 0 |
| hard gates | 12 | n/a | 0 |

The machine coverage check's 803 PNG figure is its intentionally narrow set of glyph masks/cards + object masks/cards + all pair cards. The final root validator separately opened the complete 864-PNG set after adding 16 critical enlargements, 35 contact sheets, five base renders, and five 8x landmarks.

## Targeted R3 result

G032 is now `范`, U+8303, CJK_FULL, 37x34 ink against a 30-pixel strict threshold. Its native300 card and 8x landmark show the grass crown and lower component intact. The source contains `未规范化目标` exactly once, contains neither older phrase, and contains no U+4E00 `一`.

All 30 object cards, 154 glyph cards, 435 unordered-pair cards, 16 critical enlargements, the full-page view, Poppler view, grayscale view, and five 8x landmarks were manually inspected. Intended endpoint/border/rule contacts remain whitelisted topology; no unintended collision, clipping, broken stroke, empty mask, or semantic drift was found.

Worktree scope remains one modified P602 source file with cumulative diffstat 10+/10- on branch `v2.7.0/dialogue-c-visual` at HEAD `eea4060c5229168e2b973bbaea81cf391e7a9dfd`. TeX-family processes were zero at terminal validation. No TeX retry, commit, fresh role, next figure, shared state, or inventory write occurred.
