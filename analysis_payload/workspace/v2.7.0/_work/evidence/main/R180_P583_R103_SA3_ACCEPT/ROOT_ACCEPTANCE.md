# P583 R103 fresh isolated SA3 central acceptance

- figure: `FIG-P583-01`
- role identity: `A-R103-P583-SA3-FRESH-ISOLATED-20260825`
- verdict: `ROOT_ACCEPT / A_LOCAL_PASS`
- official candidate audited: R103, 817 pages, 4,967,184 bytes, SHA-256 `9379A489E0C2A57A7DA670C98029BB27B3F1A385BF8E4C3BD14FE9B606AA0F23`
- SA3 report: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\reports\P583_R2_R103_FRESH_SA3_REPORT.md`
- immutable handoff: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\handoff\A\A-R103-P583-SA3-FRESH-ISOLATED-20260825.md`

## Independent denominator adjudication

SA1 used `N=90` (71 glyph + 19 graphic); SA3 independently used `N=142` (119 glyph + 23 graphic), `C=10,011`, with 328 critical/relationship checks. The difference is accepted as a conservative refinement, not a contradiction: SA3 includes 48 caption glyph instances omitted by SA1's figure-body boundary and decomposes additional visible graphic components. Both roles bind the same source, page and visible figure, and the larger SA3 denominator introduces no missing, failed or semantically conflicting object.

## Mechanical and human gates

- 119 glyph + 23 graphic IDs, 10,011 unique unordered pair rows and 328 critical/relationship rows close without illegal overlap, clip or machine hard failure.
- minimum reported clearances: text-text 39.8121 px, text/formula-line 6 px, text-border 14 px, crop edge 11 px.
- manual ledger has 142 unique object IDs, blank notes `0`, non-PASS decisions `0`; repeated notes are limited to same-class caption/tick judgments. Evidence scripts read and validate the manual ledger and do not generate reviewer/decision/note fields.
- 34/34 evidence artifacts were opened by SA3; main independently opened the full page, figure crop, grayscale view, full pair matrix, semantic overlay and caption glyph contact sheet.
- geometry, formula, `O(N^{-1/2})`, triangle `x4 / divide by 2`, iid/finite-variance condition, caption and page integration pass the R168 hard gates.

## Evidence package

- root payload `225`; manifest entries `227` including two external identities; actual root ordinary files `228` including both manifests and `WRITE_STOPPED`.
- manifest path/size/SHA mismatch `0`; extra/missing `0`; all root/external files read-only; ADS/cache/pyc/post-seal writes `0`; marker strictly latest.

P583 therefore moves from SA3 to the fourth shared terminal local-pass bucket. This is not a whole-book final PASS; strict final remains `0/99`.
