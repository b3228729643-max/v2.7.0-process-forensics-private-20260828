import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { FileBlob, SpreadsheetFile } from "@oai/artifact-tool";

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const projectRoot = path.resolve(scriptDir, "..");
const workbookPath = path.join(projectRoot, "qa", "统计学习方法讲义_v2.0.0_问题关闭台账.xlsx");
const seedPath = path.join(projectRoot, "qa", "source_cache", "issue_ledger_seed.json");
const verificationPath = path.join(projectRoot, "qa", "source_cache", "gate_b_ledger_verification.json");
const previewDir = path.join(projectRoot, "qa", "previews", "gate_b_ledger");

const gateBReport = "qa/gate_b_math_teaching.md";
const gateBBuild = "build/gate_b/main_full.pdf（771页，10,903,263字节）";
const pendingIssueIds = new Set(["ISS-009", "ISS-010", "ISS-011"]);
const gateBCommit = String(process.env.GATE_B_COMMIT ?? "").trim();
if (!/^[0-9a-f]{7,40}$/i.test(gateBCommit)) {
  throw new Error("GATE_B_COMMIT must be an explicit Git commit hash.");
}

function appendEvidence(existing, addition) {
  const text = String(existing ?? "").trim();
  if (!text) return addition;
  if (text.includes(addition)) return text;
  return `${text}；${addition}`;
}

await fs.mkdir(previewDir, { recursive: true });
const seed = JSON.parse(await fs.readFile(seedPath, "utf8"));
if (!Array.isArray(seed.rows) || seed.rows.length !== 110) {
  throw new Error("The cached issue seed must contain exactly 110 rows.");
}

const input = await FileBlob.load(workbookPath);
const workbook = await SpreadsheetFile.importXlsx(input);
const sheet = workbook.worksheets.getItem("逐章问题");

for (const [index, row] of seed.rows.entries()) {
  const excelRow = index + 2;
  const evidence = sheet.getRange(`O${excelRow}:T${excelRow}`).values[0];
  if (pendingIssueIds.has(row.ID)) {
    sheet.getRange(`L${excelRow}`).values = [["修改中"]];
    sheet.getRange(`P${excelRow}:S${excelRow}`).values = [[
      appendEvidence(evidence[1], `${gateBReport}；Gate B内容域已通过，本项按DEC-0010留给后续专属门。`),
      appendEvidence(evidence[2], `${gateBBuild}；引用、索引、状态语义和数学分层检查通过。`),
      appendEvidence(evidence[3], "Gate B定向页无裁切或重叠；未以该证据替代Gate C整书200 dpi/灰度或Gate D最终链接验收。"),
      "修改中",
    ]];
    continue;
  }

  sheet.getRange(`L${excelRow}`).values = [["已关闭"]];
  sheet.getRange(`O${excelRow}:T${excelRow}`).values = [[
    appendEvidence(evidence[0], gateBCommit),
    appendEvidence(evidence[1], `${gateBReport}；Gate B数学与教学内容验收通过。`),
    appendEvidence(evidence[2], `${gateBBuild}；未解析引用/重跑/致命/缺字/重复目标均为0；双索引0警告。`),
    appendEvidence(evidence[3], "150 dpi定向复核首读分层、例题、IIS、交叉验证、状态语义及七组算法/条带页序；无裁切、重叠或顺序倒置。"),
    "已关闭",
    null,
  ]];
}

const statusValues = sheet.getRange("S2:S111").values.flat();
const statusCounts = statusValues.reduce((counts, value) => {
  const key = String(value ?? "");
  counts[key] = (counts[key] ?? 0) + 1;
  return counts;
}, {});
const expectedCounts = { 已关闭: 107, 修改中: 3 };
for (const [status, expected] of Object.entries(expectedCounts)) {
  if (statusCounts[status] !== expected) {
    throw new Error(`Unexpected ${status} count: ${statusCounts[status]} (expected ${expected}).`);
  }
}
for (const status of Object.keys(statusCounts)) {
  if (!(status in expectedCounts)) {
    throw new Error(`Unexpected remaining status after Gate B: ${status}`);
  }
}

const exportBlob = await SpreadsheetFile.exportXlsx(workbook);
await exportBlob.save(workbookPath);

const previewRanges = ["L1:T16", "L96:T111"];
const previews = [];
for (const [index, range] of previewRanges.entries()) {
  const preview = await workbook.render({ sheetName: "逐章问题", range, scale: 1, format: "png" });
  const outputPath = path.join(previewDir, `gate-b-${index + 1}.png`);
  await fs.writeFile(outputPath, new Uint8Array(await preview.arrayBuffer()));
  previews.push(outputPath);
}

const globalRows = await workbook.inspect({
  kind: "table",
  sheetId: "逐章问题",
  range: "A1:T16",
  include: "values,formulas",
  tableMaxRows: 16,
  tableMaxCols: 20,
  maxChars: 26000,
});
const formulaErrors = await workbook.inspect({
  kind: "match",
  searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A",
  options: { useRegex: true, maxResults: 100 },
  summary: "Gate B issue ledger formula error scan",
  maxChars: 4000,
});

await fs.writeFile(
  verificationPath,
  `${JSON.stringify({
    workbookPath,
    issueRows: seed.rows.length,
    gateBCommit,
    closedCount: 107,
    pendingIssueIds: [...pendingIssueIds],
    statusCounts,
    expectedCounts,
    globalRows: globalRows.ndjson ?? "",
    formulaErrors: formulaErrors.ndjson ?? "",
    previews,
  }, null, 2)}\n`,
  "utf8",
);

process.stdout.write(`${JSON.stringify({ workbookPath, gateBCommit, statusCounts, verificationPath, previews })}\n`);
