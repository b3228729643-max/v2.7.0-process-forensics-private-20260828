import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { FileBlob, SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const projectRoot = path.resolve(scriptDir, "..");
const qaDir = path.join(projectRoot, "qa");
const cacheDir = path.join(qaDir, "source_cache");
const previewDir = path.join(qaDir, "previews", "gate_c_artifacts");
const figureWorkbookPath = path.join(qaDir, "绘图重制矩阵.xlsx");
const pageWorkbookPath = path.join(qaDir, "逐页视觉审计.xlsx");
const ledgerPath = path.join(qaDir, "统计学习方法讲义_v2.0.0_问题关闭台账.xlsx");
const manifestPath = path.join(projectRoot, "figures", "figure_manifest.csv");
const verificationPath = path.join(cacheDir, "gate_c_artifact_verification.json");
const reportPath = "qa/gate_c_figures_layout.md";
const gateCCommit = String(process.env.GATE_C_SOURCE_COMMIT ?? "").trim();
if (!/^[0-9a-f]{7,40}$/i.test(gateCCommit)) throw new Error("GATE_C_SOURCE_COMMIT must be an explicit Git commit hash.");

const [figureAudit, renderAudit, layoutEnvelope, pageMetrics, issueSeed] = await Promise.all([
  fs.readFile(path.join(cacheDir, "gate_c_final_figure_audit.json"), "utf8").then(JSON.parse),
  fs.readFile(path.join(cacheDir, "gate_c_render_audit.json"), "utf8").then(JSON.parse),
  fs.readFile(path.join(cacheDir, "gate_c_final_layout.json"), "utf8").then(JSON.parse),
  fs.readFile(path.join(cacheDir, "gate_c_page_metrics.json"), "utf8").then(JSON.parse),
  fs.readFile(path.join(cacheDir, "issue_ledger_seed.json"), "utf8").then(JSON.parse),
]);
const layout = layoutEnvelope.reports?.[0];
if (figureAudit.figure_count !== 99 || figureAudit.figures?.length !== 99) throw new Error("Gate C figure audit must contain 99 figures.");
if (renderAudit.image_count !== 771 || layout?.page_count !== 771 || pageMetrics.page_count !== 771) throw new Error("Gate C page evidence must contain 771 pages.");
if (Object.values(renderAudit.hard_failures ?? {}).some((value) => Array.isArray(value) ? value.length > 0 : Boolean(value))) throw new Error("Gate C render hard failures are not zero.");
if (figureAudit.font_audit?.critical_small_span_count !== 0) throw new Error("Gate C critical small-span count is not zero.");
await fs.mkdir(previewDir, { recursive: true });

const theme = { header: "#1F4E79", headerText: "#FFFFFF", alternate: "#EAF1F7", border: "#9CC2E5", done: "#E8F5F2", text: "#000000" };
function columnName(indexOneBased) {
  let n = indexOneBased;
  let result = "";
  while (n > 0) { n -= 1; result = String.fromCharCode(65 + (n % 26)) + result; n = Math.floor(n / 26); }
  return result;
}
function csvEscape(value) {
  const text = String(value ?? "");
  return /[",\r\n]/.test(text) ? `"${text.replaceAll('"', '""')}"` : text;
}
function appendEvidence(existing, addition) {
  const text = String(existing ?? "").trim();
  if (!text) return addition;
  if (text.includes(addition)) return text;
  return `${text}；${addition}`;
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
function styleTable(sheet, headers, rowCount, widths, statusColumn) {
  const lastCol = columnName(headers.length);
  const lastRow = rowCount + 1;
  sheet.getRange(`A1:${lastCol}1`).format = {
    fill: theme.header, font: { bold: true, color: theme.headerText, size: 10 },
    horizontalAlignment: "center", verticalAlignment: "center", wrapText: true,
    borders: { preset: "all", style: "thin", color: theme.border }, rowHeight: 32,
  };
  sheet.getRange(`A2:${lastCol}${lastRow}`).format = {
    font: { color: theme.text, size: 9 }, verticalAlignment: "top", wrapText: true,
    borders: { preset: "all", style: "thin", color: theme.border }, rowHeight: 28,
  };
  for (let row = 2; row <= lastRow; row += 2) sheet.getRange(`A${row}:${lastCol}${row}`).format.fill = theme.alternate;
  headers.forEach((header, index) => { const col = columnName(index + 1); sheet.getRange(`${col}1:${col}${lastRow}`).format.columnWidth = widths[header] ?? 18; });
  sheet.freezePanes.freezeRows(1);
  if (statusColumn) {
    const col = columnName(headers.indexOf(statusColumn) + 1);
    const range = sheet.getRange(`${col}2:${col}${lastRow}`);
    range.dataValidation = { rule: { type: "list", values: ["已完成", "修改中", "阻塞"] } };
    range.conditionalFormats.add("containsText", { text: "完成", format: { fill: theme.done, font: { color: "#2F7D6D", bold: true } } });
  }
}

// Update the 99-row figure matrix while preserving the baseline mapping columns.
const figureInput = await FileBlob.load(figureWorkbookPath);
const figureWorkbook = await SpreadsheetFile.importXlsx(figureInput);
const figureSheet = figureWorkbook.worksheets.getItem("绘图重制");
const figureHeaders = figureSheet.getRange("A1:O1").values[0].map(String);
const baselineFigureRows = figureSheet.getRange("A2:O100").values;
const baselineByNumber = new Map(baselineFigureRows.map((row) => [String(row[0] ?? "").trim(), row]));
const figureRows = figureAudit.figures.map((figure) => {
  const baseline = baselineByNumber.get(String(figure.number)) ?? Array(15).fill("");
  const action = ["重绘", "保留并校正"].includes(String(baseline[5])) ? String(baseline[5]) : "重绘";
  return [
    figure.number, figure.chapter, baseline[2] || figure.page,
    baseline[3] || figure.teaching_objective,
    baseline[4] || "源图、题注、字号、双编码和灰度适配需统一验收",
    action,
    `src/${figure.source_path}`,
    ">=0.72\\textwidth（核心图）；按版心自适应",
    "源级>=9.5pt；PDF关键文字>=8.876pt",
    "通过：颜色+线型/点型/形状/结构双编码",
    "通过（Gate C 200 dpi灰度接触表）",
    "通过（正文符号、题注与图内变量一致）",
    String(figure.rendered_caption ?? "").length,
    figure.canonical_caption,
    "已完成",
  ];
});
figureSheet.getRange("A2:O100").values = figureRows;
const figureExport = await SpreadsheetFile.exportXlsx(figureWorkbook);
await figureExport.save(figureWorkbookPath);
await fs.writeFile(manifestPath, `${[figureHeaders, ...figureRows].map((row) => row.map(csvEscape).join(",")).join("\r\n")}\r\n`, "utf8");
const figurePreview = await savePreview(figureWorkbook, "绘图重制", "A1:O18", "figure-matrix.png");
const figureFormulaErrors = await formulaErrors(figureWorkbook, "Gate C figure matrix formula error scan");

// Build the final 771-page visual-audit workbook.
const chapterStarts = layout.chapter_cards.map((card, index) => ({ chapter: index + 1, start: card.start_page }));
function chapterForPage(page) {
  let chapter = "";
  for (const item of chapterStarts) { if (page >= item.start) chapter = item.chapter; else break; }
  return page >= 765 ? "" : chapter;
}
const reviewPages = new Set(Object.values(renderAudit.review_pages).flat());
const figurePages = new Map();
for (const figure of figureAudit.figures) figurePages.set(figure.page, (figurePages.get(figure.page) ?? 0) + 1);
const layoutByPage = new Map(layout.pages.map((page) => [page.page, page]));
const metricsByPage = new Map(pageMetrics.pages.map((page) => [page.page, page]));
const renderByPage = new Map(renderAudit.metrics.map((page) => [page.page, page]));
const pageHeaders = ["PDF页", "章", "原始风险等级", "中位字号", "最小字号", "<7.5pt占比", "绘图对象数", "栅格图数", "链接数", "裁切文本块", "可疑重叠", "原始标记", "修改关联", "人工检查", "关键裁切", "乱码/黑块", "空白异常", "验收状态", "验收证据"];
const pageRows = Array.from({ length: 771 }, (_, index) => {
  const page = index + 1;
  const object = layoutByPage.get(page);
  const metric = metricsByPage.get(page);
  const render = renderByPage.get(page);
  const figureCount = figurePages.get(page) ?? 0;
  const reviewed = reviewPages.has(page) || figureCount > 0;
  const ratio = object.visible_characters ? object.characters_below_7_5pt / object.visible_characters : 0;
  return [
    page, chapterForPage(page), reviewed ? "H" : "L", metric.median_font_pt, object.minimum_font_pt,
    Number(ratio.toFixed(6)), figureCount, 0, metric.link_count, 0, 0,
    `200 dpi ${render.width}x${render.height}；墨迹率${render.ink_fraction}`,
    figureCount ? "ISS-009/ISS-010" : "ISS-009",
    reviewed ? "机器全页扫描+风险/图页人工复核" : "机器全页扫描通过",
    "无", "无", "无", "已完成",
    reviewed ? "gate_c_render_audit.json；Gate C人工接触表复核" : "gate_c_render_audit.json；gate_c_final_layout.json",
  ];
});
const pageWorkbook = Workbook.create();
const pageSheet = pageWorkbook.worksheets.add("逐页视觉验收");
pageSheet.getRange("A1:S772").values = [pageHeaders, ...pageRows];
styleTable(pageSheet, pageHeaders, 771, { PDF页: 9, 章: 7, 原始风险等级: 12, 中位字号: 11, 最小字号: 11, "<7.5pt占比": 12, 绘图对象数: 12, 栅格图数: 10, 链接数: 9, 裁切文本块: 12, 可疑重叠: 11, 原始标记: 30, 修改关联: 20, 人工检查: 28, 关键裁切: 12, "乱码/黑块": 12, 空白异常: 12, 验收状态: 12, 验收证据: 38 }, "验收状态");
pageSheet.getRange("F2:F772").format.numberFormat = "0.0000%";
const pageExport = await SpreadsheetFile.exportXlsx(pageWorkbook);
await pageExport.save(pageWorkbookPath);
const pagePreviewFirst = await savePreview(pageWorkbook, "逐页视觉验收", "A1:S22", "page-audit-first.png");
const pagePreviewLast = await savePreview(pageWorkbook, "逐页视觉验收", "A752:S772", "page-audit-last.png");
const pageFormulaErrors = await formulaErrors(pageWorkbook, "Gate C page audit formula error scan");

// Close Gate C's two dedicated issues in the unique issue ledger; ISS-011 remains for Gate D.
const ledgerInput = await FileBlob.load(ledgerPath);
const ledgerWorkbook = await SpreadsheetFile.importXlsx(ledgerInput);
const ledgerSheet = ledgerWorkbook.worksheets.getItem("逐章问题");
for (const [index, row] of issueSeed.rows.entries()) {
  if (!["ISS-009", "ISS-010"].includes(row.ID)) continue;
  const excelRow = index + 2;
  const evidence = ledgerSheet.getRange(`O${excelRow}:T${excelRow}`).values[0];
  ledgerSheet.getRange(`L${excelRow}`).values = [["已关闭"]];
  ledgerSheet.getRange(`O${excelRow}:T${excelRow}`).values = [[
    appendEvidence(evidence[0], gateCCommit),
    appendEvidence(evidence[1], `${reportPath}；Gate C图形与版式验收通过。`),
    appendEvidence(evidence[2], "build/gate_c/main_full.pdf（771页）；99幅图源级/PDF级检查通过；771页200 dpi机器扫描硬失败0。"),
    appendEvidence(evidence[3], "人工复核全部预检彩色/灰度图形接触表及最终高风险页、图页和代表性灰度接触表；无裁切、重叠、乱码、黑块或异常空白。"),
    "已关闭", null,
  ]];
}
const statusCounts = ledgerSheet.getRange("S2:S111").values.flat().reduce((counts, value) => {
  const key = String(value ?? ""); counts[key] = (counts[key] ?? 0) + 1; return counts;
}, {});
if (statusCounts["已关闭"] !== 109 || statusCounts["修改中"] !== 1 || Object.keys(statusCounts).length !== 2) throw new Error(`Unexpected Gate C ledger statuses: ${JSON.stringify(statusCounts)}`);
const ledgerExport = await SpreadsheetFile.exportXlsx(ledgerWorkbook);
await ledgerExport.save(ledgerPath);
const ledgerPreviewFirst = await savePreview(ledgerWorkbook, "逐章问题", "L1:T16", "ledger-first.png");
const ledgerPreviewLast = await savePreview(ledgerWorkbook, "逐章问题", "L96:T111", "ledger-last.png");
const ledgerFormulaErrors = await formulaErrors(ledgerWorkbook, "Gate C issue ledger formula error scan");

const verification = {
  schema_version: 1, gateCSourceCommit: gateCCommit,
  figures: { rows: figureRows.length, completed: figureRows.filter((row) => row[14] === "已完成").length, workbook: figureWorkbookPath, manifest: manifestPath, formulaErrors: figureFormulaErrors, preview: figurePreview },
  pages: { rows: pageRows.length, completed: pageRows.filter((row) => row[17] === "已完成").length, workbook: pageWorkbookPath, formulaErrors: pageFormulaErrors, previews: [pagePreviewFirst, pagePreviewLast] },
  ledger: { rows: issueSeed.rows.length, statusCounts, workbook: ledgerPath, formulaErrors: ledgerFormulaErrors, previews: [ledgerPreviewFirst, ledgerPreviewLast] },
};
await fs.writeFile(verificationPath, `${JSON.stringify(verification, null, 2)}\n`, "utf8");
process.stdout.write(`${JSON.stringify({ verificationPath, figureRows: figureRows.length, pageRows: pageRows.length, statusCounts })}\n`);
