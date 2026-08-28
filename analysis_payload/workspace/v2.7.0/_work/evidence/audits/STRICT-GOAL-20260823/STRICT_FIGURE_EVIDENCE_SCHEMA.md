# v2.7.0 严格逐图证据规范

权威来源：发布根 Goal 第 9.2.1 节。此文件只把硬门转成统一落盘格式，不降低任何阈值。

## 每图目录

最终候选证据放在 `evidence/figures/<UID>/STRICT_FINAL/`。失败轮放在带轮次的中间目录，不能复制进 `STRICT_FINAL` 或最终视觉证据 ZIP。

每图至少包含：

- `full_page_200dpi.png`
- `figure_crop_300dpi.png`
- `standalone_300dpi.png`
- `grayscale_300dpi.png`
- `after_font_audit.csv`
- `after_pixel_measurements.csv`
- `after_overlap_report.csv`
- `after_text_measurement_overlay_300dpi.png`
- `after_visual_acceptance.md`
- SA1、SA2（若发生修复）、SA3 与根线程结论记录

300 dpi 图必须直接由最终候选 PDF 渲染，渲染后不得 resize；浏览器、聊天、查看器截图和 200 dpi 图不得用于像素测量。测量框叠加图必须标出全部 `ELEMENT_ID`、bbox 与角色。

原生 300 dpi、1:1 掩膜是唯一计数坐标。`8x_nearest` 只用于审查者逐像素目视确认，禁止在 8× 图上重新阈值化、测距或把放大后的像素数写回 CSV。每个渲染包必须记录最终 PDF、物理页、页面 pt 尺寸、原生像素网格和裁图在整页中的整数坐标，防止 standalone、旧页或二次裁放混入。

## 字号与像素门

- 一般可见文字 `effective_pt >= 9.5pt`；合法 TeX 上下标只能由不低于 9.5pt 的基公式自然产生。
- 字体必须与图幅、线宽、节点和同页正文形成自然层级，不得因机械放大而显得突兀、抢占图形或破坏阅读路径。允许为恢复协调性适当缩小，但缩小后的每个可见对象仍须同时满足 `effective_pt >= 9.5pt`、逐字形像素下限、同角色/跨面板比例、零重叠、净空和整页可读性；任一项不满足即 FAIL。
- 同面板同角色源级字号 `max/min <=1.03` 且绝对差 `<=0.25pt`；跨面板同角色 `max/min <=1.05`。
- 墨迹阈值使用相对局部背景至少 `20/255` 的有效前景。
- 中文/全角/全字面字符 `H_INK_PX>=30`；拉丁大写/数字 `>=24`；x-height 拉丁/希腊小写 `>=17`；基准数学/运算符/分数主体 `>=22`；合法自然脚本 `>=15`。
- `−`、`+`、`=`、省略号、逗号及其他承担语义的运算符/标点必须分别建立独立 substring、bbox 与无膨胀 raw mask，按自身 `H_INK_PX` 判门；禁止用父公式、整行、分数或相邻字形的高度替代。
- 上述“按自身判门”不得把低轮廓标点机械伪装成全字面字符、数学运算符或自然脚本。`−`、`+`、`=`、关系号及真正的基准数学运算符仍按 `22px`；分数的分子、分母和分数主体也按 `22px`，不得降格为 `15px` script。句点/小数点、逗号/顿号、冒号/分号、省略点及其全角/CJK 变体属于 `LOW_PROFILE_PUNCTUATION`：一般可见基字号仍须 `>=9.5pt`，其 raw mask 必须非空、完整、纯净，并与“相同 codepoint、字体、字重、颜色、有效字号（绝对差 <=0.25pt）、300dpi、20/255 阈值”的独立校准字形比较，`H_INK` 与有效墨迹面积比例都须位于 `[0.92,1.08]`，跨面板同角色极值比 `<=1.10`。若当前候选没有合格同字形参照，必须从实际 PDF 字体/同一 TeX 字体命令在相同有效字号下单独渲染校准字形并保存 source、native raw mask 与 1×/8×证据；缺校准或借用不同字形/父对象高度即证据 FAIL。具有全高轮廓的括号/方括号等仍按其实际全字面/数学类别，不适用本条。
- 每个文字 raw mask 只能含该 ELEMENT_ID/字形自身的最终可见墨迹。若 bbox 内还经过同色边框、曲线、邻字或另一行，必须通过 PDF 字形级渲染、绘制顺序或可追溯减法分离；把附近图形或邻字计入 H_INK、同类比例或重叠，证据直接 FAIL。低笔画 CJK 字形仍按 CJK 门，不得重分类为 script；只有合法 TeX 上下标/上下限使用 15px 门。
- 每个可见字形必须闭合 `CHAR ↔ 实际轮廓 ↔ 语义父对象 ↔ bbox ↔ raw mask` 映射，并以覆盖 100% 字形的 contact sheet 在原生像素上人工复核。每个 contact cell 必须用同一 native bbox/pad/8× nearest 物理并排显示三视图：未改动的 `ORIGINAL`、仅将唯一目标 mask 着红的 `TARGET OVERLAY`、以及只含目标字形的 `MASK ONLY`；缺任一视图即 FAIL。审查者必须实际打开全部 contact sheet，并为每个字形逐行填写 reviewer/sheet/cell/original-match/overlay-complete/mask-only-pure/missing-stroke-px/foreign-pixel-px/decision/note ledger；禁止用一个全局布尔值批量把所有字形改成 PASS。机器污染门必须证明该 mask 不含纹理、阴影、邻字、线条、箭头、标记或边框像素；机器完整性门还必须证明该 mask 覆盖目标字形全部达到 20/255 对比阈值的最终可见笔画，不能因紧 bbox 众数背景、颜色误分或路径相交而漏掉横画、竖画、部件或标点。无法可靠隔离、映射错误、缺笔、待定、人工行缺失/重复、污染交集非零或可见轮廓覆盖不闭合均为证据 FAIL，不得用伪精确计数替代。
- TeX 数学重音和规则不得因不出现在 PDF `rawdict` 字符流中而漏审。每条可见 `\overline`/`\underline`、帽号或矢量重音的独立路径、根号横线、分数线、消去斜线及其他由 PDF drawing/path 绘制的公式规则，必须以唯一 `GRAPHIC/MATH_RULE` 前景对象记录绘制序号、语义公式父对象、bbox、非空 raw mask 和 `ORIGINAL/TARGET OVERLAY/MASK ONLY/8× nearest` 人工行；它与同父公式字形的设计性组成关系可逐对语义白名单，但仍必须进入总对象分母和全部无序 pair，并与轴、边框、曲线、箭头、标记、相邻文字及跨面板对象执行正常重叠/净空门。必须对 PDF 字符流与全部可见 foreground drawing/path 做双向盘点；任何未归属的公式规则、空 mask、把规则误并入轴线/邻字，或仅凭文字 bbox 得出的假净空，证据直接 FAIL。
- 所有 `ELEMENT_ID`/glyph/关系 ID 写入文件名时必须映射为跨平台安全且唯一的普通文件名，并保留 `ID ↔ SAFE_FILENAME` 清单。Windows 下禁止把冒号 ID 直接作为路径写成 NTFS alternate data stream；机器终检须枚举并实际打开预期数量的普通 PNG/JSON，核对唯一性、尺寸、bbox 和引用路径。缺文件、ADS、重名覆盖或不可移植路径均为证据 FAIL。
- 同面板同脚本同角色，每个元素/类中位数在 `[0.92,1.08]`；同角色中位数极值比 `<=1.08`；跨面板角色中位数极值比 `<=1.10`。
- 相对 BASE：轴标题/单位 `[1.00,1.18]`，图例与普通注释 `[0.95,1.10]`，公式块 `[1.00,1.18]`，面板标号 `[1.05,1.20]`；预先说明的强调仍须在 `[0.90,1.25]`。

## 零重叠、零裁切与净空

`OVERLAP_PIXEL_COUNT=0`、`CLIP_PIXEL_COUNT=0`。任何非法交叠像素 `>=1` 直接 FAIL。

必查：TEXT-TEXT、TEXT/FORMULA-LINE_ARROW、TEXT/FORMULA-MARKER、TEXT/FORMULA-NODE_BORDER、TEXT/FORMULA-PANEL_BORDER、LEGEND-DATA_CURVE、ANNOTATION-DATA_CURVE、ARROWHEAD-TEXT。

最低净空：文字-文字 bbox `>=4px`；文字/公式墨迹到线、箭头、标记 `>=3px`；节点文字/公式到边框 `>=5px`；文字到面板裁切边/图像边 `>=6px`；相邻面板最近读者元素 `>=8px`。

所有重叠结论必须来自最终 PDF 原生 300 dpi、1:1 像素坐标上的双方分离 raw foreground masks 与交集 mask；不得使用形态膨胀、扩大 bbox、paint-order 污染或缩放后的截图代替。每个失败或临界关系必须保存原图 ROI、双方 mask、overlay/overlap，并由审查者放大到具体像素核看，区分真实非法碰撞与有意的线—线、线—节点几何连接。

节点内部文字到边框的净空只按文字最终墨迹到 `final-visible` 边框描边 raw mask 计算；“文字 bbox 被节点外框 bbox 包含”本身不等于 0px。反之，若原生双方 mask 在某像素相贴，即使缩放预览看似留白，也必须保留实测 0px。节点 fill/注释底色属于背景，不能混入边框 mask；边框 mask 必须只含实际矢量描边的最终可见像素，卡片或节点的白色内部填充不得作为描边参与 overlap/clearance。

若源码存在真实不透明文字底、双边框白缝或 halo，必须同时保留 `pre-occlusion`、真实不透明 `halo/background` 与 `final-visible = pre - opaque` 三套掩膜及绘制顺序证据；质量关系只使用最终读者可见前景。不得把虚构 halo、普通白色页面背景或为结果服务的掩膜删减当作遮挡证据。

同一题注自然段的自动换行按一个语义父对象处理；其自然行距不得误套独立文字—文字 4 px 门，但仍必须检查真实前景交集、与图体/页边的净空及整体可读性。

同一语义公式父对象内的基字符、分子分母、上下标和上下限属于公式内部排版，不互相套用独立 `TEXT-TEXT >=4px` 门；公式父对象与其他独立文字/公式仍须执行该门。无论是否同父对象，任意非设计性字形墨迹交叠、字符缺损或遮挡仍按 `OVERLAP_PIXEL_COUNT>=1` 或可读性失败处理，并须在绘制顺序证据中解释。

## PASS 矩阵

SA1 与 SA3 必须分别从源码、`full_page_200dpi`、`figure_crop_300dpi`、`standalone_300dpi`、`grayscale_300dpi` 独立取证，并对文字 overlay、每个失败/临界 ROI 和分离 mask 作 1:1 像素放大核验。视觉报告须单列 `FONT_VISUAL_HARMONY_PASS`，说明字号是否过大/过小/突兀以及任何缩小是否仍保持整体观看；不得在脚本中硬编码视觉 PASS。须有逐视图及逐 panel/role/script 的 reviewer ledger，记录实际打开的证据、pt/字高中位数、D/E 状态、拥挤/突兀、跨面板一致性、灰度和页面融合判断；空项或 pending 直接 FAIL。全部布尔项为 true、两个像素计数为 0、各类净空达标且所有 CSV 行均 PASS 后才可返回 PASS。空值、`UNKNOWN`、缺行、缺文件或不可复核均为 FAIL。

每轮必须有机器终检，至少交叉核对：manifest 对象数与唯一 ID、ID↔安全文件名及普通文件可打开数、CHAR 映射/字形 contact sheet 覆盖数、PDF字符流与可见foreground drawing/path双向覆盖数、数学重音/规则对象及人工行数、可见轮廓完整性及污染交集数、全部必查关系/无序 pair 数、空 mask 数、overlap/clip/clearance 失败数、字号/像素/D/E 失败数、每个失败/临界关系的 raw/A/B/intersection/1:1/8× 证据数，以及底层 CSV、JSON、Markdown 汇总和最终 RESULT 是否完全一致。任一底层 FAIL 被汇总写成 PASS、任一报告引用的证据不存在、任一字形映射/掩膜污染或缺笔未闭合、任一可见数学规则/路径漏出对象分母、路径落成 ADS/重名覆盖、或空 graphic mask 未被显式判为证据失败时，本轮证据完整性直接 FAIL。

唯一闭环：SA1 FAIL → SA2 白名单修复 → 新构建与全量新证据 → 新 SA1；SA1 PASS 后才启动隔离 SA3；SA3 FAIL 时回到 SA2，再走新 SA1 与新 SA3。根线程不得覆盖硬性 FAIL。
