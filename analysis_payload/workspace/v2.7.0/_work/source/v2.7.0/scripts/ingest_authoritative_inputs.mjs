import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { FileBlob, SpreadsheetFile } from "@oai/artifact-tool";

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const projectRoot = path.resolve(scriptDir, "..");
const workspaceRoot = path.resolve(projectRoot, "..");
const sourceWorkbook = path.join(workspaceRoot, "统计学习方法讲义_v1.9.0_全书审计工作簿.xlsx");
const sourceReport = path.join(workspaceRoot, "统计学习方法讲义_v1.9.0_全量审校与重构方案.md");
const cacheDir = path.join(projectRoot, "qa", "source_cache");
const previewDir = path.join(projectRoot, "qa", "previews", "source_workbook");

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

function safeName(value) {
  return value.replace(/[<>:"/\\|?*\x00-\x1f]/g, "_");
}

function parseReport(text) {
  const lines = text.split(/\r?\n/);
  const sections = [];
  let current = { level: 0, title: "前言", startLine: 1, lines: [] };
  for (let index = 0; index < lines.length; index += 1) {
    const match = /^(#{1,6})\s+(.+?)\s*$/.exec(lines[index]);
    if (match) {
      current.endLine = index;
      current.text = current.lines.join("\n").trim();
      delete current.lines;
      sections.push(current);
      current = {
        level: match[1].length,
        title: match[2],
        startLine: index + 1,
        lines: [],
      };
    } else {
      current.lines.push(lines[index]);
    }
  }
  current.endLine = lines.length;
  current.text = current.lines.join("\n").trim();
  delete current.lines;
  sections.push(current);
  const issueIds = [...new Set(text.match(/ISS-\d{3}/g) ?? [])].sort();
  return {
    source: sourceReport,
    lineCount: lines.length,
    charCount: text.length,
    issueIds,
    sections,
  };
}

await fs.mkdir(cacheDir, { recursive: true });
await fs.mkdir(previewDir, { recursive: true });

const input = await FileBlob.load(sourceWorkbook);
const workbook = await SpreadsheetFile.importXlsx(input);
const sheets = workbook.worksheets.items;
const workbookCache = {
  source: sourceWorkbook,
  parsedAtUtc: new Date().toISOString(),
  sheets: [],
};

for (let index = 0; index < sheets.length; index += 1) {
  const sheet = sheets[index];
  const used = sheet.getUsedRange(true) ?? sheet.getRange("A1");
  const values = used.values ?? [];
  const formulas = used.formulas ?? [];
  const rowCount = values.length;
  const columnCount = values.reduce((maximum, row) => Math.max(maximum, row?.length ?? 0), 0);
  const previewRows = Math.max(1, Math.min(rowCount || 1, 40));
  const previewColumns = Math.max(1, Math.min(columnCount || 1, 20));
  const previewRange = `A1:${columnName(previewColumns)}${previewRows}`;
  let styleNdjson = "";
  try {
    const style = await workbook.inspect({
      kind: "computedStyle",
      sheetId: sheet.name,
      range: `A1:${columnName(previewColumns)}${Math.min(previewRows, 4)}`,
      maxChars: 3000,
    });
    styleNdjson = style.ndjson ?? "";
  } catch (error) {
    styleNdjson = `STYLE_INSPECT_FAILED: ${error?.message ?? String(error)}`;
  }
  const preview = await workbook.render({
    sheetName: sheet.name,
    range: previewRange,
    scale: 1,
    format: "png",
  });
  const previewPath = path.join(previewDir, `${String(index + 1).padStart(2, "0")}_${safeName(sheet.name)}.png`);
  await fs.writeFile(previewPath, new Uint8Array(await preview.arrayBuffer()));
  workbookCache.sheets.push({
    index,
    name: sheet.name,
    rowCount,
    columnCount,
    previewRange,
    previewPath,
    styleNdjson,
    values,
    formulas,
  });
}

const reportText = await fs.readFile(sourceReport, "utf8");
const reportCache = parseReport(reportText);
await fs.writeFile(
  path.join(cacheDir, "workbook_v1.9.0.json"),
  `${JSON.stringify(workbookCache, null, 2)}\n`,
  "utf8",
);
await fs.writeFile(
  path.join(cacheDir, "report_v1.9.0.json"),
  `${JSON.stringify(reportCache, null, 2)}\n`,
  "utf8",
);
await fs.writeFile(
  path.join(cacheDir, "ingest_summary.json"),
  `${JSON.stringify(
    {
      workbook: sourceWorkbook,
      report: sourceReport,
      sheetCount: workbookCache.sheets.length,
      sheets: workbookCache.sheets.map(({ name, rowCount, columnCount, previewRange, previewPath }) => ({
        name,
        rowCount,
        columnCount,
        previewRange,
        previewPath,
      })),
      reportLineCount: reportCache.lineCount,
      reportSectionCount: reportCache.sections.length,
      reportIssueIds: reportCache.issueIds,
    },
    null,
    2,
  )}\n`,
  "utf8",
);

process.stdout.write(
  `${JSON.stringify({
    sheetCount: workbookCache.sheets.length,
    sheets: workbookCache.sheets.map(({ name, rowCount, columnCount }) => ({ name, rowCount, columnCount })),
    reportLineCount: reportCache.lineCount,
    reportSections: reportCache.sections.length,
    reportIssueIds: reportCache.issueIds.length,
  })}\n`,
);

