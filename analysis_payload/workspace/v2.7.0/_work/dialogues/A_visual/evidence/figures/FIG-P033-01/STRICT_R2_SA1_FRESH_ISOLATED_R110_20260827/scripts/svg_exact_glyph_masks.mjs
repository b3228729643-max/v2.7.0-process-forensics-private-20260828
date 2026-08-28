import fs from 'fs';
import path from 'path';
import { createRequire } from 'module';
const require = createRequire(import.meta.url);
const { chromium } = require(String.raw`C:\Users\ASUS\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\node_modules\playwright`);

const root = String.raw`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P033-01\STRICT_R2_SA1_FRESH_ISOLATED_R110_20260827`;
const svgPath = path.join(root, 'tmp', 'page29.svg');
const outDir = path.join(root, 'payload', 'vector_selectors');
fs.mkdirSync(outDir, {recursive: true});

const browser = await chromium.launch({
  headless: true,
  executablePath: String.raw`C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe`,
});
const context = await browser.newContext({
  viewport: {width: 596, height: 842},
  deviceScaleFactor: 300 / 72,
});
const page = await context.newPage();
await page.setContent(fs.readFileSync(svgPath, 'utf8'), {waitUntil: 'load'});
await page.evaluate(() => {
  const svg = document.querySelector('svg');
  svg.style.width = '595.276px';
  svg.style.height = '841.89px';
  svg.style.display = 'block';
  document.body.style.margin = '0';
  document.body.style.background = 'transparent';
});

const uses = await page.evaluate(() => {
  const svg = document.querySelector('svg');
  const sr = svg.getBoundingClientRect();
  return [...svg.querySelectorAll('use')].map((el, index) => {
    const r = el.getBoundingClientRect();
    return {index, x0: r.left - sr.left, top: r.top - sr.top, x1: r.right - sr.left, bottom: r.bottom - sr.top};
  });
});
if (uses.length !== 720) throw new Error(`Expected 720 SVG glyph uses, found ${uses.length}`);
const selected = uses.filter(x => x.top >= 455 && x.bottom <= 660 && x.x0 >= 50 && x.x1 <= 535);
if (selected.length !== 85) throw new Error(`Expected 85 visible figure+caption glyph uses, found ${selected.length}`);

const metadata = [];
for (const item of selected) {
  const clip = {
    x: Math.max(0, item.x0 - 2),
    y: Math.max(0, item.top - 2),
    width: Math.min(595.276, item.x1 + 2) - Math.max(0, item.x0 - 2),
    height: Math.min(841.89, item.bottom + 2) - Math.max(0, item.top - 2),
  };
  await page.evaluate((targetIndex) => {
    const svg = document.querySelector('svg');
    for (const el of svg.querySelectorAll('*')) {
      if (!el.closest('defs')) el.style.visibility = 'hidden';
    }
    const target = svg.querySelectorAll('use')[targetIndex];
    target.style.visibility = 'visible';
  }, item.index);
  const filename = `U${String(item.index).padStart(4, '0')}.png`;
  const buffer = await page.screenshot({clip, omitBackground: true, animations: 'disabled'});
  fs.writeFileSync(path.join(outDir, filename), buffer);
  metadata.push({...item, clip, filename});
}
await browser.close();
fs.writeFileSync(path.join(outDir, 'vector_selector_metadata.json'), JSON.stringify({
  source_svg: svgPath,
  source_pdf: String.raw`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r110_fullbook\main_full.pdf`,
  physical_page: 29,
  svg_use_count: uses.length,
  selected_use_count: selected.length,
  device_scale_factor: 300 / 72,
  purpose: 'Per-glyph vector isolation selector; final raw mask pixels are taken only from the official Poppler 300 dpi raster.',
  items: metadata,
}, null, 2));
process.stdout.write(JSON.stringify({svgUseCount: uses.length, selectedUseCount: selected.length, output: outDir}));
