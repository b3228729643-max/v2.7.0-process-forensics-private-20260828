# FIG-P602-01 — Fresh Isolated SA3 Review (Official R101)

## Verdict

- **RESULT: FAIL**
- **FIGURE_STRICT_RESULT: FAIL**
- **PACKAGE_COMPLETENESS: PASS**
- The evidence package is complete and denominator-closed, but the official R101 figure fails the current strict glyph, peer-consistency, and role-consistency gates. No exception was invented or inherited.

## Isolation and access attestation

This review was performed independently from zero. Project evidence inputs were limited to the official PDF, the current figure source, the necessary adjacent chapter source, `GOAL.md`, the v2.7.0 Goal prompt, the strict pixel/typography protocol, and the strict figure-evidence schema. The PDF and codex-lean skill files were used only as procedural execution instructions and were not treated as project evidence. No prior or sibling P602 evidence, SA1 report, ledger, root/reseal/handoff, C or central state/inventory, historical chat conclusion, other-agent output, or other figure evidence was read.

All business sources were read-only. No TeX engine, LuaLaTeX, latexmk, build, or compilation was invoked. No source, chapter, macro, state, inventory, or handoff file was written. Every generated script, temporary artifact, render, measurement, ledger, and report is under this isolated root.

## Official input identity and independently located page

| Input | Bytes | SHA-256 | mtime_ns |
|---|---:|---|---:|
| official `main_full.pdf` | 4,947,496 | `0870ff226dc383875c4a1b6eabb06aab942317da294d90d2864b3030d46df1a1` | 1787597833697911500 |
| current figure source | 2,711 | `18b88f4bc48a21d3fd1a246ac5b6909deeb19900a3d0721c65f9a44369444084` | 1787625127884934000 |
| necessary adjacent chapter | 105,168 | `00f3537ae9dd6738f1bab414d587f18870a6b08d64663283c6f9a3f3048e6ba7` | 1787625128206720800 |

The official PDF contains 814 pages with A4 media size approximately 595.276 × 841.890 pt. I used PDF text-token search across the local neighborhood and native page rendering to locate the target independently. The target is **physical PDF page 651**, printed page **638**, figure **32.5**. The originally supplied page number was treated only as a search hint, not as a conclusion. Page-neighborhood evidence and the printed footer/caption confirmation are recorded under `identity/`.

## Mandatory native views

All mandatory views were rendered directly from the official PDF with no resize:

| View | DPI/mode | Native pixels | Reproducible crop in native 300-dpi page coordinates |
|---|---|---:|---|
| `full_page_200dpi.png` | 200 dpi RGB | 1654 × 2339 | full page |
| `figure_crop_300dpi.png` | 300 dpi RGB | 1835 × 1565 | `[300,1430,2135,2995]` |
| `standalone_300dpi.png` | 300 dpi RGB | 1835 × 1480 | `[300,1430,2135,2910]` |
| `grayscale_300dpi.png` | 300 dpi grayscale | 1835 × 1565 | `[300,1430,2135,2995]` |

All four manual view decisions are PASS. The measurement render and masks were likewise obtained from a direct native 300-dpi official-PDF render.

## Denominator closure

| Gate family | Total | PASS | FAIL | Closure |
|---|---:|---:|---:|---|
| semantic objects | 32 | 32 | 0 | complete |
| visible glyphs | 175 | 158 | 17 | complete |
| all unordered object pairs | 496 | 496 | 0 | complete; `C(32,2)=496` |
| critical pairs | 17 | 17 | 0 | complete |
| peer rows | 42 | 36 | 6 | complete |
| role rows | 3 | 2 | 1 | complete |
| clipping rows | 32 | 32 | 0 | complete |
| mandatory views | 4 | 4 | 0 | complete |
| hard gates | 12 | 8 | 4 | complete |

The machine layer found zero empty object masks, zero illegal-overlap pixels across all 496 pairs, zero clipped pixels across all 32 objects, and zero source-font audit failures. The pre-seal closure validator parsed and aligned every manual ledger to its machine denominator, verified all individual evidence paths, confirmed all 981 PNG files parse, and rehashed the three business inputs unchanged.

## Semantic object decomposition

The 32-object denominator consists of 19 text/formula objects and 13 GRAPHIC/MATH_RULE objects:

- Text/formula: `O-T01` through `O-T19`, covering the current/proposal/decision/accepted/rejected labels and formulae, edge labels, self-loop label, and both caption parts.
- Graphics: `O-G01` current border; `O-G02` proposal border; `O-G03` ratio border; `O-G04` visible fraction rule (independent `MATH_RULE` object); `O-G05` decision diamond; `O-G06` accepted border; `O-G07` rejected double border; `O-G08` proposal arrow; `O-G09` calculation arrow; `O-G10` decision arrow; `O-G11` accept arrow; `O-G12` reject arrow; `O-G13` self-loop.

Foreground PDF drawing indices accounted for are `[2,3,4,5,6,7,8,9,10,11,13,14,16,17,19,20,22,23,25,26]`. Drawing indices `12,15,18,21,24,27` are white label-background fills, not foreground semantic objects; each exclusion is recorded in the manifest/source audit. Every object has an isolated native mask, individual card, machine measurement, and unique manual decision reason.

## Strict glyph failures

All 175 visible glyph IDs have native-300-dpi measurements, isolated masks, cards, and 100%-coverage original/overlay/mask-only contact sheets. The following 17 fail the protocol exactly as written:

| ID | Failure |
|---|---|
| G007 | `U+003D`, H=12 px < fixed 22-px MATH_OPERATOR minimum |
| G013 | `U+002C`, same-codepoint/font/size calibrated H ratio 10/11=0.9091 < 0.92 |
| G014 | `U+22C5`, H=5 px < 22 px |
| G021 | `U+003D`, H=12 px < 22 px |
| G032 | `U+002C`, calibrated H ratio 10/11=0.9091 < 0.92 |
| G044 | `U+003D`, H=14 px < 22 px |
| G051 | `U+02DC`, H=6 px < 22 px |
| G062 | `U+02DC`, H=6 px < 22 px |
| G077 | `U+223C`, H=9 px < 22 px |
| G081 | `U+002C`, calibrated H ratio 11/10=1.10 > 1.08 |
| G092 | `U+002C`, calibrated H ratio 11/10=1.10 > 1.08 |
| G104 | `U+003D`, H=12 px < 22 px |
| G118 | `U+003D`, H=12 px < 22 px |
| G132 | `U+FF1A`, official-PDF calibration H ratio 21/25=0.84 < 0.92 |
| G160 | `U+4E00`, H=5 px < fixed 30-px CJK minimum; natural one-stroke shape is not an allowed reclassification |
| G164 | `U+FF1A`, official-PDF calibration H ratio 22/25=0.88 < 0.92 |
| G167 | `U+3001`, official-PDF calibration H ratio 16/10=1.60 > 1.08 |

The official-PDF same-codepoint/font/size calibration evidence used for punctuation is present in six calibration cards. No “looks natural” waiver or uncalibrated exception was used.

## Pair, overlap, clearance, and critical review

The all-pair table contains exactly every unordered pair once: 496 unique pair IDs for `C(32,2)`. Every pair has native 1× raw masks/overlay plus nearest-neighbor 8× raw-mask detail, a distance/overlap classification, an individual card, and a pair-specific manual reason. All 496 pass: no illegal overlap is present.

The 17 critical pairs were independently reviewed from their final cards and all pass:

`P0007`, `P0037`, `P0038`, `P0045`, `P0067`, `P0068`, `P0107`, `P0123`, `P0124`, `P0125`, `P0150`, `P0176`, `P0177`, `P0326`, `P0377`, `P0476`, `P0487`.

These include designed arrow/border contacts and overlaps, the decision-diamond contacts, the self-loop/rejected-border contact, the fraction-rule/formula relation, and the nearest title/formula or label/formula clearances. Each disposition is recorded by ID in `manual_critical_review.csv` rather than inferred globally.

## Peer and role failures

Six of 42 peer rows fail:

- `PEER21` (`O-T02` NODE_FORMULA lowercase): 20/24.5=0.8163, below bound.
- `PEER22` (`O-T05` NODE_FORMULA lowercase): 29/24.5=1.1837, above bound.
- `PEER23` (`O-T14` NODE_FORMULA lowercase): 29/24.5=1.1837, above bound.
- `PEER24` (`O-T16` NODE_FORMULA lowercase): 20/24.5=0.8163, below bound.
- `PEER38` (`O-T04` NODE_TEXT lowercase): 24/22=1.0909 > 1.08.
- `PEER39` (`O-T10` NODE_TEXT lowercase): 20/22=0.9091 < 0.92.

One of three role rows fails: `ROLE03` FORMULA_BLOCK has comparable median H=30 px versus NODE_FORMULA base 24.5 px, ratio 1.22449 > the strict maximum 1.18. EDGE_LABEL and ANNOTATION roles pass.

## Clip, view, and hard-gate conclusions

All 32 clipping rows pass with zero clip pixels. All four mandatory views pass. Hard gates `HARD03` (17 glyph failures), `HARD07` (six peer failures), `HARD08` (one role failure), and aggregate `HARD12` fail; the other eight hard gates pass. Because any strict threshold failure is dispositive, the figure result is FAIL even though objects, every pair, every critical relation, clipping, views, source-font audit, and semantic coverage pass.

## Evidence personally viewed

Using the image viewer at original detail, I personally inspected:

- all four mandatory views;
- all four object contact sheets (100% of 32 objects);
- all fifteen glyph contact sheets (100% of 175 glyphs), including the corrected `G120` mask presentation and the intrinsic enclosure of `G136` (`图`);
- all twenty pair contact sheets (100% of 496 unordered pairs);
- all seventeen final critical cards individually;
- all six calibration cards;
- the individual object/glyph/pair cards needed to resolve every manual row, together with the machine tables and 1×/8× mask panels.

Every row in the object, glyph, pair, critical, peer, role, clip, view, and hard-gate manual ledgers has a concrete ID, explicit decision, evidence reference, and ID-specific verifiable reason. No loop-generated, default, or global manual verdict was used.

## Required remediation boundary

The strict failures can only be addressed by an authorized source writer and a newly built official candidate followed by a fresh evidence run. This SA3 task did not request or perform any source write, TeX operation, compilation, build, or remediation request.

## Package sealing model

`evidence_manifest.csv` lists every ordinary file under this isolated root except itself and the strictly-final `WRITE_STOPPED.json`. It records relative path, bytes, SHA-256, exact UTC mtime at NTFS 100-ns precision, and raw `mtime_ns`. `WRITE_STOPPED.json` records the manifest identity, exact listed/unlisted coverage, official source identities, denominators, and the verdict. The marker is written strictly last; all verification after it is read-only and reported externally so that post-seal writes remain zero.
