# FIG-P756-01 root acceptance of SA1 failure

- Reviewed evidence: `STRICT_R9_REQUAL_R115_SA1_20260824` on official R95 physical page 801 / printed page 788.
- Seal integrity: 3,494 files, zero zero-byte files, zero alternate data streams, and `WRITE_STOPPED` is the last agent write.
- Root opened the P1408 native 1× original/overlay/intersection package and its 8× nearest views. `O-G016` and `O-G017` share 792 final-visible pixels and have 0 px clearance. The current source defines them as two separate supervised and unsupervised route nodes; it contains no shared-boundary declaration. This is a real forbidden graphic–graphic overlap/contact, not a rendering or mask artifact.
- Root opened the native and 8× evidence for `G0208`, `G0212`, and `G0222`. Each is the non-low-profile CJK glyph `口`, has effective size 9.5641 pt, and measures 29 px against the 30 px current threshold.
- The remaining reported gates—375 glyph pixel passes, D/E, clipping, calibrations, and the sealed terminal counts—are internally consistent with the inspected failure evidence. Neither passing geometry elsewhere nor acceptable overall font hierarchy can cancel either hard failure.

Root disposition: `EVIDENCE_INTEGRITY=PASS`, `FIGURE_HARD_GATES=FAIL`, `ROUTE_TO_SA2`. This is not a final figure pass and does not increase the strict 0/99 count.
