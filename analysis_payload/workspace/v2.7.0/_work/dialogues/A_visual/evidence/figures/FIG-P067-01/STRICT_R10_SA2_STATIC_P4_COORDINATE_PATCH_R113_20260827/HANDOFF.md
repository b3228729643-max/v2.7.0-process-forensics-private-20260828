# P067 static patch handoff

- HANDOFF_ID: `A-R113-P067-SA2-STATIC-P4-COORDINATE-PATCH-20260827`
- Verdict: `P067_SOURCE_STATIC_READY_REQUEST_BUILD_SLOT`
- Source before: 4014 bytes, SHA-256 `2881377AEEF78E8C7BD7502AD8A303E19AAC395F1936475BDC6D569195900920`.
- Source after: 4014 bytes, SHA-256 `11BF3681D069F6A38C479B3074F39F93E8EB6144FF155AC543508E3589A51144`.
- Exact diff: one file, 1 insertion and 1 deletion; only `.89` to `.85` in the `p_4` node y coordinate.
- Static projection: old two 34 px overlaps are predicted to become zero shared ink, with 5 px and 6 px complete blank separation respectively; next unrelated object remains 20.10 px away.
- Validation completed: source identity, exact diff, name-only, numstat, empty index, and `git diff --check`.
- Not performed or claimed: TeX/build, rendered PASS, commit, fresh role, second UID/source, or central-state mutation.
- Next action: Main may independently review this immutable static package and, if accepted, grant one controlled standalone/direct LuaLaTeX slot.
