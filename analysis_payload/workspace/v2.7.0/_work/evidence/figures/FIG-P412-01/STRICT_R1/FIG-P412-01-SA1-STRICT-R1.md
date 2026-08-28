# FIG-P412-01 — SA1 STRICT-R1 独立审计

RESULT: **FAIL**

## 对象定位与冻结身份

- Canonical UID: `FIG-P412-01`; current label: `fig:V3-C07-selection-loop`; current printed figure number: `23.1`.
- Official frozen candidate: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r93_fullbook\main_full.pdf` (directory identity `strict_current_r93_fullbook`, R93).
- Actual PDF physical page (1-based): `449` of 813; printed page: `436`; task-ID page token `P412` is historical and does not identify the current R93 placement.
- Source: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第03册_优化模型与序列模型\V3-C07\fig_v3_c07_selection_loop.tex` lines 3–43. Adjacent source: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\讲义源码\第03册_优化模型与序列模型\chapters\V3-C07.tex` lines 223–230.
- The source has no formula, Latin/Greek variable, or `+`/`−`/`=` basic-operator element inside the figure; those operator/script gates are explicitly `NOT_PRESENT`, not sampled away.

## Strict gate matrix

| Gate | Result | Measured evidence |
|---|---:|---|
| SOURCE_FONT_PASS | `false` | `14` failed text elements; `FAIL: caption declared_pt/effective_pt unavailable in permitted source scope；FAIL: effective_pt=9.0<9.5；FAIL: effective_pt=9.2<9.5；FAIL: effective_pt=9.4<9.5` |
| PIXEL_HEIGHT_PASS | `true` | closest threshold: `T05` `33 px` vs `30 px` |
| SAME_CLASS_RATIO_PASS | `true` | `same_class_ratio_audit.csv` |
| ROLE_RATIO_PASS | `true` | `role_ratio_audit.csv` |
| OVERLAP_PIXEL_COUNT | `0` | independent real-PDF span/vector masks in `after_overlap_report.csv` |
| CLIP_PIXEL_COUNT | `0` | `after_edge_clip_report.csv` |
| MIN_TEXT_CLEARANCE_PX | `7.000` | category minima and nearest points in `after_overlap_report.csv` |
| VISUAL_HARMONY_PASS | `true` | four native views reviewed; visual hierarchy is coherent, but it cannot override font-gate failure |
| MATH_SEMANTICS_PASS | `true` | selection/test flow semantics match source, caption, and adjacent text |
| TEXT_CONSISTENCY_PASS | `true` | labels/caption match source and adjacent body |
| GRAYSCALE_PASS | `true` | `grayscale_300dpi.png` retains direction, containment, and warning distinctions |
| PAGE_INTEGRATION_PASS | `true` | `full_page_200dpi.png`: figure, caption, footer and preceding paragraph do not collide |

## Quantitative threshold record

| Audit family | Measured result | Rule / result | Evidence |
|---|---:|---|---|
| Source node-label effective fonts | `9.2–9.4 pt`; max/min `1.021739`; difference `0.200 pt` | internal consistency passes (`<=1.03`, `<=0.25 pt`), but all are `<9.5 pt` → FAIL | `after_font_audit.csv` |
| Source annotation effective fonts | `9.0 pt`; max/min `1.000000`; difference `0.000 pt` | internally consistent, but `<9.5 pt` → FAIL | `after_font_audit.csv` |
| Caption source font | `UNKNOWN` (PDF vector span is 9.962640 PDF pt, but declaration is outside permitted source scope) | unknown effective source font → FAIL | `after_font_audit.csv`, `raw_pdf/raw_pdf_spans.json` |
| CJK/fullwidth ink heights | `33–38 px` | `>=30 px` → PASS | `after_pixel_measurements.csv` |
| Caption number ink height | `28 px` | `>=24 px` → PASS | `after_pixel_measurements.csv` |
| Same-class node-label ratio | element range `0.970588–1.000000`; max/min `1.0303030303030303` | `[0.92,1.08]`; role max/min `<=1.08` → PASS | `same_class_ratio_audit.csv` |
| Cross-panel same-role ratio | `N/A` | single panel; no cross-panel comparison exists | `same_class_ratio_audit.csv` |
| Annotation/base role ratio | `0.9705882352941176` (annotation median `33.0 px`, base `34.0 px`) | `[0.95,1.10]` → PASS | `role_ratio_audit.csv` |
| Axis / legend / formula / panel-label roles | `NOT_PRESENT` | no applicable role band | `object_register.csv`, source lines 14–42 |
| Text–text PDF/vector bbox clearance | `9.752 px` | `>=4 px` → PASS | `after_overlap_report.csv` |
| Text/formula–line/arrow ink clearance | `7.000 px` (T05↔V08) | `>=3 px` → PASS | `after_overlap_report.csv`, `pairs/T05__V08_overlay_300dpi.png` |
| Node-text–node-border ink clearance | `17.000 px` (T10↔V15) | `>=5 px` → PASS | `after_overlap_report.csv` |
| Text–figure-image-edge clearance | `30.370 px` | `>=6 px` → PASS | `after_pixel_measurements.csv` |
| Independent foreground intersections | `0 px` | exactly 0 → PASS | `after_overlap_report.csv`, `after_overlap_overlay_300dpi.png` |
| Independent edge clips | `0 px` | exactly 0 → PASS | `after_edge_clip_report.csv` |

## Hard-failure basis

Every reader-visible source-owned figure text is declared at 9.0, 9.2, or 9.4 pt; all are below the required 9.5 pt effective minimum. The current R93 PDF vector font sizes corroborate those declarations after TeX/PDF unit conversion. Caption source size is unavailable within this strictly limited read scope (caption macro is outside current figure source), so the caption source-font field is `UNKNOWN`; Goal §9.2.1 requires this to fail rather than be assumed. Pixel readability, ratios, mask overlap, clipping, semantics, and visual integration do not cure this source-effective-font failure.

Per Goal §9.2.1-I, SA3 is prohibited at this point. The sole next step is **SA2 targeted source repair**, then a new standalone/final-PDF render and a full independent re-audit.

## SUPERSEDED provisional-mask result

`SUPERSEDED`: a first provisional color-only reconstruction treated the feedback line as a solid path and incorrectly counted `T05↔V08 = 161` overlapping pixels. It was not retained as a current finding: native R93 PDF drawing 17 has dash array `[2.98883 1.99255] 0`, and drawing 19 is the subsequently painted opaque white feedback-label background. The corrected true-PDF span/vector masks preserve that dash array and paint order: `T05↔V08` has `MASK_OVERLAP_PX=0` and `NEAREST_DISTANCE_PX=7.000`. The raw pair/overlay/mask in `pairs/T05__V08_*` is the current evidence.

## Required SA2 repair targets

1. Raise every source-owned visible figure text to an effective size of at least 9.5 pt without any `scale`, `transform shape`, `resizebox`, or `scalebox` workaround: top/terminal node labels (lines 14–17, 27–29), feedback label (line 22), locked node text (line 36–37), and red note (line 39–40).
2. Preserve the measured role bands: ordinary node labels remain the base; annotations remain within 0.95–1.10 of base. Recheck the feedback label’s own path clearance rather than relying on its white background.
3. Make the caption source font auditable through the permitted task source/configuration path, or provide an authoritative, scoped declaration for it; unknown effective font cannot pass.

## Evidence and method

- Four required views: `full_page_200dpi.png`, `figure_crop_300dpi.png`, `standalone_300dpi.png`, `grayscale_300dpi.png`. Each PNG is a direct native R93 PDF rendering/crop at the stated dpi; no image resizing occurred. The standalone view is a direct graphic-field crop of the frozen final PDF, not a recompiled substitute.
- `raw_pdf/raw_pdf_spans.json` stores the native PDF spans/characters and PDF bboxes; `raw_pdf/raw_pdf_vectors.json` stores native `get_drawings()` paths, widths and IDs.
- Text masks are thresholded only inside their exact raw PDF character boxes (local-background difference >=20/255). Vector masks are rebuilt from actual PDF vector operators, including native widths, Béziers, dash arrays, and the opaque-background paint order, rather than expanded bboxes. Each object has a tight 1:1 raw ROI, mask, and overlay under `raw_1to1/`, `masks/`, and `overlays/`.
- `object_register.csv` contains 14 text spans, 16 foreground vector objects, and the one excluded background fill. Pair CSV rows carry both parents, vector/PDF bbox clearance, real-mask intersection count, mask/raw paths, and nearest foreground pixel coordinates. All `315` pairs (91 text–text + 224 text–vector) are measured without sampling; detail images are emitted for every same-color text pair and every near text/vector pair.
- `after_text_measurement_overlay_300dpi.png` and `after_vector_object_overlay_300dpi.png` identify the PDF bboxes used for every text/vector object.

## Independent content assessment

The diagram correctly encodes the intended statistical protocol: task definition → candidate family → training → validation selection; only validation returns to the candidate family; frozen configuration then permits one final test and report; the locked test-set arrow is one-way into the test and cannot return to development. This is consistent with the caption and the immediately following explanatory sentence. No mathematical formula/operator is present to audit. The left-to-right top flow and the freeze-to-final-test lower flow are readable; the grayscale view preserves the distinct node/arrow structure and warning placement.
