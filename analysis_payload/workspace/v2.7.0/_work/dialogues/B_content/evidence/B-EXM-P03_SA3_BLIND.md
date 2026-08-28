# B-EXM-P03 SA3 隔离盲审

- 角色：隔离只读 SA3（`gpt-5.6-sol`，xhigh）。
- 独立性：未读取 SA1/机械结论；未写文件、未提交、未启动 LuaLaTeX/latexmk。
- 初末 TeX 进程：NONE。
- 最终结论：`FINAL_DECISION=PASS`。
- Findings：`NONE`。

## 独立复算

| 例题 | 独立结果 | Verdict |
|---|---|---|
| 1.1 | $Xw=(2,3,-1)^{\mathsf T}\in\mathbb R^3$ | PASS |
| 2.1 | $a=2$，$p=(2,2)^{\mathsf T}$，$r=(1,-1)^{\mathsf T}$，$d=\sqrt2$ | PASS |
| 3.1 | 梯度、Hessian 正定；原点唯一全局极小，值为 0 | PASS |
| 4.1 | $A\cap B=\{4,6\}$，$A\cup B=\{2,4,5,6\}$，概率$2/3$ | PASS |
| 4.2 | 全方差$1+1=2$，组内/组间各为 1 | PASS |
| 4.3 | $P(D\mid+)=19/118\approx0.161016949$ | PASS |
| 5.1 | 唯一 MLE $\hat p=0.7$；对数似然差$0.822828785$ | PASS |
| 6.1 | 双向 KL 为$0.091516222$、$0.104649629$ | PASS |
| 7.1 | KKT 解为$(2,0)$、$(0,2)$ | PASS |
| 7.2 | $x^\star=ba/\|a\|_2^2$，$\alpha^\star=b/\|a\|_2^2$，最优值$b^2/(2\|a\|_2^2)$ | PASS |

## 结构与写域

- `STRUCTURE=PASS`：十块七阶段各且仅一次，共 70/70。
- `QUESTION_SPECIFIC=PASS`：题意、条件、方法、计划、核验和答案均为对象专属。
- `UNIQUE_ANSWER=PASS`：十题均有唯一答案或唯一所求量。
- `WRITE_DOMAIN=PASS`：Git 仅有 V1-C01.tex 至 V1-C07.tex 七文件变化；全部 hunk 位于指定十个 `solution` 块；`git diff --check` PASS。
- `.fls` 六个项目输出均位于指定构建目录；一个 TeX 临时缓存探针 `m_t_x_t_e_s_t.tmp` 未写入源码、证据或状态域。

## PDF、日志与视觉

- `PDF=PASS`：814 页；全部 MediaBox 为 595.276 x 841.890 pt，旋转 0，A4。
- `LOG=PASS`：正常写出 814 页、4,943,198 bytes。
- 硬错误、Fatal/Emergency stop、Undefined control sequence、缺文件、未定义引用、rerun、Overfull/Underfull：全部 0。
- `VISUAL=PASS`：17/17 页逐张检查，页码 17、18、29、30、48、49、62、65、67、68、81、99、100、115、116、121、122。
- 跨页续题标识正常；无裁切、重叠、乱码、边框断裂、公式畸形或页眉页脚异常。

## 实际只读检查

`Get-Process`、Git status/name-status/stat/diff/check、`rg` 定位、源码/日志读取、PowerShell 数学复算与结构统计、`pdfinfo`、pypdf MediaBox/Rotation 检查、日志/`.fls` 扫描，以及 `view_image` 逐张目检 17 页。
