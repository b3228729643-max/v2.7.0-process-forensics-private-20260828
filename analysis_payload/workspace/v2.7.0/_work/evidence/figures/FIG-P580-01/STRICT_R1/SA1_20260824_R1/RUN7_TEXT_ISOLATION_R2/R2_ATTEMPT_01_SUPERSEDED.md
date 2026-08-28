# R2 attempt 01 — superseded before manual review

This 05:53 initial generation is not terminal evidence and must not be used
for any pixel, D/E, mapping, package, or contact conclusion.  It exposed that
the character ownership ROI was based only on rounded rawdict layout boxes,
leaving text-replay antialias pixels outside those boxes and producing a false
global unassigned-pixel failure.  The next R2 rebuild uses the documented
rawdict/texttrace integer-bbox union with frozen paint-order ownership.

No contact cell in this attempt was manually reviewed.  `RUN_STATE.json` and
`STRICT_R1_INTERIM_PENDING.md` record its non-terminal status.
