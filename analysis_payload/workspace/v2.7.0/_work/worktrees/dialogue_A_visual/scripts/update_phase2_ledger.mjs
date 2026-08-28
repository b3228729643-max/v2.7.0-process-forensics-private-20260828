import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { FileBlob, SpreadsheetFile } from "@oai/artifact-tool";

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const projectRoot = path.resolve(scriptDir, "..");
const workbookPath = path.join(projectRoot, "qa", "统计学习方法讲义_v2.0.0_问题关闭台账.xlsx");
const seedPath = path.join(projectRoot, "qa", "source_cache", "issue_ledger_seed.json");
const verificationPath = path.join(projectRoot, "qa", "source_cache", "phase2_ledger_verification.json");
const previewDir = path.join(projectRoot, "qa", "previews", "phase2_ledger");

function issueId(number) {
  return `ISS-${String(number).padStart(3, "0")}`;
}

function issueRange(first, last) {
  return Array.from({ length: last - first + 1 }, (_, index) => issueId(first + index));
}

const agentAComplete = new Set([
  ...issueRange(1, 3),
  issueId(5),
  issueId(15),
  issueId(16),
  ...issueRange(18, 20),
  ...issueRange(22, 29),
  issueId(31),
  issueId(32),
  issueId(36),
]);
const agentAPartial = new Set([issueId(4), issueId(17), issueId(21), issueId(30), ...issueRange(33, 35)]);
const agentBComplete = new Set(issueRange(37, 69));
const agentCComplete = new Set(issueRange(70, 110));
const globalReview = new Set([issueId(6), issueId(8), issueId(13), issueId(14)]);
const globalInProgress = new Set([issueId(7), ...issueRange(9, 12)]);

const partialReasons = {
  "ISS-004": "正文仍有若干17—36步进阶工程契约；需迁入后置契约附录或进一步压成≤10步数学层。",
  "ISS-017": "第1章已降格5道低风险解析，但仍有14个solution环境；需逐题保留边界/反例后收敛到6—8道完整解析。",
  "ISS-021": "固定步长梯度下降的首读核心已补，但原异常分支长框仍需后移，主体尚未稳定达到≤10行。",
  "ISS-030": "第8章已声明专项边界并链接第17章；IIS推导/算法副本仍待确认第17章承载后删除。",
  "ISS-033": "五节点无泄漏流程已加入；17步交叉验证工程契约仍在正文，待后移到后置契约附录。",
  "ISS-034": "章节侧已放大并补灰度说明；绘图源仍需实/虚线与圆/三角标记的最小补丁。",
  "ISS-035": "23项内容已改名章末项目检查表；其23步进阶实现契约仍保留算法编号并出现孤行，待迁入后置附录。",
  "ISS-007": "固定模板噪声已在代理改写范围内减少，但尚未在Gate A/B合并总册中完成跨章验收。",
  "ISS-009": "高风险页抽查无裁切，但仍存在19—36步小字号工程契约；全书字号门须在Gate C完成。",
  "ISS-010": "全局图样式与若干目标图已改善；99幅图的线型/标记与灰度验收尚未在Gate C完成。",
  "ISS-011": "分册引用已收敛；结构移动后的最终内部链接和书签须在合并总册Gate D检查。",
  "ISS-012": "代理已压缩部分例题并使用三级接口；第1章完整解析数量及全书常规题3—6步要求尚未全部收敛。",
};

function baseRecord() {
  return {
    sourceFile: "",
    sourceLocation: "",
    commit: "",
    evidence: "",
    automated: "",
    manual: "",
    finalStatus: "修改中",
    reason: "",
  };
}

function recordFor(id) {
  const record = baseRecord();
  if (agentAComplete.has(id) || agentAPartial.has(id)) {
    Object.assign(record, {
      sourceFile: "src/讲义源码/合并总册; common/foundation_routes.tex; 第01册章节",
      sourceLocation: `见 logs/subagent_a_handoff.md 的 ${id} 记录`,
      commit: "1633e4d; 09089c5",
      evidence: `Subagent A handoff 与合并提交中的 ${id} 定向修改`,
      automated: "git diff --check; 第1册LuaLaTeX 174页/2694478字节；索引生成",
      manual: "前置页、第10—11章目标页已检查，无裁切；Gate A/B/C/D待最终复核",
    });
    if (agentAComplete.has(id)) record.finalStatus = "待复核";
  } else if (agentBComplete.has(id)) {
    Object.assign(record, {
      sourceFile: "src/讲义源码/第02册章节; 第03册章节",
      sourceLocation: `见 logs/subagent_b_handoff.md 的 ${id} 记录`,
      commit: "85be84a",
      evidence: `Subagent B handoff 与合并提交中的 ${id} 定向修改`,
      automated: "git diff --check; 第2册100页/1633558字节；第3册153页/2405249字节；0条分册未解析引用",
      manual: "决策树、SVM、EM目标页已检查，无裁切；Gate B/C待最终复核",
      finalStatus: "待复核",
    });
  } else if (agentCComplete.has(id)) {
    Object.assign(record, {
      sourceFile: "src/讲义源码/第04册章节; 第05册章节",
      sourceLocation: `见 logs/subagent_c_handoff.md 的 ${id} 记录`,
      commit: "7f701da; 5f2d772",
      evidence: `Subagent C handoff 与合并提交中的 ${id} 定向修改`,
      automated: "git diff --check; 第4册130页/2078564字节；第5册228页/3549607字节；0条分册未解析引用",
      manual: "SVD、Gibbs、LDA、PageRank与评价协议目标页已检查；Gate B/C待最终复核",
      finalStatus: "待复核",
    });
  } else if (globalReview.has(id) || globalInProgress.has(id)) {
    Object.assign(record, {
      sourceFile: "src/讲义源码/common/statlearnbook.sty; 全书章节; build_v2.0.0.ps1",
      sourceLocation: `DEC-0006/DEC-0007 与 ${id} 全局接口`,
      commit: "bb70224; c9c4b60",
      evidence: `公共样式、状态、索引或构建接口中的 ${id} 修改`,
      automated: "9页公共模板通过；五册定向构建通过；顶层构建DryRun与路径护栏通过",
      manual: "公共模板9页及分册高风险目标页已检查；合并总册质控门待完成",
    });
    if (globalReview.has(id)) record.finalStatus = "待复核";
  }
  record.reason = partialReasons[id] ?? "";
  return record;
}

await fs.mkdir(previewDir, { recursive: true });
const seed = JSON.parse(await fs.readFile(seedPath, "utf8"));
if (!Array.isArray(seed.rows) || seed.rows.length !== 110) {
  throw new Error("The cached issue seed must contain exactly 110 rows.");
}

const statusCounts = { 待复核: 0, 修改中: 0 };
const bodyValues = seed.rows.map((row) => {
  const record = recordFor(row.ID);
  if (!(record.finalStatus in statusCounts)) {
    throw new Error(`Unexpected phase-2 status for ${row.ID}: ${record.finalStatus}`);
  }
  statusCounts[record.finalStatus] += 1;
  return [
    record.sourceFile,
    record.sourceLocation,
    record.commit,
    record.evidence,
    record.automated,
    record.manual,
    record.finalStatus,
    record.reason,
  ];
});
const originalStatusValues = bodyValues.map((row) => [row[6]]);

const input = await FileBlob.load(workbookPath);
const workbook = await SpreadsheetFile.importXlsx(input);
const sheet = workbook.worksheets.getItem("逐章问题");
sheet.getRange("L2:L111").values = originalStatusValues;
sheet.getRange("M2:T111").values = bodyValues;

const exportBlob = await SpreadsheetFile.exportXlsx(workbook);
await exportBlob.save(workbookPath);

const previewTop = await workbook.render({ sheetName: "逐章问题", range: "A1:T24", scale: 1, format: "png" });
await fs.writeFile(path.join(previewDir, "rows-001-023.png"), new Uint8Array(await previewTop.arrayBuffer()));
const previewTail = await workbook.render({ sheetName: "逐章问题", range: "A100:T111", scale: 1, format: "png" });
await fs.writeFile(path.join(previewDir, "rows-099-110.png"), new Uint8Array(await previewTail.arrayBuffer()));

const keyRange = await workbook.inspect({
  kind: "table",
  sheetId: "逐章问题",
  range: "A1:T12",
  include: "values,formulas",
  tableMaxRows: 12,
  tableMaxCols: 20,
  maxChars: 12000,
});
const formulaErrors = await workbook.inspect({
  kind: "match",
  searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A",
  options: { useRegex: true, maxResults: 100 },
  summary: "phase-2 issue ledger formula error scan",
  maxChars: 4000,
});
await fs.writeFile(
  verificationPath,
  `${JSON.stringify(
    {
      workbookPath,
      issueRows: seed.rows.length,
      statusCounts,
      partialIssueIds: Object.keys(partialReasons),
      keyRange: keyRange.ndjson ?? "",
      formulaErrors: formulaErrors.ndjson ?? "",
      previews: [
        path.join(previewDir, "rows-001-023.png"),
        path.join(previewDir, "rows-099-110.png"),
      ],
    },
    null,
    2,
  )}\n`,
  "utf8",
);

process.stdout.write(`${JSON.stringify({ workbookPath, statusCounts, verificationPath })}\n`);
