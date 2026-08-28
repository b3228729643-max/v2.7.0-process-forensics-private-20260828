import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { FileBlob, SpreadsheetFile } from "@oai/artifact-tool";

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const projectRoot = path.resolve(scriptDir, "..");
const workbookPath = path.join(projectRoot, "qa", "统计学习方法讲义_v2.0.0_问题关闭台账.xlsx");
const seedPath = path.join(projectRoot, "qa", "source_cache", "issue_ledger_seed.json");
const verificationPath = path.join(projectRoot, "qa", "source_cache", "phase3_content_ledger_verification.json");
const previewDir = path.join(projectRoot, "qa", "previews", "phase3_content_ledger");

const commit = "3f6f7bb";
const report = "qa/数学修复回归.md";
const contentIssueIds = new Set([
  "ISS-004", "ISS-012", "ISS-017", "ISS-021",
  "ISS-030", "ISS-033", "ISS-034", "ISS-035",
]);

const issueEvidence = {
  "ISS-004": "全书首读层与进阶实现层分离；29个长工程算法均有进阶条带，缺失0。",
  "ISS-012": "第1章保留8组代表性完整解析，其余常规题改为A级答案或提示。",
  "ISS-017": "第1章完整解析数量由14组收敛为8组，保留代表性边界、反例与核验。",
  "ISS-021": "固定步长梯度下降首读算法压缩为6个可见步骤，完整C1—C12契约仍可追溯。",
  "ISS-030": "第8章删除IIS算法副本，只保留到第17章的依赖预告。",
  "ISS-033": "k折交叉验证压缩为7个可见步骤，显式保留无泄漏折内流水线。",
  "ISS-034": "训练/验证曲线采用实线圆点与虚线三角双编码，选定点另用菱形和参考线。",
  "ISS-035": "23项内容改为项目检查表；工程闭环压缩为6阶段且不编号为数学算法。",
};

await fs.mkdir(previewDir, { recursive: true });
const seed = JSON.parse(await fs.readFile(seedPath, "utf8"));
if (!Array.isArray(seed.rows) || seed.rows.length !== 110) {
  throw new Error("The cached issue seed must contain exactly 110 rows.");
}

const input = await FileBlob.load(workbookPath);
const workbook = await SpreadsheetFile.importXlsx(input);
const sheet = workbook.worksheets.getItem("逐章问题");

for (const [index, row] of seed.rows.entries()) {
  if (!contentIssueIds.has(row.ID)) continue;
  const excelRow = index + 2;
  const evidence = issueEvidence[row.ID];
  sheet.getRange(`L${excelRow}`).values = [["待复核"]];
  sheet.getRange(`O${excelRow}:T${excelRow}`).values = [[
    commit,
    `${report}；${evidence}`,
    "git diff --check；长算法29/条带缺失0；第1章solution=8；活动scriptsize/tiny=0；第1册171页构建通过。",
    "150 dpi检查物理页14—17、37、112、141—142、160—161；无裁切或重叠，曲线灰度可区分。",
    "待复核",
    null,
  ]];
}

const statusValues = sheet.getRange("S2:S111").values.flat();
const statusCounts = statusValues.reduce((counts, value) => {
  const key = String(value ?? "");
  counts[key] = (counts[key] ?? 0) + 1;
  return counts;
}, {});
const expectedCounts = { 已关闭: 14, 待复核: 92, 修改中: 4 };
for (const [status, expected] of Object.entries(expectedCounts)) {
  if (statusCounts[status] !== expected) {
    throw new Error(`Unexpected ${status} count: ${statusCounts[status]} (expected ${expected}).`);
  }
}

const exportBlob = await SpreadsheetFile.exportXlsx(workbook);
await exportBlob.save(workbookPath);

const preview = await workbook.render({ sheetName: "逐章问题", range: "L1:T36", scale: 1, format: "png" });
const previewPath = path.join(previewDir, "content-items.png");
await fs.writeFile(previewPath, new Uint8Array(await preview.arrayBuffer()));

const keyRows = await workbook.inspect({
  kind: "table",
  sheetId: "逐章问题",
  range: "L1:T36",
  include: "values,formulas",
  tableMaxRows: 36,
  tableMaxCols: 9,
  maxChars: 24000,
});
const formulaErrors = await workbook.inspect({
  kind: "match",
  searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A",
  options: { useRegex: true, maxResults: 100 },
  summary: "Phase 3 content ledger formula error scan",
  maxChars: 4000,
});

await fs.writeFile(
  verificationPath,
  `${JSON.stringify({
    workbookPath,
    issueRows: seed.rows.length,
    advancedIssueIds: [...contentIssueIds],
    statusCounts,
    expectedCounts,
    keyRows: keyRows.ndjson ?? "",
    formulaErrors: formulaErrors.ndjson ?? "",
    preview: previewPath,
  }, null, 2)}\n`,
  "utf8",
);

process.stdout.write(`${JSON.stringify({ workbookPath, statusCounts, verificationPath, previewPath })}\n`);
