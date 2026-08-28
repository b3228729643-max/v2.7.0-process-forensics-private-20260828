# Root decision: direct LuaLaTeX for the next authorized build

- `DECISION`: after a future explicit mainline grant, use one direct `lualatex` controller rather than `latexmk` for P654's next local build attempt.
- `CURRENT_BUILD_AUTHORITY`: none; B-P05 R2 owns the current TeX slot.
- `AUTOMATIC_BUILD_AFTER_PREFLIGHT`: forbidden.

## Reason

P654 R4 and R5 both failed inside the latexmk chain before `ctexbook.cls` or the business source was read. R5's shell assignments alone did not prove the child-visible/resolved cache state, whereas R6 now proves with the intended parent/child environment chain that all three cache variables are visible, expand through `kpsewhich` to one exact absolute path, and are writable by the child token.

Mainline additionally supplied one project-local diagnostic precedent: in a P608 local build, latexmk still encountered the luaotfload cache failure even with three cache variables and an ASCII junction, while one direct lualatex invocation with the same three-variable cache binding succeeded. This fact is used only as a P654 root-diagnostic routing reason. It must not be copied, messaged or written into any P608 fresh-SA1 context or evidence.

Direct lualatex removes the failing latexmk/runscript controller layer while preserving the same read-only P654 standalone wrapper, target source, engine options and single-controller discipline. It does not relax any visual or evidence gate.

## Future boundary

A future build requires all three conditions: `B_P05_R2_BUILD_SLOT_RELEASED`, mainline confirmation that latexmk/lualatex/luatex/luahbtex are all NONE, and a new explicit P654 grant. Because this R6 package will be sealed, no future engine or cache may write here; the grant must designate a fresh build/evidence root using the same verified triple-binding pattern. Success would still require native 300 dpi `N=116`, `C(116,2)=6,670`, 1x/8x, per-ID manual ledgers, `FRM_TRIAL_005 H_INK>=22px`, and every regression gate.
