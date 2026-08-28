import { FileBlob, SpreadsheetFile } from "@oai/artifact-tool";

const workbookPath = process.argv[2];
if (!workbookPath) {
  throw new Error("usage: node inspect_workbook.mjs <workbook.xlsx>");
}

const input = await FileBlob.load(workbookPath);
const workbook = await SpreadsheetFile.importXlsx(input);
const result = await workbook.inspect({
  kind: "sheet",
  include: "id,name",
  maxChars: 12000,
});

process.stdout.write(result.ndjson ?? `${JSON.stringify(result, null, 2)}\n`);
