# FIG-P689-01 reader-visible denominator freeze

HANDOFF_ID: `C-FIG-P689-01-R115-SA1-FRESH-ISOLATED-V1`

Current candidate: R115, physical PDF page 739 (printed page 726), Figure 35.5.

The denominator covers every reader-visible text line/object inside the figure and its caption. The immediately preceding explanatory paragraph and the following body text are page-integration context, not part of the figure denominator. The source-only `alt` string is not reader-visible and is excluded. Panel borders, arrows, curves, marks, and axis strokes are semantic graphic objects and are covered by object/semantic overlays and text-versus-graphic review, but they are not text-denominator members.

Frozen text denominator: `N=22`.

Required unordered pairs: `C=N(N-1)/2=231`.

IDs:

1. E01 left-panel title: 证据的长度分解
2. E02 left total-evidence label: log p(w)
3. E03 left ELBO-bar label: L(q)：证据下界
4. E04 left KL-bar label: KL 间隙
5. E05 left identity formula: log p(w)=L(q)+KL(q(h)||p(h|w))
6. E06 left note line 1: KL>=0，故 L(q)<=log p(w)；变分族受限
7. E07 left note line 2: 时，间隙可保持为正。
8. E08 right-panel title: 坐标更新下的 ELBO 非降阶梯
9. E09 right upper-bound annotation: 未知全局上限
10. E10 right endpoint annotation: 坐标稳定／局部驻点
11. E11 right x-axis label: 坐标更新轮次
12. E12 right x tick 0
13. E13 right x tick 1
14. E14 right x tick 2
15. E15 right x tick 3
16. E16 right x tick 4
17. E17 right x tick 5
18. E18 right x tick 6
19. E19 caption label: 图 35.5
20. E20 caption text line 1
21. E21 caption text line 2
22. E22 caption text line 3

This denominator is frozen before creation of any manual verdict ledger. Any later discovery of an omitted reader-visible figure/caption text object would invalidate the review rather than silently changing `N`.
