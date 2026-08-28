# R318 — FIG-P641-01 R110 fresh SA3 main acceptance

- UID: `FIG-P641-01`
- role: `C-FIG-P641-01-R110-SA3-FRESH-ISOLATED-V1`
- actual instance: `/root/sa3_fig_p641_r110_fresh_isolated_v1`
- model / effort / fork: `gpt-5.6-sol / xhigh / none`
- sealed root: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P641-01\sa3_r110_fresh_isolated_v1`
- frozen input: R110 physical 691 / printed 678 / Fig. 33.8
- source SHA-256: `8773FF1EFFCB79DDD44734E72F0B0101292F135165021B32A760A6151DC0DE15`
- main repository HEAD: `b819e9f4810a2afc04d24a2f0b8bdaa2a3ccb079` (clean)
- decision time: `2026-08-27T08:13:42+08:00`

## Independent mechanical acceptance

The main thread recomputed the sealed root rather than accepting the role summary at face value:

- manifest rows / payload files: `497 / 497`;
- ordinary files: `499` (`497` payload + manifest + `WRITE_STOPPED.json`);
- duplicate / missing / extra / bytes mismatch / SHA mismatch: `0 / 0 / 0 / 0 / 0`;
- read-only files: `499 / 499`;
- read-only directories including root: `8 / 8`;
- WSTOP ticks: `639233856152288303`;
- maximum other-file ticks: `639233855700175645`;
- strict-latest margin: `452112658` NTFS ticks;
- files at or after WSTOP excluding marker: `0`;
- ADS / cache / pyc / reparse findings: `0 / 0 / 0 / 0`.

The following immutable identities independently matched:

- `REPORT.md`: `F297F7B6BFC76DF98858D1A281897378ABAED78B35AFD3992CE7321C8144AF7A`;
- `HANDOFF.json`: `7CD70E663E08903FF65952CCA9BB0BD9DE3DD4A376723E114670C291F887AD31`;
- `MANIFEST.sha256.csv`: `645211249D30CAF1C7FDC077744769402F37461212EC9BEBB89D27D7F455878C`;
- `WRITE_STOPPED.json`: `BF9D4292B6B770CA3C7E1A9EC12982852796E7D730BD0EC452E7EAF4B08E227E`.

## Denominator and manual-ledger acceptance

- visible object denominator: `N=180` (`162` glyphs + `18` graphic/path objects);
- all unordered pairs: `C(180,2)=16110`, duplicate/self-pair count `0`;
- raw nonzero contacts: `14`, total `258` pixels, all mapped to intended source connections;
- manual rows: glyph `162`, graphic `18`, critical relation `41`, semantic text `11`, hard gate `6`, views `36`, typography roles `7`;
- duplicate IDs, non-PASS decisions, blank reviewer fields and blank notes: all `0`.

The independent semantic recomputation agrees with the current source and page: for the theta update,
`pi(theta|alpha,z,y) proportional to p(theta|alpha)p(z,y|theta)`; `p(alpha)` is constant in theta and is removed; the displayed Markov blanket is exactly `{alpha,z,y}`.

## Main visual inspection

The main thread actually opened and inspected:

- native 300 dpi full page;
- color and grayscale figure-plus-caption crops;
- semantic-object overlay;
- critical-relation contact sheet;
- all three contact sheets containing the 18 glyphs of the explicit 9.2 pt blanket legend;
- nearest-neighbour 8x ROIs for the alpha blanket clearance and the eliminated-annotation versus conditional-formula relationship.

No counterevidence was found. Text and mathematics are complete and readable; the 9.2 pt blanket legend is visually balanced and remains `R168 ADVISORY_ONLY`; group borders and node borders retain visible separation; edge/node contacts are intentional; the elimination annotation, conditional formula, caption, grayscale rendering and page integration are clear. There is no true clipping, illegal overlap, missing/tofu/wrong codepoint, unreadability, severe imbalance, or semantic/geometric inconsistency.

## Central decision

`FIG-P641-01 = C_LOCAL_PASS`.

The R110 SA3 source identity, sealed evidence root, report, handoff and role are permanently frozen. C must not repeat this UID, start TeX/source writes, or start a next UID without a new explicit main route.
