# R168｜P654 R21 构建主线预检

Status: `BUILD_IDENTITY_AND_ROOT_VISUAL_PRECHECK_ACCEPTED`；尚非 local PASS。

## 构建身份

- 唯一获准链：PowerShell 7 direct LuaLaTeX；controller PID `22992`，LuaLaTeX PID `508`。
- `invocation=1`、`latexmk=0`、`retry=0`、自然退出 `0`，未中止。
- source 前后 SHA-256 均为 `2EF1663B13A7982ACD5835217D0BB317FBF44146B08BE19F439430A2B42FABE7`。
- PDF：1 页 A4、43,970 bytes、SHA-256 `3F1D7A22BCA99828074360790CBED5EA755F6A5C27CB1AE821ABB77FE457C241`。
- 释放后 `latexmk/lualatex/luatex/luahbtex=NONE`。

## 主线视觉预检

- 主线以 Poppler 220 dpi 独立渲染并打开整页。
- 8 个节点、7 条关系、箭头、节点边框与文字均完整；未见真实裁切、实质重叠、错接或断边。
- 公式中的目标 `n`、三个数学加号、总数 `N` 与自然下标均清晰可读，未见 tofu、错码、数学语义错误或肉眼明显字号失衡。
- LDA 下移后的应用标签与节点边框保持可见净距。

## R168 用户授权字体口径

- 字体审查改为“可读性、语义和整体一致性优先”。缺字/tofu、错码或错误数学语义、实际不可读、肉眼明显失衡、真实裁切/重叠仍是硬失败。
- `[0.92,1.08]` 微比例、精细 taxonomy/peer 比较及 1--2 px 栅格差异降为 advisory，不能单独触发返源、重建或 `FAIL_TO_SA2`。
- 几何、关系、公式语义、真实裁切/重叠门保持硬门。

A 现仅需执行精简机器门、关键几何/语义反证和真实人工终验；不得以字体微差启动新 TeX。通过后再走既定提交、官方候选与 fresh role 链。
