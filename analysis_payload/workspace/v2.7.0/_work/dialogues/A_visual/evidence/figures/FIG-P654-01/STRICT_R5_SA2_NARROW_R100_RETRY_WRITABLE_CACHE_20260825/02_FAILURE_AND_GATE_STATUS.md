# R5 failure and gate status

## Observed result

- `PDF_COUNT`: `0`
- `RESULT`: `BUILD_FAIL_NO_CANDIDATE_CONTINUE_SA2`
- Failure occurs during LuaHBTeX initialization at document line 1, before document-class/body processing and before the P654 target source is read.
- The engine again reports `luaotfload ... no writeable cache path, quitting` while loading `basics-gen`.
- Both explicitly created R5 cache directories remained empty after the controller exited.

The direct evidence supports only this statement: LuaHBTeX did not accept a writable cache path in R5. The actual child-process values of `TEXMFVAR`/`TEXMFCACHE` and the engine's resolved cache paths were not captured, so the evidence cannot distinguish failed environment inheritance, failed cache-path resolution, or rejection after resolution. A Windows CP936/non-ASCII-path visibility issue is possible because latexmk's transcript renders the Chinese path as replacement glyphs, but that explanation is not proven and is not promoted to a fact.

## Gates not run

Because there is no new PDF, R5 did not run or claim:

- native 300 dpi rendering or post-patch `FRM_TRIAL_005` height;
- `N=116` object closure or `C(116,2)=6,670` complete unordered pairs;
- native1x/8x object evidence, manual per-ID ledgers, ownership, overlap, clearance, clip, font harmony, grayscale or page-integration gates.

The source-only static checks remain valid, but they do not establish SA2 PASS. No third build is authorized or attempted.
