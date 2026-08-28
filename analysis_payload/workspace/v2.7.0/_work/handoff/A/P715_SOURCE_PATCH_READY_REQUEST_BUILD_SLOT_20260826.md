# P715_SOURCE_PATCH_READY_REQUEST_BUILD_SLOT

- UID：`FIG-P715-01`
- 路由：`SA2 / STATIC_SINGLE_SOURCE_SCOPE_GRANTED`
- 工作树：`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_A_visual`
- 分支：`v2.7.0/dialogue-a-visual`
- 当前 parent：`420921f6513a69f6d7f3d2d6c1580ef43bbb3ab5`
- 唯一修改源：`src/绘图源码/第05册_采样方法主题模型与图排序/V5-C07/web_random_walk.tex`
- before SHA-256：`51B21C62DE42564CB4B915C51F7A213F36D8784475CD15A92474497D2F6EED2F`
- after SHA-256：`900C3A8F72A7A6434101FEE9914019150D3D5F655A23FC5BF41EDB853C25EE87`
- diff：1 file，13 insertions / 13 deletions；`git diff --check` PASS；staged=0。

## 补丁结论

静态补丁只重排现有说明、矩阵和公式的局部坐标/换行：

- 首要 `PAIR_08396`：保留原说明文字，仅将“矩阵行、列顺序均为 (i,j,h)”拆成两行；按 R15 native300dpi 坐标投影，文字相对 node-j 边框由相交37px变为约90px水平白隙。
- 左面板右边框：拆行后末行相对面板右边框投影约142px白隙，消除旧3px净空失败。
- 左公式、M矩阵下方上标、右侧说明/P矩阵、P矩阵下公式栈均作统一几何重排；目标投影净空分别约6px、10px、11px、4–8px，最底公式到面板约12px。

业务保持：四条图边、A/M/P矩阵数值、列随机/行随机转置语义、所有公式token、结点与标签、题注、字体字号style全部不变；未引入缩放或变换。

## 静态证据

根：`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P715-01\STATIC_R16_SA2_SOURCE_GEOMETRY_PATCH_20260826`

- `STATIC_SCOPE_AND_PROJECTION.md`：2616 bytes，SHA-256 `631AC81F1CBF219D8632BC9C85D042B5ED5E14201C92159B2267BD5EB22D424A`
- `STATIC_FAILURE_CLOSURE.csv`：1492 bytes，SHA-256 `F1A9912B54EA8D73073C87A63968254CA44AA782487342CF3C00108EB59118E2`
- `SOURCE_IDENTITY.json`：786 bytes，SHA-256 `29C23D0DC5C6078670983B072082C4576125F958A82285E2F4629ECA00D5BE10`

## 边界与请求

- 本阶段 A 未启动 TeX/LuaLaTeX/latexmk；当前检查时四类 TeX 进程为 NONE。
- 未提交、未暂存、未修改第二源、未启动第二 UID 或 fresh 角色。
- 请求主线授予一次受控构建槽。获授后只从新 PDF 从零复核对象分母/all-pairs、全部旧硬失败关系、裁切/非法重叠及语义回归；构建前不宣称 PASS。
