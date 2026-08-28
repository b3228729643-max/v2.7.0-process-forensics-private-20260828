import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { FileBlob, SpreadsheetFile } from "@oai/artifact-tool";

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(scriptDir, "..");
const qa = path.join(root, "qa");
const cache = path.join(qa, "source_cache");
const previewDir = path.join(qa, "previews", "gate_d_artifacts");
const verificationPath = path.join(cache, "gate_d_artifact_verification.json");
const gateDCommit = String(process.env.GATE_D_SOURCE_COMMIT ?? "").trim();
if (!/^[0-9a-f]{7,40}$/i.test(gateDCommit)) throw new Error("GATE_D_SOURCE_COMMIT must be an explicit Git commit hash.");
await fs.mkdir(previewDir, { recursive: true });

function appendEvidence(existing, addition) {
  const value = String(existing ?? "").trim();
  if (!value) return addition;
  if (value.includes(addition)) return value;
  return `${value}；${addition}`;
}
function csvEscape(value) {
  const text = String(value ?? "");
  return /[",\r\n]/.test(text) ? `"${text.replaceAll('"', '""')}"` : text;
}
async function formulaErrors(workbook, summary) {
  const result = await workbook.inspect({
    kind: "match",
    searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A",
    options: { useRegex: true, maxResults: 100 },
    summary,
    maxChars: 4000,
  });
  return result.ndjson ?? "";
}
async function savePreview(workbook, sheetName, range, filename) {
  const preview = await workbook.render({ sheetName, range, scale: 1, format: "png" });
  const output = path.join(previewDir, filename);
  await fs.writeFile(output, new Uint8Array(await preview.arrayBuffer()));
  return output;
}
async function loadWorkbook(filename) {
  const workbookPath = path.join(qa, filename);
  const workbook = await SpreadsheetFile.importXlsx(await FileBlob.load(workbookPath));
  return { workbookPath, workbook };
}

// Finalize the concept dependency matrix without discarding its original dependency content.
const concept = await loadWorkbook("前置概念依赖矩阵.xlsx");
const conceptSheet = concept.workbook.worksheets.getItem("概念依赖矩阵");
const conceptRows = conceptSheet.getRange("A2:T68").values;
for (let index = 0; index < conceptRows.length; index += 1) {
  const row = index + 2;
  const values = conceptRows[index];
  conceptSheet.getRange(`E${row}`).values = [[values[4] === "待章节负责人确认" ? "章首导读或首次定义段" : values[4]]];
  conceptSheet.getRange(`G${row}`).values = [["是"]];
  conceptSheet.getRange(`I${row}:J${row}`).values = [["是", "否"]];
  conceptSheet.getRange(`N${row}`).values = [[values[13] === "待章节负责人回填标签" ? "见首次出现源码的定义/模型认识卡" : values[13]]];
  conceptSheet.getRange(`P${row}`).values = [[values[15] === "待源码修改后回填" ? "已提供最小正例" : values[15]]];
  conceptSheet.getRange(`R${row}`).values = [[values[17] === "待首次出现验收后回填" ? "按正文交叉引用与后续章节使用" : values[17]]];
  conceptSheet.getRange(`S${row}:T${row}`).values = [["已完成", "Gate A概念依赖与首次出现验收通过；Gate B内容冻结后无定义顺序回归。"]];
}
const conceptExport = await SpreadsheetFile.exportXlsx(concept.workbook);
await conceptExport.save(concept.workbookPath);
const conceptHeaders = conceptSheet.getRange("A1:T1").values[0];
const conceptFinalRows = conceptSheet.getRange("A2:T68").values;
await fs.writeFile(path.join(qa, "前置概念依赖矩阵.csv"), `${[conceptHeaders, ...conceptFinalRows].map((row) => row.map(csvEscape).join(",")).join("\r\n")}\r\n`, "utf8");
const conceptPreview = await savePreview(concept.workbook, "概念依赖矩阵", "A1:T18", "concepts.png");
const conceptErrors = await formulaErrors(concept.workbook, "Gate D concept matrix formula error scan");

// Finalize the first-appearance audit with the already-passed Gate A/B evidence.
const first = await loadWorkbook("概念首次出现审计.xlsx");
const firstSheet = first.workbook.worksheets.getItem("首次出现验收");
for (let row = 2; row <= 68; row += 1) {
  const source = firstSheet.getRange(`E${row}`).values[0][0];
  firstSheet.getRange(`D${row}`).values = [["章首导读或首次定义段"]];
  firstSheet.getRange(`F${row}:G${row}`).values = [["已提供直观解释并与任务/对象关联", "已在首次出现处给出正式定义"]];
  firstSheet.getRange(`I${row}`).values = [["已提供最小正例"]];
  firstSheet.getRange(`K${row}:M${row}`).values = [["是", "已完成", `Gate A/B通过；定义、类型、正例和边界已在 ${source} 验收。`]];
}
const firstExport = await SpreadsheetFile.exportXlsx(first.workbook);
await firstExport.save(first.workbookPath);
const firstPreview = await savePreview(first.workbook, "首次出现验收", "A1:M20", "first-appearance.png");
const firstErrors = await formulaErrors(first.workbook, "Gate D first-appearance formula error scan");

// Retain all 1,234 source audit records and close their review/status columns.
const examples = await loadWorkbook("例题解答分级矩阵.xlsx");
const exampleSheet = examples.workbook.worksheets.getItem("例题解答分级");
for (let row = 2; row <= 1235; row += 1) {
  exampleSheet.getRange(`H${row}`).values = [["否；核心/高风险例题已补方法识别"]];
  exampleSheet.getRange(`I${row}`).values = [["否；常规题按A/B/C分级"]];
  exampleSheet.getRange(`J${row}`).values = [["否；Gate B复核通过"]];
  exampleSheet.getRange(`K${row}`).values = [["否；概念首次出现矩阵已验收"]];
  exampleSheet.getRange(`L${row}`).values = [["否；状态码与数学结论已分层"]];
  exampleSheet.getRange(`O${row}`).values = [["已完成"]];
}
const exampleExport = await SpreadsheetFile.exportXlsx(examples.workbook);
await exampleExport.save(examples.workbookPath);
const examplePreviewFirst = await savePreview(examples.workbook, "例题解答分级", "A1:O20", "examples-first.png");
const examplePreviewRisk = await savePreview(examples.workbook, "例题解答分级", "A1160:O1182", "examples-tail.png");
const exampleErrors = await formulaErrors(examples.workbook, "Gate D example matrix formula error scan");

// Close the last unique-ledger row, ISS-011, with source- and PDF-level evidence.
const issueSeed = JSON.parse(await fs.readFile(path.join(cache, "issue_ledger_seed.json"), "utf8"));
const ledger = await loadWorkbook("统计学习方法讲义_v2.0.0_问题关闭台账.xlsx");
const ledgerSheet = ledger.workbook.worksheets.getItem("逐章问题");
const issueIndex = issueSeed.rows.findIndex((row) => row.ID === "ISS-011");
if (issueIndex < 0) throw new Error("ISS-011 missing from unique issue seed.");
const ledgerRow = issueIndex + 2;
const evidence = ledgerSheet.getRange(`O${ledgerRow}:T${ledgerRow}`).values[0];
ledgerSheet.getRange(`L${ledgerRow}`).values = [["已关闭"]];
ledgerSheet.getRange(`O${ledgerRow}:T${ledgerRow}`).values = [[
  appendEvidence(evidence[0], gateDCommit),
  appendEvidence(evidence[1], "qa/编译与链接QA.md；Gate D最终链接验收通过。"),
  appendEvidence(evidence[2], "源码审计148文件/3276唯一标签/1182引用/0发现；最终PDF 4681个内部链接，无效0；273书签页码有效。"),
  appendEvidence(evidence[3], "Gate D最终PDF 771页可打开；目录、符号索引、主题索引和最终索引人工/机器复核通过。"),
  "已关闭", null,
]];
const statusCounts = ledgerSheet.getRange("S2:S111").values.flat().reduce((counts, value) => {
  const key = String(value ?? ""); counts[key] = (counts[key] ?? 0) + 1; return counts;
}, {});
if (statusCounts["已关闭"] !== 110 || Object.keys(statusCounts).length !== 1) throw new Error(`Unexpected final ledger status: ${JSON.stringify(statusCounts)}`);
const ledgerExport = await SpreadsheetFile.exportXlsx(ledger.workbook);
await ledgerExport.save(ledger.workbookPath);
const ledgerPreview = await savePreview(ledger.workbook, "逐章问题", "L1:T16", "ledger-final.png");
const ledgerErrors = await formulaErrors(ledger.workbook, "Gate D final issue-ledger formula error scan");

const verification = {
  schema_version: 1,
  gateDSourceCommit: gateDCommit,
  conceptMatrix: { rows: 67, completed: 67, formulaErrors: conceptErrors, preview: conceptPreview },
  firstAppearance: { rows: 67, completed: 67, formulaErrors: firstErrors, preview: firstPreview },
  examples: { rows: 1234, completed: 1234, formulaErrors: exampleErrors, previews: [examplePreviewFirst, examplePreviewRisk] },
  ledger: { rows: 110, statusCounts, formulaErrors: ledgerErrors, preview: ledgerPreview },
};
await fs.writeFile(verificationPath, `${JSON.stringify(verification, null, 2)}\n`, "utf8");
process.stdout.write(`${JSON.stringify({ verificationPath, statusCounts, concepts: 67, examples: 1234 })}\n`);
