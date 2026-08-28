import fs from "node:fs";

const dumpPath = "D:/Users/ASUS/Desktop/机器学习/v2.7.0/_work/input_read/xlsx/workbook_dump.json";
const dump = JSON.parse(fs.readFileSync(dumpPath, "utf8"));

function normalized(value) {
  if (value === null || value === undefined) return "";
  return String(value).trim();
}

function histogram(rows, columnIndex) {
  const counts = new Map();
  for (const row of rows.slice(1)) {
    const key = normalized(row[columnIndex]) || "(blank)";
    counts.set(key, (counts.get(key) ?? 0) + 1);
  }
  return Object.fromEntries([...counts.entries()].sort((a, b) => b[1] - a[1]));
}

const result = { sheets: [] };
for (const sheet of dump.sheets) {
  const headers = (sheet.values[0] ?? []).map(normalized);
  const summary = {
    name: sheet.name,
    dataRows: Math.max(0, sheet.rows - 1),
    columns: sheet.columns,
    headers,
    categorical: {},
  };
  for (let index = 0; index < headers.length; index += 1) {
    const header = headers[index];
    if (/严重|优先级|结构配对|类别|问题判断/.test(header)) {
      summary.categorical[`${index + 1}:${header}`] = histogram(sheet.values, index);
    }
  }
  result.sheets.push(summary);
}

process.stdout.write(`${JSON.stringify(result, null, 2)}\n`);
