import fs from "node:fs/promises";
import path from "node:path";
import { FileBlob, SpreadsheetFile } from "@oai/artifact-tool";

const inputPath = "D:/Users/ASUS/Desktop/机器学习/v2.7.0/统计学习方法讲义_v2.7.0_Codex_Goal执行包_固定工作目录与完整交付版/02_索引与优化材料/统计学习方法讲义_v2.6.0_全量索引库.xlsx";
const outputDir = "D:/Users/ASUS/Desktop/机器学习/v2.7.0/_work/input_read/xlsx";
await fs.mkdir(outputDir, { recursive: true });

const workbook = await SpreadsheetFile.importXlsx(await FileBlob.load(inputPath));
const sheets = workbook.worksheets.items;
const dump = { inputPath, sheets: [] };

function columnName(oneBasedColumn) {
  let value = oneBasedColumn;
  let result = "";
  while (value > 0) {
    value -= 1;
    result = String.fromCharCode(65 + (value % 26)) + result;
    value = Math.floor(value / 26);
  }
  return result || "A";
}

for (let index = 0; index < sheets.length; index += 1) {
  const sheet = sheets[index];
  const used = sheet.getUsedRange();
  const values = used ? used.values : [];
  const formulas = used ? used.formulas : [];
  let nonempty = 0;
  let formulaCount = 0;
  for (let r = 0; r < values.length; r += 1) {
    for (let c = 0; c < (values[r]?.length ?? 0); c += 1) {
      const value = values[r][c];
      if (value !== null && value !== undefined && value !== "") nonempty += 1;
      const formula = formulas?.[r]?.[c];
      if (typeof formula === "string" && formula.startsWith("=")) formulaCount += 1;
    }
  }
  dump.sheets.push({
    index,
    name: sheet.name,
    rows: values.length,
    columns: values.reduce((m, row) => Math.max(m, row?.length ?? 0), 0),
    nonempty,
    formulaCount,
    values,
    formulas,
  });

  const safeName = `${String(index + 1).padStart(2, "0")}_${sheet.name.replace(/[<>:"/\\|?*]+/g, "_")}`;
  const previewRows = Math.max(1, Math.min(values.length, 40));
  const previewColumns = Math.max(1, Math.min(values.reduce((m, row) => Math.max(m, row?.length ?? 0), 0), 18));
  const previewRange = `A1:${columnName(previewColumns)}${previewRows}`;
  try {
    const preview = await workbook.render({ sheetName: sheet.name, range: previewRange, scale: 1, format: "png" });
    await fs.writeFile(path.join(outputDir, `${safeName}.png`), new Uint8Array(await preview.arrayBuffer()));
    dump.sheets[index].previewRange = previewRange;
  } catch (error) {
    dump.sheets[index].previewRange = previewRange;
    dump.sheets[index].previewError = error instanceof Error ? error.message : String(error);
  }
}

const structural = await workbook.inspect({
  kind: "workbook,sheet,table,definedName,drawing",
  maxChars: 40000,
  tableMaxRows: 8,
  tableMaxCols: 12,
  tableMaxCellChars: 120,
});
const errors = await workbook.inspect({
  kind: "match",
  searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A",
  options: { useRegex: true, maxResults: 300 },
  summary: "read-only formula error scan",
  maxChars: 20000,
});

dump.structuralInspection = structural.ndjson;
dump.formulaErrorInspection = errors.ndjson;
await fs.writeFile(path.join(outputDir, "workbook_dump.json"), JSON.stringify(dump, null, 2), "utf8");
await fs.writeFile(path.join(outputDir, "structural_inspection.ndjson"), structural.ndjson ?? "", "utf8");
await fs.writeFile(path.join(outputDir, "formula_error_inspection.ndjson"), errors.ndjson ?? "", "utf8");

console.log(`SHEET_COUNT=${dump.sheets.length}`);
for (const sheet of dump.sheets) {
  console.log(`${sheet.index + 1}\t${sheet.name}\trows=${sheet.rows}\tcols=${sheet.columns}\tnonempty=${sheet.nonempty}\tformulas=${sheet.formulaCount}`);
}
console.log(`DUMP=${path.join(outputDir, "workbook_dump.json")}`);
console.log(`PREVIEW_DIR=${outputDir}`);
console.log(`ERROR_SCAN=${(errors.ndjson ?? "").trim() || "EMPTY"}`);
