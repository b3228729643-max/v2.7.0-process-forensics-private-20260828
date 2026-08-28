# FIG-P634-01 R6 mathematical and textual consistency

Result: **PASS for local SA2 consistency review; official-root validation remains pending.**

## Mathematical sequence

- Alt text retains the exact fixed order `1,2,…,j−1,j,j+1,…,d`.
- The first state card retains `x^{[j]}` as the state after the current coordinate update.
- The second state card retains `x^{[d]}` and `x^{(t)}` and keeps the bidirectional same-state relation.
- The outgoing arrow still records only the round-end state as `轮末样本`.

## Text/formula agreement

- `前位 / 当前 / 后位 / 末位` and `前段末位 / 当前坐标 / 后段首位 / 末位坐标` describe the same ordered slots as the exact alt notation.
- `本轮新值 / 当前新值 / 前轮旧值` agrees with the system-scan invariant: already updated coordinates use current-round values and not-yet-updated coordinates use previous-round values.
- The first-card prose `起始至当前坐标` versus `后续至末位坐标` matches `x^{[j]}` without deleting the boundary semantics.
- The caption states fixed-order immediate write-back, front/new versus rear/old values, and terminal equality/recording only after the final coordinate is updated.
- The short caption, long caption, title, nodes, status bands, state cards, and alt text use one consistent vocabulary.

## Structural-repair rationale

The visible axis and node labels use natural positional prose while exact `j` and `d` notation remains where it carries mathematical state meaning.  This removes heterogeneous one-letter/script runs from ordinary navigation labels without removing algorithmic content.  Consequently, D uses same-panel/same-role/same-script groups and passes without glyph-identity grouping; E reports N/A when a script has no genuine NODE_LABEL BASE, exactly as required by the schema.
