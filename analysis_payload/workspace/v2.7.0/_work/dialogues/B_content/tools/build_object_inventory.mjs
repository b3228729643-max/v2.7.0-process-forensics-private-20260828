import fs from "node:fs/promises";
import path from "node:path";
import { FileBlob, SpreadsheetFile } from "@oai/artifact-tool";

const [workbookPath, outputDir] = process.argv.slice(2);
if (!workbookPath || !outputDir) {
  throw new Error("usage: node build_object_inventory.mjs <workbook.xlsx> <output-dir>");
}

const input = await FileBlob.load(workbookPath);
const workbook = await SpreadsheetFile.importXlsx(input);

const specs = [
  { sheet: "全局问题台账", range: "A1:F32", domain: "GLOBAL_ISSUE" },
  { sheet: "阅读阻塞残留", range: "A1:M936", domain: "READING_BLOCKER" },
  { sheet: "例题索引", range: "A1:O67", domain: "EXAMPLE" },
  { sheet: "知识点索引", range: "A1:P597", domain: "KNOWLEDGE" },
  { sheet: "定理定义索引", range: "A1:P193", domain: "THEOREM_DEFINITION" },
  { sheet: "核心推导索引", range: "A1:R60", domain: "DERIVATION" },
  { sheet: "章末练习覆盖", range: "A1:E38", domain: "EXERCISE_CHAPTER_COVERAGE" },
];

const priorityExamples = new Set(["11.1", "12.2", "24.1", "29.1", "33.2"]);

function stringValue(value) {
  if (value === null || value === undefined) return "";
  return String(value).replaceAll("\r\n", "\n");
}

function recordFrom(headers, row) {
  return Object.fromEntries(headers.map((header, index) => [stringValue(header), row[index]]));
}

function taskId(domain, record, ordinal) {
  const padded = String(ordinal).padStart(4, "0");
  if (domain === "READING_BLOCKER") return `M02-RBL-${padded}`;
  if (domain === "EXAMPLE") return `M04-EXM-${stringValue(record["例题号"])}`;
  if (domain === "KNOWLEDGE") return `M04-KN-${stringValue(record["知识点ID"])}`;
  if (domain === "THEOREM_DEFINITION") {
    return `M05-${stringValue(record["类型"])}-${stringValue(record["标签"]) || padded}`;
  }
  if (domain === "DERIVATION") return `M05-DER-${stringValue(record["推导编号"])}`;
  if (domain === "EXERCISE_CHAPTER_COVERAGE") {
    return `M06-CH-${String(record["章节"]).padStart(2, "0")}-COVERAGE`;
  }
  return `GLOBAL-${String(ordinal).padStart(3, "0")}`;
}

function currentState(domain, record) {
  if (domain === "READING_BLOCKER") {
    return "HISTORICAL_R130_ACCEPTED_CURRENT_SOURCE_UNCHECKED";
  }
  if (domain === "EXAMPLE" && priorityExamples.has(stringValue(record["例题号"]))) {
    return "IN_PROGRESS_B_EXM_P01";
  }
  if (domain === "GLOBAL_ISSUE") {
    const category = stringValue(record["类别"]);
    if (["视觉字号", "版面利用", "章首版式", "PDF可访问性", "版本与发布"].includes(category)) {
      return "ROUTE_ONLY_OUT_OF_SCOPE";
    }
  }
  return "UNREVIEWED_CURRENT_SOURCE";
}

function mapRecord(spec, record, ordinal) {
  const sourceFile = record["源码文件"] ?? record["位置"] ?? "";
  const sourceLine = record["源码行"] ?? "";
  const pdfPage = record["PDF物理页"] ?? "";
  const severity = record["问题严重度"] ?? record["优先级"] ?? "";
  const issue = record["问题判断"] ?? record["内部问题描述"] ?? record["问题"] ?? record["结构配对"] ?? "";
  const route = record["推荐解题路线"] ?? record["处理建议"] ?? record["优化版讲解"] ?? record["优化后的证明路线"] ?? record["优化版推导路线"] ?? record["修复动作"] ?? "";
  const key = record["例题号"] ?? record["知识点ID"] ?? record["标签"] ?? record["推导编号"] ?? record["检查对象"] ?? record["章节"] ?? ordinal;
  return {
    task_id: taskId(spec.domain, record, ordinal),
    domain: spec.domain,
    source_sheet: spec.sheet,
    sheet_row: ordinal + 1,
    object_key: stringValue(key),
    source_file: stringValue(sourceFile),
    source_line: stringValue(sourceLine),
    pdf_page: stringValue(pdfPage),
    severity: stringValue(severity),
    issue: stringValue(issue),
    route: stringValue(route),
    current_state: currentState(spec.domain, record),
    evidence_ref: "统计学习方法讲义_v2.6.0_全量索引库.xlsx",
  };
}

function csvEscape(value) {
  const text = stringValue(value);
  return /[",\n]/.test(text) ? `"${text.replaceAll('"', '""')}"` : text;
}

const inventory = [];
const sheetStats = {};

for (const spec of specs) {
  const worksheet = workbook.worksheets.getItem(spec.sheet);
  const values = worksheet.getRange(spec.range).values;
  const headers = values[0].map(stringValue);
  const rows = values.slice(1).filter((row) => row.some((cell) => cell !== null && cell !== undefined && cell !== ""));
  sheetStats[spec.sheet] = rows.length;
  rows.forEach((row, index) => inventory.push(mapRecord(spec, recordFrom(headers, row), index + 1)));
}

const columns = [
  "task_id",
  "domain",
  "source_sheet",
  "sheet_row",
  "object_key",
  "source_file",
  "source_line",
  "pdf_page",
  "severity",
  "issue",
  "route",
  "current_state",
  "evidence_ref",
];

const duplicateTaskIds = [...inventory.reduce((map, row) => {
  map.set(row.task_id, (map.get(row.task_id) ?? 0) + 1);
  return map;
}, new Map()).entries()].filter(([, count]) => count > 1);

const exerciseTotal = inventory
  .filter((row) => row.domain === "EXERCISE_CHAPTER_COVERAGE")
  .reduce((sum, row) => {
    const worksheet = workbook.worksheets.getItem("章末练习覆盖");
    const count = worksheet.getRange(`C${row.sheet_row}:C${row.sheet_row}`).values[0][0];
    return sum + Number(count || 0);
  }, 0);

const summary = {
  generated_at: new Date().toISOString(),
  workbook: workbookPath,
  total_inventory_rows: inventory.length,
  sheet_stats: sheetStats,
  exercise_total_from_chapter_coverage: exerciseTotal,
  priority_examples: [...priorityExamples],
  duplicate_task_ids: duplicateTaskIds,
  status_counts: Object.fromEntries([...inventory.reduce((map, row) => {
    map.set(row.current_state, (map.get(row.current_state) ?? 0) + 1);
    return map;
  }, new Map()).entries()]),
};

await fs.mkdir(outputDir, { recursive: true });
const csv = [columns.join(","), ...inventory.map((row) => columns.map((column) => csvEscape(row[column])).join(","))].join("\r\n") + "\r\n";
await fs.writeFile(path.join(outputDir, "B_OBJECT_INVENTORY.csv"), csv, "utf8");
await fs.writeFile(path.join(outputDir, "B_OBJECT_SUMMARY.json"), `${JSON.stringify(summary, null, 2)}\n`, "utf8");

process.stdout.write(`${JSON.stringify(summary, null, 2)}\n`);
