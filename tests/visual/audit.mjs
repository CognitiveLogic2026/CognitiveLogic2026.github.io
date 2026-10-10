import { chromium } from 'playwright';
import fs from 'node:fs';

const base = 'https://cognitivelogic.it';
const pages = [
  '/',
  '/index_en.html',
  '/qen-sovereign/',
  '/digital-presence/',
  '/ristorazione.html',
  '/restaurant-assessment/',
  '/hotellerie-assessment/',
  '/international-watch/',
  '/research.html',
  '/osservatorio-bolkestein/'
];

const widths = [390, 768, 1024, 1440];
const results = [];

fs.mkdirSync('visual-report/screenshots', { recursive: true });

const browser = await chromium.launch({ headless: true });

try {
  for (const path of pages) {
    for (const width of widths) {
      const page = await browser.newPage({
        viewport: { width, height: 900 },
        deviceScaleFactor: 1
      });

      const errors = [];
      const failedCSS = [];

      page.on('pageerror', error => {
        errors.push(error.message);
      });

      page.on('response', response => {
        if (
          response.url().split('?')[0].endsWith('.css') &&
          response.status() >= 400
        ) {
          failedCSS.push({
            url: response.url(),
            status: response.status()
          });
        }
      });

      try {
        const response = await page.goto(base + path, {
          waitUntil: 'domcontentloaded',
          timeout: 30000
        });

        const layout = await page.evaluate(() => ({
          viewport: window.innerWidth,
          documentWidth: document.documentElement.scrollWidth,
          bodyWidth: document.body.scrollWidth
        }));

        const overflow = Math.max(
          layout.documentWidth,
          layout.bodyWidth
        ) > layout.viewport + 2;

        const name = (
          path.replace(/[^a-z0-9]/gi, '-') || 'home'
        ).replace(/^-+|-+$/g, '');

        const screenshot =
          `visual-report/screenshots/${name}-${width}.png`;

        await page.screenshot({
          path: screenshot,
          fullPage: true
        });

        results.push({
          path,
          width,
          http: response?.status() ?? 0,
          overflow,
          ...layout,
          failedCSS,
          errors,
          screenshot
        });

        console.log(
          `${path} | ${width}px | HTTP ${response?.status()} | overflow=${overflow}`
        );

      } catch (error) {
        results.push({
          path,
          width,
          error: error.message
        });
        console.log(`ERROR ${path} ${width}: ${error.message}`);
      } finally {
        await page.close();
      }
    }
  }
} finally {
  await browser.close();
}

fs.writeFileSync(
  'visual-report/report.json',
  JSON.stringify(results, null, 2)
);

const problems = results.filter(r =>
  r.error ||
  r.http !== 200 ||
  r.overflow ||
  r.failedCSS?.length ||
  r.errors?.length
);

console.log(`\nChecks: ${results.length}`);
console.log(`Potential problems: ${problems.length}`);

fs.writeFileSync(
  'visual-report/problems.json',
  JSON.stringify(problems, null, 2)
);

if (problems.length) process.exitCode = 1;
