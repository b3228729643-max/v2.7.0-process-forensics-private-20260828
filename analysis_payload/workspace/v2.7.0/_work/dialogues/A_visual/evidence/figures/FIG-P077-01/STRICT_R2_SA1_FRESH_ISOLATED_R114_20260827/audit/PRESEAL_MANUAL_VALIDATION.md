# Pre-seal manual validation

- Handoff: `A-R114-P077-SA1-FRESH-ISOLATED-20260827`
- Official PDF identity rechecked at the final identity boundary: 4,967,122 bytes; SHA-256 `C3BB9B1C7FC9D7AF9178CD33F227F24899AA505FAB81840DB6E3AD8BD6CE78A6`.
- Current source identity rechecked at the final identity boundary: 2,603 bytes; SHA-256 `ED96F120CFF0815122B2914D7D94D12884FAC3DB328D30E883F93457C68484E4`.
- Machine visible objects: 30; manual visible-object rows: 30.
- Machine unordered pairs: 435; manual pair rows: 435; unique pair IDs: 435; missing: 0; duplicates: 0.
- Manual font rows: 13; manual pixel rows: 13; manual overlap-candidate rows: 13.
- Opened-view rows: 18.
- Per-object native-300-dpi mask files: 30.
- Critical ROI pairs: 6 native1x plus 6 exact nearest8x.
- Zero-length root files before this audit: 0.
- `RESULT = PASS` appears exactly once in the final manual acceptance file.
- Root `WRITE_STOPPED` marker before sealing: absent, as required.
- R168 hard-fail audit: no missing/tofu/wrong codepoint or math meaning; no unreadability/obvious imbalance; no true clipping; no illegal visible-ink overlap; no semantic/geometric error.
- Canonical pixels: candidate 2; mask contamination 2; true illegal overlap 0; clip 0; minimum confirmed visible text clearance 8 px; unresolved 0.

Pre-seal decision: complete and internally consistent. Next exact action is to generate the content manifest, stage the fully resolved read-only marker outside the root, set and verify root contents read-only, then move that marker into the root as the sole final root mutation.
