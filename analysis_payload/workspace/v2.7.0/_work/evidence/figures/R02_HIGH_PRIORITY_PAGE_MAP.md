# R02 高优先级图页码映射

候选：`_work/source/v2.7.0/build/final/main_full.pdf`（785 页，R02 首个候选）。

映射依据：最终 `main_full.aux` 的正式图标签页码；正文页码前有 13 个物理页，因此 `PDF物理页 = aux 页码 + 13`。多页文本搜索命中只作旁证，不用引用出现页冒充图所在页。

| 图号 | UID | R02 物理页 | 基线物理页 | 图源 |
|---|---|---:|---:|---|
| 30.2 | FIG-P547-01 | 573 | 645 | `V5-C01/fig_v5_c01_transition_graph.tex` |
| 32.5 | FIG-P602-01 | 631 | 710 | `V5-C03/fig_v5_c03_mh_accept_reject.tex` |
| 32.8 | FIG-P608-01 | 638 | 718 | `V5-C03/fig_v5_c03_trace_running_mean.tex` |
| 32.9 | FIG-P609-01 | 638 | 718 | `V5-C03/fig_v5_c03_autocorrelation_ess.tex` |
| 33.1 | FIG-P630-01 | 657 | 738 | `V5-C04/fig_v5_c04_dependency_graph.tex` |
| 33.3 | FIG-P634-01 | 660 | 742 | `V5-C04/fig_v5_c04_coordinate_sweep.tex` |
| 33.7 | FIG-P640-01 | 665 | 747 | `V5-C04/fig_v5_c04_mixing_rho_comparison.tex` |
| 34.8 | FIG-P668-01 | 691 | 775 | `V5-C05/fig_v5_c05_dirichlet_shape_atlas.tex` |
| 34.9 | FIG-P669-01 | 692 | 775 | `V5-C05/fig_v5_c05_concentration_mean.tex` |
| 35.3 | FIG-P684-01 | 708 | 794 | `V5-C06/fig_v5_c06_generative_process.tex` |
| 35.7 | FIG-P694-01 | 717 | 805 | `V5-C06/fig_v5_c06_variational_updates.tex` |
| 35.8 | FIG-P695-01 | 718 | 805 | `V5-C06/fig_v5_c06_method_comparison.tex` |
| 36.4 | FIG-P717-01 | 740 | 830 | `V5-C07/inbound_contribution.tex` |
| 36.7 | FIG-P721-01 | 743 | 834 | `V5-C07/numerical_rank_trajectory.tex` |
| 37.2 | FIG-P736-01 | 759 | 852 | `V5-C08/method_family_relationships.tex` |
| 37.3 | FIG-P737-01 | 760 | 852 | `V5-C08/task_representation_inference_cube.tex` |
| 37.4 | FIG-P740-01 | 761 | 854 | `V5-C08/matrix_probability_bridge.tex` |
| 37.5 | FIG-P745-01 | 765 | 857 | `V5-C08/fig_v5_c08_validation_protocols.tex` |
| 37.6 | FIG-P748-01 | 767 | 860 | `V5-C08/evaluation_dashboard.tex` |
| 37.7 | FIG-P750-01 | 768 | 861 | `V5-C08/method_selection_decision_map.tex` |
| 37.8 | FIG-P756-01 | 773 | 866 | `V5-C08/full_course_synthesis_map.tex` |

此表只冻结 R02 候选映射；任何后续分页变化都从该轮最终 `.aux` 定向更新，不重新扫描七项输入。
