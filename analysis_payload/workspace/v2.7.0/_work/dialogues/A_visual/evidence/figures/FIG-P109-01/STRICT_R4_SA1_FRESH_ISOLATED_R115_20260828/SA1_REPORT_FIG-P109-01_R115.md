# Fresh isolated SA1 report

## Identity

- HANDOFF_ID: `A-R115-P109-SA1-FRESH-ISOLATED-20260828`
- Canonical task: `/root/p109_r115_fresh_sa1`
- Model / reasoning: `gpt-5.6-sol` / `xhigh`
- UID: `FIG-P109-01`
- Official candidate: R115, SHA-256 `93ADF6E1FBF9EED2A392FA150C81738DD60FC50F50C00EBDF99C0F4168D4726F`, 4,967,161 bytes, 817 pages.
- Independently located current page: physical page 116.

## Coverage

- 15/15 reader-visible semantic objects manually reviewed.
- 105/105 unordered object pairs manually reviewed after the denominator freeze.
- 9/9 subdivided text measurement IDs manually reviewed.
- 5/5 primary view classes actually opened: full page, native1x, nearest8x, grayscale, and page integration.
- 12/12 critical ROI images actually opened: six ROIs at native1x and nearest8x.
- Mathematical/semantic checks: 6/6 explicit checks clear.
- Grayscale and page-integration checks: clear.

## Findings

The current R115 figure correctly depicts the defining segment property of a convex set. Every glyph and codepoint is present, including the implication and lambda symbols. The chord and all five markers form intentional geometry and remain inside the visible convex region. All 105 pair rows contain a genuine manual classification. There are no unresolved pairs, no illegal visible-ink overlap pixels, and no clipped visible pixels.

The closest critical visible-ink separation is the region label to the visible region boundary: 8.000 px for the Chinese label and 9.440 px for the mathematical C. The opaque backing is visibly effective and no boundary line crosses text. The legacy numerical font/pixel/ratio limits are advisory under R168; source labels are 9.2 pt and are plainly readable without obvious imbalance at native page scale.

## Verdict

`PASS` for this fresh isolated SA1 role.

This is not final figure closure and does not migrate inventory. Main should request a new fresh isolated SA3. This instance performed no SA2 or SA3 work and made no source, build, Git, central-state, or other-UID change.
