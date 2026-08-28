# R10 scope certificates

## Low-profile peer calibration

The R10-native object denominator contains 95 glyph objects and 21 foreground graphic objects. The machine ledger classifies zero glyph objects as `LOW_PROFILE_PUNCTUATION`. Therefore the low-profile peer-calibration set is empty by the frozen schema, not skipped. The certificate denominator is `0/0`, with no peer decisions fabricated.

## Low-profile hard minimum

Because the same native denominator contains zero low-profile punctuation objects, the strict low-profile hard-minimum set is also empty. The certificate denominator is `0/0`; no manual override or exact-glyph regrouping was used.

## Taxonomy scope

The frozen R8 global classifier is `PANEL_ID + SEMANTIC_ROLE + TYPOGRAPHIC_CLASS`. Its R10 recomputation maps all 95 glyph objects exactly once into 10 groups. Classifier assignment does not consume `ELEMENT_ID`, measured height, mask area, pass/fail state, or rank. Singleton groups remain explicit members of the complete denominator and are not treated as peer comparison groups.

## Manual scope

Actual opening preceded the manual ledgers: 16 glyph sheets; 21 graphic native-1x and exact-nearest-8x triples; 50 critical native-1x and exact-nearest-8x bundles; 5 views; 3 semantic gates; 10 taxonomy groups; 4 source same-role groups; and 4 source hierarchy groups. The resulting 192 decisions were written manually and are not machine-generated fields.
