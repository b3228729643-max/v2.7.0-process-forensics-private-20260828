# FIG-P372-01-SA1-STRICT-R1

RESULT: **FAIL**  
TASK_ID: FIG-P372-01  
ROLE: Independent read-only subagent1, strict R1

## Coverage

- Frozen candidate: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r93_fullbook\main_full.pdf` (4,933,710 bytes).
- Located in that candidate by caption/body confirmation: physical PDF page **405**, printed page **392**, **图 21.1**, label `fig:V3-C05-lattice`.
- Source reviewed: `src\绘图源码\第03册_优化模型与序列模型\V3-C05\fig_v3_c05_lattice.tex`, and local body context `V3-C05.tex` lines 429–445.
- Four views inspected: whole page 200dpi, figure crop 300dpi, direct-vector clipped standalone graph 300dpi, and grayscale 300dpi. All 300dpi measurements use a direct frozen-PDF render, 1:1, without a resize.
- Coverage includes every real PDF text component (89), every semantic text parent (41), every native vector object (123), and every required relation in `relation_clearance.csv`.

## Blockers

1. **Source effective-font gate fails.** Of 89 real reader-visible text components, 82 fail the 9.5pt requirement: 21 tick components at 8.7pt; common annotation at 8.8pt; 27 node bases at 9.2pt; 27 scripts deriving from an illegal 9.2pt base; and six caption components with effective size not recoverable from the allowed local source context. The title-only 9.5pt runs are the seven passing source rows.
2. **Role-ratio gate fails.** With the mandated ordinary-node base (29px), panel labels are 38px / 29px = **1.310** (limit 1.05–1.20) and ordinary annotation is 34px / 29px = **1.172** (limit 0.95–1.10).

These two failures independently force FAIL. No exception is taken for local readability, apparent neatness, or zero overlap.

## Mathematical findings

PASS. The forward, backward, and Viterbi panels express the intended three aggregations on the same two-state, three-time lattice. The highlighted edge directions and Viterbi backtrace agree with the immediately adjacent explanation and the caption.

## Text consistency and reading order

PASS. The figure uses `q_1`, `q_2`, and `x_1,x_2,x_3` consistently; its caption is the specified single reading conclusion. The reading path is left-to-right by panel, then within each panel by time, then to the shared annotation and caption.

## Strict visual metrics

| Gate | Result | Evidence |
| --- | --- | --- |
| Source effective font | FAIL | `after_font_audit.csv` |
| 300dpi pixel height | PASS | `after_pixel_measurements.csv` |
| Same-class / cross-panel ratios | PASS | `same_class_ratio_audit.csv` |
| Role ratio | FAIL | `role_ratio_audit.csv` |
| Illegal overlap pixels | PASS, 0 | `after_overlap_report.csv` |
| Clipped pixels | PASS, 0 | `audit_facts.json`, `audit_run_manifest.json` |
| Text–text bbox clearance | PASS, min 17px | `relation_clearance.csv` |
| Text–graphic ink clearance | PASS, min 14px | `relation_clearance.csv` |
| Text–image edge | PASS, min 53px | `relation_clearance.csv` |
| Cross-panel reader-element bbox clearance | PASS, min 147px | `relation_clearance.csv` |
| Visual harmony | FAIL | role-ratio failure, four-view review |
| Grayscale | PASS | `after_grayscale_300dpi.png` |
| Page integration | PASS | `after_full_page_200dpi.png` |

## Pixel and mask method

Text evidence is derived only from actual PDF `RAWDICT` spans. Each mask is bounded by the corresponding real PDF character boxes and accepts pixel foreground only at a local RGB difference of at least 20/255; no morphology, dilation, or same-colour flood-fill is used. Vector masks come from the PDF’s native `get_drawings()` paths, replayed separately at 300dpi with their original coordinates, stroke, fill, dash, cap, and join. Node fills are separately classified as background and never counted as an illegal overlap with their internal label.

The two closest reported relationships are fully reproducible:

- `relation_01_TG_020_010_*`: `F_X_2` ↔ `D021_NODE_BORDER`, `BBOX_CLEARANCE_PX=0`, **actual** nearest mask clearance 14px, coordinates `(608,494)` and `(608,508)`, zero overlap.
- `relation_02_TT_000_005_*`: `F_TITLE` ↔ `F_TICK_2`, `BBOX_CLEARANCE_PX=17`, actual mask clearance 18px, zero overlap.

This explicitly retains bbox clearance as a gate independent of foreground distance.

## Required fix

SA2 must modify only the stated figure source, eliminate all <9.5pt effective non-script text without a global scale workaround, make the caption’s effective size reconstructible, and rebalance title/annotation versus node-base hierarchy. It must generate a new candidate PDF and complete a fresh evidence set. Per protocol, **do not send this candidate to SA3**; the only next step is SA2.

## Evidence used

- `after_full_page_200dpi.png`
- `after_figure_crop_300dpi.png`
- `after_standalone_300dpi.png`
- `after_grayscale_300dpi.png`
- `after_text_measurement_overlay_300dpi.png`
- `after_font_audit.csv`
- `after_pixel_measurements.csv`
- `same_class_ratio_audit.csv`
- `role_ratio_audit.csv`
- `object_inventory.csv`
- `relation_clearance.csv`
- `after_overlap_report.csv`
- `audit_run_manifest.json`
- `audit_facts.json`
