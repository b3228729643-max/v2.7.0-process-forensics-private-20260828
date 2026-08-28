# FIG-P608-01 — R7A fresh SA1 evidence reseal

## Terminal conclusion

`FAIL_TO_SA2_AWAIT_ROOT`

This is an R7A SA1 finding awaiting a new root mechanical plus sampling/counterexample review. It is neither a central `FAIL_TO_SA2` declaration nor `A_LOCAL_PASS`. SA3 was not started.

## Frozen identities

- Handoff: `A-R101-P608-SA1-FRESH-R7A-EVIDENCE-RESEAL-20260825`.
- Route: `SA1=gpt-5.6-sol/xhigh`.
- Figure source: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C03\fig_v5_c03_trace_running_mean.tex`.
- Source identity: ordinary file; 3,429 bytes; SHA-256 `78C30F4A934F63E0EF1BBACF400A24F22477D38589F99503AE468F7024A35C05`.
- Candidate: `main_full.pdf`; 814 A4 pages; 4,947,496 bytes; SHA-256 `0870FF226DC383875C4A1B6EABB06AAB942317DA294D90D2864B3030D46DF1A1`.
- Target mapping: physical page 659 (1-based), printed page 646, Fig. 32.8. The historical stable UID `P608` is not the R101 physical page number.
- TeX, LuaLaTeX and latexmk were not run. Business source and the R7 sealed package remained read-only.

## R7 root rejection and permitted reuse

The formal root gap report rejected R7 for bulk-generated manual ledgers, PENDING preliminary manual fields/incomplete CSV asset references, absent source identity binding, peer-purity conflicts, and a pyc write into the sealed root. Those facts are recorded only as provenance in `R7_ROOT_REJECT_PROVENANCE.md`; no R7 manual row, review note, PASS/FAIL summary, RESULT or handoff was migrated or used as the R7A conclusion.

R7A copied 1,893 machine-only files into `machine_reuse`. `reuse_identity_ledger.json` binds every source/destination path, byte count, SHA-256 and mtime to the frozen PDF/page and P608 source hash. The consumer validator re-opened and re-hashed all 1,893 R7/R7A pairs successfully. The R7 root was never imported or executed and received no write/cache.

## Independent denominator and pair closure

- Page rawdict conservation: `837 = 120 target-domain chars + 717 outside-domain chars`.
- Domain conservation: `120 = 112 non-space glyphs + 8 whitespace chars`.
- Non-space conservation: `778 = 112 target glyphs + 666 outside-domain non-space chars`.
- Drawing conservation: `89 = 6 preceding-equation drawings + 58 target explicit drawings + 2 corner artifacts + 2 following-prose rules + 21 following-figure drawings`.
- Pattern guard: two visible hatch layers are not emitted by `get_drawings`; they are separate `PATTERN` objects and cede shared pixels to later explicit graphics, so no path is double-counted.
- Final denominator: `N=172 = 112 GLYPH + 58 explicit GRAPHIC + 2 PATTERN`.
- Complete unordered pairs: `C=172×171/2=14,706`; all 14,706 unique pair IDs and valid endpoints were consumer-validated.
- Formula rules: six `MATH_RULE` objects are nonempty and independently reviewed.

## Manual review closure

Exactly 391 new R7A decisions were written explicitly before consumer validation:

| Ledger | Rows |
|---|---:|
| object | 172 |
| critical relation | 102 |
| preliminary | 64 |
| peer | 13 |
| panel/role/script | 35 |
| view | 4 |
| hard failure | 1 |
| **total** | **391** |

Every row has a unique decision ID, reviewer, concrete asset/sheet/cell or view, numeric manual missing/foreign values where applicable, a decision, and an object/relation-specific note. The consumer validator found no missing/duplicate IDs, blank notes or `PENDING/UNKNOWN/TBD/DEFAULT/BULK/HARDCODE` tokens.

## Critical designed connections

`PAIR-117-125` is the top y-axis shaft versus marker t=1. The source places t=1 at the x-domain minimum, visually centred on the y-axis boundary. Clean pre-occlusion masks share 70 intended pixels; final-visible ownership cedes the covered shaft to the marker and yields zero final overlap. The disk and exposed shaft are both complete and retain their distinct marker/line semantics.

`PAIR-118-125` is the y-arrowhead versus the same t=1 marker. Clean pre-occlusion masks share 35 intended pixels at the domain start; final-visible masks have zero shared pixels. The arrow remains pointed and directional and the circle remains complete. These are protocol line–marker/assembled-axis connections, not independent accidental collisions.

## Sole hard failure

`HARD-LOWPROFILE-TXT-098` — caption semicolon `；`:

- target mask: H=28 px, area=56 px, complete and pure;
- full-book exact-metadata candidate set: 64 entries, frozen before pixel metrics;
- deterministic mandatory peer: physical page 187, rawdict sequence 345, rank 1;
- peer raw mask: H=28 px, area=72 px;
- independent component inspection: semicolon components have areas 21 and 40; a disconnected right-edge component is a foreign 1×11 rule;
- after transparent manual accounting for that foreign component: clean peer area=61 px;
- height ratio `28/28=1.000000000` passes;
- clean area ratio `56/61=0.918032787` fails the fixed `[0.92,1.08]` interval;
- the unclean raw ratio `56/72=0.777777778` also fails.

The candidate rank, 300 dpi/native coordinate, 20/255 threshold and interval were not altered. No different glyph/size/weight was substituted and no fallback candidate was selected after seeing pixels. The accepted peer/manual/role/preliminary/hard ledgers consistently record this one failure and no PASS/PENDING conflict.

## Machine terminal validation

`consumer_validation.json` reports PASS with zero validator failures: source/PDF identities, 1,893 machine reuse bindings, N/C closure, mask/contact counts, 391 manual row counts/sets, accepted preliminary assets, JSON parse, and single-failure consistency all passed.

The payload manifest, parse/ADS report and terminal write controls are produced after this report. No evidence-root write is permitted after final sealing.

