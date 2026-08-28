import fs from 'node:fs/promises';
import { createRequire } from 'node:module';
const require = createRequire(import.meta.url);
const sharp = require('sharp');

const jobsUrl = new URL('./03_glyph_render_jobs.json', import.meta.url);
const jobs = JSON.parse(await fs.readFile(jobsUrl, 'utf8'));
let rendered = 0;
for (const job of jobs) {
  const info = await sharp(job.input, { density: 72 })
    .png()
    .toFile(job.output);
  if (info.width !== job.width || info.height !== job.height) {
    throw new Error(`Dimension mismatch for ${job.output}: ${info.width}x${info.height}, expected ${job.width}x${job.height}`);
  }
  rendered += 1;
}
process.stdout.write(JSON.stringify({ rendered, expected: jobs.length }, null, 2));
