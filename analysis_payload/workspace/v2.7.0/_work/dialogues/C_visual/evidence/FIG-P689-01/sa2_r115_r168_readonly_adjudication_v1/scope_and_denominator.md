# FIG-P689-01 SA2 R168 read-only adjudication scope

- HANDOFF_ID: `C-FIG-P689-01-R115-SA2-R168-READONLY-ADJUDICATION-V1`
- INSTANCE: `/root/sa2_fig_p689_r115_r168_readonly_v1`
- OFFICIAL_CANDIDATE: R115, physical PDF page 739, printed page 726
- CURRENT_FIGURE: Figure 35.5, label `fig:V5-C06-elbo-geometry`
- CURRENT_CAPTION: 观测对数证据等于ELBO与变分分布到真实后验的KL散度之和；平均场坐标更新可使ELBO逐步不降，但非凸目标下有限运行通常只得到坐标稳定点或局部驻点，多启动比较也不构成全局最优证明
- OBSERVATION_ORDER: full page 200 dpi; full page 300 dpi; native figure+caption 300 dpi; grayscale 300 dpi; object, semantic, text overlays; foreground mask; each of eight critical ROIs at native1x and nearest8x; only then the manual ledgers.

## Frozen denominator

`N=31` reader-visible semantic objects and `C=N(N-1)/2=465` unordered pairs.

The denominator is source-level and reader-visible. Every reader-visible text element has its own `Txx` ID, including each tick label and the caption number/body. Repeated circular plot markers are one multipart `G11` source-level semantic object because one `\addplot` mark encoding creates the set; the continuous staircase is the separate `G10` line encoding. The x-axis plus its homogeneous tick-mark set is `G08`, while the y-axis is `G09`. Fills are included because they convey the ELBO/KL decomposition, even though they are background rather than illegal-overlap foreground. No decorative hidden object is counted.

`object_index.csv` freezes IDs, roles, source references and geometry. `pair_index_no_verdict.csv` enumerates all 465 unordered pairs without verdict fields. `manual_pair_matrix.csv` supplies the post-observation verdict for every indexed pair.

## R168 rule applied

The 9.0--9.2 pt source declarations and legacy numeric font/pixel/ratio thresholds were treated as advisory. A hard failure would require an actual missing/tofu/wrong codepoint or math, actual unreadability or obvious imbalance, true clipping, confirmed illegal visible-ink overlap, or semantic/geometric/math error. None was observed.
