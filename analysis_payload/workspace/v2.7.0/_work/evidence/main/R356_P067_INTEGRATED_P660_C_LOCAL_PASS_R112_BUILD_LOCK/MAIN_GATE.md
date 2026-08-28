# R356 — P067 integration, P660 C_LOCAL_PASS, and R112 unique build lock

## P067 atomic integration

- A commit `ab199fc685753015c3aa4d930ea1217e80aedf63`, parent `d8f1e5fb15abdf09ce5ead5245c270b43abd5741`, subject `fix(fig-p067): separate adjacent PMF tick labels`, was independently verified to contain exactly one path and numstat3/1.
- Source identity is 4,015 bytes/SHA-256 `C570597B72EEA4610380359A84EA078B24C810EC89039215BC9B42AB0F8AFFA0`; A worktree/index are clean and immutable commit handoff identity matches.
- Main cherry-picked from clean HEAD `b819e9f4810a2afc04d24a2f0b8bdaa2a3ccb079` to clean HEAD `27fca4d1a0c9034807a161c1bffa4f4d8f099339`. The integrated commit contains exactly the P067 target source with numstat3/1; no conflict or additional path.
- P067 remains `LOCAL_SA2_PASS_AWAIT_OFFICIAL_CANDIDATE_AND_FRESH_SA1`; its source/evidence/report/handoff and A role are frozen. No fresh role begins before R112 is formally frozen.

## P660 fresh SA3 acceptance

Main accepts `C-FIG-P660-01-R111-SA3-FRESH-ISOLATED-V1` as `C_LOCAL_PASS`.

- Fresh current-input denominator N16 semantic visible objects, all C(16,2)=120 unordered pairs, manual objects16/16, pairs120/120, text/glyph20/20.
- The semantic granularity is accepted because each composite geometry/container object explicitly inventories all visible grid, boundary, projection, marker, card-frame and caption primitives; the separate 20 text elements cover every reader-visible line. This is a granularity choice, not an omission.
- P001's 922 candidate pixels are the intended simplex-grid × component-projection/marker construction. Native1x/nearest8x and current-source coordinates close the topology; true illegal overlap0 and unresolved0. The other119 pairs have shared foreground0 and 3px-dilated candidates0; minimum non-P001 gap26px; clip0.
- Barycentric `(0.2,0.3,0.5)`, sum1, normalized side distances approximately `(0.2000044,0.3000066,0.5)`, simplex dimension/face/vertex statements, caption/alt/current context, glyphs, grayscale and page integration all pass. Main actually opened the full local figure+caption, visible-object overlay, and P001 nearest8x; no visual counterevidence.
- Root audit: payload92+controls4=ordinary96; file manifest92 and directory manifest9; duplicate/missing/extra/path/bytes/SHA/creation FILETIME/last-write FILETIME/directory creation/reparse mismatch all0. Files ReadOnly96/96, directories/root9/9; JSON/CSV/PNG signature failures0, ADS/cache/pyc/reparse0. WSTOP ticks639234114215340268, max-other639234114195259383, strict margin20,080,885 ticks, at-or-after excluding marker0.
- The manifest `*_utc_ticks` dialect is Windows FILETIME and was independently checked with `ToFileTimeUtc()`; a discarded .NET `DateTime.Ticks` comparison is not a root defect.

P660 source/evidence/report/handoff/roles are permanently frozen. C must not rerun P660 or start another UID before Main's next explicit route.

## R112 unique full-book build lock

The only authorized parent call is:

`build_v2.7.0.ps1 -Engine lualatex -OutputDir src\build\strict_current_r112_fullbook -NoPublish`

Preflight at 2026-08-27T15:15:16+08:00: main HEAD is clean `27fca4d1a0c9034807a161c1bffa4f4d8f099339`; output root is absent as both file and directory; build script exists; `latexmk/lualatex/luatex/luahbtex=NONE`.

Exactly one parent invocation is authorized, with no manual retry, Resume, second parent call, concurrent A/B/C TeX, source write, commit, process interruption, or next role. A natural internal latexmk convergence sequence is part of the one parent call. On failure or platform interruption, preserve the output unchanged and return for adjudication. On natural completion, immediately release the build lock and freeze PDF/log/index/page/font/navigation identities before any fresh review.

Inventory after P660 acceptance: `31 SA1 / 39 SA2 / 0 SA3 / 29 local pass`; strict final remains0/99 and B remains66/66.

