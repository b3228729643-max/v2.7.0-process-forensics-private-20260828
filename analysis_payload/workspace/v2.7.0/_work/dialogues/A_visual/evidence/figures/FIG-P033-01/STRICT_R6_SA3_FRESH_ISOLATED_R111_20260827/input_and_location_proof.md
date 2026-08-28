# Input identity and independent target location

## Input identity

- Official R111 PDF: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r111_fullbook\main_full.pdf`
  - bytes: `4,967,076`
  - SHA-256: `DAB1062500E39DD2C34C6B4A9FF51CAC2BE0A4C84B2F45F5FB8E645C4BC012D6`
  - pages: `817`
  - media size: `595.276 × 841.890 pt` (`A4`)
- Current P033 source: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第01册_数学基础与统计学习基本理论\V1-C02\fig_v1_c02_projection.tex`
  - bytes: `2,383`
  - SHA-256: `D3C1D38ECB8468EC3294F7D18BD886316829F14690A516000189CE853A07BC05`
- Necessary current chapter context: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\讲义源码\第01册_数学基础与统计学习基本理论\chapters\V1-C02.tex`
  - bytes: `61,067`
  - SHA-256: `9B3107C9DFDB40F4CD9960F6C7965FEBFE0A9B917D5785C9D75A7D373F2CF5D4`

The two task-pinned hashes match their expected values exactly.

## Fresh PDF location proof

The official PDF was converted to text once inside this new evidence root and split on PDF form-feed boundaries. Searching the resulting page segments for the exact target caption phrase independently returned exactly one segment:

- physical PDF page: `29`
- printed page number on that page: `16`
- exact caption: `图 2.1 向量的正交分解。投影向量属于子空间，残差属于其正交补，虚线残差给出到子空间的最短距离。`

The target's extracted figure-body text bboxes occupy approximately `x=170.759..421.094 pt`, `y=471.887..634.767 pt`; the caption occupies `x=62.360..522.500 pt`, `y=639.700..654.120 pt`. The page-native render visually confirms this is the target.
