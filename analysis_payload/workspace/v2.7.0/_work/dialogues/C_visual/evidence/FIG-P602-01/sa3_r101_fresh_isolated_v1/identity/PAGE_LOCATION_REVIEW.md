# Independent target-page location

The supplied page claim was treated only as a search hint. I independently extracted native text from physical PDF pages 649–653 and inspected the native page rendering. Physical page 651 alone simultaneously contains:

- running/printed page number `638`;
- figure number `图 32.5`;
- caption token `Metropolis–Hastings`;
- the self-loop wording `自环：保留`;
- the full proposal → ratio → decision → accept/reject flow.

Therefore the independently verified target identity is official PDF physical page **651**, printed page **638**, figure **32.5**. The exact token checks are in `page_location_checks.csv`; official file/page/source identities and crop coordinates are in `official_candidate_identity.json`.

The PDF has 814 pages and A4 page geometry about 595.276 × 841.890 pt. Mandatory views are direct Poppler native renders (integer crop only, no resize). The measurement base is a direct PyMuPDF 300 dpi pixmap, also without resize.

