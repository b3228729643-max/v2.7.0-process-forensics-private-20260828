# R233 — FIG-P715-01 R17 main-takeover local SA2 acceptance

- Verdict: `MAIN_TAKEOVER_LOCAL_SA2_ACCEPT_SOURCE_COMMIT_AUTHORIZED`
- This is not `A_LOCAL_PASS`; fresh official-candidate SA1 and fresh isolated SA3 remain mandatory.
- Reason for takeover: Dialogue A reached its platform usage limit after the only authorized R17 build completed. The source, PDF, machine denominator, regression bundle, views, and glyph ledger were already present. Main did not rerun TeX and did not modify the interrupted R17 evidence root.

## Frozen identities

- Source: `src/绘图源码/第05册_采样方法主题模型与图排序/V5-C07/web_random_walk.tex`
- Before source SHA-256: `51B21C62DE42564CB4B915C51F7A213F36D8784475CD15A92474497D2F6EED2F`
- After source SHA-256: `900C3A8F72A7A6434101FEE9914019150D3D5F655A23FC5BF41EDB853C25EE87`
- Exact source diff: one file, 13 insertions and 13 deletions; `git diff --check` passed.
- R17 standalone PDF: 1 A4 page, 40,898 bytes, PDF 1.7, unencrypted.
- PDF SHA-256: `0392F5BF4AF6E3620C57F5EA0047A8958022E52B3386984A3D51CC38B4DFF024`
- Build invocation: one direct LuaLaTeX invocation, controller PID 18200, child PID 19508, exit 0, no retry, terminal TeX processes none.

## Evidence accepted

- Strongest machine layer: `STRICT_R17_SA2_R16_GEOMETRY_DIRECT_BUILD_20260826/evidence_v3`.
- Denominator: 216 text glyphs plus 43 drawing objects = `N=259`.
- All unordered pairs: `C(259,2)=33,411`, actual 33,411.
- Empty glyph/drawing masks: 0/0; object boxes outside standalone: 0.
- Protocol relation gates:
  - text–text minimum 4 px at a 4 px gate;
  - text/formula–line/arrow minimum 13 px at a 3 px gate;
  - text/formula–node border minimum 22 px at a 5 px gate;
  - text/formula–panel border minimum 18 px at a 6 px gate;
  - text/formula–cell border minimum 9 px at a 5 px gate.
- Protocol foreground intersections: 0; under-threshold relations: 0.
- The 21 accepted prior-failure relations were all regenerated at native 1x and nearest-neighbour 8x; 21/21 mechanically passed.
- Decisive prior failure `PAIR_08396` (`TXT_G0035` “矩” versus `DRW_0004` node-j border): old intersection 37 px / gap 0; new intersection 0 / white gap 92 px.
- Existing manual glyph ledger contains 216/216 unique element IDs, 216 non-empty and unique notes, and 216 `ACCEPT` decisions. It was not generated or rewritten by main.
- Main independently rendered the R17 PDF at native 300 dpi outside the evidence root and opened the full page. The node-j/“矩” separation, three matrices, directed graph, all formula stacks, both panels, grayscale readability, and bottom clearances showed no real overlap, crop, missing glyph, wrong code point, unreadability, or semantic regression.
- An independent `gpt-5.6-sol/xhigh` read-only audit confirmed the same geometry direction and independently identified the 92 px node-j/“矩” gap. R168 micro typography observations remain advisory only.

## Scope preserved

- Four directed graph edges and all values in `A`, `M`, and `P` are unchanged.
- Column-stochastic/row-stochastic transpose semantics, formula tokens, labels, caption, and font styles are unchanged.
- The patch only repositions explanatory/formula nodes and wraps the existing sentence “矩阵行、列顺序均为 (i,j,h)” onto two lines.

## Control-layer limitation

Dialogue A was interrupted before writing its final `after_*` reports, manifest, seal, and `WRITE_STOPPED`. Therefore the interrupted R17 root is not promoted as a sealed final evidence package. This central adjudication accepts the actual local SA2 source/PDF result for atomic source commit and official-candidate integration only. It does not waive the required fresh SA1→fresh isolated SA3 chain on the next official candidate.
