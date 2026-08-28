# FIG-P580-01 R2B graphic-pair discovery result

Result: `SA2_LOCAL_FAIL_DISCOVERY`.

The 25 final native 300 dpi graphic raw masks were independently recomputed across all 300 graphic–graphic unordered pairs. Coverage is 300/300; 26 pairs have native overlap, 24 further pairs have zero overlap but one-pixel-centre adjacency (`clearance=max(distance-1,0)=0`), and 250 pairs have positive clearance. Fifty critical packages contain raw ROI, A, B, intersection, and overlay evidence at native 1× and nearest-neighbour 8×.

Two independent-semantic overlaps are illegal and require source repair:

1. `PAIR_GR004_GR025`, 11 pixels: several missing-support hatch/region pixels enter the x-axis arrowhead interior. The package is `critical_pairs/PAIR_GR004_GR025/`.
2. `PAIR_GR020_GR024`, 2 pixels: the fixed-height `q_R` proposal curve crosses the upper edge of the independent `p(4)` target triangle marker. The package is `critical_pairs/PAIR_GR020_GR024/`.

R2B did not modify the business source; its SHA-256 remained `74a21ea35bdb09d5c01858e027b96aec844233f6850f6e7a8a9da03524466ef0`. This directory is discovery evidence only, not an acceptance candidate. Repair and full replacement evidence continue in `STRICT_R2C_SA2_GRAPHIC_PAIR_REPAIR_R95_LOCAL_20260824`.
