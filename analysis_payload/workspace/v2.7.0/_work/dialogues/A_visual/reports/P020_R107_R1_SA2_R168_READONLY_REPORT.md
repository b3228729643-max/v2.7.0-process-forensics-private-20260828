# FIG-P020-01 — R107 R168 SA2 read-only adjudication report

## Verdict

`SA2_NO_SOURCE_CHANGE_READY_FOR_FRESH_SA1`

The current official figure has no R168 hard defect. The prior low-profile CJK `一` height observation is advisory only, so no source edit or TeX build was performed.

## Identity and current location

- `HANDOFF_ID=A-R107-P020-SA2-R168-READONLY-20260826`
- R107 PDF: 817 pages, 4,967,249 bytes, SHA-256 `8811950621E2D64A3C2A8F0F7A52DD0FAC2BDB12018F3EA052C1F58C94EF8DF3`.
- Current P020 source SHA-256: `FF006894E35D1D3E79F1C1D85D212B79735F3D11937B17F23A49D68DC97547CE`; main and A worktree copies are identical.
- Independently located target: physical page 17, printed page 4, unique caption `图 1.1 数学语言从对象声明到任务陈述的依赖关系。每一条箭头都表示右侧内容使用左侧定义。`
- The old list route page 20 is not the physical page in R107.

## Lean R168 evidence

The reviewer actually opened the full page at 200 dpi; direct native 300-dpi figure-plus-caption, standalone and grayscale views; and the caption `一` context plus its isolated 1×/8× contour.

All four stages, three forward arrows and one dashed reverse-audit route are intact. The labels, node contents, direction, reverse-check semantics and caption agree with the source. Text is readable and balanced; borders and arrowheads are not clipped; no independent objects illegally overlap; grayscale and page integration remain clear.

The caption character is the correct U+4E00. Its 300-dpi exact crop is 42×45 px and its ink bbox is 38×5 px with 87 thresholded ink pixels. The low horizontal outline is continuous, clean, correctly positioned and visibly readable. Under the user-authorized R168 standard, this micro-height fact is advisory and cannot by itself cause a source rewrite, rebuild or FAIL_TO_SA2.

R168 hard-failure counts are all zero: missing/tofu, wrong codepoint/meaning, unreadability, obvious severe font imbalance, real clipping, illegal overlap, geometry/relationship error and caption/page-integration error.

## Seal

- Evidence root: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P020-01\STRICT_R1_SA2_R168_READONLY_R107_20260826`
- Payload: 13 files / 612,081 bytes.
- Ordinary files: 16 = 13 payload + two manifests + `WRITE_STOPPED`.
- Both manifests: 13 identical rows; SHA-256 `D1F4BABEEFEA0220460268D495502609B4E5EE5DDE1233B1E1B579E7FE4716F9`.
- All 16 files are read-only; `WRITE_STOPPED` is strictly latest; post-seal root writes: 0.

## Routing

- Source changed: no.
- TeX invocations: 0.
- Commit: none.
- Main may dispatch one completely fresh isolated SA1 against the current official candidate. A did not start SA1/SA3 or write central state/inventory.
