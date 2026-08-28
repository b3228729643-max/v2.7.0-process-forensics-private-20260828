# FIG-P020-01 — R107 fresh isolated terminal SA3 report

## Verdict

- `HANDOFF_ID`: `A-R107-P020-SA3-FRESH-ISOLATED-20260826`
- `UID`: `FIG-P020-01`
- `ROUND`: `R107`
- `SA3_FINAL_VERDICT`: `PASS`
- `REQUIRED_OUTCOME`: `SA3_PASS_READY_FOR_MAIN_A_LOCAL_PASS_ACCEPTANCE`

This SA3 report does not issue the main acceptance decision; that authority remains with the main role.

## Actual startup identity and isolation

- Instance: `/root/p020_r107_fresh_sa3`
- Role: sole fresh isolated terminal SA3
- Model: `gpt-5.6-sol`
- Reasoning effort: `xhigh`
- Actual scheduler fork: `fork_turns=none`
- Parent history inherited: `false`

The initially spoken fork description was corrected before any persistent identity or report was written. Every persistent identity artifact records only `fork_turns=none`.

I used only the supplied R107 PDF, current P020 drawing source, active Goal and its referenced v2.7.0 Goal section, the strict protocol, the strict schema, and the genuinely necessary current V1-C01 neighboring body-text passage. I did not read any prior P020 role evidence, prior report, prior handoff, prior result, prior page/crop/object/candidate/decision, state/inventory material, route log, task packet, chat history, Git history/diff/log, or another figure. In particular, no old-role denominator or object list was read or aligned. No second role, UID, agent, TeX build, source edit, commit, or state/inventory write was performed.

## Frozen inputs

| Input | Bytes | SHA-256 |
|---|---:|---|
| Official R107 `main_full.pdf` | 4,967,249 | `8811950621E2D64A3C2A8F0F7A52DD0FAC2BDB12018F3EA052C1F58C94EF8DF3` |
| Current `fig_v1_c01_language_flow.tex` | 2,627 | `FF006894E35D1D3E79F1C1D85D212B79735F3D11937B17F23A49D68DC97547CE` |
| Referenced v2.7.0 Goal | 325,853 | `4FB8A2B615AC7EDA635D0F8DACACE9CF88692153A049D4A04BE06B56BCB53F1A` |
| Strict pixel/typography protocol | 8,066 | `D8CD892CE6A33E6B8B9874B0BB3B35FDB537C2EE169401BCC4D85985465AEFA6` |
| Strict figure evidence schema | 11,278 | `D368ACDA21E755240F1842C2009D09C6DC6F3B88E113457A10F412708C8F4C86` |

The final terminal cross-check rehashed the PDF and source and confirmed both still matched these frozen identities.

## Independent target location and native crops

- PDF pages: 817
- Target: physical PDF page 17, printed page 4
- Page size: `595.276 × 841.890 pt`
- Exact visible caption: `图 1.1 数学语言从对象声明到任务陈述的依赖关系。每一条箭头都表示右侧内容使用左侧定义。`
- Caption PDF bbox: `[80.257, 361.850, 503.680, 372.311] pt`
- Direct native 300 dpi page: `2481 × 3508 px`
- Direct native 200 dpi page: `1654 × 2339 px`
- Figure crop including caption: `[59,266,525,375] pt`, native `1944 × 455 px`
- Standalone body crop: `[59,266,525,359] pt`, native `1944 × 388 px`
- Crop method: integer crop of the direct Poppler raster; no resizing

The page, caption, and crop were located independently from the current PDF. Final views include the full page at 200/300 dpi, the figure crop, standalone body, grayscale, and measurement overlay.

## Denominator closure and correction history

The pre-manual provisional denominator was `N=79, C=3081`: 65 body glyphs plus 14 foreground graphic components. It omitted the visible caption. This provisional denominator is withdrawn.

Before any manual ledger or seal, I reclosed the complete frozen crop from my own R107 PDF character stream and visible contours. The caption was added, every machine artifact and every unordered pair was regenerated, and the corrected denominator was frozen as follows:

- Figure-body glyphs: 65
- Caption glyphs: 43
- Total text glyph objects: 108
- Foreground graphic components: 14
- Final `N = 108 + 14 = 122`
- Final exhaustive unordered pairs: `C(122,2) = 7,381`
- Actual enumerated pair rows: 7,381
- Unique pair IDs: 7,381

The body character closure is:

| Visible sequence | Glyphs |
|---|---:|
| `对象声明` | 4 |
| `关系与映射` | 5 |
| `运算与逻辑` | 5 |
| `可核验任务` | 5 |
| `集合、类型与维数` | 8 |
| `定义域` | 3 |
| `值域` | 2 |
| `复合、量词与约束` | 8 |
| `输入、输出与判据` | 8 |
| `逆向核对：任务所用定义逐项返回检查` | 17 |
| **Body total** | **65** |

The caption closure is:

| Visible sequence | Glyphs |
|---|---:|
| `图1.1` | 4 |
| `数学语言从对象声明到任务陈述的依赖关系。每一条箭头都表示右侧内容使用左侧定义。` | 39 |
| **Caption total** | **43** |

Thus, 65 is specifically the complete figure-body text count, not the complete crop text count. The corrected complete crop count is 108. Concatenating the glyph objects by their parent sequences reproduced every visible title, node-body string, inline annotation, return annotation, caption label, and caption sentence exactly. Each visible character has one distinct glyph object and a nonempty mask; there is no omission, merge, replacement, or crop-boundary truncation.

The frozen crop contains 16 visible PDF drawing/path objects. Four node borders, five arrow shafts/paths, and five arrowheads are the 14 foreground components included in `N`. Exactly two components are excluded as backgrounds: the outer pale rounded figure backing fill and the opaque white annotation backing rectangle. No formula, math accent, or mathematical rule is present, so the math-rule object count is zero. This closes all visible nonempty glyphs and drawing paths without borrowing a denominator from another role.

## Machine gates on the corrected N/C

- Empty masks: 0
- Missing/tofu/replacement/wrong-codepoint objects: 0
- Hard pixel-height failures: 0
- Independent-object illegal overlap pairs: 0
- Canonical illegal-overlap pixels: 0
- Clearance failures: 0
- Clip pixels: 0
- Source/font hard gate: PASS
- Machine semantic gate: PASS
- Overall machine status: PASS

All 7,381 corrected unordered pairs were evaluated. The only five nonzero mask intersections are designed shaft-to-own-arrowhead joints: the inline mapping arrow, three main-chain arrows, and the dashed return arrow. Their total intersection area is 517 pixels; none is an independent-object overlap.

Minimum measured clearances at the 300 dpi native render are:

- Text to text bbox: `24.000000 px`
- Text to node border: `15.000000 px`
- Text to line/arrow: `12.928388 px`
- Arrowhead to text: `13.317821 px`

The PDF/source semantic checks agree on the four-node order `对象声明 → 关系与映射 → 运算与逻辑 → 可核验任务`, the inline `定义域 → 值域` mapping, and the return path from task back toward object. The neighboring body text confirms that arrows record use/dependency rather than reversible implication.

## R168 adjudication

R168 was applied exactly:

- micro ratios in `[0.92,1.08]`: advisory only;
- font metadata differences: advisory only;
- single-horizontal-stroke CJK pixel height: advisory only;
- 1–2 pixel raster differences: advisory only.

The intact caption glyph `一` (`T091`, U+4E00, `5 × 38 px`) and low-profile punctuation remain advisory because they are nonempty, codepoint-correct, complete, pure, unclipped, and readable. No hard condition exists: no missing/tofu/wrong codepoint or meaning, unreadability, obvious severe imbalance, real clipping, illegal overlap, or geometric/semantic error.

## Final visual and manual review

Only after the final machine artifacts were fixed, I actually opened and reviewed:

- the final full-page 200 dpi view, figure crop, standalone body, grayscale view, and text-measurement overlay;
- all 11 final 8×-nearest glyph contact sheets;
- both final graphic contact sheets;
- all 22 critical/closest relation images at 1×;
- all corresponding 22 relation images at 8× nearest.

I then hand-authored row-specific ledgers:

- 108/108 glyph review rows;
- 14/14 foreground graphic review rows;
- 22/22 critical/closest relation review rows;
- 11/11 view/role/script review rows.

Every row has an object- or relation-specific note and a manual PASS. Machine scripts contain no reviewer, boolean, decision, or note fields and did not generate or overwrite the manual ledgers. Final manual gates for font harmony, visual harmony, math/diagram semantics, text consistency, grayscale, page integration, reading path, and caption all pass.

The terminal validator additionally opened all 537 PNGs successfully, resolved all 518 referenced PNGs, verified contact-sheet and relation-image cardinalities, checked safe filenames, and revalidated every denominator and manual-ledger identity.

## Seal

Evidence root:

`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P020-01\STRICT_R3_SA3_FRESH_ISOLATED_R107_20260826`

One successful seal was performed. A preceding program invocation stopped inside its read-only ADS preflight, before either manifest or `WRITE_STOPPED` existed and before any seal content was written; the argument binding was corrected before the single successful seal event.

- Sealed at: `2026-08-26T17:48:31+08:00`
- Payload entries: 565
- Common payload SHA-256: `452BE36EC624E680AFC947BE2CAF42B1A26D9E8EBD0C271230B8F0E422EE9248`
- `SEALED_MANIFEST.json`: 101,557 bytes; SHA-256 `63CC2433A971DEE1F122C895CFBDF394CB4987F4D10B9BDE6503DA30BE23E8B8`
- `SEALED_MANIFEST.tsv`: 62,221 bytes; SHA-256 `3CAE1BD9D0584505837C56D8A9542A55E2AEFBC2D8A41720A1923114057A1582`
- `WRITE_STOPPED.txt`: 616 bytes; SHA-256 `C8E1ED14E0BACA4141B1420B22F689320E508EFCE2D8141325A8150FE859E7D7`
- Ordinary files including manifests and marker: 568
- Read-only failures: 0
- ADS: 0
- cache/pyc: 0
- reparse points: 0
- Post-seal root content writes: 0

Independent post-seal verification parsed both manifests, confirmed their common payload identity, and rehashed all 565 payload entries with zero missing/byte/hash mismatches. It also confirmed every ordinary file is read-only and `WRITE_STOPPED.txt` has the latest content timestamp (`2026-08-26T09:48:31.8341051Z`, later than the maximum other-file timestamp `2026-08-26T09:48:31.7760626Z`).

## Final disposition

`SA3_PASS_READY_FOR_MAIN_A_LOCAL_PASS_ACCEPTANCE`
