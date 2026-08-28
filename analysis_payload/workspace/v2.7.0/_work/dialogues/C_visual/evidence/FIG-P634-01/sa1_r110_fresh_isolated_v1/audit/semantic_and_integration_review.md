# FIG-P634-01 independent SA1 semantic and integration review

The official R110 page independently resolves to physical page 684, printed page 671, Figure 33.3. The source label is `fig:V5-C04-coordinate-sweep`. The full visible caption is:

> 系统扫描按固定次序即时写回；当前子步的前段使用本轮新值，后段沿用前轮旧值；末位更新结束后，末位状态与本轮样本状态相同并记录为轮末样本。

The upper arrow fixes a left-to-right order across `1, 2, 省略, 前位, 当前, 后位, 省略, 末位`. The first four hatched blue slots are the already-updated prefix, the gold slot is the current coordinate, and the three dotted gray slots are the not-yet-updated suffix. This implements a systematic Gibbs sweep: at substep `j`, coordinates through `j` use the current round's values and coordinates after `j` retain the previous round's values.

The first card names that mixed state `x^[j]`. The second card states that after the last coordinate is updated, `x^[d]` and `x^(t)` denote the same state. The bidirectional arrow communicates state identity, while the following one-way arrow labeled `仅此记录` makes the round-end state the recorded sample. No intermediate state is presented as a round output.

This agrees with V5-C04 lines 218-221: the next coordinate consumes the just-updated prefix, and only `x^[d] = x^(t)` is retained as the round sample. The visible formulas, numeric labels, caption number, full-width punctuation, and mathematical italic variables have the intended codepoints. No missing glyph, tofu, wrong symbol, or semantic error is present.

Page integration is coherent. The figure immediately follows the learning-algorithm paragraph that introduces Figure 33.3, and the following `读图顺序` paragraph walks through the same sequence. The figure/caption block fits the page without clipping, orphaning, or disproportionate whitespace.

R168 is applied explicitly: the naturally low raster outlines of full-width comma/semicolon/full stop are advisory morphology only. They are correct, legible codepoints and do not create a hard failure.
