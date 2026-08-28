# Revision 486 独立裁决

## P126 R3A corrected direct build

- HANDOFF_ID=`A-R115-P126-SA2-DIRECT-BUILD-R3A-20260828`.
- 唯一 controller/direct LuaLaTeX child invocation=`1/1`，retry/latexmk/version-probe/second invocation=`0/0/0/0`，natural exit=`true`，controller/child exit=`0/0`。
- 四个 `TEXMFVAR/TEXMFCACHE/TEXMFCONFIG/TEXMFHOME` 精确相等于同一 R3A `texcache`，修正了 R3 的缓存根布局错误。
- 唯一新 PDF=`STRICT_R3A_SA2_COORDINATE_QUADRATIC_PATCH_R115_DIRECT_BUILD_20260828/build/v260_FIG-P126-01_standalone.pdf`，33,952 bytes，SHA-256=`19F221487DB1930170608EAE0E09F019313791D808C724D05DBAC23465F746B2`。
- source 仍为 4,224 bytes/SHA-256=`366C905854F0F3952225600D5BD66AAB706B637A453FD23DDF9611E4C002AC20`；wrapper/engine/controller 前后身份不变。
- 终态 TeX-family=`0/0/0/0`，构建槽已释放。Main 接受本次构建事实；从此禁止 P126 再启 TeX，只允许 A 从该唯一 PDF 继续一次非 TeX 全量回归、真实 manual 和 single seal。在 Main 接受该回归前不得 commit/fresh role/second UID。

## P683 fresh isolated SA3 substantive acceptance

- HANDOFF_ID=`C-FIG-P683-01-R115-SA3-FRESH-ISOLATED-V1`，actual=`/root/sa3_fig_p683_r115_fresh_isolated_v1`。
- R115 PDF/current source/exact chapter 身份全部重算匹配；独立定位 physical732/printed719。
- denominator=`N31`，all unordered pairs=`465`；manual elements=`31/31`，manual pairs=`465/465`，ID exact/unique，required manual blanks=`0`。
- pair classes精确合计465：`419 CLEAR_DISJOINT + 12 CLEAR_GAP + 19 CLEAR_CONTAINED + 8 LEGAL_ENDPOINT_CONTACT + 1 CLEAR_NESTED + 6 LEGAL_PLATE_CROSSING`。
- Main 已实际打开 figure+caption native300/grayscale、phi→w diagonal、nested plate labels 与 caption NN8x；文字、plate、箭头端点、题注及灰度层级无反证。内容方向保留 `SA3_PASS_AWAIT_MAIN_C_LOCAL_PASS_ACCEPTANCE`，hard/clip/illegal/unresolved=`0`。

## P683 root control rejection

- 当前 root 的 manifest/material identity、账本、全树 ReadOnly、marker schema、future FILETIME 与当前时刻的 strict-latest 均能机械闭合；这些事实不被否定。
- 决定性顺序缺陷在 manifest-bound `seal_evidence.py`：line 214 先在 root 内创建 `WRITE_STOPPED`；line 227--231 之后才修改全部 non-marker files、subdirectories 和 root 的 ReadOnly attributes；line 232--233 最后修改 marker 时间与属性。
- 因此 marker 的 root 内创建早于全树只读冻结，且 marker 创建后仍有 non-marker/root attribute writes。这与已登记的 P109 `ROOT_REJECT_PREMATURE_MARKER_BEFORE_READONLY_FREEZE` 同型，不满足当前“先冻结全树，已只读 marker 的单次 move 为绝对最后 root content/attribute operation”硬门。
- 当前 SA3 root 永久标记 `ROOT_REJECT_PREMATURE_MARKER_BEFORE_READONLY_FREEZE`；不原地修补、重封、改时戳、删除或重跑。P683 保持 SA3，暂不计 C_LOCAL。

## Narrow control-only route

- 仅授权一个 sibling evidence-only control reseal：HANDOFF_ID=`C-FIG-P683-01-R115-SA3-FRESH-ISOLATED-CONTROL-RESEAL-V1`，operation=`P683_R115_SA3_EVIDENCE_ONLY_CONTROL_RESEAL_V1`，new root=`sa3_r115_fresh_isolated_v1_control_reseal_v1`（当前 Leaf/Container/Any=`false`，Parent=`true`）。
- 只能从 rejected root 的 manifest 精确复制39 material files，old manifest/marker 复制=`0`；保持 canonical relative path/bytes/SHA-256/Creation+LastWrite FILETIME。新增 `COPY_IDENTITY`+resolved `COPY_PROVENANCE` 后 payload=`41`；controls 恰 `PAYLOAD_MANIFEST`+`SEAL_AUDIT`+`WRITE_STOPPED`，ordinary=`44`。
- 必须先写完 payload/manifest/audit，将全部已存 files/dirs/root 设 ReadOnly 并核验；再在 root 外生成 resolved multiline one-key-per-line no-BOM marker，绑定 manifest SHA/count/verdict，设置严格晚于目标 files/dirs/root 的 FILETIME 并先设 ReadOnly；单次 move 入根必须是绝对最后 root content/attribute operation，封后 content+attribute writes=`0`。
- 只允许先在 root 外准备并冻结 controller/auditor，回传逐文件 identity/AST/Move-Item/destructive/process/TeX/retry-loop 静态门后 PAUSE；未获 Main 下一次显式 ACK 不得消耗 controller/auditor invocation。
- 禁止重跑/重读判定 PDF/render/visual/N/C/pair/manual/glyph/math/semantic/page；禁 TeX/source/Git/central/process/new UID/role。
