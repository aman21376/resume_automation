const { chromium } = require('playwright');
const path = require('path');
const [, , inputPath, outputPath] = process.argv;

(async () => {
  const browser = await chromium.launch({ executablePath: process.env.CHROME_PATH || '/opt/pw-browsers/chromium-1194/chrome-linux/chrome' });
  const page = await browser.newPage({ viewport: { width: 794, height: 1123 }, deviceScaleFactor: 2 });
  await page.goto('file://' + path.resolve(inputPath));
  await page.screenshot({ path: path.resolve(outputPath), fullPage: true });
  await browser.close();
})();
