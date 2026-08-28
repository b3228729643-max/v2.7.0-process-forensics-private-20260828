# Formal R106 SA1 report — FIG-P715-01

- HANDOFF_ID: `A-R106-P715-SA1-FRESH-ISOLATED-20260826`
- Assigned scope: single fresh isolated read-only SA1 review of FIG-P715-01 against the official R106 full-book PDF and current P715 source.
- Completed: yes.
- Decision: **FAIL**.
- Route: **SA2**. No `A_LOCAL_PASS`; SA3 is not authorized.
- Evidence root: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P715-01\STRICT_R15_SA1_FRESH_ISOLATED_R106_20260826`
- Root result: `RESULT.json`, SHA256 `FCA33739A8D0820B4D7F6340CB3643F5E2775C38EFF2D9D007A5D82F5264B91F`.
- Root visual report: `after_visual_acceptance.md`, SHA256 `8F4B989AB746F461CEFC8043455A6AF68EE98CE66829129F3A9C3B74E9623D7B`.

## Candidate identity

The unique current caption was independently located on physical page 765 / printed page 752 of the 817-page official R106 PDF. The PDF is 4,967,249 bytes with SHA256 `0FA4A5A0B35D2566D71B5472B49E9B4A8A60CBAE76B3FA744B92783AFC6BC31A`. No inherited page mapping, old P715 evidence, old role result, R168 adjudication result, state file, history, or build artifact was read. No TeX engine was started and no source/build file was edited.

## Evidence and decision

The rebuilt denominator is 216 non-space glyph objects plus 43 foreground drawing paths, for 259 objects and all 33,411 unordered pairs. All 18 glyph sheets, six drawing sheets, 22 critical-pair sheets, four required views, and 21 hard-candidate native/8× ROI packages were opened and manually recorded.

The primary clean hard failure is `PAIR_08396`: the blue node-`j` border and gray glyph “矩” have 37 native intersection pixels. Other confirmed hard failures include 20–97 px independent formula/formula and formula/matrix-border intersections, a P-matrix top border drawn through the node-order note, 3 px text-to-panel clearance against the 6 px minimum, and 0 px text-to-text clearance against the 4 px minimum. Confirmed illegal intersection sum excluding two contaminated-comma relations is 888 native pixels; clip count is 0.

R168 was applied: micro font/pixel ratios, taxonomy subtleties, 1–2 px raster differences, and visually clear low-profile/small glyphs were advisory only. They did not trigger the result. Glyph/codepoint semantics, graph direction, matrices, transpose relation, grayscale legibility, and caption/page integration are otherwise correct. One comma mask (`TXT_G0081`) contains a disconnected 13-pixel foreign component, so its two relations were conservatively recorded as evidence failure and not used as standalone geometry proof.

## Seal validation

The sealed root has 507 ordinary files: 502 payload-manifest entries, four manifest/audit control files, and exactly one `WRITE_STOPPED`. All 507 are read-only. Every manifest payload hash matches; non-default ADS, cache directories, and `.pyc` files are zero. The marker is strictly newest and post-marker root writes are zero.

- Payload manifest CSV SHA256: `7C318BC5FF7BDA4F4FA80DB4786176AB0B3B3A5EC7D7CE69176EE01F28040CE0`
- Manifest identity closure SHA256: `A572F23B1D377B308973F0ADF7783947EC48A0068DD056CEFAD2ED1C48117BD4`
- Seal audit SHA256: `680833C218A1171337918E5F61F9C31860144D8ADC7ABC7D04B29D8582C91CAB`
- `WRITE_STOPPED` SHA256: `07F947B518FD01B03C6E8EE2FD38FC5FE16421770C5F91BC6F961C62948BF700`

## Next action

SA2 should increase node-to-note separation, move the right node-order note clear of the P matrix, increase space below the M/P matrices before superscript formulas, and increase vertical space between consecutive right-panel formula rows. A new official build must then receive a new fresh isolated SA1. This R106 evidence must never be promoted to SA3 or local pass.
