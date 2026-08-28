# FIG-P067-01 R7 sealed local SA2 report

## Verdict

`LOCAL_SA2_PASS_READY_FOR_MAIN_REVIEW_AND_ATOMIC_COMMIT_AUTHORIZATION`

This is a local SA2 result only. No commit, fresh role, A_LOCAL_PASS, global/final pass, or central-state mutation is claimed.

## Authorized source change

- Sole source: `src/绘图源码/第01册_数学基础与统计学习基本理论/V1-C04/fig_v1_c04_cdf.tex`
- Current identity: 4,014 bytes; SHA-256 `2881377AEEF78E8C7BD7502AD8A303E19AAC395F1936475BDC6D569195900920`
- Exact diff: one file, 1 insertion / 1 deletion; `const plot mark right` → `const plot mark left`
- Index empty; `git diff --check` passed.

## Build identity

- Handoff ID: `A-R112-P067-SA2-DIRECT-BUILD-R7-20260827`
- Controller: `P067_R7_DIRECT_BUILD_20260827.ps1`, 7,605 bytes, SHA-256 `2AEC55355D0782CE3EBDD1C540A8F7F57974E9FB116F9B459740AF33D800489E`
- Controller PID 16412; child PID 14564; UTC `2026-08-27T09:04:45.3338656Z` → `2026-08-27T09:05:46.0735606Z`; 60.740 s.
- Controller/child exit 0/0; natural=true; interrupted=false; typeset invocation=1; retry=0; latexmk=0; version probe=0.
- Wrapper: 388 bytes; SHA-256 `ADDF75D1C82DAB9AB4D5A76E6B241DA1CEB7AED9C2E536106ECFD7710B2D14BF` before and after.
- PDF: 34,211 bytes; SHA-256 `73FBE000AC977A7E270D4834A0F9B81AC24C851BAE72B38503ACCAEBC844E108`.
- Source identity was unchanged during build; terminal TeX-family process count is zero.

## Independent new-PDF review

- Frozen denominator: N=115 = 65 visible glyph atoms + 50 foreground paths; 5 background structures were rationally excluded.
- All unordered pairs: C(115,2)=6,555; rows=6,555; duplicate/self rows=0.
- Machine gates: clipping=0, empty foreground atoms=0, target-tick hard overlap=0, hard failures=0.
- The machine program generated or overwrote zero manual reviewer/decision/note fields.
- Actual post-open manual ledgers: object 115/115 PASS, critical relation 16/16 PASS, opened-view ledger 16/16; unique IDs complete; blank notes=0; non-PASS=0.
- Actually opened: standalone page, native color figure, grayscale, atomic overlay, native/8x tick ROI, three glyph sheets, three path sheets, and native/nearest-8x CDF and PMF panels.

## Semantic and visual result

The new handler produces the right-continuous CDF intervals:

- `[.5,1):0`
- `[1,2):.15`
- `[2,3):.45`
- `[3,4):.80`
- `[4,4.5]:1`

All four filled endpoints take the post-jump value and all four open endpoints mark the left limit. The jump sizes equal the PMF values 0.15, 0.30, 0.35, and 0.20, whose sum is one. Axes, labels, caption, panel order, dashed alignment guides, and PMF/CDF meanings are preserved.

The `0.35↔0.3` and `0.3↔0.15` label relations have zero shared foreground at native 300 dpi and nearest-8x. Each native bounding-box gap is one pixel (eight nearest-neighbour pixels), recorded only as R168 advisory because the labels are distinct and readable. No tofu, wrong codepoint, mathematical error, actual unreadability, obvious size imbalance, true clipping, or illegal overlap was observed.

## Seal and root audit

- Sealed root: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P067-01\STRICT_R7_SA2_CDF_STEP_HANDLER_R112_DIRECT_BUILD_20260827`
- Payload 135; controls 4; ordinary files 139; directories including root 13.
- CSV/JSON manifest rows 135/135; manifest↔filesystem path/bytes/SHA/NTFS-ticks mismatch=0.
- Files readonly 139/139; directories readonly 13/13.
- JSON parse failures=0; ADS=0; prohibited cache/pyc=0; reparse points=0.
- `WRITE_STOPPED.json` is unique and strictly latest by 1,000,064 ticks; files at or after it excluding itself=0; post-marker content/attribute snapshot differences=0.
- Manifest CSV SHA-256 `3868F43E0A5E502AA20EA9E6BEABDACDA103B6C36B3CDBF5C9D63D6431AFC973`.
- Manifest JSON SHA-256 `D1F2F705607B60D7157C5B09A8CF5E6514DD7F9FABA8D081201B642FACDFC32E`.
- Preseal SHA-256 `2A1CD66D93C8D1144A085FBCEB85593A146C293ED3BA29DDA0B2339A023B0B41`.
- WSTOP SHA-256 `BB85DFBCA9716A9EC4752F1601BA1F2CE5EADAB186582A6D529D32C9EBDCFCBA`.
- Root-external audit: 907 bytes, SHA-256 `05785191C7A579085E0896EE25D03ED3C2FA6012A6263FD98711768C44D4367E`, hard gate PASS.

## Transparent control incident

The first seal-controller attempt stopped before any root write because `Group-Object relative_path` treated ordered-dictionary rows as a blank property and falsely reported duplicates. At that boundary the root still had 135 payload files and zero controls. The controller was changed only to explicit dictionary-key grouping, then passed AST plus empty/unique/duplicate tests (`0/0/1`) and completed. Final seal controller identity: 10,098 bytes, SHA-256 `720EBD289B7D0AE7BF5B2C9B62A4B12BF844F240C085266EB465586FBF464EAA`; successful seal invocation one after the zero-write preflight failure.

Main may independently accept this sealed LOCAL_SA2_PASS and, if satisfied, authorize one atomic commit containing only the stated source diff.
