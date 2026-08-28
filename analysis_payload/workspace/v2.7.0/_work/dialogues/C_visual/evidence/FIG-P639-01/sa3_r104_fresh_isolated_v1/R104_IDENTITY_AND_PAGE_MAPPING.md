# R104 identity and independent page mapping

- HANDOFF_ID: `C-FIG-P639-01-R104-SA3-FRESH-ISOLATED-V1`
- INSTANCE: `/root/sa3_fig_p639_r104_fresh_isolated`
- REVIEWER_TYPE: `AI_SA3_VISUAL_REVIEW`
- HUMAN_CERTIFICATION: `false`
- FIGURE_ID: `FIG-P639-01`
- source UID comment: `FIG-P639-01`
- source label: `fig:V5-C04-bivariate-normal-conditionals`
- source caption anchor: `取 rho=0.6、a=1、b=0.75 时，两个满条件分布分别为 N(0.45,0.64) 与 N(0.60,0.64)`
- official candidate: `strict_current_r104_fullbook/main_full.pdf`
- official candidate bytes: `4967222`
- official candidate SHA256: `E5C871642FBDDBEC6508BE1B61BD911FE281CA5ACFBD16B0449B13357770A641`
- official candidate UTC mtime: `2026-08-25T12:02:30.1595208Z`
- official candidate FILETIME100ns: `134321329501595208`
- figure source bytes: `2038`
- figure source SHA256: `9F782BA4BDF0D6243CF8CC8BE073E54F1E4003FE25F3C9017C4AA9A8B5418964`
- figure source UTC mtime: `2026-08-13T04:00:00.0000000Z`
- figure source FILETIME100ns: `134310672000000000`

Independent mapping used the current source UID/label/caption first, then searched the official R104 PDF for the same caption plus the visible note strings `共同方差` and `均值随另一坐标改变`. The unique match is:

- PDF physical page: `689`
- printed page number: `676`
- chapter: `第 33 章 Gibbs 抽样`
- figure number: `图 33.6`

The older task-card page value 747 was not used as a denominator because it does not identify the current R104 page.

Isolation boundary: no SA1 root, R210 acceptance root, old P639 evidence, central state, inventory, Git history, other UID evidence, or prior reviewer conclusion was consulted. During adjacent-text location, one `rg` result exposed only the current V5-C04 `figure_sources.json` entry for this same figure (current caption/label/teaching metadata; no SA conclusion or old evidence). This disclosure is retained so the read boundary is auditable.

