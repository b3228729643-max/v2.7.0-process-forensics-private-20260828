# FIG-P067-01 R11A local SA2 report

- HANDOFF_ID: `A-R113-P067-SA2-DIRECT-BUILD-R11A-20260827`
- Role: SA2
- Verdict: `LOCAL_SA2_PASS_READY_FOR_MAIN_REVIEW_AND_ATOMIC_COMMIT_AUTH`
- Build authorization was consumed exactly once; no additional TeX invocation occurred during evidence review.

## Frozen identities

- PDF: `build/v260_FIG-P067-01_standalone.pdf`, 34,213 bytes, SHA-256 `586EFE2C968A05C014A9AD8D639A8CFF0EDD0B21306CA31183485A7C75A338A1`.
- Source: `fig_v1_c04_cdf.tex`, 4,014 bytes, SHA-256 `11BF3681D069F6A38C479B3074F39F93E8EB6144FF155AC543508E3589A51144`.
- Wrapper: `v260_FIG-P067-01_standalone.tex`, 388 bytes, SHA-256 `ADDF75D1C82DAB9AB4D5A76E6B241DA1CEB7AED9C2E536106ECFD7710B2D14BF`.
- Controller: 6,154 bytes, SHA-256 `732C208A630E06BF993EB3792D3E70E9B1F0E0FC67DA222D0229071C039570A9`.
- Build: controller PID 5968; child PID 13720; one direct LuaLaTeX typeset; exit 0; natural true; interrupted false; retry 0; latexmk 0; version probe 0.

## Complete denominator and machine gates

- Final visible denominator: 100 objects = 65 glyphs + 35 foreground drawings. Five real opaque text backgrounds are tracked separately and excluded from the foreground denominator.
- All unordered pairs: `C(100,2)=4,950`; actual rows 4,950; unique pair keys 4,950.
- Critical candidates: 70. All were opened in six nearest-8x sheets and manually classified.
- Empty glyph masks 0; empty drawing masks 0; independent overlap candidates 0; numeric-clearance failures 0; clip failures 0; unresolved IDs 0.
- Nine source-font numeric items are retained as R168 advisories. Actual readability/tofu/codepoint/semantic/visible-imbalance hard failures are 0.

## p4 regression closure

The previous two hard relations are closed in the new PDF and were reviewed in dedicated original/native/nearest-8x evidence:

- `P01436 T016-G007`: shared pixels 0; clearance 15 px.
- `P01437 T016-G008`: shared pixels 0; clearance 16 px.
- `P01449 T016-G024`: shared pixels 0; clearance 22 px.
- `P01519 T017-G007`: shared pixels 0; clearance 24 px.
- `P01520 T017-G008`: shared pixels 0; clearance 25 px.
- `P01532 T017-G024`: shared pixels 0; clearance 45 px.

Thus the moved `p_4` label and its subscript remain clear of the CDF plateau, dashed value-1 reference, and x=4 open endpoint. No new near-pair hard failure was found.

## Genuine post-observation review

- Manual object ledger: 100/100 rows PASS; original-match/overlay-complete/mask-only-pure all true; missing-stroke and foreign-pixel counts all 0.
- Manual critical-pair ledger: 70/70 rows PASS; every nonzero graphic intersection is an object-specific intended axis/tick/guide/curve/endpoint/marker topology.
- Manual target-pair ledger: 6/6 rows PASS.
- Manual view ledger: 34/34 actually opened views PASS: five whole/crop/gray/overlay views, twelve glyph sheets, ten drawing sheets, six critical sheets, and one p4 target sheet.
- Manual R168 typography ledger: 9/9 advisory rows reviewed; hard failures 0.
- Manual mathematical/semantic ledger: 10/10 PASS.

## Mathematical and visual regression

- The CDF is right-continuous with levels 0 on `[.5,1)`, .15 on `[1,2)`, .45 on `[2,3)`, .80 on `[3,4)`, and 1 on `[4,4.5]`.
- Open endpoints show pre-jump values and filled endpoints show post-jump values at all four supports.
- PMF masses .15, .30, .35, and .20 remain at `x=1,2,3,4` and sum to 1.
- PMF labels `0.35`, replayed `0.3`, and `0.15` remain distinct in native and grayscale views.
- Both panels, annotations, axes, guides, caption-free standalone layout, and grayscale reading order remain clear.

## Source and process boundary

- Branch: `v2.7.0/dialogue-a-visual`; pre-commit HEAD `3c371f2448c86686ef5fc198237a395f9c4668e1`.
- Worktree diff is exactly one file and one line: `at (axis cs:4.08,.89)` to `at (axis cs:4.08,.85)`; numstat `1+/1-`; index empty; `git diff --check` PASS.
- Source and wrapper identities are unchanged across the build and review.
- Terminal TeX-family process count is 0.
- No commit or fresh role is authorized by this report.

The root is ready for its single manifest/read-only/WRITE_STOPPED-last seal and root-external audit.
