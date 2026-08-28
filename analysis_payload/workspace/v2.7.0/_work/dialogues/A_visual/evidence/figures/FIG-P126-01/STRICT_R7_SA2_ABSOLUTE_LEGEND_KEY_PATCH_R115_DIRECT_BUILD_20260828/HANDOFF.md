# P126 R7 immutable handoff

- HANDOFF_ID: `A-R115-P126-SA2-DIRECT-BUILD-R7-20260828`
- UID/role: `FIG-P126-01` / `SA2`
- Verdict: `LOCAL_SA2_FAIL_RETURN_TO_MAIN_SOURCE_SCOPE`
- PDF: 33,952 bytes; SHA-256 `8EB275DEB382AD25E26C19F4B9A0EFBE01771317FE7DE475C5F2E330BCD789D6`
- Fresh denominator: `N=58`, `C=1,653`; all pair rows exact.
- Hard defects: `HARD-LEGEND-X2-CONTINUOUS`; `HARD-LABEL6-AXIS-CONTOUR-OVERLAP`; `HARD-LABEL7-MARKER-ARROW-OCCLUSION`.
- Regression: clip0; missing/tofu0; math and caption semantics PASS; color/grayscale/native1x/nearest8x confirm all three hard defects.
- Mutations after build release: TeX0, source0, Git0, commit0, second UID/role0.
- Requested next action: Main independent review and, if accepted, an explicit narrow single-source scope. No patch or build is self-authorized.
