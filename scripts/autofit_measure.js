// Measures rendered content height for an HTML string at A4 width (96dpi),
// used by autofit_resume.py to decide how much to scale content to fill
// the page. Usage: node autofit_measure.js <html_file>
const { chromium } = require('playwright');
const path = require('path');
const [, , htmlFile] = process.argv;

(async () => {
  const browser = await chromium.launch({ executablePath: process.env.CHROME_PATH || '/opt/pw-browsers/chromium-1194/chrome-linux/chrome' });
  const page = await browser.newPage({ viewport: { width: 794, height: 1123 } });
  await page.goto('file://' + path.resolve(htmlFile));
  const height = await page.evaluate(() => document.body.scrollHeight);
  console.log(height);
  await browser.close();
})();
