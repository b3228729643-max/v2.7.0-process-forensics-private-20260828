# FIG-P634-01 texture / halo audit

- `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C04\fig_v5_c04_coordinate_sweep.tex` l7 declares `pattern=north east lines`; l28--l31 draw the four textured done fields.
- l8 defines `sl634-halo` as `draw=none,fill=white`; l32--l35 draw these opaque white halos after the textures. The uniform source order proves real halo rather than result-directed mask removal.
- `masks/pre_occlusion_texture_field_node_*_300dpi.png`, `masks/true_opaque_halo_node_*_300dpi.png`, and `masks/final_visible_texture_node_*_300dpi.png` are separate. Only final-visible raw hatch pixels are in pair quality geometry; pre-field and halo are registered background/exempt layers.
- The colour-coded overlay uses blue=pre-field extent, green=true halo extent, red=final-visible hatch pixels; it is a draw-order witness, not a reconstructed substitute for final geometry.
