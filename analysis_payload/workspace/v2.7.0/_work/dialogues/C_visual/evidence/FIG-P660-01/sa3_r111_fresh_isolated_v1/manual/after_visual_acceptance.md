# FIG-P660-01 SA3 最终视觉验收

RESULT = PASS  
FIGURE_ID = FIG-P660-01  
HANDOFF_ID = C-FIG-P660-01-R111-SA3-FRESH-ISOLATED-V1

SA1_MODEL = ISOLATED_NOT_READ  
SA1_REASONING = ISOLATED_NOT_READ  
SA2_MODEL = ISOLATED_NOT_READ  
SA2_REASONING = ISOLATED_NOT_READ  
SA2_ESCALATED = ISOLATED_NOT_READ  
SA3_MODEL = gpt-5.6-sol  
SA3_REASONING = xhigh

SOURCE_FONT_PASS = true  
PIXEL_HEIGHT_PASS = true  
SAME_CLASS_RATIO_PASS = true  
ROLE_RATIO_PASS = true  
OVERLAP_CANDIDATE_PIXEL_COUNT = 922  
MASK_CONTAMINATION_PIXEL_COUNT = 922  
OVERLAP_PIXEL_COUNT = 0  
PIXEL_ADJUDICATION_STATUS = MASK_CONTAMINATION_CONFIRMED  
PIXEL_ARBITER_MODEL = NOT_USED  
PIXEL_ARBITER_REASONING = NOT_USED  
CLIP_PIXEL_COUNT = 0  
MIN_TEXT_CLEARANCE_PX = 26  
VISUAL_HARMONY_PASS = true  
MATH_SEMANTICS_PASS = true  
TEXT_CONSISTENCY_PASS = true  
GLYPH_CODEPOINT_PASS = true  
GRAYSCALE_PASS = true  
PAGE_INTEGRATION_PASS = true

## SA3 独立结论

- 官方 R111 中该图位于物理页 709（印刷页 696），图号 34.4；当前源、图面、题注与 alt 一致。
- 16 个可见语义对象和 20 个文字量测元素已逐项查看；120/120 个无序对已逐 ID 人工复核。
- 三个 8.7pt 分量标签在最终原生 300 dpi 中均为 36 px 墨迹高，native1x/NN8x 清楚可读；R168 下旧 pt 阈值只作提示，不构成硬缺陷。
- 唯一自动候选 P001 是投影构造与参考网格的允许层叠；没有文字/公式/标签碰撞，真实非法重叠像素为 0，未决候选为 0。
- 所有标签、公式、汉字、数字和数学符号完整，无 tofu、缺字、错误变量或实际错误码位；所有可见对象均未裁切。
- 独立复算得到重心坐标 `(0.2,0.3,0.5)`、和为 1，三个归一化边距与 `.2/.3/.5` 相符，支撑集维数 2；数学语义正确。
- 彩色、灰度、局部、完整页和页面融合均无实际不可读、严重失衡、真实裁切、非法重叠或几何/语义错误。

SA3_RETURN_TOKEN = SA3_PASS_AWAIT_MAIN_C_LOCAL_PASS_ACCEPTANCE
