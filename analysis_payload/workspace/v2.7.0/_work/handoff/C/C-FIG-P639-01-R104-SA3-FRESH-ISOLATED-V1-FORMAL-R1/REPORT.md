# FIG-P639-01 R104 fresh isolated SA3 formal report

- HANDOFF_ID: `C-FIG-P639-01-R104-SA3-FRESH-ISOLATED-V1`
- formal return token: `P639_SA3_FAIL_READY_FOR_MAIN`
- reviewer instance: `/root/sa3_fig_p639_r104_fresh_isolated`
- reviewer type: `AI_SA3_VISUAL_REVIEW`
- human certification: `false`
- result: `FAIL`
- disposition: `RETURN_TO_SA2`
- global/final/local-pass claim: `false`

## Immutable source evidence

- sealed root: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P639-01\sa3_r104_fresh_isolated_v1`
- `SA3_RESULT.md`: 741 bytes; SHA256 `CEA6574B91E3F0DA00047FE2081A84FAFE1FFF9A8FFC3CCE6A872BA87B486410`
- `SEALED_MANIFEST.json`: 12,858 bytes; SHA256 `1E063813B45C051924359E659EF532BFB19E74E6D76B8284179F4A06044346CC`
- `WRITE_STOPPED`: 135 bytes; SHA256 `552EE656C39763CC8A600B96D4B174438E3B9B882EC6F77A27783CF72750E5AC`
- sealed-root mutation during formal return: `NONE`

## Independent mapping and denominator

- official candidate: R104, physical page 689, printed page 676, Figure 33.6
- actual objects: 29 = 20 reader-text IDs + 9 geometry objects
- complete unordered pairs: 406
- critical pairs: 368
- overlap candidate / mask contamination / illegal overlap: `0 / 0 / 0`
- clip pixels: `0`
- minimum text clearance: `12 px`
- pixel adjudication: `CLEAR`

## Decisive hard failure

The R104 page interrupts the following Figure 33.7 introduction sentence with FIG-P639-01 and its caption. After that caption, the fragment `下的混合速度。` is left isolated. This is a real reading-order and page-integration defect, so `PAGE_INTEGRATION_PASS=false`. R168 does not relax page-flow, sentence integrity, or page-integration gates.

The P639 figure itself passes mathematics, object content, geometry, relations, native readability, grayscale, overlap, clearance, and clip review. The disposition is nevertheless SA2 because one hard gate is sufficient to fail SA3.

## Isolation disclosure

The reviewer did not read the accepted SA1 root, R210 acceptance root, old P639 evidence, state/inventory, Git history, or chat conclusions. While locating necessary adjacent current prose, one `rg` result also exposed the current V5-C04 `figure_sources.json` metadata entry for this figure. It contained no old role result or PASS/FAIL conclusion. This incidental current-source metadata hit is disclosed and was not used as evidence for the page-flow failure.

## Required next action

Mainline should accept this immutable SA3 result as `RETURN_TO_SA2` and route the sentence/page-flow repair to the authorized chapter-source writer. Do not edit or reseal the SA3 root, and do not count a local pass.
