# R1B quarantine reason; bottom evidence retained

`STRICT_R1B_SA1_FRESH_R99_20260824` is immutable and was not modified by this reseal. It is not accepted as a strict terminal package for two packaging-only defects found by the root mechanical review:

1. Its terminal self-report declared SA1 `gpt-5.6-sol/xhigh`, while the actual root-orchestrated route was `gpt-5.6-terra/max`.
2. `WRITE_STOPPED`, `evidence_manifest.json`, `RESULT.json`, `SA1_HANDOFF.md`, and `after_visual_acceptance.md` had equal `LastWriteTimeUtc` values, so a mechanical checker could not prove the marker was strictly last.

Neither defect changes the underlying findings. R1C reuses the completed R1B raw evidence and CSV facts without rerendering or remeasuring: N=298, all unordered pairs=44,253, G0012 CJK `一`=6px<30px, 19 illegal critical pairs, 943 illegal raw-intersection pixels, and `FAIL_TO_SA2`.

R1C corrects the route metadata, produces a new terminal package, delays `WRITE_STOPPED` after every other write, and then stops writing.
