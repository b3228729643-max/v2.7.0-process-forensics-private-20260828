# FIG-P608-01 R6A — root acceptance

- `ROOT_DECISION`: `ACCEPT_LOCAL_SA2_PASS_AWAIT_OFFICIAL_CANDIDATE_AND_FRESH_SA1`
- `HANDOFF_ID`: `A-R99-P608-SA2-NARROW-R6A-EVIDENCE-RESEAL-20260825`
- `MODEL_ROUTE`: `SA2=gpt-5.6-sol/max`
- `EVIDENCE`: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P608-01\STRICT_R6A_SA2_REPAIR_R99_LOCAL_EVIDENCE_RESEAL_20260825`
- `QUARANTINED_PREDECESSOR`: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P608-01\STRICT_R6_SA2_REPAIR_R99_LOCAL_20260825`

## Root verification

- Source scope is exactly one P608 drawing source. The only change is one insertion: `ylabel style={rotate=-90,anchor=east,at={(axis description cs:-0.12,0.5)}},`.
- Frozen local PDF identity matched: 42,989 bytes, one A4 page, SHA-256 `638A722CC86D848E6B0FDEB69F08BB6DDBD3F0AD33E262AB36690C2943FD03BB`. Source SHA-256 is `78C30F4A934F63E0EF1BBACF400A24F22477D38589F99503AE468F7024A35C05`.
- Object denominator closes at `N=170 = 112 glyphs + 58 foreground paths`; all `C(170,2)=14,365` unordered pairs are unique and complete. Pair failures, illegal visible overlap and clip are zero.
- The repaired target glyphs `GLYPH_0025` and `GLYPH_0056` are each 21px high against the 15px natural-script gate, with 115.430px and 86.000px minimum clearance.
- Strict low-profile punctuation closes at 15/15 with zero failures under the mandatory `[0.92,1.08]` height and area ratios. The previously disputed `GLYPH_0072` uses the predeclared nearest exact peer, official R99 Figure 32.5 on physical page 652. Ownership-clean target and peer are both H=7px, W=7px and area=41px; normalized mask symmetric difference is zero.
- Explicit human decisions close at `170 objects + 13 critical pairs + 7 views + 9 roles = 199`. IDs, decision IDs and individualized notes are unique and match the four final ledgers; no default, missing-ID auto-decision, global review flag, pending, unknown or empty accepted cell exists.
- Package integrity passed independently: `842 = 835 inventory rows + inventory itself + 6 terminal/seal files`; all 835 accepted entries match by path, bytes and SHA-256. The 813 reused entries match both source and destination hashes. All 842 files open; 784 PNGs decode, 14 JSON files parse and 22 CSV files import; ADS=0.
- `WRITE_STOPPED` is strictly latest by 1.750810 seconds and no file was written afterward.
- Root visually inspected the frozen final figure and the strict peer/target masks. The y-axis labels are horizontal, legible and clear of tick labels; page/crop hierarchy remains balanced.

## R6 quarantine

R6 is rejected and must never be used as accepted evidence because it retained pending data, generated manual PASS rows through global booleans, and applied a non-schema low-profile punctuation gate. Only R6A is accepted.

## Route

This is a local SA2 repair acceptance only. It is not an official full-book candidate and is not `A_LOCAL_PASS`. After the single-source commit is integrated, mainline must build and freeze a new official candidate and commission a completely fresh isolated SA1 for FIG-P608-01. SA3 may start only if that fresh SA1 passes.
