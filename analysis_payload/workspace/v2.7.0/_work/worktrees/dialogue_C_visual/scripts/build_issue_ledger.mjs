import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { FileBlob, SpreadsheetFile } from "@oai/artifact-tool";

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const projectRoot = path.resolve(scriptDir, "..");
const workspaceRoot = path.resolve(projectRoot, "..");
const sourceWorkbook = path.join(workspaceRoot, "统计学习方法讲义_v1.9.0_全书审计工作簿.xlsx");
const cachePath = path.join(projectRoot, "qa", "source_cache", "workbook_v1.9.0.json");
const outputWorkbook = path.join(projectRoot, "qa", "统计学习方法讲义_v2.0.0_问题关闭台账.xlsx");
const temporaryWorkbook = path.join(projectRoot, "qa", ".issue_ledger_base.tmp.xlsx");
const previewPath = path.join(projectRoot, "qa", "previews", "issue_closure_ledger.png");
const verificationPath = path.join(projectRoot, "qa", "source_cache", "issue_ledger_verification.json");
const seedPath = path.join(projectRoot, "qa", "source_cache", "issue_ledger_seed.json");

const addedHeaders = [
  "源文件",
  "源代码行/标签",
  "修改提交",
  "修改证据",
  "自动检查",
  "人工检查",
  "最终状态",
  "保留理由",
];
const allowedStatuses = ["未开始", "修改中", "待复核", "已关闭", "保留并说明", "阻塞"];

await fs.mkdir(path.dirname(outputWorkbook), { recursive: true });
await fs.mkdir(path.dirname(previewPath), { recursive: true });
await fs.copyFile(sourceWorkbook, temporaryWorkbook);

try {
  const cache = JSON.parse(await fs.readFile(cachePath, "utf8"));
  const issueCache = cache.sheets.find((sheet) => sheet.name === "逐章问题");
  if (!issueCache || issueCache.rowCount !== 111 || issueCache.columnCount !== 12) {
    throw new Error("Cached 逐章问题 sheet does not match the 110-row/12-column authority baseline.");
  }

  const input = await FileBlob.load(temporaryWorkbook);
  const workbook = await SpreadsheetFile.importXlsx(input);
  const sheet = workbook.worksheets.getItem("逐章问题");
  const lastRow = issueCache.rowCount;
  const headerRange = sheet.getRange("M1:T1");
  const bodyRange = sheet.getRange(`M2:T${lastRow}`);
  const statusRange = sheet.getRange(`S2:S${lastRow}`);

  headerRange.values = [addedHeaders];
  const bodyValues = Array.from({ length: lastRow - 1 }, () => ["", "", "", "", "", "", "未开始", ""]);
  bodyRange.values = bodyValues;

  headerRange.format = {
    fill: "#1F4E79",
    font: { bold: true, color: "#FFFFFF", size: 10 },
    horizontalAlignment: "center",
    verticalAlignment: "center",
    wrapText: true,
    borders: { preset: "all", style: "thin", color: "#6EC1E4" },
  };
  bodyRange.format = {
    font: { color: "#000000", size: 9 },
    verticalAlignment: "top",
    wrapText: true,
    borders: { preset: "all", style: "thin", color: "#6EC1E4" },
  };
  for (let row = 2; row <= lastRow; row += 2) {
    sheet.getRange(`M${row}:T${row}`).format.fill = "#C6E7F3";
  }
  sheet.getRange(`M3:T${lastRow}`).format.rowHeight = 32;
  sheet.getRange(`M1:M${lastRow}`).format.columnWidth = 30;
  sheet.getRange(`N1:N${lastRow}`).format.columnWidth = 22;
  sheet.getRange(`O1:O${lastRow}`).format.columnWidth = 18;
  sheet.getRange(`P1:P${lastRow}`).format.columnWidth = 34;
  sheet.getRange(`Q1:R${lastRow}`).format.columnWidth = 22;
  sheet.getRange(`S1:S${lastRow}`).format.columnWidth = 16;
  sheet.getRange(`T1:T${lastRow}`).format.columnWidth = 30;
  statusRange.dataValidation = { rule: { type: "list", values: allowedStatuses } };
  statusRange.conditionalFormats.deleteAll();
  statusRange.conditionalFormats.add("containsText", {
    text: "已关闭",
    format: { fill: "#E8F5F2", font: { color: "#2F7D6D", bold: true } },
  });
  statusRange.conditionalFormats.add("containsText", {
    text: "阻塞",
    format: { fill: "#FCEBEC", font: { color: "#B23A48", bold: true } },
  });
  statusRange.conditionalFormats.add("containsText", {
    text: "待复核",
    format: { fill: "#FFF7E6", font: { color: "#B7791F", bold: true } },
  });

  const exportBlob = await SpreadsheetFile.exportXlsx(workbook);
  await exportBlob.save(outputWorkbook);

  const preview = await workbook.render({
    sheetName: "逐章问题",
    range: "A1:T24",
    scale: 1,
    format: "png",
  });
  await fs.writeFile(previewPath, new Uint8Array(await preview.arrayBuffer()));

  const keyRange = await workbook.inspect({
    kind: "table",
    sheetId: "逐章问题",
    range: "A1:T8",
    include: "values,formulas",
    tableMaxRows: 8,
    tableMaxCols: 20,
    maxChars: 8000,
  });
  const formulaErrors = await workbook.inspect({
    kind: "match",
    searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A",
    options: { useRegex: true, maxResults: 100 },
    summary: "issue ledger formula error scan",
    maxChars: 4000,
  });
  const seedRows = issueCache.values.slice(1).map((row) => {
    const original = Object.fromEntries(issueCache.values[0].map((header, index) => [String(header), row[index] ?? ""]));
    return {
      ...original,
      源文件: "",
      "源代码行/标签": "",
      修改提交: "",
      修改证据: "",
      自动检查: "",
      人工检查: "",
      最终状态: "未开始",
      保留理由: "",
    };
  });
  await fs.writeFile(
    seedPath,
    `${JSON.stringify({ sourceSheet: "逐章问题", rowCount: seedRows.length, rows: seedRows }, null, 2)}\n`,
    "utf8",
  );
  await fs.writeFile(
    verificationPath,
    `${JSON.stringify(
      {
        outputWorkbook,
        sourceRowCount: issueCache.rowCount - 1,
        addedHeaders,
        allowedStatuses,
        keyRange: keyRange.ndjson ?? "",
        formulaErrors: formulaErrors.ndjson ?? "",
        previewPath,
      },
      null,
      2,
    )}\n`,
    "utf8",
  );
  process.stdout.write(
    `${JSON.stringify({ outputWorkbook, issueRows: seedRows.length, addedHeaders, previewPath })}\n`,
  );
} finally {
  await fs.rm(temporaryWorkbook, { force: true });
}
