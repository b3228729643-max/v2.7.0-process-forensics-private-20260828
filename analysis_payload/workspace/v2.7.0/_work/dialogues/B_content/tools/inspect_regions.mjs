import { FileBlob, SpreadsheetFile } from "@oai/artifact-tool";

const workbookPath = process.argv[2];
if (!workbookPath) {
  throw new Error("usage: node inspect_regions.mjs <workbook.xlsx>");
}

const input = await FileBlob.load(workbookPath);
const workbook = await SpreadsheetFile.importXlsx(input);
const requests = [
  ["例题索引", "A1:O3"],
  ["知识点索引", "A1:P3"],
  ["定理定义索引", "A1:P3"],
  ["核心推导索引", "A1:R3"],
  ["阅读阻塞残留", "A1:M3"],
  ["章末练习覆盖", "A1:E3"],
  ["全局问题台账", "A1:F32"],
];

for (const [sheetId, range] of requests) {
  const result = await workbook.inspect({
    kind: "region",
    sheetId,
    range,
    tableMaxRows: 40,
    tableMaxCols: 20,
    tableMaxCellChars: 500,
    maxChars: 50000,
  });
  process.stdout.write(`SHEET=${sheetId}\n`);
  process.stdout.write(result.ndjson ?? `${JSON.stringify(result, null, 2)}\n`);
  process.stdout.write("\n");
}
