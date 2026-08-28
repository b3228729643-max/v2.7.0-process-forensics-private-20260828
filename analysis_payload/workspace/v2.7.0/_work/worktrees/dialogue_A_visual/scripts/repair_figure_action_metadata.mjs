import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { FileBlob, SpreadsheetFile } from "@oai/artifact-tool";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const qa = path.join(root, "qa");
const workbookPath = path.join(qa, "绘图重制矩阵.xlsx");
const manifestPath = path.join(root, "figures", "figure_manifest.csv");
const previewPath = path.join(qa, "previews", "gate_d_artifacts", "figure-actions.png");
const verificationPath = path.join(qa, "source_cache", "gate_d_figure_action_verification.json");

function csvEscape(value) {
  const text = String(value ?? "");
  return /[",\r\n]/.test(text) ? `"${text.replaceAll('"', '""')}"` : text;
}

// Frozen by H1 commit 14a1cf1. All other figure identities are `重绘`.
const h1KeepAndCorrect = new Set([
  "1.1", "2.1", "3.1", "4.1", "5.1", "6.1", "7.1", "8.1", "9.1", "11.1", "13.2", "29.1",
  "30.1", "30.2", "30.3", "30.4", "30.5", "30.6", "30.7", "31.1", "31.4", "31.6", "31.7", "31.8",
  "31.9", "32.4", "32.5", "32.6", "32.8", "32.9", "32.10", "33.1", "33.4", "33.5", "33.8", "35.4",
  "35.5", "36.7", "37.8",
]);

const workbook = await SpreadsheetFile.importXlsx(await FileBlob.load(workbookPath));
const sheet = workbook.worksheets.getItem("绘图重制");
const rows = sheet.getRange("A2:O100").values;
for (let index = 0; index < rows.length; index += 1) {
  const action = h1KeepAndCorrect.has(String(rows[index][0])) ? "保留并校正" : "重绘";
  sheet.getRange(`F${index + 2}`).values = [[action]];
  rows[index][5] = action;
}

const exported = await SpreadsheetFile.exportXlsx(workbook);
await exported.save(workbookPath);
const headers = sheet.getRange("A1:O1").values[0];
await fs.writeFile(
  manifestPath,
  `${[headers, ...rows].map((row) => row.map(csvEscape).join(",")).join("\r\n")}\r\n`,
  "utf8",
);

const preview = await workbook.render({ sheetName: "绘图重制", range: "A1:O18", scale: 1, format: "png" });
await fs.writeFile(previewPath, new Uint8Array(await preview.arrayBuffer()));
const formulaErrors = await workbook.inspect({
  kind: "match",
  searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A",
  options: { useRegex: true, maxResults: 100 },
  summary: "Gate D figure action metadata formula error scan",
  maxChars: 4000,
});
const counts = rows.reduce((result, row) => {
  const key = String(row[5]);
  result[key] = (result[key] ?? 0) + 1;
  return result;
}, {});
if (counts["重绘"] !== 60 || counts["保留并校正"] !== 39 || Object.keys(counts).length !== 2) {
  throw new Error(`unexpected figure action counts: ${JSON.stringify(counts)}`);
}

const result = {
  schema_version: 1,
  rows: rows.length,
  action_counts: counts,
  completed: rows.filter((row) => row[14] === "已完成").length,
  formula_errors: formulaErrors.ndjson ?? "",
  preview: previewPath,
  source_pdf_rebuild_required: false,
  result: "PASS",
};
await fs.writeFile(verificationPath, `${JSON.stringify(result, null, 2)}\n`, "utf8");
console.log(JSON.stringify(result, null, 2));
