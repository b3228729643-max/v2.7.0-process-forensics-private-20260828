# FIG-P640-01 SOURCE R2 static-only proposal

- HANDOFF_ID: `C-FIG-P640-01-SA2-SOURCE-R2-STATIC-ONLY-V1`
- STATUS: `STATIC_ONLY_NOT_APPLIED`
- CURRENT_SOURCE_BYTES: `2717`
- CURRENT_SOURCE_SHA256: `FFAE906011BBAD21FD1AD53997693934828394C2AE516649CCCF8DA5938D9B89`
- PROJECTED_SOURCE_BYTES: `2717`
- PROJECTED_SOURCE_SHA256: `044431D3E6B2ABAFE786EB151B7F4B01585F8E83F158EADEF736E005F6161F38`
- AUTHORIZATION_REQUIRED_FOR_SOURCE_WRITE: `YES`
- TEX_AUTHORIZATION: `NONE`

## Narrow R2 proposal

Change exactly one unique token in the already-authorized P640 source:

```diff
- width=4.9cm,height=4.2cm,xmin=0,xmax=.99,ymin=-.04,ymax=1,
+ width=4.9cm,height=4.2cm,xmin=0,xmax=.99,ymin=-.06,ymax=1,
```

No source write has been made. The proposed replacement exists once in memory and changes one byte; reverse replacement reconstructs the current source identity.

The following remain byte-for-byte unchanged under the proposal:

- `xtick={0,.5,.99}` and `xticklabels={0,.5,.99}`;
- true point `coordinates {(.99,0.0100499975)}`;
- displayed endpoint label `$(.99,\,.010)$` at the same data coordinate;
- `axis lines=left`, curve formula/domain/sampling, marker style, limit note, mathematics, panel sizes, caption and all left-panel content.

## Static clearance derivation from the sealed R1 PDF

Measured R1 geometry at native PDF precision:

- physical right-panel top/bottom: `110.170013 / 184.393021 pt`;
- `.99` vertical tick upper edge: `182.267090 pt`;
- marker data y: `0.0100499975`;
- marker ring vertical radius including stroke envelope: `1.793297 pt`;
- native scale: `300/72 = 4.166667 px/pt`.

With fixed physical panel bounds and `ymax=1`, the marker center predicted for candidate lower bound `m` is:

`center_y(m) = top + (1 - 0.0100499975) / (1 - m) * (bottom - top)`.

Requiring three native300dpi blank pixels between the marker bottom and tick upper edge gives `m <= -0.055951065`. The narrow rounded value `ymin=-.06` predicts:

- marker center `179.488000 pt`;
- marker bottom `181.281297 pt`;
- tick-to-marker gap `0.985793 pt = 4.107 px`;
- static margin above the required 3px gate: `1.107 px`.

Thus `-.06` is the smallest simple two-decimal value that clears the requested threshold with a modest raster-quantization margin. `-.05` predicts only `1.357px`, and `-.055` predicts `2.739px`; neither qualifies.

## Residual risk and verification boundary

The model is anchored to actual R1 PDF vector coordinates and therefore has high confidence, but final clearance still depends on PGFPlots stroke placement and raster quantization. Only a separately authorized single candidate build can convert the prediction into evidence. No TeX invocation or source commit is authorized by this handoff.

If a future authorized build contradicts the prediction and still yields less than 3px clearance, the fallback is not to move or relabel the true point. The narrow fallback would retain ordinary ticks `0,.5`, express `.99` as an `extra x tick` with its label preserved, and set only that extra tick's `major tick length=0pt`. This removes the `.99` tick line while preserving the `.99` label and endpoint semantics. The fallback is not selected or applied in this proposal.

## Prior R1 status

The prior evidence root remains immutable `FAIL_TO_SA2`: `PAIR_0779 / G08-G10` had six shared native300dpi mask pixels. This proposal does not downgrade that collision and does not modify or reseal the R1 root.
