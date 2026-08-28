# Revision 266｜R109 正式冻结、P609 SA1 接受与两条 fresh 角色授权

时间：2026-08-26T22:15:01+08:00

## R109 final candidate

- main HEAD=`59e7afd81ba3171ab9de5c90ed589fed3424155e`，worktree clean。
- 唯一父调用为 `build_v2.7.0.ps1 -Engine lualatex -OutputDir src\build\strict_current_r109_fullbook -NoPublish`；自然 exit0，wrapper=`PASS`，latexmk=`All targets up-to-date`，未启动第二父调用、retry 或 Resume。
- 构建根创建于 `2026-08-26T21:54:58+08:00`；最终 PDF mtime=`2026-08-26T22:08:23.1327162+08:00`；结束后 `latexmk/lualatex/luatex/luahbtex=NONE`，R109 构建锁正式释放。
- 正式 PDF=`src/build/strict_current_r109_fullbook/main_full.pdf`：817 pages、4,967,054 bytes、SHA-256=`936162A637DCE09EE02B3F83CB1C21A61A87EFBB9A7C8DDE2FB11A326EB552A9`；817/817 均为 595.276×841.890pt A4、rotation0、PDF1.7、unencrypted。
- final log=`260,299 bytes`、SHA-256=`0AF9FD20DE4A10D276B1C1F213D0C9CDA55B3B444BC2A2A606ABFEF4A41BB361`。hard TeX/package、missing/I/O、memory、undefined refs/cites、missing chars、duplicate、final rerun、overfull、underfull 均为0。
- 主索引731 accepted/0 rejected/0 warnings；符号索引355 accepted/0 rejected/0 warnings。日志另有6条既有PDF-string token提醒与2条imakeidx再次运行提醒；latexmk已自然收敛且索引 `.ilg` 均0 warnings，故不构成硬失败。
- R109 取代 R108 成为唯一官方候选。

## P582 official-page visual

- 由新 PDF 文本层独立定位 `FIG-P582-01` 至 physical632 / printed619 / Fig31.7。
- 主线实际打开300dpi整页与图裁图；运行均值折线、四点、真值线、`.640/.325/.380/.325`、三处方向注释、坐标轴及题注完整清楚。
- `.380` 与“再下降”箭头保持可见白隙，无shared ink、裁切、断线、异常拉伸或页面融合回归；R109官方页视觉PASS。
- 视觉文件：`page_632_300dpi.png`、`p582_crop_300dpi.png`。

## P609 fresh SA1 acceptance

- actual=`C-FIG-P609-01-R108-SA1-FRESH-ISOLATED-V1` / `/root/sa1_fig_p609_r108_fresh_isolated_v1` / `gpt-5.6-sol/xhigh/fork_turns=none`。
- 内容从零闭合 `N32/C496`；人工32对象与496 pairs完成，true overlap/clip/hard failures均0；一般可见源级最小字号9.6pt，有限窗ACF/ESS语义复算一致。3.25px vector-bbox间隔具有20行真实白色像素，仅按R168作advisory。
- 主线轻量机械复核：ordinary45，manifest pre-payload43；45/45文件与2/2目录只读，ADS/cache/pyc/reparse0；WSTOP严格最后。报告、manifest、WSTOP、handoff的bytes/SHA与回传逐项一致。
- 主线实际打开figure+caption与cutoff native/8x证据；截断窗、K=6边界、ACF杆点、ESS公式/正性条件、说明与题注均清晰，无反证。正式接受SA1 PASS，原SA1根永久冻结。

## Fresh role authorizations

- A：授权一个全新 `gpt-5.6-sol/xhigh/fork_turns=none` P582 R109 fresh isolated SA1；新根启动前必须不存在，仅读R109/当前main P582单源/Goal/strict protocol-schema/必要V5-C02正文；绝对禁读全部旧P582 evidence/role/root/handoff/state/chat/Git结论，禁TeX/源码写/提交/第二角色。PASS只请求另一fresh SA3。
- C：授权一个不同实例、全新根的 `gpt-5.6-sol/xhigh/fork_turns=none` P609 R109 fresh isolated SA3；仅读R109/当前main P609单源/Goal/strict protocol-schema/必要V5-C03正文；绝对禁读本SA1、旧SA2/reseal及全部旧P609结论，禁TeX/源码写/提交/第二角色。PASS只回中央接受。
- actual identity回传前，中央inventory仍为 `32 SA1 / 48 SA2 / 0 SA3 / 19 local pass`；严格最终仍为0/99，B累计66/66。

