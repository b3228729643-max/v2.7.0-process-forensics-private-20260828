# FIG-P109-01 — isolated SA2 R168 read-only review

## Identity

- HANDOFF_ID: `A-R114-P109-SA2-R168-READONLY-20260828`
- Canonical reviewer instance: `/root/p109_r114_r168_sa2`
- Model / effort: `gpt-5.6-sol` / `xhigh`
- fork_turns: `none`
- Candidate: R114
- Fixed evidence root: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P109-01\STRICT_R1_SA2_R168_READONLY_R114_20260828`

The fixed root and exact UID parent both tested `Leaf=false, Container=false, Any=false` before their one successful creation at the specified paths. No fallback, replacement root, or restarted reviewer was used.

## Verified inputs

- Official PDF: 4,967,122 bytes; SHA-256 `C3BB9B1C7FC9D7AF9178CD33F227F24899AA505FAB81840DB6E3AD8BD6CE78A6`.
- Current figure source: 1,865 bytes; SHA-256 `E8B3303A3893491A69815F407423C68BC17663CC017DC3AB49953235E615FD98`.
- Exact chapter context: 56,386 bytes; SHA-256 `7E3B9DD542327B56022FE6E8358ABD3F87F81386CF5D9CD609DC0A7B0E532E37`.

The current caption was located independently from the current source, chapter context, and R114 PDF. It occurs exactly once at physical page 116 of 817 (printed page 103). The historic Goal-card physical page was not used as location evidence.

## Complete observation scope

The frozen denominator contains 14 reader-visible objects and all 91 unordered object pairs. Post-observation ledgers additionally cover six text/glyph IDs, six mathematical relations, eight semantic checks, six page-integration checks, and eleven R168 hard gates.

I opened the full page at 200 dpi and native 300 dpi, the native-300 figure+caption crop, the native-300 grayscale crop, object/text/semantic overlays, and all six critical ROI pairs at native1x and nearest8x. The render came directly from the frozen R114 PDF without secondary resize; the nearest8x views only magnify native pixels.

## R168 finding

One true hard defect is present. In pair `O01-O11` / `P010`, the convex-set boundary crosses the mathematical `C` glyph in the domain label `凸可行域 C`. The collision is visible in the native 300 dpi crop and is unambiguous in `R06_nearest8x.png`. This is independent semantic geometry and text foreground occupying the same visual path, not an advisory font-size or ratio issue.

No other hard defect was observed: all expected objects and glyphs exist; there is no tofu or wrong codepoint; formulas and caption preserve the convex-set meaning; no object is clipped; the remaining 90 unordered pairs are clear or intentional semantic contacts/enclosures; grayscale encoding is stable; text is actually readable without serious imbalance; and page integration is sound.

The source's 9.2pt declarations and historic numeric pixel/ratio thresholds were treated as advisory under R168. They do not create a hard failure because the text is actually readable. The direct boundary/glyph collision does create a hard failure.

## Sealed business route

`FAIL_TO_MAIN_SOURCE_SCOPE`

Exact single-source scope: `fig_v1_c07_convex_set.tex`, lines 29-30 only. Move the domain-label node or give it an opaque protective background so the set boundary no longer crosses the `C` or any label glyph. Do not alter the figure's mathematics, set shape, segment/marker geometry, statement, caption, chapter text, labels, numbering, or build entry.

This reviewer made no source change, did not invoke TeX or a build, did not write central/state/inventory files, did not use Git, did not start a second role or UID, and did not migrate the result.
