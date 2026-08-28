# Immutable SA2 R168 read-only report — FIG-P077-01

Handoff ID: `A-R114-P077-SA2-R168-READONLY-20260827`

## Outcome

`SA2_NO_SOURCE_CHANGE_READY_FOR_FRESH_SA1`

No true R168 hard defect was observed. The official R114 page has no missing/tofu/wrong-codepoint or mathematical-meaning defect, unreadability, obvious imbalance, true clipping, illegal visible-ink overlap, or geometry/semantic error. The source’s older 8.8/9.2/9.4 pt declarations are explicitly retained as advisory facts and are not used alone to force source return.

## Independent evidence

- Official R114 identity matched exactly: 4,967,122 bytes; SHA-256 `C3BB9B1C7FC9D7AF9178CD33F227F24899AA505FAB81840DB6E3AD8BD6CE78A6`.
- Current main source identity matched exactly: 2,603 bytes; SHA-256 `ED96F120CFF0815122B2914D7D94D12884FAC3DB328D30E883F93457C68484E4`.
- A full-PDF caption search found exactly one current occurrence on physical page 79 of 817.
- Full-page 200 dpi and native 300 dpi, native figure crop, grayscale crop, object overlay, and five native1x/nearest8x critical ROI pairs were generated and opened.
- Frozen visible-object denominator: 20.
- Complete unordered-pair denominator: 190.
- Manual object ledger: 20/20 unique IDs; no blank reviewer/decision/note fields.
- Manual pair ledger: 190/190 unique IDs; no missing/extra/mapping mismatch/blank manual fields.
- Threshold-20/255 native observations: numeric tick ink heights 26–27 px; italic x 21 px; direct-label rows 46–47 px; area row 36 px; caption runs 35–39 px.
- Illegal visible foreground overlap pixels: 0. True clipping pixels: 0. Minimum observed text-to-visible-line clearance: approximately 3.3 px at the opaque area annotation boundary.
- Mathematical semantics agree: the standard normal peak is `1/sqrt(2pi)`, the `N(0,2^2)` peak is `1/(2sqrt(2pi))`, both are centered at zero, and both integrate to one.

## Mutation scope

Source/build/Git/central/process-management changes: **0**. The only created material is this task’s new evidence package and its immutable external report/handoff/control.

## Sealed identities

- Evidence root: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P077-01\STRICT_R1_SA2_R168_READONLY_R114_20260827`
- External report: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P077-01\STRICT_R1_SA2_R168_READONLY_R114_20260827_REPORT.md`
- External handoff: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P077-01\STRICT_R1_SA2_R168_READONLY_R114_20260827_HANDOFF.json`
- Final root control: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P077-01\STRICT_R1_SA2_R168_READONLY_R114_20260827\WRITE_STOPPED`

Seal contract: all 32 pre-marker root files and the root directory are ReadOnly before the already-ReadOnly control marker is moved into place as the sole final root content/attribute-affecting operation. The sealed root therefore contains 33 ReadOnly files.

Next action: the main coordinator may start a genuinely fresh SA1. This role must not self-start SA1/SA3 or another UID.
