import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { Workbook, SpreadsheetFile } from "@oai/artifact-tool";

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const projectRoot = path.resolve(scriptDir, "..");
const cachePath = path.join(projectRoot, "qa", "source_cache", "workbook_v1.9.0.json");
const qaDir = path.join(projectRoot, "qa");
const previewDir = path.join(qaDir, "previews", "implementation_matrices");
const verificationPath = path.join(qaDir, "source_cache", "implementation_matrices_verification.json");

const theme = {
  header: "#1F4E79",
  headerText: "#FFFFFF",
  alternate: "#EAF1F7",
  border: "#9CC2E5",
  pending: "#FFF7E6",
  done: "#E8F5F2",
  error: "#FCEBEC",
  text: "#000000",
};

function columnName(indexOneBased) {
  let n = indexOneBased;
  let result = "";
  while (n > 0) {
    n -= 1;
    result = String.fromCharCode(65 + (n % 26)) + result;
    n = Math.floor(n / 26);
  }
  return result;
}

function asObjects(sheet) {
  const headers = sheet.values[0].map(String);
  return sheet.values.slice(1).map((row) =>
    Object.fromEntries(headers.map((header, index) => [header, row[index] ?? ""])),
  );
}

function csvEscape(value) {
  const text = String(value ?? "");
  return /[",\r\n]/.test(text) ? `"${text.replaceAll('"', '""')}"` : text;
}

async function writeCsv(outputPath, headers, rows) {
  const lines = [headers.map(csvEscape).join(",")];
  for (const row of rows) lines.push(headers.map((header) => csvEscape(row[header])).join(","));
  await fs.writeFile(outputPath, `${lines.join("\r\n")}\r\n`, "utf8");
}

async function writeWorkbook({ outputPath, sheetName, headers, rows, widths, statusColumn, allowedStatuses }) {
  const workbook = Workbook.create();
  const sheet = workbook.worksheets.add(sheetName);
  const lastColumn = columnName(headers.length);
  const lastRow = rows.length + 1;
  const values = [headers, ...rows.map((row) => headers.map((header) => row[header] ?? ""))];
  sheet.getRange(`A1:${lastColumn}${lastRow}`).values = values;
  sheet.getRange(`A1:${lastColumn}1`).format = {
    fill: theme.header,
    font: { bold: true, color: theme.headerText, size: 10 },
    horizontalAlignment: "center",
    verticalAlignment: "center",
    wrapText: true,
    borders: { preset: "all", style: "thin", color: theme.border },
    rowHeight: 32,
  };
  if (rows.length) {
    sheet.getRange(`A2:${lastColumn}${lastRow}`).format = {
      font: { color: theme.text, size: 9 },
      verticalAlignment: "top",
      wrapText: true,
      borders: { preset: "all", style: "thin", color: theme.border },
      rowHeight: 30,
    };
    for (let row = 2; row <= lastRow; row += 2) {
      sheet.getRange(`A${row}:${lastColumn}${row}`).format.fill = theme.alternate;
    }
  }
  headers.forEach((header, index) => {
    const col = columnName(index + 1);
    sheet.getRange(`${col}1:${col}${lastRow}`).format.columnWidth = widths[header] ?? 18;
  });
  sheet.freezePanes.freezeRows(1);
  if (statusColumn && allowedStatuses) {
    const index = headers.indexOf(statusColumn);
    if (index >= 0 && rows.length) {
      const col = columnName(index + 1);
      const range = sheet.getRange(`${col}2:${col}${lastRow}`);
      range.dataValidation = { rule: { type: "list", values: allowedStatuses } };
      range.conditionalFormats.deleteAll();
      range.conditionalFormats.add("containsText", {
        text: "完成",
        format: { fill: theme.done, font: { color: "#2F7D6D", bold: true } },
      });
      range.conditionalFormats.add("containsText", {
        text: "关闭",
        format: { fill: theme.done, font: { color: "#2F7D6D", bold: true } },
      });
      range.conditionalFormats.add("containsText", {
        text: "阻塞",
        format: { fill: theme.error, font: { color: "#B23A48", bold: true } },
      });
      range.conditionalFormats.add("containsText", {
        text: "待",
        format: { fill: theme.pending, font: { color: "#B7791F", bold: true } },
      });
    }
  }
  const blob = await SpreadsheetFile.exportXlsx(workbook);
  await blob.save(outputPath);
  const previewRows = Math.min(lastRow, 24);
  const preview = await workbook.render({
    sheetName,
    range: `A1:${columnName(Math.min(headers.length, 14))}${previewRows}`,
    scale: 1,
    format: "png",
  });
  const previewPath = path.join(previewDir, `${path.basename(outputPath, ".xlsx")}.png`);
  await fs.writeFile(previewPath, new Uint8Array(await preview.arrayBuffer()));
  const errors = await workbook.inspect({
    kind: "match",
    searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A",
    options: { useRegex: true, maxResults: 100 },
    summary: `${sheetName} formula errors`,
    maxChars: 4000,
  });
  return { outputPath, sheetName, rows: rows.length, previewPath, formulaErrors: errors.ndjson ?? "" };
}

function sourceForChapter(chapter) {
  if (chapter <= 11) return `src/讲义源码/第01册_数学基础与统计学习基本理论/chapters/V1-C${String(chapter).padStart(2, "0")}.tex`;
  if (chapter <= 16) return `src/讲义源码/第02册_基础监督学习方法/chapters/V2-C${String(chapter - 11).padStart(2, "0")}.tex`;
  if (chapter <= 23) return `src/讲义源码/第03册_优化模型与序列模型/chapters/V3-C${String(chapter - 16).padStart(2, "0")}.tex`;
  if (chapter <= 29) return `src/讲义源码/第04册_无监督学习与矩阵分解/chapters/V4-C${String(chapter - 23).padStart(2, "0")}.tex`;
  return `src/讲义源码/第05册_采样方法主题模型与图排序/chapters/V5-C${String(chapter - 29).padStart(2, "0")}.tex`;
}

const conceptSeedText = `
1|数学对象|mathematical object||L|建立全书声明对象与类型的起点|集合、数、向量或函数|对象必须先给类型和取值范围
1|映射|mapping|数学对象|L|解释模型和随机变量都是带定义域的映射|f:X→Y|定义域、陪域和值域不能混同
1|标量、向量与矩阵|scalar, vector, matrix|数学对象|L|统一符号类型和维数|a∈R, x∈R^d, A∈R^{m×n}|x^2不能默认解释为向量平方
1|样本、特征与标签|sample, feature, label|标量、向量与矩阵|L|建立统计学习数据语言|x_i∈R^d, y_i∈Y|样本编号与坐标编号必须区分
2|线性组合与张成|linear combination and span|标量、向量与矩阵|M|说明向量空间如何由少量方向生成|向量与系数|系数域与向量维数必须一致
2|线性无关、基与维数|linear independence, basis, dimension|线性组合与张成|L|解释坐标、秩与模型自由度|向量组|基向量数量等于空间维数
2|秩与零空间|rank and null space|线性无关、基与维数|L|连接线性方程、SVD与低秩模型|矩阵A及ker(A)|零矩阵具有秩0
2|正交与投影|orthogonality and projection|线性组合与张成|L|支撑最小二乘、PCA和几何解释|内积空间中的向量|投影对象与目标子空间必须声明
2|特征值与特征向量|eigenvalue and eigenvector|线性无关、基与维数|M|解释不变方向与谱方法|方阵A、非零向量v|一般方阵未必可对角化
3|偏导数与梯度|partial derivative and gradient|标量、向量与矩阵|L|把多元变化率转成优化方向|f:R^d→R, ∇f∈R^d|梯度依赖所选内积和变量顺序
3|方向导数与Hessian|directional derivative and Hessian|偏导数与梯度|M|连接一阶方向变化和二阶曲率|方向u与矩阵∇²f|Hessian存在需二阶可微条件
3|Taylor局部模型|Taylor local model|方向导数与Hessian|L|解释Newton法与局部近似|函数、展开点、增量|余项阶和适用邻域必须说明
3|链式法则与矩阵微分|chain rule and matrix calculus|偏导数与梯度|L|支撑复合模型参数求导|复合映射与维数|转置方向必须逐步核验
4|样本空间与事件|sample space and event|集合|L|把随机试验结果转成集合语言|Ω与其子集|事件集合需处于σ-代数
4|随机变量|random variable|映射;样本空间与事件|L|说明随机变量不是随机变化的数值表，而是可测映射|X:Ω→R|可测性与值域必须声明
4|PMF、PDF与CDF|PMF, PDF, CDF|随机变量|L|区分离散质量、连续密度和累计概率|函数或测度|密度值可大于1但积分为1
4|联合、边缘与条件分布|joint, marginal, conditional distribution|PMF、PDF与CDF|L|支撑图模型和Bayes公式|多个随机变量|条件事件概率必须为正或用核表述
4|期望、方差与协方差|expectation, variance, covariance|联合、边缘与条件分布|L|概括位置、波动和线性关联|随机变量与矩阵|存在性和有限二阶矩条件不能省略
5|总体、样本、参数与统计量|population, sample, parameter, statistic|随机变量|L|区分数据生成对象与从样本计算的量|参数θ与统计量T(X)|统计量不能依赖未知参数
5|似然与最大似然|likelihood and maximum likelihood|联合、边缘与条件分布|L|解释固定数据后如何比较参数|L(θ;x)|似然不是关于数据的概率分布
5|先验、后验与MAP|prior, posterior, MAP|似然与最大似然|L|连接先验知识与观测证据|π(θ), p(θ|x)|MAP对参数化可能敏感
6|信息量与熵|information and entropy|PMF、PDF与CDF|L|量化意外程度及其平均|有限离散分布|0log0按极限约定处理
6|交叉熵与KL散度|cross entropy and KL divergence|信息量与熵|L|度量编码代价与分布差异|同一支持上的分布p,q|KL不对称且支持不匹配可为无穷
6|互信息|mutual information|交叉熵与KL散度|M|量化两个变量共享的信息|联合与边缘分布|互信息非负但不是距离
7|优化变量、目标与可行域|optimization variable, objective, feasible set|映射|L|先声明“优化谁、满足什么条件”|x∈X, f(x), constraints|参数与优化变量不能混用
7|局部最优、全局最优与驻点|local/global optimum and stationary point|优化变量、目标与可行域;偏导数与梯度|L|区分一阶条件与真正最优性|可微目标|驻点不必是局部最优
7|凸集与凸函数|convex set and convex function|线性组合与张成;优化变量、目标与可行域|L|给出局部到全局结论的条件|集合C与函数f|定义只在线段位于定义域时适用
7|Lagrange对偶与KKT|Lagrange duality and KKT|凸集与凸函数|L|处理约束优化并解释证书|乘子、原始/对偶变量|Slater条件限定凸问题
8|数学收敛与数值停止|mathematical convergence and numerical stop|局部最优、全局最优与驻点|L|统一全书算法状态语义|序列、残差、容差与预算|参数变化小不等于数学收敛
8|梯度下降与线搜索|gradient descent and line search|偏导数与梯度;数学收敛与数值停止|L|解释下降方向和步长选择|x_{k+1}=x_k-α_k∇f|0<ρ<1且各参数作用需定义
8|Newton、DFP与BFGS|Newton, DFP, BFGS|方向导数与Hessian;梯度下降与线搜索|L|解释二阶及拟Newton更新|Hessian或其近似|通用BFGS不要求特征非负
9|模型、策略与算法|model, strategy, algorithm|样本、特征与标签;优化变量、目标与可行域|L|分开表示空间、评价准则和求解过程|假设空间、损失、优化器|三者不能用同一公式替代
9|损失、经验风险与期望风险|loss, empirical risk, expected risk|模型、策略与算法;期望、方差与协方差|L|区分单样本误差、训练平均和总体表现|L(y,f(x)), R_hat, R|训练风险低不保证泛化
10|正则化与复杂度控制|regularization and complexity control|损失、经验风险与期望风险|L|解释为什么限制假设空间|惩罚项或约束|正则强度与数据拟合需权衡
11|泛化与数据划分|generalization and data splitting|损失、经验风险与期望风险;正则化与复杂度控制|L|区分训练拟合、验证选参与测试评估|训练/验证/测试集合|测试集不能参与选参
12|感知机与线性判别|perceptron and linear discrimination|样本、特征与标签;偏导数与梯度|M|建立第一个监督分类模型|w∈R^d,b∈R|线性可分性决定经典收敛结论
13|k近邻与距离投票|k-nearest neighbors and voting|样本、特征与标签;正交与投影|M|解释非参数局部预测|距离、邻域和k|算法必须实现一般k而非只写1-NN
14|条件独立与朴素Bayes|conditional independence and naive Bayes|联合、边缘与条件分布;先验、后验与MAP|L|把高维联合概率分解为可估计因子|类别与特征变量|零频需平滑且条件独立是假设
15|决策树与递归划分|decision tree and recursive partition|信息量与熵;模型、策略与算法|M|解释按特征逐步缩小候选空间|节点、分支、叶|缺失值和未见类别必须有默认策略
16|逻辑斯谛与最大熵|logistic regression and maximum entropy|似然与最大似然;交叉熵与KL散度|L|连接条件概率、线性打分和凸优化|w∈R^d,b∈R|决策边界需w≠0
17|间隔、原始与对偶SVM|margin, primal and dual SVM|Lagrange对偶与KKT;模型、策略与算法|L|用间隔和对偶解释支持向量|w,b,α|软间隔、核和SMO顺序不能倒置
18|提升与加法模型|boosting and additive model|模型、策略与算法;梯度下降与线搜索|L|解释弱学习器如何逐轮组合|基学习器与权重|无正边应返回no_weak_edge
19|模型评估与风险界|model evaluation and risk bounds|泛化与数据划分;损失、经验风险与期望风险|L|区分经验比较和概率保证|有限模型族与δ|单侧和双侧界常数不同
20|隐变量、边缘化与EM|latent variable, marginalization and EM|联合、边缘与条件分布;似然与最大似然|L|解释观测不到的变量如何参与估计|X,Z,θ|参数小变化只能叫numerical_stop
21|状态、路径与动态规划|state, path and dynamic programming|随机变量;模型、策略与算法|L|避免枚举全部序列历史|状态序列与递推表|不可行路径需no_feasible_path
21|HMM转移与发射|HMM transition and emission|状态、路径与动态规划;联合、边缘与条件分布|L|建立序列生成模型|A,B,π|不可约和非周期不应提前作为主线先修
22|因子、势函数与配分函数|factor, potential, partition function|联合、边缘与条件分布;模型、策略与算法|L|解释CRF非规范化权重如何归一化|局部因子与Z(x)|势函数不必是概率
22|CRF链与终止因子|CRF chain and terminal factor|因子、势函数与配分函数;状态、路径与动态规划|L|统一局部分解和前向终止式|M_i与stop因子|终止因子必须显式或声明吸收
23|有限模型族泛化界|finite-class generalization bound|模型评估与风险界|M|给出可计算的高概率界|M,n,δ|绝对偏差需log(2M/δ)
24|无标签数据与聚类|unlabeled data and clustering|样本、特征与标签;正交与投影|L|说明无监督任务输出不是标签预测|样本、距离、簇|距离选择影响簇结构
25|层次聚类与linkage|hierarchical clustering and linkage|无标签数据与聚类|M|解释树状合并和簇间距离|簇、树状图|centroid linkage可能产生倒置
26|奇异值分解|singular value decomposition|秩与零空间;正交与投影;特征值与特征向量|L|统一低秩、几何变换和矩阵近似|A=UΣV^T|零矩阵必须有秩0分支
27|主成分与低维投影|principal component and low-dimensional projection|奇异值分解;期望、方差与协方差|L|用最大方差方向压缩数据|样本按行的数据矩阵|中心化和样本方向必须明确
28|词—文档矩阵与潜在语义|term-document matrix and latent semantics|奇异值分解;样本、特征与标签|L|桥接文档表示与低秩语义空间|词×文档矩阵|需给出与样本按行主约定的转置桥
29|非负矩阵分解与PLSA|NMF and PLSA|词—文档矩阵与潜在语义;先验、后验与MAP|L|区分代数分解与概率混合|非负因子或主题分布|非负约束只属于相应模型
30|随机过程与转移矩阵|stochastic process and transition matrix|随机变量;联合、边缘与条件分布|L|从单次随机变量推广到随时间演化|可数状态、时间、K|初学主线限定可数/有限状态
30|平稳分布与细致平衡|stationary distribution and detailed balance|随机过程与转移矩阵|L|解释长期不变分布和可逆性|πK=π|细致平衡是充分条件而非必要条件
31|Monte Carlo估计与误差|Monte Carlo estimation and error|期望、方差与协方差;数学收敛与数值停止|L|用随机样本近似期望|样本均值与标准误|有限样本停止不等于数学收敛
32|Metropolis–Hastings|Metropolis-Hastings|平稳分布与细致平衡;Monte Carlo估计与误差|L|构造以目标分布为平稳分布的链|提议核与接受率|坐标奇异核不能直接套全维密度证明
33|Gibbs条件更新|Gibbs conditional update|Metropolis–Hastings;联合、边缘与条件分布|L|用全条件分布逐坐标更新|状态向量与条件核|需独立证明坐标核不变性
34|概率单纯形与Dirichlet|probability simplex and Dirichlet|PMF、PDF与CDF;先验、后验与MAP|L|表示离散概率向量的不确定性|θ_k≥0,Σθ_k=1|参数必须为正并区分总浓度
34|共轭先验与计数更新|conjugate prior and count update|概率单纯形与Dirichlet|L|解释后验为何保持同族|先验参数+类别计数|计数和参数索引必须一致
35|LDA生成过程与推断|LDA generative process and inference|共轭先验与计数更新;词—文档矩阵与潜在语义|L|统一文档、主题、词和词元层级|文档主题与主题词分布|多启动记录必须封装feasible/status/objective
36|有向图与随机游走|directed graph and random walk|随机过程与转移矩阵|L|把链接结构转成概率推进|节点、边、出度、随机矩阵|悬挂节点需修复
36|PageRank与阻尼|PageRank and damping|有向图与随机游走;平稳分布与细致平衡|L|解释随机跳转保证稳健排序|行/列随机约定与阻尼因子|数学收敛证书与数值停止分开
37|单层与嵌套交叉验证|single and nested cross-validation|泛化与数据划分;模型评估与风险界|L|统一选参与无偏评估协议|C_in,C_out和独立测试集|图、算法和文字必须使用同一数据流
37|方法选择地图|model-selection map|单层与嵌套交叉验证;模型、策略与算法|M|按任务、假设和数据条件组织全书方法|模型族与评估协议|不得把排名图当作普适优劣结论
`;

function buildConceptRows() {
  const seeds = conceptSeedText.trim().split("\n").map((line) => line.split("|"));
  return seeds.map(([chapterRaw, zh, en, prerequisites, level, why, type, boundary], index) => {
    const chapter = Number(chapterRaw);
    return {
      Concept_ID: `CON-${String(index + 1).padStart(3, "0")}`,
      中文概念: zh,
      英文概念: en,
      首次出现章: chapter,
      首次出现节: "待章节负责人确认",
      首次出现源码: sourceForChapter(chapter),
      当前是否已定义: "待验收",
      直接先修概念: prerequisites,
      先修是否已讲: prerequisites ? "待依赖核对" : "是",
      是否顺序倒置: "待验收",
      桥接等级: level,
      为什么需要: why,
      直观解释: `以本章最小的二维、有限状态或小数据表示例解释“${zh}”。`,
      正式定义位置: "待章节负责人回填标签",
      "对象类型/维数": type,
      最小正例: "待源码修改后回填",
      反例或边界: boundary,
      后续使用章节: "待首次出现验收后回填",
      修改状态: "待回填",
      验收证据: "",
    };
  });
}

const cache = JSON.parse(await fs.readFile(cachePath, "utf8"));
const sheet = (name) => {
  const found = cache.sheets.find((item) => item.name === name);
  if (!found) throw new Error(`Missing cached sheet: ${name}`);
  return found;
};

await fs.mkdir(previewDir, { recursive: true });
await fs.mkdir(path.join(projectRoot, "figures"), { recursive: true });
const results = [];

const conceptHeaders = [
  "Concept_ID", "中文概念", "英文概念", "首次出现章", "首次出现节", "首次出现源码", "当前是否已定义",
  "直接先修概念", "先修是否已讲", "是否顺序倒置", "桥接等级", "为什么需要", "直观解释", "正式定义位置",
  "对象类型/维数", "最小正例", "反例或边界", "后续使用章节", "修改状态", "验收证据",
];
const conceptRows = buildConceptRows();
results.push(await writeWorkbook({
  outputPath: path.join(qaDir, "前置概念依赖矩阵.xlsx"),
  sheetName: "概念依赖矩阵",
  headers: conceptHeaders,
  rows: conceptRows,
  widths: { Concept_ID: 13, 中文概念: 22, 英文概念: 28, 首次出现章: 12, 首次出现节: 22, 首次出现源码: 48, 当前是否已定义: 16, 直接先修概念: 32, 先修是否已讲: 16, 是否顺序倒置: 16, 桥接等级: 12, 为什么需要: 36, 直观解释: 40, 正式定义位置: 24, "对象类型/维数": 30, 最小正例: 28, 反例或边界: 38, 后续使用章节: 24, 修改状态: 16, 验收证据: 36 },
  statusColumn: "修改状态",
  allowedStatuses: ["待回填", "修改中", "待验收", "已完成", "阻塞"],
}));
await writeCsv(path.join(qaDir, "前置概念依赖矩阵.csv"), conceptHeaders, conceptRows);

const firstAuditHeaders = ["Concept_ID", "中文概念", "首次出现章", "首次出现节", "首次出现源码", "直观含义", "正式定义", "对象类型/维数", "最小正例", "反例或边界", "定义先于使用", "验收状态", "验收证据"];
const firstAuditRows = conceptRows.map((row) => ({
  Concept_ID: row.Concept_ID,
  中文概念: row.中文概念,
  首次出现章: row.首次出现章,
  首次出现节: row.首次出现节,
  首次出现源码: row.首次出现源码,
  直观含义: "待源码修改后验收",
  正式定义: "待源码修改后验收",
  "对象类型/维数": row["对象类型/维数"],
  最小正例: row.最小正例,
  反例或边界: row.反例或边界,
  定义先于使用: "待验收",
  验收状态: "未开始",
  验收证据: "",
}));
results.push(await writeWorkbook({
  outputPath: path.join(qaDir, "概念首次出现审计.xlsx"),
  sheetName: "首次出现验收",
  headers: firstAuditHeaders,
  rows: firstAuditRows,
  widths: { Concept_ID: 13, 中文概念: 22, 首次出现章: 12, 首次出现节: 22, 首次出现源码: 48, 直观含义: 28, 正式定义: 28, "对象类型/维数": 28, 最小正例: 26, 反例或边界: 36, 定义先于使用: 16, 验收状态: 16, 验收证据: 36 },
  statusColumn: "验收状态",
  allowedStatuses: ["未开始", "修改中", "待验收", "已完成", "阻塞"],
}));

const exampleSource = asObjects(sheet("例题解答审计"));
const exampleHeaders = ["题号", "PDF页", "章节", "角色", "标题", "当前解答类型", "目标解答类型", "是否缺少方法选择", "是否文字过多", "是否数学跳步", "是否存在定义未先讲", "是否状态码侵入", "自动标记", "修改文件", "验收结果"];
const exampleRows = exampleSource.map((row) => {
  const risk = String(row.自动标记 ?? "");
  const core = /证明|推导|KKT|EM|HMM|CRF|MCMC|Dirichlet|LDA|SVD|对偶/.test(String(row.标题));
  return {
    题号: row.编号 || row.索引,
    PDF页: row.PDF页,
    章节: row.章,
    角色: row.角色,
    标题: row.标题,
    当前解答类型: Number(row.内容字符数 || 0) > 1200 ? "B类倾向（长解答）" : "A类倾向",
    目标解答类型: core || risk ? "B类（必要时附C核验）" : "A类",
    是否缺少方法选择: core ? "待人工复核" : "未触发自动证据",
    是否文字过多: risk.includes("文字叙述偏多") ? "是" : "否",
    是否数学跳步: "待人工复核",
    是否存在定义未先讲: "待概念矩阵联查",
    是否状态码侵入: risk.includes("工程状态侵入") ? "是" : "否",
    自动标记: risk,
    修改文件: row.章 ? sourceForChapter(Number(row.章)) : "待定位",
    验收结果: risk ? "高风险待人工复核" : "未开始",
  };
});
results.push(await writeWorkbook({
  outputPath: path.join(qaDir, "例题解答分级矩阵.xlsx"),
  sheetName: "例题解答分级",
  headers: exampleHeaders,
  rows: exampleRows,
  widths: { 题号: 12, PDF页: 10, 章节: 10, 角色: 12, 标题: 42, 当前解答类型: 20, 目标解答类型: 24, 是否缺少方法选择: 20, 是否文字过多: 16, 是否数学跳步: 16, 是否存在定义未先讲: 22, 是否状态码侵入: 18, 自动标记: 28, 修改文件: 48, 验收结果: 22 },
  statusColumn: "验收结果",
  allowedStatuses: ["未开始", "高风险待人工复核", "修改中", "待验收", "已完成", "阻塞"],
}));

const figureSource = asObjects(sheet("绘图审计"));
const figureHeaders = ["旧图号", "章节", "原物理页", "教学问题", "当前问题", "处理动作", "新图源", "图宽", "最小标签字号", "颜色/线型编码", "灰度检查", "正文变量一致性", "题注长度", "读图结论", "验收状态"];
const figureRows = figureSource.map((row) => {
  const problem = String(row.问题 ?? "").trim();
  const risk = String(row.风险 ?? "").trim();
  return {
    旧图号: row.图号,
    章节: row.章,
    原物理页: row.PDF页,
    教学问题: `读者看完图${row.图号}后，应能用正文变量说明：${String(row["题注/正文关联"] ?? "").slice(0, 120)}`,
    当前问题: problem || `${risk || "一般"}：需按9pt、线宽、灰度和图文一致性门槛复核`,
    处理动作: problem ? "重绘" : "保留并校正",
    新图源: "待第二轮绘图负责人定位",
    图宽: ">=0.72\\textwidth（核心图）",
    最小标签字号: ">=9pt",
    "颜色/线型编码": "颜色+线型/点型/形状双编码",
    灰度检查: "未开始",
    正文变量一致性: "待验收",
    题注长度: String(row["题注/正文关联"] ?? "").length,
    读图结论: "待重绘/校正后回填1—3句",
    验收状态: "未开始",
  };
});
results.push(await writeWorkbook({
  outputPath: path.join(qaDir, "绘图重制矩阵.xlsx"),
  sheetName: "绘图重制",
  headers: figureHeaders,
  rows: figureRows,
  widths: { 旧图号: 12, 章节: 10, 原物理页: 12, 教学问题: 46, 当前问题: 38, 处理动作: 16, 新图源: 42, 图宽: 24, 最小标签字号: 18, "颜色/线型编码": 30, 灰度检查: 16, 正文变量一致性: 18, 题注长度: 14, 读图结论: 34, 验收状态: 16 },
  statusColumn: "验收状态",
  allowedStatuses: ["未开始", "修改中", "待验收", "已完成", "保留并说明", "阻塞"],
}));
await writeCsv(path.join(projectRoot, "figures", "figure_manifest.csv"), figureHeaders, figureRows);

const visualSource = asObjects(sheet("逐页视觉风险"));
const visualHeaders = ["PDF页", "章", "原始风险等级", "中位字号", "最小字号", "<7.5pt占比", "绘图对象数", "栅格图数", "链接数", "裁切文本块", "可疑重叠", "原始标记", "修改关联", "人工检查", "关键裁切", "乱码/黑块", "空白异常", "验收状态", "验收证据"];
const visualRows = visualSource.map((row) => ({
  PDF页: row.PDF页,
  章: row.章,
  原始风险等级: row.风险等级,
  中位字号: row.中位字号,
  最小字号: row.最小字号,
  "<7.5pt占比": row["<7.5pt占比"],
  绘图对象数: row.绘图对象数,
  栅格图数: row.栅格图数,
  链接数: row.链接数,
  裁切文本块: row.裁切文本块,
  可疑重叠: row.可疑重叠,
  原始标记: row.原始标记,
  修改关联: "待门C/D按新页码映射",
  人工检查: "未开始",
  关键裁切: "待验收",
  "乱码/黑块": "待验收",
  空白异常: "待验收",
  验收状态: "未开始",
  验收证据: "",
}));
results.push(await writeWorkbook({
  outputPath: path.join(qaDir, "逐页视觉审计.xlsx"),
  sheetName: "逐页视觉验收",
  headers: visualHeaders,
  rows: visualRows,
  widths: { PDF页: 10, 章: 10, 原始风险等级: 16, 中位字号: 12, 最小字号: 12, "<7.5pt占比": 14, 绘图对象数: 14, 栅格图数: 12, 链接数: 12, 裁切文本块: 14, 可疑重叠: 14, 原始标记: 28, 修改关联: 26, 人工检查: 16, 关键裁切: 16, "乱码/黑块": 16, 空白异常: 16, 验收状态: 16, 验收证据: 34 },
  statusColumn: "验收状态",
  allowedStatuses: ["未开始", "自动扫描通过", "待人工复核", "修改中", "已完成", "阻塞"],
}));

await fs.writeFile(verificationPath, `${JSON.stringify({ generatedAtUtc: new Date().toISOString(), results, counts: { concepts: conceptRows.length, examples: exampleRows.length, figures: figureRows.length, pages: visualRows.length } }, null, 2)}\n`, "utf8");
process.stdout.write(`${JSON.stringify({ results: results.map(({ outputPath, rows }) => ({ outputPath, rows })), conceptsCsv: path.join(qaDir, "前置概念依赖矩阵.csv"), figureManifest: path.join(projectRoot, "figures", "figure_manifest.csv") })}\n`);
