# FIG-P582-02 R115 SA1 visual acceptance — independent requalification

Reviewer: `R115_SA1_requalification_current_identity`  
Manual review time: `2026-08-24T11:24:07+08:00`  
Authority: official R95 `main_full.pdf`, physical PDF page 630 (printed page 617), Figure 31.8.

## Four required views actually opened

| View | Manual finding | Result |
|---|---|---|
| `full_page_200dpi.png` | Figure integrates with nearby prose and caption; reading order is intact. The chart text is visibly smaller than the surrounding body hierarchy. | FAIL on font-size gate; otherwise PASS |
| `figure_crop_300dpi.png` | No unintended collision, clipping, or occlusion is visible in the native crop. Tick/annotation/card text remains undersized. | FAIL on font-size gate; otherwise PASS |
| `standalone_300dpi.png` | Bar hierarchy, reference line and annotation card are readable and uncrowded. | FAIL on font-size gate; otherwise PASS |
| `grayscale_300dpi.png` | Semantic hierarchy and reference-line distinction survive grayscale. | FAIL on font-size gate; otherwise PASS |

## FONT_VISUAL_HARMONY

- `FONT_SIZE_HARMONY_PASS = FAIL`. The 8.6pt ticks and 9.2/9.4pt labels, annotation and card note are undersized beside the page body/chart geometry; 67 of 149 visible glyphs measure below 9.5pt.
- `FONT_WEIGHT_HARMONY_PASS = PASS`. No unintended bold/weight conflict is visible; stroke hierarchy is restrained.
- `FONT_COLOR_HARMONY_PASS = PASS`. Blue tall bar, teal residual bars and gray reference/card form a coherent semantic palette and remain structurally distinguishable in grayscale.
- `FONT_VISUAL_HARMONY_PASS = FAIL`, solely because size is a hard gate. Reducing any element would not cure an already below-floor size.

## Other visual gates

- 1×/8× mask and critical-ROI review: no visible non-design overlap, missing ink, foreign ink, clipping or occlusion.
- Formula/card/reference/caption communicate the same normalized-weight ESS message as neighboring prose.
- This is not an acceptance: the strict raw recomputation has three physical height failures (`=`, `≈`, caption `一`) and 21 punctuation rows without required independent calibration closure; those are recorded separately in the evidence-integrity matrix.
