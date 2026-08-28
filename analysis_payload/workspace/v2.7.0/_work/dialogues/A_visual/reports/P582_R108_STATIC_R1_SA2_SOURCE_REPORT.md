# FIG-P582-01 R108 SA2 static source report

## Verdict

`P582_SOURCE_STATIC_READY_REQUEST_BUILD_SLOT`

- HANDOFF_ID: `A-R108-P582-SA2-STATIC-20260826`
- Only source: `src/绘图源码/第05册_采样方法主题模型与图排序/V5-C02/fig_v5_c02_running_mean.tex`
- Before SHA-256: `C075D4A44A60B95848614543D1D2DBCCCB53F1F776FFDD79A3BF1FEAE3F6550C`
- After SHA-256: `4AB4E8D14252B20576F05BD1D5CB54BCB28F162B9E33EF439BD3ED6E01DBC65C`
- Exact diffstat: one file, 12 additions / 12 deletions; `git diff --check` PASS.
- TeX invocations / commits / fresh roles / second UID: 0 / 0 / 0 / 0.

## Exact static patch

Only twelve explicit font declarations change:

- six `9.2pt/11pt` declarations become `9.5pt/11.4pt`;
- two `8.6pt/10.3pt` tick-label declarations become `9.5pt/11.4pt`;
- four `8.5pt/10.2pt` numeric declarations become `9.5pt/11.4pt`.

The two existing `9.6pt/11.5pt` axis-label declarations remain unchanged. All 14 explicit font declarations are now at least 9.5pt. `resizebox`, `scalebox`, and `transform shape` counts remain zero. Normalizing the font-size/leading declarations makes the before and after source byte-for-byte equivalent, proving there is no other source change.

All raw data, running means, the one-third truth line, axis limits, coordinates, ticks, labels, curves, markers, styles, colors, formula, caption, label, and page relationship are preserved.

## R108 native collision adjudication

The current R108 figure was independently located on physical page 632, printed page 619, figure 31.7. Full-page, crop, standalone, grayscale, and native/8x value-arrow views were opened.

The historical arrow/value issue is not a current R108 hard collision:

- `.640`/first down arrow: shared pixels 0; approximately 18.5858 white pixels clearance.
- `.380`/second down arrow: shared pixels 0; nearest ink-center distance 5 px, approximately 3.5858 white pixels clearance.

Both pairs are separately readable at native scale and 8x. Consequently no geometry change was made for an old conclusion.

## Build risk ledger

The `.380`/second-down-arrow region is the narrowest current clearance and must be the first native1x/8x regression check after building the enlarged-font source. Four numeric labels and all tick labels also widen, so their marker/curve and axis-border clearances must be remeasured. If the new PDF produces a real collision, any later geometry repair must be separately evidenced and narrowly authorized.

## Static seal

- Evidence root: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P582-01\STATIC_R1_SA2_SOURCE_R108_20260826`
- Payload 18; controls 3; ordinary 21.
- Manifest rows 18/18; manifest↔filesystem path/bytes/SHA mismatch 0.
- Read-only 21/21; ADS/cache/pyc/reparse 0.
- `WRITE_STOPPED` ticks `639233460952569555`; maximum other ticks `639233460733311237`; strict margin `219,258,318 ticks`; files at or after marker 0.

Requested next action: grant one controlled build slot for the current single-source patch. This report does not authorize or start TeX.
