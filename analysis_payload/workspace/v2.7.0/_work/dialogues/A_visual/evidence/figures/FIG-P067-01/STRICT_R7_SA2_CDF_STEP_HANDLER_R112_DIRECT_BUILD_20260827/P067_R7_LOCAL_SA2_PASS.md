# FIG-P067-01 R7 local SA2 review

- Handoff: `A-R112-P067-SA2-DIRECT-BUILD-R7-20260827`
- Result: `LOCAL_SA2_PASS_READY_FOR_MAIN_REVIEW_AND_ATOMIC_COMMIT_AUTHORIZATION`
- Source: 4,014 bytes, SHA-256 `2881377AEEF78E8C7BD7502AD8A303E19AAC395F1936475BDC6D569195900920`
- Standalone PDF: 34,211 bytes, SHA-256 `73FBE000AC977A7E270D4834A0F9B81AC24C851BAE72B38503ACCAEBC844E108`
- Build: one direct LuaLaTeX child, exit 0, natural completion, retry/latexmk/version-probe 0, terminal TeX processes 0.
- Denominator: 65 visible glyph atoms + 50 foreground paths = N115; all C(115,2)=6,555 unordered pairs were enumerated once.
- Machine hard gates: overlap candidate hard failures 0, clip 0, empty foreground atoms 0, duplicate/self pair rows 0.
- Manual review: 115 object rows, 16 critical relation rows, and 16 opened-view rows; all unique, all object/relationship specific, blank notes 0, non-PASS 0. Machine code generated or overwrote no manual field.
- CDF semantics: `[.5,1):0`, `[1,2):.15`, `[2,3):.45`, `[3,4):.80`, `[4,4.5]:1`; four open/filled endpoint pairs encode right continuity and the four jumps equal PMF masses `0.15,0.30,0.35,0.20`.
- Tick regression: `0.35↔0.3` and `0.3↔0.15` each have zero shared foreground at native 300 dpi and nearest-8x. The one-native-pixel gap is recorded only as R168 advisory because all labels are actually readable.
- Visual regression: native color, grayscale, atomic overlay, three glyph sheets, three path sheets, CDF and PMF native/nearest-8x panels, and standalone page were opened. No tofu, wrong codepoint, mathematical error, unreadability, obvious imbalance, true clipping, or illegal overlap was observed.
- Git scope remains exactly one file / 1 insertion / 1 deletion: `const plot mark right` to `const plot mark left`; index is empty and `git diff --check` passes.

This report does not authorize or create a commit, start a fresh role, run TeX again, or change central state.
