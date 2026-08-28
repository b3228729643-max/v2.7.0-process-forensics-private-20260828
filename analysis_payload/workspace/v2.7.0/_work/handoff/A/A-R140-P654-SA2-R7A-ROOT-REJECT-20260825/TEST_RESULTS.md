# P654 R7A root test results

- Frozen identity: PASS, source/wrapper/PDF bytes and SHA-256 agree.
- Machine reuse: PASS, 935 exact source/destination identities; prohibited R7 manual/final artifacts 0.
- Denominator: PASS, N=116 = 95 glyph + 21 graphic.
- All unordered pairs: PASS, C=6,670 / 6,670.
- Target FRM_TRIAL_005: PASS, H=22 px, area=297 px, missing/foreign/clip/ownership loss all 0.
- Human ledger authenticity and coverage: PASS, 203 unique decisions with no empty/exact/numeric-normalized duplicate notes or script-written manual fields.
- Consumer: PASS, 37 checks / 0 errors; validator pre/terminal identity unchanged.
- Root visual audit: target n and sampled glyph/graphic/critical/view/semantic evidence show no missing, contamination, clip, ownership or design-whitelist counterexample.
- D/E strict hard gate: FAIL, at least 8 elements outside [0.92,1.08].
- GAMMA/LATIN_GREEK_LOWER: TXT_GAMMA_009 t = 27/22 = 1.227273.
- POSTERIOR_FORMULA/BASE_MATH: plus = 29/24 = 1.208333.
- PREDICTIVE_FORMULA/BASE_MATH: three 24 px elements = 0.905660; two plus elements = 1.094340; N = 33/26.5 = 1.245283.
- Manifest: PASS, 973/973 payload; actual ordinary files 978.
- Parse/open, ADS and PYC: PASS, zero failures/streams/cache artifacts; one exact-SHA CP936 fallback was independently reproduced.
- Seal order: PASS, WRITE_STOPPED latest with zero post-seal file writes.
- Provenance reservation: attempt1 finalizer source content was not retained; only its frozen bytes/SHA remains. R2 same-path finalizer identity is independently frozen.
- Root verdict: ROOT_REJECT_R7A_FAIL_TO_SA2_CONTINUE.
