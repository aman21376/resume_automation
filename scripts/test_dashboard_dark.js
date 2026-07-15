const { chromium } = require('playwright');
const path = require('path');
const [, , inputPath, outputPath] = process.argv;

(async () => {
  const browser = await chromium.launch({ executablePath: process.env.CHROME_PATH || '/opt/pw-browsers/chromium-1194/chrome-linux/chrome' });
  const page = await browser.newPage({ viewport: { width: 1200, height: 900 }, colorScheme: 'dark' });
  await page.goto('file://' + path.resolve(inputPath));
  await page.waitForTimeout(300);
  await page.screenshot({ path: path.resolve(outputPath), fullPage: false });
  await browser.close();
})();
