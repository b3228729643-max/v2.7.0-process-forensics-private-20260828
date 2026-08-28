# FIG-P582-02 root acceptance of SA1 failure

- Reviewed evidence: `STRICT_R10_REQUAL_R115_SA1_20260824` on official R95 physical page 630 / printed page 617.
- Seal integrity: 764 files, zero zero-byte files, zero alternate data streams, and `WRITE_STOPPED` is the last agent write.
- Root inspected the native figure, text overlay, standalone, grayscale, and the 1×/8× glyph packages for the decisive `=`, `≈`, and caption `一` rows. The raw measurements are 12 px versus 22 px, 18 px versus 22 px, and 9 px versus 30 px, respectively.
- Independently from those raw-height rows, the current source explicitly declares 8.6 pt ticks, 9.2 pt ordinary labels/annotations, and a 9.4 pt formula card. The sealed audit consequently records 67/149 visible glyphs below the 9.5 pt hard floor and a failed font-size/harmony gate.
- Evidence integrity itself is not eligible for PASS: 21 low-profile punctuation rows lack the required independent same-codepoint/font/weight/effective-size calibration closure. The package correctly reports this as `EVIDENCE_INTEGRITY=FAIL`; it cannot be repaired by changing only the terminal prose.
- The 125 audited relations, 10 edge checks, three occlusion checks, and mathematical semantics may remain physical passes, but they cannot cancel the source-size, raw-height, harmony, or calibration failures.

Root disposition: `EVIDENCE_INTEGRITY=FAIL`, `FIGURE_HARD_GATES=FAIL`, `ROUTE_TO_SA2`. This is not a final figure pass and does not increase the strict 0/99 count.
