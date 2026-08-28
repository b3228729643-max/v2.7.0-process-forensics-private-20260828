import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { FileBlob, SpreadsheetFile } from "@oai/artifact-tool";

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const projectRoot = path.resolve(scriptDir, "..");
const workbookPath = path.join(projectRoot, "qa", "统计学习方法讲义_v2.0.0_问题关闭台账.xlsx");
const seedPath = path.join(projectRoot, "qa", "source_cache", "issue_ledger_seed.json");
const verificationPath = path.join(projectRoot, "qa", "source_cache", "gate_a_ledger_verification.json");
const previewDir = path.join(projectRoot, "qa", "previews", "gate_a_ledger");

const gateAReport = "qa/gate_a_structure_dependency.md";
const gateABuild = "build/final/main_full.pdf（772 页，10,936,190 字节）";
const p0Evidence = new Map([
  ["ISS-001", "终稿全文与 273 个书签均未出现入门诊断、约4分钟、双路线、复测与返回点。"],
  ["ISS-002", "终稿全文与书签均未出现参考资料或参考来源，目录末项为主题索引。"],
  ["ISS-003", "物理页 3--17 核验目录→符号索引→阅读图例→正文；正文阿拉伯页码从第1册分册页 1 开始。"],
  ["ISS-015", "物理页 23：练习 1.9 明确区分 x^2、x^(2) 与 A^T。"],
  ["ISS-048", "物理页 263：Newton 算法数据行在使用前给出 δ_min≤δ_0≤δ_max。"],
  ["ISS-050", "物理页 283：BFGS 输入为有限实值特征，不含非负特征限制。"],
  ["ISS-057", "物理页 332：梯度提升回溯参数明确满足 0<ρ<1。"],
  ["ISS-065", "V3-C06.tex 第254、701--705行：路径分解显式包含终止因子 M_(n+1)。"],
  ["ISS-068", "物理页 409 与 V3-C07.tex 第149--154、421--429行：定理和解析使用同一单侧上界。"],
  ["ISS-074", "物理页 459：零矩阵返回合法秩0紧SVD与 completed，而非数值失败。"],
  ["ISS-085", "物理页 547 及 V5-C01.tex 第112--120、217--224行：有限/可数单点定义与一般可测空间核定义分层一致。"],
  ["ISS-091", "物理页 606：单坐标MH证明改用三元组支配测度，覆盖全维奇异提议。"],
  ["ISS-100", "物理页 705：多启动 record 只在相同评价口径的可接受集合中比较。"],
  ["ISS-106", "物理页 747 及 V5-C08.tex 第397--421行：图、算法与文字一致区分开发集选择+锁定测试和嵌套交叉验证。"],
]);

await fs.mkdir(previewDir, { recursive: true });
const seed = JSON.parse(await fs.readFile(seedPath, "utf8"));
if (!Array.isArray(seed.rows) || seed.rows.length !== 110) {
  throw new Error("The cached issue seed must contain exactly 110 rows.");
}

const input = await FileBlob.load(workbookPath);
const workbook = await SpreadsheetFile.importXlsx(input);
const sheet = workbook.worksheets.getItem("逐章问题");

for (const [index, row] of seed.rows.entries()) {
  const evidence = p0Evidence.get(row.ID);
  if (!evidence) continue;
  const excelRow = index + 2;
  sheet.getRange(`L${excelRow}`).values = [["已关闭"]];
  sheet.getRange(`P${excelRow}:S${excelRow}`).values = [[
    `${gateAReport}；${evidence}`,
    `${gateABuild}；LuaLaTeX 干净构建退出码0；未解析引用/致命错误/公式错误均为0；终稿文本与书签禁词命中0。`,
    `Gate A 以120 dpi定向渲染核验；${evidence}`,
    "已关闭",
  ]];
}

const statusValues = sheet.getRange("S2:S111").values.flat();
const statusCounts = statusValues.reduce((counts, value) => {
  const key = String(value ?? "");
  counts[key] = (counts[key] ?? 0) + 1;
  return counts;
}, {});
const expectedCounts = { 已关闭: 14, 待复核: 84, 修改中: 12 };
for (const [status, expected] of Object.entries(expectedCounts)) {
  if (statusCounts[status] !== expected) {
    throw new Error(`Unexpected ${status} count: ${statusCounts[status]} (expected ${expected}).`);
  }
}

const exportBlob = await SpreadsheetFile.exportXlsx(workbook);
await exportBlob.save(workbookPath);

const previewRanges = ["A1:T16", "A48:T76", "A85:T108"];
const previews = [];
for (const [index, range] of previewRanges.entries()) {
  const preview = await workbook.render({ sheetName: "逐章问题", range, scale: 1, format: "png" });
  const outputPath = path.join(previewDir, `p0-group-${index + 1}.png`);
  await fs.writeFile(outputPath, new Uint8Array(await preview.arrayBuffer()));
  previews.push(outputPath);
}

const keyRows = await workbook.inspect({
  kind: "table",
  sheetId: "逐章问题",
  range: "L1:T16",
  include: "values,formulas",
  tableMaxRows: 16,
  tableMaxCols: 9,
  maxChars: 18000,
});
const formulaErrors = await workbook.inspect({
  kind: "match",
  searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A",
  options: { useRegex: true, maxResults: 100 },
  summary: "Gate A issue ledger formula error scan",
  maxChars: 4000,
});

await fs.writeFile(
  verificationPath,
  `${JSON.stringify({
    workbookPath,
    issueRows: seed.rows.length,
    closedIssueIds: [...p0Evidence.keys()],
    statusCounts,
    expectedCounts,
    keyRows: keyRows.ndjson ?? "",
    formulaErrors: formulaErrors.ndjson ?? "",
    previews,
  }, null, 2)}\n`,
  "utf8",
);

process.stdout.write(`${JSON.stringify({ workbookPath, statusCounts, verificationPath })}\n`);
