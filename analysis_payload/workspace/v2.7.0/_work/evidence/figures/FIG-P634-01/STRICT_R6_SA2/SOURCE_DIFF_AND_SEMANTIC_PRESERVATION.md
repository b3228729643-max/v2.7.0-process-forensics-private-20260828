# FIG-P634-01 R6 source diff and semantic preservation

Scope: the sole business-source edit is `fig_v5_c04_coordinate_sweep.tex`.  The exact before/after hunks are retained in `source_diff.patch`.

## Changed source lines

- `16–17`: synchronized alt text and title; the exact coordinate order `1,2,…,j−1,j,j+1,…,d`, substep state `x^[j]`, terminal equality `x^[d]=x^(t)`, and the condition “only after the final coordinate update” remain explicit.
- `21–25`: the upper band now names relative positions `前位 / 当前 / 后位 / 末位`; the slots, centers, order, arrow, and two leading coordinates are unchanged.
- `35–42`: node labels use `前段末位 / 当前坐标 / 后段首位 / 末位坐标`; state bands use `本轮新值 / 当前新值 / 前轮旧值`.  The four completed, one current, and three pending node styles are unchanged.
- `45`: only the first-card title coordinate changes from `y=-1.25` to `y=-1.34`; its mathematical state stays `x^{[j]}` and the title becomes `当前子步状态`.
- `47,49`: the first-card partitions are expressed as `起始至当前坐标` and `后续至末位坐标`, retaining the new/old split without repeating heterogeneous single-letter indices.
- `56`: `同一状态` becomes the equivalent `状态相同`.
- `61`: short and long captions are synchronized to fixed-order immediate write-back, front/new versus rear/old substep state, and equality with the recorded round-end sample only after the final coordinate is updated.

## Semantic invariants

1. Scan order is unchanged: the same eight slots and the same left-to-right arrow encode the fixed order.
2. The current substep is unchanged: the orange fifth slot remains current and the first card still displays `x^{[j]}`.
3. The update invariant is unchanged: the front segment uses current-round values while the rear segment uses previous-round values.
4. The sampling rule is unchanged: the bottom card still contains `x^{[d]}` and `x^{(t)}`, joined by a bidirectional same-state arrow, followed by a one-way record arrow to `轮末样本`.
5. Exact index notation is not erased: it remains in alt text and the dedicated state formulas; positional prose is used only where it is more natural for the visible instructional labels.
6. Source literal CJK `一` count after the edit is zero.  No key instructional proposition was removed.

## Non-mask clearance repair

The EL-035 repair is geometric: moving the existing title node by `0.09` TikZ units increases genuine whitespace to the unchanged card border.  No new fill, white patch, clipping path, opacity trick, mask, or overlay was added.  The pre-existing `sl634-halo` nodes remain confined to the four hatched completed-coordinate cells and were not changed or used for EL-035.

## Font invariant

The edit does not reduce any font.  Explicit ordinary bases remain `9.6pt`, `9.8pt`, `10.0pt`, and `10.6pt`; the minimum is `9.6pt >= 9.5pt`.
