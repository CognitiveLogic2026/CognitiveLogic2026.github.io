import { chromium } from 'playwright';
import fs from 'node:fs';

const html = fs.readFileSync(
  'digital-presence/index.html', 'utf8'
);

const match = html.match(
  /\/\* Digital Presence: mobile layout containment \*\/[\s\S]*?(?=\s*@media \(max-width: 900px\))/
);

if (!match) {
  throw new Error('CSS patch not found');
}

const browser = await chromium.launch();
const widths = [390, 768, 1024, 1440];
let failed = false;

try {
  for (const width of widths) {
    const page = await browser.newPage({
      viewport: { width, height: 900 }
    });

    await page.goto(
      'https://cognitivelogic.it/digital-presence/',
      { waitUntil: 'domcontentloaded' }
    );

    const before = await page.evaluate(
      () => document.documentElement.scrollWidth
    );

    await page.addStyleTag({ content: match[0] });

    const after = await page.evaluate(
      () => document.documentElement.scrollWidth
    );

    console.log(
      `${width}px: before=${before}, after=${after}`
    );

    if (after > width + 2) failed = true;

    await page.close();
  }
} finally {
  await browser.close();
}

if (failed) process.exitCode = 1;
