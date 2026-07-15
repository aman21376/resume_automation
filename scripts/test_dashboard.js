const { chromium } = require('playwright');
const path = require('path');
const [, , inputPath, outputPath] = process.argv;

(async () => {
  const browser = await chromium.launch({ executablePath: process.env.CHROME_PATH || '/opt/pw-browsers/chromium-1194/chrome-linux/chrome' });
  const page = await browser.newPage({ viewport: { width: 1200, height: 1400 } });
  const errors = [];
  page.on('console', msg => { if (msg.type() === 'error') errors.push(msg.text()); });
  page.on('pageerror', err => errors.push('PAGEERROR: ' + err.message));
  await page.goto('file://' + path.resolve(inputPath));
  await page.waitForTimeout(300);
  // expand first row
  const firstRow = await page.$('.row-head');
  if (firstRow) await firstRow.click();
  await page.waitForTimeout(300);
  await page.screenshot({ path: path.resolve(outputPath), fullPage: false });
  console.log('Console errors:', JSON.stringify(errors));
  await browser.close();
})();
