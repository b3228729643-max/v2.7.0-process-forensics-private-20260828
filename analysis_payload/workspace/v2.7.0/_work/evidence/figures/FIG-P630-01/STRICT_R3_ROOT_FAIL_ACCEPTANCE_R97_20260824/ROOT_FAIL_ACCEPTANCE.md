# FIG-P630-01｜R97 独立 SA1 失败的 root 验收

- Root decision：**接受 `SA1_FAIL_ROUTE_SA2`**。
- 本记录只接受图33.1的失败路由；不是图形PASS，不增加严格最终计数。
- SA1候选：官方R97，813页、SHA-256 `062AD81020CB19A5C6688A45C73E00965F5060E0960A69AF820D7DC154DEE814`；物理页678／印刷页665。
- 当前连续候选R98相对R97只改物理页591，故物理页678逐页栅格相同，本失败直接适用于R98。
- 只读源SHA-256：`746163570B90750C1BE9731029C450B2F800D43296075FC22D71B9D9F72F2E43`。

## Root 分母复算

- 123个唯一前景对象 = 102 GLYPH + 21 GRAPHIC/PATH。
- 7,503/7,503无序pair = `C(123,2)`；pair ID唯一7,503、无序对象键唯一7,503、自配对0、未知对象0、最终可见重叠pair 0。
- glyph机器账102行、硬FAIL 3、空mask 0；glyph人工账102行、FAIL 3；graphic人工账21行、非PASS 0；path账21行、空mask 0、数学rule path 0；critical pair人工账19行、非PASS 0。
- 源字号、D/E、字体视觉协调、净空、裁切、数学语义、箭头方向与灰度整体视图均通过，但不能抵消字形硬门。

## Root 实际开图与决定性失败

Root打开三项失败各自的original、target overlay、mask-only与8×nearest卡，并打开其所在glyph contact sheets 2/3/4、官方300dpi全页、300dpi图体和灰度图体。三张mask均非空、完整、纯净；图体未见其他可见重叠、裁切或突兀字号。

硬失败均为`BASE_MATH_OPERATOR`，门槛为原生300dpi `H_INK >= 22px`；自然下标中的语义负号不能降格为15px脚本门，乘点也不能借低轮廓标点校准：

1. `GLYPH-013` U+2212 `−`：H=3px、area=57px，`3<22`。
2. `GLYPH-022` U+22C5 `⋅`：H=5px、area=25px，`5<22`。
3. `GLYPH-025` U+2212 `−`：H=3px、area=57px，`3<22`。

三者均为读者可见真实轮廓，不是mask污染、映射错误或缺笔。任一项已足以判FAIL。

## 封存完整性

- `evidence_manifest.csv` 946行：root逐项复算missing/bytes/SHA mismatch均0；文件SHA-256 `01523D96FD068577266EAB94A4FEC82E902C07D7CA9F98207A6A66ACB0CA493E`。
- `MANIFEST.sha256` 947项：格式错误0、missing 0、SHA mismatch 0；文件SHA-256 `D7C631BD66E5A79E2A4B5970D67F85A1E2E2FE0541C59A2A9E2956BA2C98601E`。
- 实际949文件与`947 manifest项 + MANIFEST.sha256 + WRITE_STOPPED`集合规范化后严格相等，missing/extra均0。
- 0-byte 0、非默认ADS 0、ADS错误0、stop后写入0；`WRITE_STOPPED`最后写，SHA-256 `05ECE2250ABE4D53FEC761E89DD4346D6C459FC2DE2A11367E53975799FFB77D`。

## 路由

FIG-P630-01正式转入唯一串行SA2队列。后续可优先用语义等价的自然文案去除两次`x_{-j}`与一次`\cdot`的低轮廓依赖；局部PASS后仍须root构建新官方候选，再走全新SA1、隔离SA3和root签发。
