import fs from 'fs';
import path from 'path';
import { pathToFileURL } from 'url';
import { createRequire } from 'module';
const require = createRequire(import.meta.url);
const { chromium } = require(String.raw`C:\Users\ASUS\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\node_modules\playwright`);

const root = String.raw`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P033-01\STRICT_R2_SA1_FRESH_ISOLATED_R110_20260827`;
const svgPath = path.join(root, 'tmp', 'page29.svg');
const browser = await chromium.launch({headless: true, executablePath: String.raw`C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe`});
const page = await browser.newPage({viewport: {width: 700, height: 900}});
await page.setContent(fs.readFileSync(svgPath, 'utf8'), {waitUntil: 'load'});
const data = await page.evaluate(() => {
  const svg = document.querySelector('svg');
  svg.style.width = '595.276px';
  svg.style.height = '841.89px';
  document.body.style.margin = '0';
  const srect = svg.getBoundingClientRect();
  return [...svg.querySelectorAll('use')].map((el, index) => {
    const r = el.getBoundingClientRect();
    return {
      index,
      href: el.getAttribute('xlink:href') || el.getAttribute('href'),
      x0: r.left - srect.left,
      top: r.top - srect.top,
      x1: r.right - srect.left,
      bottom: r.bottom - srect.top,
    };
  });
});
await browser.close();
fs.writeFileSync(path.join(root, 'tmp', 'svg_use_bboxes.json'), JSON.stringify(data, null, 2));
const selected = data.filter(x => x.top >= 455 && x.bottom <= 660 && x.x0 >= 50 && x.x1 <= 535);
process.stdout.write(JSON.stringify({all: data.length, selected: selected.length, firstSelected: selected.slice(0, 5)}, null, 2));
