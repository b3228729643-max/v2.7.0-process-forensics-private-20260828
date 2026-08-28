# FIG-P582-01 R109 R4 fresh-isolated SA3 handoff

HANDOFF_ID=`A-R109-P582-SA3-FRESH-ISOLATED-20260826`  
RESULT=`FAIL`  
ACCEPTANCE=`NOT_ELIGIBLE_FOR_A_LOCAL_PASS`

Official figure location: physical page 632, printed page 619, Figure 31.7.

Frozen current denominator: 156 visible objects = 139 text glyphs + 17 drawing/path objects. Complete unordered-pair universe: 12,090/12,090. Machine identity, location, font, R168-aware pixel, mask-openability, pair-completeness, semantic recomputation, and 8× native-mask-coverage gates pass.

Binding failure: `P05555`, T042 down arrow in “↓再下降” versus T062 terminal zero in `.380`; 14 native-300-dpi intersection pixels, 0 px clearance, visually confirmed at 1× and nearest-neighbor 8×. Classification: `TRUE_ILLEGAL_OVERLAP`.

R168 advisory only: P04848 has 0 intersection/13.1421 px clearance; P05554 has 0 intersection/6.6158 px clearance; the 12 px low-profile equals sign is readable and correct. Semantics pass: samples `(0.8,0.1,0.7,0.4)`, squares `(0.64,0.01,0.49,0.16)`, running means `(0.64,0.325,0.38,0.325)`, trend down/up/down, reference `1/3`.

Sealed evidence root:

`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P582-01\STRICT_R4_SA3_FRESH_ISOLATED_R109_20260826`

External report:

`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\reports\FIG-P582-01_R109_STRICT_R4_SA3_FRESH_ISOLATED_REPORT_20260826.md`

Seal facts: one `WRITE_STOPPED`, strict latest; 568 files all read-only; exact double-manifest identity; ADS/pyc/__pycache__/reparse/postmarker/manual-time errors all zero. Payload-manifest SHA256 `EE07986A7385A5C49661BACFB74E4CCF08E816D8F4AF8F55DA913BAD986C50A3`; seal-manifest SHA256 `050046F83982C79134C1790CB1B1603C45F076E5BF753DB275C0395CD6D9AF38`. Root-external read-only auditor result: PASS.

Do not accept this R109 figure as `A_LOCAL_PASS`. Do not migrate state or start another UID/role from this handoff. The main flow may later create a corrected candidate by separating the second downward annotation from `.380`, then rerun a fresh independent acceptance cycle.
